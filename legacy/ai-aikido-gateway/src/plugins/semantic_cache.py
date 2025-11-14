"""Semantic cache plugin using embeddings for similarity matching."""

import hashlib
import json
import logging
from typing import Any, Dict, Optional, List

from src.core.cache.semantic import SemanticCacheBackend
from src.core.cache.qdrant import QdrantBackend
from src.core.cache.semantic_timeseries import SemanticMetricsRecorder
from src.core.context import RequestContext
from src.core.embeddings import (
    EmbeddingProvider,
    OpenAIEmbeddingProvider,
    SentenceTransformersProvider,
)
from src.core.plugin import BasePlugin

logger = logging.getLogger(__name__)


class SemanticCachePlugin(BasePlugin):
    """Semantic cache plugin using embedding-based similarity.

    This plugin uses embeddings to find semantically similar prompts
    and returns cached responses when similarity exceeds the threshold.
    Falls back to verbatim cache if enabled.

    Configuration:
        enabled: Enable/disable the plugin
        priority: Execution priority (run after verbatim cache)
        embedding_provider: Provider for embeddings (openai, custom)
        embedding_api_key: API key for embedding provider
        embedding_model: Model name for embeddings
        similarity_threshold: Minimum similarity score (0.0-1.0)
        max_cache_entries: Maximum number of cached items
        ttl_seconds: Cache entry time-to-live
        fallback_to_verbatim: Skip if verbatim cache hit
        metadata_filters: Metadata keys to match (e.g., model)
    """

    def __init__(
        self,
        name: str,
        config: Optional[Dict[str, Any]] = None,
        enabled: bool = True,
        priority: int = 6,
    ):
        super().__init__(name, config, enabled, priority)

        if config is None:
            config = {}

        # Embedding provider setup
        provider_type = config.get("embedding_provider", "openai")
        self.provider_type = provider_type

        if provider_type == "openai":
            embedding_api_key = config.get("embedding_api_key")
            if not embedding_api_key:
                logger.warning(
                    "No embedding_api_key provided for OpenAI, semantic cache will be disabled"
                )
                self.enabled = False
                return

            embedding_model = config.get("embedding_model", "text-embedding-ada-002")
            self.embedding_provider: EmbeddingProvider = OpenAIEmbeddingProvider(
                api_key=embedding_api_key,
                model=embedding_model
            )
        elif provider_type == "sentence_transformers":
            service_url = config.get("embedding_service_url", "http://localhost:8001")
            embedding_model = config.get("embedding_model", "all-MiniLM-L6-v2")
            self.embedding_provider = SentenceTransformersProvider(
                service_url=service_url,
                model=embedding_model
            )
        else:
            raise ValueError(f"Unknown embedding provider: {provider_type}")

        # Cache backend setup
        backend_type = config.get("cache_backend", "faiss")
        fallback_backend = config.get("fallback_backend", "faiss")
        self.backend_type = backend_type
        self.backend_fallback_reason: Optional[str] = None
        similarity_threshold = config.get("similarity_threshold", 0.85)
        max_entries = config.get("max_cache_entries", 10000)
        ttl_seconds = config.get("ttl_seconds", 3600)

        search_candidate_limit = int(config.get("search_candidate_limit", 5))

        def _build_faiss_backend() -> SemanticCacheBackend:
            return SemanticCacheBackend(
                dimension=self.embedding_provider.dimension,
                similarity_threshold=similarity_threshold,
                max_entries=max_entries,
                ttl_seconds=ttl_seconds,
                search_limit=search_candidate_limit,
            )

        if backend_type == "faiss":
            self.cache_backend = _build_faiss_backend()
        elif backend_type == "qdrant":
            qdrant_host = config.get("qdrant_host", "localhost")
            qdrant_port = config.get("qdrant_port", 6333)
            collection_name = config.get("qdrant_collection", "semantic_cache")
            try:
                self.cache_backend = QdrantBackend(
                    host=qdrant_host,
                    port=qdrant_port,
                    collection_name=collection_name,
                    dimension=self.embedding_provider.dimension,
                    similarity_threshold=similarity_threshold,
                    max_entries=max_entries,
                    ttl_seconds=ttl_seconds,
                    search_limit=search_candidate_limit,
                )
            except Exception as exc:
                if fallback_backend == "faiss":
                    logger.warning(
                        "Failed to initialize Qdrant backend (%s); falling back to FAISS.",
                        exc,
                    )
                    self.cache_backend = _build_faiss_backend()
                    self.backend_type = "faiss"
                    self.backend_fallback_reason = str(exc)
                else:
                    raise
        elif backend_type == "auto":
            try:
                qdrant_host = config.get("qdrant_host", "localhost")
                qdrant_port = config.get("qdrant_port", 6333)
                collection_name = config.get("qdrant_collection", "semantic_cache")
                self.cache_backend = QdrantBackend(
                    host=qdrant_host,
                    port=qdrant_port,
                    collection_name=collection_name,
                    dimension=self.embedding_provider.dimension,
                    similarity_threshold=similarity_threshold,
                    max_entries=max_entries,
                    ttl_seconds=ttl_seconds,
                    search_limit=search_candidate_limit,
                )
                self.backend_type = "qdrant"
            except Exception as exc:
                logger.warning(
                    "Auto backend falling back to FAISS (Qdrant unavailable: %s)", exc
                )
                self.cache_backend = _build_faiss_backend()
                self.backend_type = "faiss"
                self.backend_fallback_reason = str(exc)
        else:
            raise ValueError(f"Unknown cache backend: {backend_type}")

        # Plugin settings
        self.fallback_to_verbatim = config.get("fallback_to_verbatim", True)
        self.metadata_filters = config.get("metadata_filters", ["model"])

        # Initialize time-series metrics recorder
        self.metrics_recorder: Optional[SemanticMetricsRecorder] = None
        if config.get("enable_timeseries", True):
            try:
                db_path = config.get("timeseries_db", "./data/semantic_metrics.db")
                sample_interval = config.get("timeseries_sample_interval", 60)
                retention_hours = config.get("timeseries_retention_hours", 168)

                self.metrics_recorder = SemanticMetricsRecorder(
                    db_path=db_path,
                    sample_interval=sample_interval,
                    retention_hours=retention_hours,
                )

                logger.info(
                    f"Time-series metrics enabled: db={db_path}, "
                    f"interval={sample_interval}s, retention={retention_hours}h"
                )
            except Exception as e:
                logger.warning(
                    f"Failed to initialize metrics recorder: {e}. "
                    "Time-series tracking will be disabled."
                )
                self.metrics_recorder = None

        logger.info(
            f"Semantic cache plugin '{self.name}' initialized: provider={provider_type}, "
            f"model={self.embedding_provider.model_name}, "
            f"threshold={self.cache_backend.similarity_threshold}, "
            f"dimension={self.embedding_provider.dimension}"
        )

    def _extract_prompt_text(self, request: Any) -> str:
        """Extract text from request for embedding.

        Args:
            request: Chat completion request

        Returns:
            Concatenated text from messages
        """
        if not hasattr(request, "messages") or not request.messages:
            return ""

        # Concatenate all message content
        texts = []
        for msg in request.messages:
            if hasattr(msg, "content") and msg.content:
                role = getattr(msg, "role", "user")
                texts.append(f"{role}: {msg.content}")

        return "\n".join(texts)

    def _build_metadata_filters(self, ctx: RequestContext) -> Dict[str, Any]:
        """Metadata used for matching (stable fields only)."""
        metadata: Dict[str, Any] = {}
        request = ctx.request
        for key in self.metadata_filters:
            if hasattr(request, key):
                metadata[key] = getattr(request, key)
        return metadata

    def _build_storage_metadata(
        self,
        ctx: RequestContext,
        base_filters: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Metadata persisted alongside cache entry."""
        metadata = dict(base_filters)
        metadata["cache_type"] = "semantic"
        prompt_text = ctx.metadata.get("semantic_prompt_text")
        if prompt_text:
            metadata["prompt_text"] = prompt_text
        timestamp = ctx.metadata.get("timestamp")
        if not timestamp and hasattr(ctx, "timestamp"):
            timestamp = ctx.timestamp.isoformat()
        metadata["timestamp"] = timestamp
        return metadata

    def _record_embedding_usage(self, ctx: RequestContext, result) -> None:
        """Record embedding cost/tokens on the context."""
        if not result:
            return
        ctx.add_cost_entry(
            {
                "type": "embedding",
                "model": result.model or self.embedding_provider.model_name,
                "prompt_tokens": result.prompt_tokens,
                "cost": result.cost,
                "latency_ms": result.latency_ms,
            }
        )

    async def before_request(self, ctx: RequestContext):
        """Check semantic cache before making LLM request.

        Args:
            ctx: Request context with prompt and metadata
        """
        if not self.enabled:
            return

        # Skip if already cached by verbatim cache
        if self.fallback_to_verbatim and ctx.metadata.get("cache_hit"):
            logger.debug("Skipping semantic cache - verbatim cache hit")
            return

        try:
            # Extract prompt text
            prompt_text = self._extract_prompt_text(ctx.request)
            if not prompt_text:
                logger.warning("Empty prompt text, skipping semantic cache")
                return
            ctx.metadata["semantic_prompt_text"] = prompt_text

            # Generate embedding
            logger.debug(f"Generating embedding for prompt (length={len(prompt_text)})")
            embedding_result = await self.embedding_provider.embed(prompt_text)
            embedding = embedding_result.vector
            ctx.metadata["semantic_embedding"] = embedding
            self._record_embedding_usage(ctx, embedding_result)

            # Search semantic cache
            metadata_filters = self._build_metadata_filters(ctx)
            result = await self.cache_backend.get(embedding, metadata_filters)

            if result:
                response, similarity_score = result

                # Cache hit!
                ctx.response = response
                ctx.metadata["cached"] = True
                ctx.metadata["cache_hit"] = True
                ctx.metadata["cache_type"] = "semantic"
                ctx.metadata["similarity_score"] = similarity_score

                logger.info(
                    f"Semantic cache HIT: similarity={similarity_score:.3f}, "
                    f"model={metadata_filters.get('model', 'unknown')}"
                )

                # Stop pipeline to prevent unnecessary API call
                ctx.stop_pipeline()
            else:
                # Cache miss
                ctx.metadata["semantic_cache_checked"] = True

                logger.debug("Semantic cache MISS")

        except Exception as e:
            logger.error(f"Error in semantic cache lookup: {e}", exc_info=True)
            # Don't fail the request, continue without cache

    async def after_response(self, ctx: RequestContext):
        """Store response in semantic cache after LLM call.

        Args:
            ctx: Request context with response
        """
        if not self.enabled:
            return

        # Don't cache if already a semantic cache hit (avoid duplication)
        if ctx.metadata.get("cache_hit") and ctx.metadata.get("cache_type") == "semantic":
            return

        # Don't cache errors
        if ctx.metadata.get("error"):
            return

        try:
            # Check if we already have the embedding from lookup
            embedding = ctx.metadata.get("semantic_embedding")

            if not embedding:
                # Generate embedding if not already done
                prompt_text = self._extract_prompt_text(ctx.request)
                if not prompt_text:
                    logger.warning("Empty prompt text, skipping cache storage")
                    return

                logger.debug("Generating embedding for cache storage")
                embedding_result = await self.embedding_provider.embed(prompt_text)
                embedding = embedding_result.vector
                ctx.metadata["semantic_embedding"] = embedding
                ctx.metadata.setdefault("semantic_prompt_text", prompt_text)
                self._record_embedding_usage(ctx, embedding_result)

            # Store in semantic cache
            metadata_filters = self._build_metadata_filters(ctx)
            metadata = self._build_storage_metadata(ctx, metadata_filters)
            logger.info(
                f"Semantic cache: storing response - embedding_len={len(embedding)}, "
                f"response_type={type(ctx.response)}, model={metadata.get('model', 'unknown')}"
            )
            await self.cache_backend.set(embedding, ctx.response, metadata)

            logger.info(
                f"✅ Stored in semantic cache: model={metadata.get('model', 'unknown')}, "
                f"cache_size={self.cache_backend.get_stats()['size']}"
            )

        except Exception as e:
            logger.error(f"❌ Error storing in semantic cache: {e}", exc_info=True)
            # Don't fail the request

    async def on_startup(self):
        """Initialize plugin on startup."""
        if self.enabled:
            logger.info(
                f"Semantic cache plugin started: "
                f"threshold={self.cache_backend.similarity_threshold}, "
                f"max_entries={self.cache_backend.max_entries}"
            )

            # Start time-series metrics recorder
            if self.metrics_recorder:
                embedding_model = self.embedding_provider.model_name
                await self.metrics_recorder.start(
                    self.cache_backend,
                    embedding_model=embedding_model
                )
                logger.info("Time-series metrics recording started")

    async def on_shutdown(self):
        """Cleanup on shutdown."""
        if self.enabled:
            # Stop time-series recorder
            if self.metrics_recorder:
                await self.metrics_recorder.stop()
                logger.info("Time-series metrics recording stopped")

            stats = self.cache_backend.get_stats()
            logger.info(f"Semantic cache plugin shutdown: {stats}")

    def update_similarity_threshold(self, threshold: float) -> Dict[str, Any]:
        """Update similarity threshold at runtime."""
        if not self.enabled or not hasattr(self, "cache_backend"):
            raise RuntimeError("Semantic cache plugin is not enabled")

        updated = self.cache_backend.update_similarity_threshold(threshold)
        logger.info("Semantic cache threshold updated to %.3f", updated)
        return self.get_stats()

    async def preview_candidates(
        self,
        prompt_text: str,
        model: Optional[str] = None,
        limit: int = 3,
    ) -> List[Dict[str, Any]]:
        """Preview semantic cache candidates for a raw prompt."""
        if not self.enabled:
            return []

        prompt_text = prompt_text.strip()
        if not prompt_text:
            return []

        embedding_result = await self.embedding_provider.embed(prompt_text)
        embedding = embedding_result.vector
        metadata_filter: Dict[str, Any] = {}
        if model and "model" in self.metadata_filters:
            metadata_filter["model"] = model

        return await self.cache_backend.search_candidates(
            embedding,
            metadata_filter or None,
            limit=limit,
            include_below_threshold=True,
        )

    def list_entries(self, limit: int = 20) -> List[Dict[str, Any]]:
        """List recent semantic cache entries."""
        if not self.enabled:
            return []
        return self.cache_backend.list_entries(limit=limit)

    def get_stats(self) -> Dict[str, Any]:
        """Get semantic cache statistics.

        Returns:
            Dictionary with cache stats
        """
        if not self.enabled:
            return {"enabled": False}

        stats = {
            "enabled": True,
            "embedding_model": self.embedding_provider.model_name,
            "embedding_dimension": self.embedding_provider.dimension,
            "provider": self.provider_type,
            "backend": self.backend_type,
            "fallback_reason": self.backend_fallback_reason,
            "timeseries_enabled": self.metrics_recorder is not None,
            **self.cache_backend.get_stats(),
        }

        # Add time-series recorder stats if available
        if self.metrics_recorder:
            recorder_stats = self.metrics_recorder.get_stats()
            stats["timeseries"] = recorder_stats
            stats["timeseries_available"] = recorder_stats.get("total_samples", 0) > 0

        return stats
