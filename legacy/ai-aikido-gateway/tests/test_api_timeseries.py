"""Tests for semantic cache time-series API endpoints."""

import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.main import app


class TestSemanticTimeSeriesAPI:
    """Test suite for semantic cache time-series API endpoints."""

    @pytest.fixture
    def mock_semantic_plugin(self):
        """Create a mock semantic cache plugin."""
        plugin = MagicMock()
        plugin.enabled = True

        # Mock metrics recorder
        recorder = MagicMock()
        recorder.query_timeseries = AsyncMock(
            return_value=[
                {
                    "timestamp": int(time.time()) - 600,
                    "hits": 10,
                    "misses": 5,
                    "hit_rate": 0.67,
                    "average_similarity": 0.88,
                    "similarity_threshold": 0.85,
                    "index_size": 100,
                    "evictions": 2,
                    "embedding_model": "text-embedding-ada-002",
                },
                {
                    "timestamp": int(time.time()) - 300,
                    "hits": 15,
                    "misses": 6,
                    "hit_rate": 0.71,
                    "average_similarity": 0.90,
                    "similarity_threshold": 0.85,
                    "index_size": 105,
                    "evictions": 2,
                    "embedding_model": "text-embedding-ada-002",
                },
            ]
        )
        plugin.metrics_recorder = recorder

        return plugin

    def test_get_timeseries_success(self, mock_semantic_plugin):
        """Test successful retrieval of time-series data."""
        client = TestClient(app)
        with patch.object(
            client.app.state, "semantic_cache_plugin", mock_semantic_plugin, create=True
        ):
            response = client.get("/v1/cache/semantic/timeseries")

            assert response.status_code == 200

            data = response.json()
            assert data["object"] == "timeseries"
            assert "start" in data
            assert "end" in data
            assert "data" in data
            assert "count" in data
            assert data["count"] == 2
            assert len(data["data"]) == 2

    def test_get_timeseries_with_parameters(self, mock_semantic_plugin):
        """Test time-series query with custom parameters."""
        client = TestClient(app)
        with patch.object(
            client.app.state, "semantic_cache_plugin", mock_semantic_plugin, create=True
        ):
            now = int(time.time())
            start = now - 3600
            end = now

            response = client.get(
                f"/v1/cache/semantic/timeseries?start={start}&end={end}&limit=50"
            )

            assert response.status_code == 200

            data = response.json()
            assert data["start"] == start
            assert data["end"] == end

            # Verify that query_timeseries was called with correct parameters
            mock_semantic_plugin.metrics_recorder.query_timeseries.assert_called_once()
            call_kwargs = (
                mock_semantic_plugin.metrics_recorder.query_timeseries.call_args[1]
            )
            assert call_kwargs["start"] == start
            assert call_kwargs["end"] == end
            assert call_kwargs["limit"] == 50

    def test_get_timeseries_respects_limit_max(self, mock_semantic_plugin):
        """Test that limit is capped at 1000."""
        client = TestClient(app)
        with patch.object(
            client.app.state, "semantic_cache_plugin", mock_semantic_plugin, create=True
        ):
            response = client.get("/v1/cache/semantic/timeseries?limit=5000")

            assert response.status_code == 200

            # Verify that limit was capped at 1000
            call_kwargs = (
                mock_semantic_plugin.metrics_recorder.query_timeseries.call_args[1]
            )
            assert call_kwargs["limit"] == 1000

    def test_get_timeseries_plugin_not_available(self):
        """Test time-series endpoint when semantic cache plugin is not available."""
        client = TestClient(app)
        with patch.object(client.app.state, "semantic_cache_plugin", None, create=True):
            response = client.get("/v1/cache/semantic/timeseries")

            assert response.status_code == 503
            assert "Semantic cache plugin is not available" in response.json()["detail"]

    def test_get_timeseries_plugin_disabled(self):
        """Test time-series endpoint when semantic cache plugin is disabled."""
        mock_plugin = MagicMock()
        mock_plugin.enabled = False

        client = TestClient(app)
        with patch.object(client.app.state, "semantic_cache_plugin", mock_plugin, create=True):
            response = client.get("/v1/cache/semantic/timeseries")

            assert response.status_code == 503
            assert "Semantic cache plugin is not available" in response.json()["detail"]

    def test_get_timeseries_no_recorder(self):
        """Test time-series endpoint when metrics recorder is not available."""
        mock_plugin = MagicMock()
        mock_plugin.enabled = True
        mock_plugin.metrics_recorder = None

        client = TestClient(app)
        with patch.object(client.app.state, "semantic_cache_plugin", mock_plugin, create=True):
            response = client.get("/v1/cache/semantic/timeseries")

            assert response.status_code == 503
            assert "Time-series tracking is not enabled" in response.json()["detail"]

    def test_get_timeseries_error_handling(self, mock_semantic_plugin):
        """Test error handling in time-series endpoint."""
        # Make query_timeseries raise an exception
        mock_semantic_plugin.metrics_recorder.query_timeseries = AsyncMock(
            side_effect=Exception("Database error")
        )

        client = TestClient(app)
        with patch.object(
            client.app.state, "semantic_cache_plugin", mock_semantic_plugin, create=True
        ):
            response = client.get("/v1/cache/semantic/timeseries")

            assert response.status_code == 500
            assert "Failed to fetch semantic timeseries" in response.json()["detail"]

    def test_history_stats_includes_timeseries_metadata(self, mock_semantic_plugin):
        """Test that /v1/history/stats includes time-series availability."""
        # Mock history plugin
        mock_history = MagicMock()
        mock_history.get_stats = MagicMock(
            return_value={
                "total_requests": 100,
                "avg_cost_per_request": 0.001,
            }
        )

        # Mock cache plugin
        mock_cache = MagicMock()
        mock_cache.get_cache_stats = MagicMock(
            return_value={
                "hits": 30,
                "misses": 20,
                "hit_rate": 0.6,
            }
        )

        # Setup semantic plugin with timeseries stats
        mock_semantic_plugin.get_stats = MagicMock(
            return_value={
                "enabled": True,
                "hits": 10,
                "misses": 5,
                "hit_rate": 0.67,
                "timeseries": {
                    "running": True,
                    "total_samples": 50,
                    "last_sample_time": int(time.time()),
                },
                "timeseries_available": True,
            }
        )

        client = TestClient(app)
        with (
            patch.object(client.app.state, "history_plugin", mock_history, create=True),
            patch.object(client.app.state, "cache_plugin", mock_cache, create=True),
            patch.object(client.app.state, "semantic_cache_plugin", mock_semantic_plugin, create=True),
        ):
            response = client.get("/v1/history/stats")

            assert response.status_code == 200

            data = response.json()
            assert "semantic_cache_metrics" in data
            assert data["semantic_cache_metrics"]["enabled"] is True
            assert "timeseries" in data["semantic_cache_metrics"]
            assert data["semantic_cache_metrics"]["timeseries_available"] is True


