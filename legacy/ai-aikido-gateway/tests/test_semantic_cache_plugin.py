"""Unit tests for SemanticCachePlugin configuration."""

from unittest.mock import MagicMock, patch

import pytest

from src.plugins.semantic_cache import SemanticCachePlugin


class TestSemanticCachePluginConfig:
    """Covers backend/provider configuration scenarios."""

    def test_falls_back_when_qdrant_unavailable(self):
        config = {
            "embedding_provider": "sentence_transformers",
            "embedding_service_url": "http://localhost:8001",
            "embedding_model": "all-MiniLM-L6-v2",
            "cache_backend": "qdrant",
            "fallback_backend": "faiss",
            "qdrant_host": "localhost",
            "qdrant_port": 6333,
            "qdrant_collection": "test",
        }

        with (
            patch("src.plugins.semantic_cache.SentenceTransformersProvider") as provider,
            patch("src.plugins.semantic_cache.QdrantBackend", side_effect=RuntimeError("boom")),
            patch("src.plugins.semantic_cache.SemanticCacheBackend") as faiss_backend,
        ):
            provider.return_value.dimension = 384
            provider.return_value.model_name = "all-MiniLM-L6-v2"
            faiss_backend.return_value.get_stats.return_value = {
                "size": 0,
                "max_entries": 100,
                "hits": 0,
                "misses": 0,
                "hit_rate": 0,
                "average_similarity": 0,
                "evictions": 0,
                "similarity_threshold": 0.85,
                "ttl_seconds": 3600,
                "backend": "faiss",
            }

            plugin = SemanticCachePlugin(name="semantic_cache", config=config)

        assert plugin.backend_type == "faiss"
        assert plugin.backend_fallback_reason is not None

    def test_stats_include_provider_and_backend(self):
        config = {
            "embedding_provider": "sentence_transformers",
            "embedding_service_url": "http://localhost:8001",
            "embedding_model": "all-MiniLM-L6-v2",
            "cache_backend": "faiss",
        }

        with (
            patch("src.plugins.semantic_cache.SentenceTransformersProvider") as provider,
            patch("src.plugins.semantic_cache.SemanticCacheBackend") as faiss_backend,
        ):
            provider.return_value.dimension = 384
            provider.return_value.model_name = "all-MiniLM-L6-v2"
            faiss_backend.return_value.get_stats.return_value = {
                "size": 0,
                "max_entries": 100,
                "hits": 0,
                "misses": 0,
                "hit_rate": 0,
                "average_similarity": 0,
                "evictions": 0,
                "similarity_threshold": 0.85,
                "ttl_seconds": 3600,
                "backend": "faiss",
            }

            plugin = SemanticCachePlugin(name="semantic_cache", config=config)

        stats = plugin.get_stats()
        assert stats["provider"] == "sentence_transformers"
        assert stats["backend"] == "faiss"
