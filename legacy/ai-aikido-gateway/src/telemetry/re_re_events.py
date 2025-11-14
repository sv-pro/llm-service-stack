"""
Telemetry helpers for Re^Re (Reason → Act → Reflect → Re-reason) workflow demos.

Provides:
- WorkflowEvent dataclass describing timeline events
- ReReTelemetryEmitter for publishing events to Redis + SQLite
- ReReTelemetrySession for convenient per-execution emission
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import sqlite3
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import redis.asyncio as redis_async
except ImportError:  # pragma: no cover - optional dependency
    redis_async = None

logger = logging.getLogger(__name__)


def _env_flag(name: str, default: bool = False) -> bool:
    """Parse boolean-like environment variables."""

    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


@dataclass
class WorkflowEvent:
    """Structured telemetry event for the Re^Re loop."""

    event_id: str
    thread_id: str
    intent: str
    phase: str
    status: str
    step_index: int
    node: str
    tool: Optional[str]
    budget_used: float
    remaining_budget: float
    quality_score: Optional[float]
    reasoning_tokens: Optional[int]
    metadata: Dict[str, Any]
    created_at: datetime

    def to_payload(self) -> Dict[str, Any]:
        """Convert dataclass to JSON-serializable payload."""

        payload = asdict(self)
        payload["created_at"] = self.created_at.isoformat()
        return payload


_emitter_logs: List[Dict[str, Any]] = []
_global_emitter_ref: Optional["ReReTelemetryEmitter"] = None


class ReReTelemetryEmitter:
    """Publish workflow events to Redis and persist snapshots to SQLite."""

    def __init__(self) -> None:
        global _global_emitter_ref

        self.enabled = _env_flag("RE_RE_DEMO_ENABLED", False)
        self.channel = os.getenv("RE_RE_TELEMETRY_CHANNEL", "re-re.telemetry")
        self.redis_url = os.getenv("RE_RE_TELEMETRY_REDIS_URL", os.getenv("REDIS_URL"))
        self.history_db_path = Path(os.getenv("RE_RE_HISTORY_DB_PATH", "./data/history.db"))
        self.history_db_path.parent.mkdir(parents=True, exist_ok=True)

        self._redis_client: Optional["redis_async.Redis"] = None
        self._redis_lock = asyncio.Lock()
        self._redis_unavailable = False

        self._status_snapshot = {
            "enabled": self.enabled,
            "channel": self.channel,
            "redis_url": self.redis_url,
            "history_db_path": str(self.history_db_path),
            "last_event_id": None,
            "redis_available": False,
        }

        if not self.enabled:
            logger.info("Re^Re telemetry emitter disabled (RE_RE_DEMO_ENABLED not set)")
        _global_emitter_ref = self

    async def _get_redis(self) -> Optional["redis_async.Redis"]:
        """Create (or reuse) a Redis client for pub/sub."""

        if self._redis_unavailable or not self.redis_url or redis_async is None:
            return None

        async with self._redis_lock:
            if self._redis_client is None:
                try:
                    self._redis_client = redis_async.from_url(self.redis_url)
                    await self._redis_client.ping()
                    self._status_snapshot["redis_available"] = True
                except Exception as exc:  # pragma: no cover - external service
                    logger.warning("Failed to initialize Redis telemetry client: %s", exc)
                    self._redis_client = None
                    self._redis_unavailable = True
                    self._status_snapshot["redis_available"] = False
            return self._redis_client

    async def _publish_async(self, event: WorkflowEvent) -> None:
        client = await self._get_redis()
        if not client:
            return

        try:
            await client.publish(self.channel, json.dumps(event.to_payload()))
        except Exception as exc:  # pragma: no cover - external service
            logger.warning("Unable to publish Re^Re telemetry event: %s", exc)

    async def _persist_async(self, event: WorkflowEvent, state_snapshot: Optional[Dict[str, Any]]) -> None:
        payload = event.to_payload()
        if state_snapshot:
            payload["state_snapshot"] = state_snapshot
        metadata_json = json.dumps(payload.pop("metadata", {}))
        state_json = json.dumps(state_snapshot) if state_snapshot else None

        def _write():
            conn = sqlite3.connect(str(self.history_db_path), check_same_thread=False)
            try:
                _ensure_re_re_table(conn)
                conn.execute(
                    """
                    INSERT INTO re_re_events (
                        event_id,
                        thread_id,
                        intent,
                        phase,
                        status,
                        step_index,
                        node,
                        tool,
                        budget_used,
                        remaining_budget,
                        quality_score,
                        reasoning_tokens,
                        state_snapshot,
                        metadata,
                        created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        payload["event_id"],
                        payload["thread_id"],
                        payload["intent"],
                        payload["phase"],
                        payload["status"],
                        payload["step_index"],
                        payload["node"],
                        payload["tool"],
                        payload["budget_used"],
                        payload["remaining_budget"],
                        payload["quality_score"],
                        payload["reasoning_tokens"],
                        state_json,
                        metadata_json,
                        payload["created_at"],
                    ),
                )
                conn.commit()
            finally:
                conn.close()

        await asyncio.to_thread(_write)
        self._status_snapshot["last_event_id"] = event.event_id
        _emitter_logs.append(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "event_id": event.event_id,
                "thread_id": event.thread_id,
                "phase": event.phase,
                "status": event.status,
            }
        )
        del _emitter_logs[:-50]

    async def _broadcast_async(
        self,
        event: WorkflowEvent,
        state_snapshot: Optional[Dict[str, Any]],
    ) -> None:
        try:
            from .re_re_ws import broadcast_event
        except ImportError:  # pragma: no cover - FastAPI optional
            return

        payload = {
            "type": "workflow_event",
            "event": event.to_payload(),
            "state": state_snapshot,
        }
        await broadcast_event(event.thread_id, payload)

    async def _dispatch_async(
        self,
        event: WorkflowEvent,
        state_snapshot: Optional[Dict[str, Any]],
    ) -> None:
        await asyncio.gather(
            self._publish_async(event),
            self._persist_async(event, state_snapshot),
            self._broadcast_async(event, state_snapshot),
        )

    def dispatch(
        self,
        event: WorkflowEvent,
        *,
        state_snapshot: Optional[Dict[str, Any]] = None,
    ) -> None:
        if not self.enabled:
            return

        try:
            loop = asyncio.get_running_loop()
            loop.create_task(self._dispatch_async(event, state_snapshot))
        except RuntimeError:
            asyncio.run(self._dispatch_async(event, state_snapshot))

    def create_session(
        self,
        thread_id: str,
        intent: str,
        base_metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional["ReReTelemetrySession"]:
        if not self.enabled:
            return None

        return ReReTelemetrySession(self, thread_id, intent, base_metadata or {})


class ReReTelemetrySession:
    """Per-execution telemetry helper that builds WorkflowEvent payloads."""

    def __init__(
        self,
        emitter: ReReTelemetryEmitter,
        thread_id: str,
        intent: str,
        base_metadata: Dict[str, Any],
    ) -> None:
        self.emitter = emitter
        self.thread_id = thread_id
        self.intent = intent
        self.base_metadata = base_metadata

    def emit(
        self,
        *,
        phase: str,
        status: str,
        node: str,
        state: "PlaybookState",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        if not self.emitter.enabled:
            return

        event = WorkflowEvent(
            event_id=str(uuid.uuid4()),
            thread_id=self.thread_id,
            intent=self.intent,
            phase=phase,
            status=status,
            step_index=len(state.get("steps_completed", [])),
            node=node,
            tool=state.get("selected_tool"),
            budget_used=state.get("budget_used", 0.0),
            remaining_budget=state.get("remaining_budget", 0.0),
            quality_score=state.get("quality_score"),
            reasoning_tokens=state.get("reasoning_tokens"),
            metadata=self._build_metadata(state, metadata),
            created_at=datetime.now(timezone.utc),
        )

        self.emitter.dispatch(event, state_snapshot=_sanitize_state(state))

    def _build_metadata(
        self, state: "PlaybookState", metadata: Optional[Dict[str, Any]]
    ) -> Dict[str, Any]:
        combined: Dict[str, Any] = {
            **self.base_metadata,
            "current_step": state.get("current_step"),
            "tool_input": state.get("tool_input"),
            "tool_result": state.get("tool_result"),
            "last_decision": (state.get("decision_log") or [None])[-1],
            "last_artifact": (state.get("artifacts") or [None])[-1],
            "last_budget_event": (state.get("budget_events") or [None])[-1],
        }
        if metadata:
            combined.update(metadata)
        return combined


def _ensure_re_re_table(conn: sqlite3.Connection) -> None:
    """Create telemetry table if it does not exist."""

    conn.execute(
        """
        CREATE TABLE IF NOT EXISTS re_re_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            event_id TEXT NOT NULL,
            thread_id TEXT,
            intent TEXT,
            phase TEXT,
            status TEXT,
            step_index INTEGER,
            node TEXT,
            tool TEXT,
            budget_used REAL,
            remaining_budget REAL,
            quality_score REAL,
            reasoning_tokens INTEGER,
            state_snapshot TEXT,
            metadata TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """
    )
    conn.execute(
        """
        CREATE INDEX IF NOT EXISTS idx_re_re_events_thread
        ON re_re_events(thread_id, created_at DESC)
        """
    )

    # Ensure state_snapshot column exists for older tables
    cursor = conn.execute("PRAGMA table_info(re_re_events)")
    columns = {row["name"] for row in cursor.fetchall()}
    if "state_snapshot" not in columns:
        conn.execute("ALTER TABLE re_re_events ADD COLUMN state_snapshot TEXT")
        conn.commit()


def _sanitize_state(state: "PlaybookState") -> Dict[str, Any]:
    """Build a JSON-serializable snapshot of the workflow state."""
    import json

    # Copy to avoid mutating original state object
    snapshot: Dict[str, Any] = {}
    for key, value in state.items():
        if key == "context":
            context = dict(value or {})
            # Remove non-serializable objects like tool registries
            context.pop("tool_registry", None)
            snapshot[key] = context
        else:
            snapshot[key] = value

    def _default(obj: Any) -> Any:
        return str(obj)

    return json.loads(json.dumps(snapshot, default=_default))


def get_emitter_diagnostics() -> Dict[str, Any]:
    return {
        "status": getattr(_global_emitter_ref, "_status_snapshot", {}),
        "event_log": list(_emitter_logs),
    }