class TestSemanticStatsEndpoint:
    """Tests for /v1/cache/semantic/stats."""

    @pytest.fixture
    def semantic_plugin_with_metrics(self):
        plugin = MagicMock()
        plugin.enabled = True
        plugin.get_stats = MagicMock(
            return_value={
                "enabled": True,
                "provider": "sentence_transformers",
                "embedding_model": "all-MiniLM-L6-v2",
                "embedding_dimension": 384,
                "backend": "qdrant",
                "hits": 42,
                "misses": 8,
                "hit_rate": 0.84,
                "similarity_threshold": 0.85,
                "ttl_seconds": 3600,
                "timeseries_enabled": True,
                "timeseries_available": True,
                "timeseries": {"running": True, "total_samples": 25},
            }
        )

        recorder = MagicMock()
        recorder.get_similarity_histogram = MagicMock(
            return_value={
                "buckets": [
                    {"label": "0.50-0.60", "count": 1},
                    {"label": "0.90-0.95", "count": 5},
                ],
                "total_samples": 6,
            }
        )
        recorder.query_timeseries = AsyncMock(
            return_value=[
                {
                    "timestamp": int(time.time()) - 120,
                    "hit_rate": 0.8,
                    "average_similarity": 0.9,
                }
            ]
        )
        plugin.metrics_recorder = recorder
        return plugin

    def test_semantic_stats_success(self, semantic_plugin_with_metrics):
        client = TestClient(app)
        mock_history = MagicMock()
        mock_history.get_stats = MagicMock(
            return_value={
                "embedding_cost_total": 0.00042,
                "net_cost_total": 0.42,
                "avoided_cost_total": 0.12,
            }
        )

        with (
            patch.object(
                client.app.state, "semantic_cache_plugin", semantic_plugin_with_metrics, create=True
            ),
            patch.object(client.app.state, "history_plugin", mock_history, create=True),
        ):
            response = client.get("/v1/cache/semantic/stats")

        assert response.status_code == 200
        payload = response.json()
        assert payload["object"] == "semantic_cache_stats"
        assert payload["semantic_cache_metrics"]["provider"] == "sentence_transformers"
        assert payload["histogram"]["total_samples"] == 6
        assert payload["timeseries"]["available"] is True
        assert payload["timeseries"]["recent_samples"][0]["hit_rate"] == pytest.approx(0.8)
        assert payload["cost_summary"]["embedding_cost_total"] == 0.00042

    def test_semantic_stats_without_recorder(self):
        client = TestClient(app)
        plugin = MagicMock()
        plugin.enabled = True
        plugin.metrics_recorder = None
        plugin.get_stats = MagicMock(
            return_value={
                "enabled": True,
                "provider": "sentence_transformers",
                "embedding_model": "all-MiniLM-L6-v2",
                "embedding_dimension": 384,
                "backend": "faiss",
                "hits": 0,
                "misses": 0,
                "hit_rate": 0.0,
                "timeseries_enabled": False,
                "timeseries_available": False,
            }
        )

        with patch.object(client.app.state, "semantic_cache_plugin", plugin, create=True):
            response = client.get("/v1/cache/semantic/stats")

        assert response.status_code == 200
        payload = response.json()
        assert payload["timeseries"]["available"] is False
        assert payload["histogram"] is None

    def test_semantic_stats_plugin_missing(self):
        client = TestClient(app)
        with patch.object(client.app.state, "semantic_cache_plugin", None, create=True):
            response = client.get("/v1/cache/semantic/stats")

        assert response.status_code == 503
        assert "Semantic cache plugin is not available" in response.json()["detail"]


