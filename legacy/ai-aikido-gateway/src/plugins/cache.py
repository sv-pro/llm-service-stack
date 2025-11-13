"""
Intelligent response caching plugin.

This plugin adds a two-tier (memory + SQLite) cache in front of LLM providers.
Requests are normalized, hashed into deterministic cache keys, and responses are
persisted with model-aware TTL policies so duplicate prompts skip outbound calls.
"""

from __future__ import annotations

import hashlib
import json
import logging
import sqlite3
import time
from collections import OrderedDict
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

from src.core.context import RequestContext
from src.core.costs import calculate_completion_cost
from src.core.plugin import BasePlugin

logger = logging.getLogger(__name__)


# ============================================================================
# Helpers
# ============================================================================


class LRUCache:
    """Simple LRU cache used as an in-memory hot cache."""

    def __init__(self, max_size: int = 256):
        self.max_size = max_size
        self._store: OrderedDict[str, Dict[str, Any]] = OrderedDict()

    def get(self, key: str) -> Optional[Dict[str, Any]]:
        """Return cached entry if present and not expired."""
        if key not in self._store:
            return None

        entry = self._store[key]
        expires_at = entry.get("expires_at")
        if expires_at and expires_at <= time.time():
            self._store.pop(key, None)
            return None

        self._store.move_to_end(key)
        return entry

    def set(self, key: str, entry: Dict[str, Any], ttl_seconds: int) -> None:
        """Store entry with TTL (per-entry)."""
        if key in self._store:
            self._store.pop(key)

        if len(self._store) >= self.max_size:
            self._store.popitem(last=False)

        expires_at = time.time() + ttl_seconds if ttl_seconds else None
        entry_with_ttl = dict(entry)
        entry_with_ttl["expires_at"] = expires_at
        self._store[key] = entry_with_ttl

    def clear(self) -> None:
        self._store.clear()

    def __len__(self) -> int:
        return len(self._store)


@dataclass
class CacheEntry:
    cache_key: str
    model: str
    response: Dict[str, Any]
    ttl_seconds: int
    created_at: float
    expires_at: float
    estimated_cost: float
    request_signature: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None