class TestTransparencyHeaders:
    """Test transparency headers for semantic cache."""

    def test_semantic_cache_hit_headers(self):
        """Test that semantic cache hits add proper transparency headers."""
        from src.core.context import RequestContext
        from src.api.models import ChatCompletionRequest, ChatMessage
        from src.plugins.transparency import TransparencyPlugin

        # Create request context
        request = ChatCompletionRequest(
            model="gpt-3.5-turbo", messages=[ChatMessage(role="user", content="test")]
        )
        ctx = RequestContext(request=request)

        # Simulate semantic cache hit
        ctx.metadata["cache_hit"] = True
        ctx.metadata["cache_type"] = "semantic"
        ctx.metadata["similarity_score"] = 0.923
        ctx.metadata["latency_ms"] = 45.2
        ctx.metadata["model"] = "gpt-3.5-turbo"

        # Create transparency plugin and add headers
        plugin = TransparencyPlugin(
            name="transparency",
            config={
                "show_cache_status": True,
                "show_latency": True,
                "show_model": True,
            },
        )

        headers = plugin._build_headers(ctx)

        assert headers["X-Gateway-Cache-Status"] == "HIT"
        assert headers["X-Gateway-Cache-Type"] == "semantic"
        assert headers["X-Gateway-Cache-Similarity"] == "0.923"
        assert headers["X-Gateway-Latency-Ms"] == "45.20"
        assert headers["X-Gateway-Original-Model"] == "gpt-3.5-turbo"

    def test_verbatim_cache_hit_headers(self):
        """Test that verbatim cache hits use correct cache type."""
        from src.core.context import RequestContext
        from src.api.models import ChatCompletionRequest, ChatMessage
        from src.plugins.transparency import TransparencyPlugin

        request = ChatCompletionRequest(
            model="gpt-3.5-turbo", messages=[ChatMessage(role="user", content="test")]
        )
        ctx = RequestContext(request=request)

        # Simulate verbatim cache hit (no cache_type means verbatim)
        ctx.metadata["cache_hit"] = True
        ctx.metadata["latency_ms"] = 12.5

        plugin = TransparencyPlugin(
            name="transparency",
            config={"show_cache_status": True, "show_latency": True},
        )

        headers = plugin._build_headers(ctx)

        assert headers["X-Gateway-Cache-Status"] == "HIT"
        assert headers["X-Gateway-Cache-Type"] == "verbatim"
        assert "X-Gateway-Cache-Similarity" not in headers

    def test_cache_miss_headers(self):
        """Test that cache misses don't add similarity headers."""
        from src.core.context import RequestContext
        from src.api.models import ChatCompletionRequest, ChatMessage
        from src.plugins.transparency import TransparencyPlugin

        request = ChatCompletionRequest(
            model="gpt-3.5-turbo", messages=[ChatMessage(role="user", content="test")]
        )
        ctx = RequestContext(request=request)

        # Simulate cache miss
        ctx.metadata["cache_miss"] = True

        plugin = TransparencyPlugin(
            name="transparency", config={"show_cache_status": True}
        )

        headers = plugin._build_headers(ctx)

        assert headers["X-Gateway-Cache-Status"] == "MISS"
        assert "X-Gateway-Cache-Type" not in headers
        assert "X-Gateway-Cache-Similarity" not in headers