class SQLiteCacheBackend:
    """SQLite-backed cache store for persistence."""

    def __init__(self, db_path: Path, max_entries: int = 5000):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self.max_entries = max_entries
        self.conn: Optional[sqlite3.Connection] = None

    def connect(self) -> None:
        if self.conn:
            return

        self.conn = sqlite3.connect(str(self.db_path), check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self._ensure_schema()

    def close(self) -> None:
        if self.conn:
            self.conn.close()
            self.conn = None

    def _ensure_schema(self) -> None:
        assert self.conn is not None
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS cache_entries (
                cache_key TEXT PRIMARY KEY,
                model TEXT NOT NULL,
                request_signature TEXT NOT NULL,
                response_json TEXT NOT NULL,
                ttl_seconds INTEGER NOT NULL,
                created_at REAL NOT NULL,
                expires_at REAL NOT NULL,
                hit_count INTEGER NOT NULL DEFAULT 0,
                estimated_cost REAL NOT NULL DEFAULT 0.0,
                last_accessed REAL,
                metadata TEXT
            )
            """
        )
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_cache_model ON cache_entries(model)"
        )
        self.conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_cache_expires ON cache_entries(expires_at)"
        )
        self.conn.commit()

    def fetch(self, cache_key: str) -> Optional[CacheEntry]:
        assert self.conn is not None
        cursor = self.conn.execute(
            """
            SELECT cache_key, model, response_json, ttl_seconds,
                   created_at, expires_at, estimated_cost, request_signature, metadata
            FROM cache_entries
            WHERE cache_key = ?
            """,
            (cache_key,),
        )
        row = cursor.fetchone()
        if not row:
            return None

        now = time.time()
        if row["expires_at"] <= now:
            self.delete(cache_key)
            return None

        response = json.loads(row["response_json"])
        signature = json.loads(row["request_signature"])
        metadata = {}
        raw_metadata = row["metadata"]
        if raw_metadata:
            try:
                metadata = json.loads(raw_metadata)
            except json.JSONDecodeError:
                logger.warning("Failed to decode cache metadata for key %s", cache_key)
                metadata = {}

        self.conn.execute(
            """
            UPDATE cache_entries
            SET hit_count = hit_count + 1,
                last_accessed = ?
            WHERE cache_key = ?
            """,
            (now, cache_key),
        )
        self.conn.commit()

        return CacheEntry(
            cache_key=cache_key,
            model=row["model"],
            response=response,
            ttl_seconds=row["ttl_seconds"],
            created_at=row["created_at"],
            expires_at=row["expires_at"],
            estimated_cost=row["estimated_cost"],
            request_signature=signature,
        )

    def store(self, entry: CacheEntry) -> None:
        assert self.conn is not None
        metadata_json = json.dumps(entry.metadata or {}, sort_keys=True)
        self.conn.execute(
            """
            INSERT INTO cache_entries (
                cache_key, model, request_signature, response_json,
                ttl_seconds, created_at, expires_at,
                hit_count, estimated_cost, last_accessed, metadata
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, 0, ?, ?, ?)
            ON CONFLICT(cache_key) DO UPDATE SET
                model = excluded.model,
                request_signature = excluded.request_signature,
                response_json = excluded.response_json,
                ttl_seconds = excluded.ttl_seconds,
                created_at = excluded.created_at,
                expires_at = excluded.expires_at,
                estimated_cost = excluded.estimated_cost,
                last_accessed = excluded.last_accessed,
                metadata = excluded.metadata,
                hit_count = 0
            """,
            (
                entry.cache_key,
                entry.model,
                json.dumps(entry.request_signature, sort_keys=True),
                json.dumps(entry.response),
                entry.ttl_seconds,
                entry.created_at,
                entry.expires_at,
                entry.estimated_cost,
                entry.created_at,
                metadata_json,
            ),
        )
        self.conn.commit()
        self._prune_if_needed()

    def delete(self, cache_key: str) -> None:
        assert self.conn is not None
        self.conn.execute(
            "DELETE FROM cache_entries WHERE cache_key = ?", (cache_key,)
        )
        self.conn.commit()

    def clear(self) -> None:
        assert self.conn is not None
        self.conn.execute("DELETE FROM cache_entries")
        self.conn.commit()

    def count(self) -> int:
        assert self.conn is not None
        cursor = self.conn.execute("SELECT COUNT(*) AS total FROM cache_entries")
        row = cursor.fetchone()
        return row["total"] if row else 0

    def _prune_if_needed(self) -> None:
        if self.max_entries <= 0:
            return

        assert self.conn is not None
        total = self.count()
        if total <= self.max_entries:
            return

        excess = total - self.max_entries
        logger.info("Pruning %s cache entries to maintain size", excess)

        self.conn.execute(
            """
            DELETE FROM cache_entries
            WHERE cache_key IN (
                SELECT cache_key
                FROM cache_entries
                ORDER BY expires_at ASC
                LIMIT ?
            )
            """,
            (excess,),
        )
        self.conn.commit()


# ============================================================================
# Cache Plugin
# ============================================================================


class CachePlugin(BasePlugin):
    """Plugin that provides intelligent caching of LLM responses."""

    def __init__(
        self,
        name: str,
        config: Optional[Dict[str, Any]] = None,
        enabled: bool = True,
        priority: int = 10,
    ):
        super().__init__(name, config, enabled, priority)

        self.backend = (self.config.get("backend") or "sqlite").lower()
        self.default_ttl = int(self.config.get("default_ttl_seconds", 3600))
        self.model_ttls: Dict[str, int] = {
            str(model): int(ttl)
            for model, ttl in (self.config.get("model_ttl_seconds") or {}).items()
        }
        self.track_savings = bool(self.config.get("track_savings", True))

        max_memory_entries = int(self.config.get("max_memory_entries", 0) or 0)
        self.hot_cache: Optional[LRUCache] = (
            LRUCache(max_size=max_memory_entries) if max_memory_entries > 0 else None
        )

        self.sqlite_backend: Optional[SQLiteCacheBackend] = None
        if self.backend == "sqlite":
            db_path = Path(self.config.get("db_path", "./data/cache.db"))
            max_storage_entries = int(
                self.config.get("max_storage_entries", 5000) or 0
            )
            self.sqlite_backend = SQLiteCacheBackend(
                db_path=db_path, max_entries=max_storage_entries
            )
        elif self.backend == "memory":
            if not self.hot_cache:
                self.hot_cache = LRUCache(
                    max_size=int(self.config.get("max_entries", 1000))
                )
        else:
            raise ValueError(
                f"Unsupported cache backend '{self.backend}'. "
                "Supported backends: sqlite, memory"
            )

        self.metrics: Dict[str, Any] = {
            "lookups": 0,
            "hits": 0,
            "misses": 0,
            "writes": 0,
            "evictions": 0,
            "expired": 0,
            "estimated_savings": 0.0,
            "last_hit_at": None,
            "last_write_at": None,
        }

    # ------------------------------------------------------------------ utils

    def _get_model_ttl(self, model: Optional[str]) -> int:
        if not model:
            return self.default_ttl
        return self.model_ttls.get(model, self.default_ttl)

    def _normalize_request_payload(self, ctx: RequestContext) -> Dict[str, Any]:
        """Produce a deterministic payload for hashing and storage."""
        request = ctx.request
        if hasattr(request, "model_dump"):
            payload = request.model_dump(exclude_none=True)
        elif isinstance(request, dict):
            payload = deepcopy(request)
        else:
            payload = json.loads(json.dumps(request, default=str))

        model = payload.get("model") or ctx.metadata.get("model")

        from src.api.routes import normalize_payload_for_model

        normalized_payload, changes = normalize_payload_for_model(
            deepcopy(payload), model
        )

        # Keep record for transparency plugins and debugging
        if changes:
            existing = ctx.metadata.setdefault("normalizations", [])
            for change in changes:
                if change not in existing:
                    existing.append(change)

        # Remove fields that should not affect cache identity
        normalized_payload.pop("user", None)

        ctx.metadata["normalized_request_payload"] = normalized_payload
        return normalized_payload

    def _generate_cache_key(self, payload: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """Generate deterministic cache key based on normalized payload."""
        key_material = json.dumps(payload, sort_keys=True, ensure_ascii=True)
        cache_key = hashlib.sha256(key_material.encode("utf-8")).hexdigest()
        return cache_key, payload

    def _record_hit(self, cost: float) -> None:
        self.metrics["hits"] += 1
        self.metrics["lookups"] += 1
        self.metrics["last_hit_at"] = datetime.now(timezone.utc).isoformat()
        if self.track_savings:
            self.metrics["estimated_savings"] += cost

    def _record_miss(self) -> None:
        self.metrics["misses"] += 1
        self.metrics["lookups"] += 1

    def _capture_metadata_snapshot(self, ctx: RequestContext) -> Dict[str, Any]:
        """Capture metadata needed to recreate transparency headers on hits."""
        snapshot: Dict[str, Any] = {}
        retry_summary = ctx.metadata.get("retry_summary")
        if retry_summary:
            snapshot["retry_summary"] = deepcopy(retry_summary)
        cache_type = ctx.metadata.get("cache_type")
        if cache_type:
            snapshot["cache_type"] = cache_type
        return snapshot

    def _rehydrate_cached_metadata(self, ctx: RequestContext, cached_entry: Optional[Dict[str, Any]]) -> None:
        """Restore cached metadata back onto the context for downstream plugins."""
        if not cached_entry:
            return

        metadata = (cached_entry.get("metadata") or {}) if isinstance(cached_entry, dict) else {}
        retry_summary = metadata.get("retry_summary")
        if retry_summary:
            ctx.set_metadata("retry_summary", deepcopy(retry_summary))
            return

        provider = ctx.metadata.get("provider") or metadata.get("provider")
        signature = cached_entry.get("request_signature") or {}
        model = (
            ctx.metadata.get("model")
            or metadata.get("model")
            or signature.get("model")
        )
        if provider and model:
            ctx.set_metadata(
                "retry_summary",
                [
                    {
                        "provider": provider,
                        "model": model,
                        "attempts": 0,
                        "failures": 0,
                        "successful": True,
                        "is_fallback": False,
                        "source": cached_entry.get("source", "cache"),
                    }
                ],
            )

    # ---------------------------------------------------------------- lifecycle

    async def on_startup(self) -> None:
        if self.sqlite_backend:
            self.sqlite_backend.connect()
        logger.info(
            "CachePlugin ready (backend=%s, default_ttl=%ss, hot_cache=%s)",
            self.backend,
            self.default_ttl,
            "enabled" if self.hot_cache is not None else "disabled",
        )

    async def on_shutdown(self) -> None:
        if self.sqlite_backend:
            self.sqlite_backend.close()
        logger.info("CachePlugin stopped")

    # ---------------------------------------------------------------- pipeline

    async def before_request(self, ctx: RequestContext) -> None:
        normalized_payload = self._normalize_request_payload(ctx)
        cache_key, signature = self._generate_cache_key(normalized_payload)
        ctx.set_metadata("cache_key", cache_key)

        lookup_start = time.time()
        cached_entry: Optional[Dict[str, Any]] = None
        entry_model = normalized_payload.get("model")

        if self.hot_cache is not None:
            cached_entry = self.hot_cache.get(cache_key)
            if cached_entry:
                cached_entry = dict(cached_entry)
                cached_entry["source"] = "memory"

        if not cached_entry and self.sqlite_backend:
            sqlite_entry = self.sqlite_backend.fetch(cache_key)
            if sqlite_entry:
                cached_entry = {
                    "response": sqlite_entry.response,
                    "ttl_seconds": sqlite_entry.ttl_seconds,
                    "created_at": sqlite_entry.created_at,
                    "expires_at": sqlite_entry.expires_at,
                    "estimated_cost": sqlite_entry.estimated_cost,
                    "request_signature": sqlite_entry.request_signature,
                    "metadata": sqlite_entry.metadata,
                    "source": "sqlite",
                }
                if self.hot_cache is not None:
                    self.hot_cache.set(
                        cache_key,
                        cached_entry,
                        sqlite_entry.ttl_seconds,
                    )

        lookup_end = time.time()
        ctx.set_metadata("cache_lookup_ms", (lookup_end - lookup_start) * 1000)

        if cached_entry:
            self._record_hit(cached_entry.get("estimated_cost", 0.0))
            logger.debug(
                "Cache hit for key=%s source=%s",
                cache_key[:8],
                cached_entry.get("source", "unknown"),
            )
            ctx.response = cached_entry["response"]
            ctx.set_metadata("cached", True)
            ctx.set_metadata("cache_hit", True)
            ctx.set_metadata("cache_type", "verbatim")
            ctx.set_metadata("cache_backend", cached_entry.get("source", "memory"))
            ctx.set_metadata("cache_created_at", cached_entry.get("created_at"))
            ctx.set_metadata("cache_expires_at", cached_entry.get("expires_at"))
            ctx.set_metadata(
                "cache_ttl_seconds", self._get_model_ttl(entry_model)
            )
            ctx.set_metadata(
                "cache_estimated_savings",
                cached_entry.get("estimated_cost", 0.0),
            )
            self._rehydrate_cached_metadata(ctx, cached_entry)
            ctx.stop_pipeline()
            return

        self._record_miss()
        logger.debug("Cache miss for key=%s", cache_key[:8])
        ctx.set_metadata("cached", False)
        ctx.set_metadata("cache_hit", False)
        ctx.set_metadata("cache_ttl_seconds", self._get_model_ttl(entry_model))

    async def after_response(self, ctx: RequestContext) -> None:
        if ctx.get_metadata("cache_hit"):
            # Served from cache, no need to store again
            return

        if not ctx.response:
            return

        # Don't cache error responses
        if "error" in ctx.response:
            logger.debug("Response contains error, skipping cache")
            return

        if ctx.errors:
            logger.debug(
                "Context has %d prior errors but response succeeded; proceeding to cache",
                len(ctx.errors),
            )

        cache_key = ctx.get_metadata("cache_key")
        if not cache_key:
            return

        normalized_payload = ctx.get_metadata("normalized_request_payload") or {}
        model = normalized_payload.get("model") or ctx.metadata.get("model")
        ttl_seconds = self._get_model_ttl(model)
        if ttl_seconds <= 0:
            return

        usage = ctx.response.get("usage") or {}
        prompt_tokens = usage.get("prompt_tokens") or 0
        completion_tokens = usage.get("completion_tokens") or 0

        estimated_cost = 0.0
        if self.track_savings and model:
            estimated_cost = calculate_completion_cost(model, prompt_tokens, completion_tokens)

        cache_type = ctx.get_metadata("cache_type")
        if not cache_type or cache_type == "api":
            ctx.set_metadata("cache_type", "verbatim")

        now = time.time()
        entry = CacheEntry(
            cache_key=cache_key,
            model=model or "unknown",
            response=ctx.response,
            ttl_seconds=ttl_seconds,
            created_at=now,
            expires_at=now + ttl_seconds if ttl_seconds else now,
            estimated_cost=estimated_cost,
            request_signature=normalized_payload,
            metadata=self._capture_metadata_snapshot(ctx),
        )

        if self.sqlite_backend:
            self.sqlite_backend.store(entry)

        if self.hot_cache is not None:
            self.hot_cache.set(
                cache_key,
                {
                    "response": entry.response,
                    "ttl_seconds": entry.ttl_seconds,
                    "created_at": entry.created_at,
                    "expires_at": entry.expires_at,
                    "estimated_cost": entry.estimated_cost,
                    "request_signature": entry.request_signature,
                    "metadata": entry.metadata,
                    "source": "memory",
                },
                entry.ttl_seconds,
            )

        self.metrics["writes"] += 1
        self.metrics["last_write_at"] = datetime.now(timezone.utc).isoformat()
        ctx.set_metadata("cache_stored", True)

    # ------------------------------------------------------------------ api

    def get_cache_stats(self) -> Dict[str, Any]:
        """Expose cache metrics for API/dashboard."""
        hits = self.metrics["hits"]
        misses = self.metrics["misses"]
        lookups = self.metrics["lookups"]
        hit_rate = (hits / lookups) if lookups else 0.0

        stats = {
            "backend": self.backend,
            "default_ttl_seconds": self.default_ttl,
            "hits": hits,
            "misses": misses,
            "lookups": lookups,
            "hit_rate": hit_rate,
            "writes": self.metrics["writes"],
            "estimated_savings": round(self.metrics["estimated_savings"], 6),
            "last_hit_at": self.metrics["last_hit_at"],
            "last_write_at": self.metrics["last_write_at"],
            "hot_cache_size": len(self.hot_cache) if self.hot_cache else 0,
        }

        if self.sqlite_backend:
            stats["storage_entries"] = self.sqlite_backend.count()
        else:
            stats["storage_entries"] = len(self.hot_cache) if self.hot_cache else 0

        return stats

    def clear_cache(self) -> None:
        """Clear both memory and persistent caches."""
        if self.hot_cache is not None:
            self.hot_cache.clear()
        if self.sqlite_backend:
            self.sqlite_backend.clear()
        self.metrics.update(
            {
                "lookups": 0,
                "hits": 0,
                "misses": 0,
                "writes": 0,
                "estimated_savings": 0.0,
                "last_hit_at": None,
                "last_write_at": None,
            }
        )
