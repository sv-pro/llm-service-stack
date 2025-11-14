"""Tests for semantic cache time-series metrics recording."""

import asyncio
import os
import sqlite3
import tempfile
import time
from pathlib import Path

import pytest

from src.core.cache.semantic import SemanticCacheBackend
from src.core.cache.semantic_timeseries import SemanticMetricsRecorder


@pytest.fixture
def temp_db():
    """Create a temporary database file for testing."""
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=".db") as f:
        db_path = f.name

    yield db_path

    # Cleanup
    if os.path.exists(db_path):
        os.unlink(db_path)


@pytest.fixture
def mock_cache_backend():
    """Create a mock cache backend with predictable stats."""

    class MockCacheBackend:
        def __init__(self):
            self.stats_data = {
                "hits": 10,
                "misses": 5,
                "hit_rate": 0.67,
                "average_similarity": 0.88,
                "similarity_threshold": 0.85,
                "size": 100,
                "evictions": 2,
            }

        def get_stats(self):
            return self.stats_data.copy()

    return MockCacheBackend()


class TestSemanticMetricsRecorder:
    """Test suite for SemanticMetricsRecorder."""

    def test_init_creates_database(self, temp_db):
        """Test that initialization creates the database schema."""
        recorder = SemanticMetricsRecorder(db_path=temp_db)

        # Check that database file exists
        assert os.path.exists(temp_db)

        # Check that table was created
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='semantic_cache_metrics'"
        )
        result = cursor.fetchone()
        conn.close()

        assert result is not None
        assert result[0] == "semantic_cache_metrics"

    def test_init_creates_index(self, temp_db):
        """Test that initialization creates the timestamp index."""
        recorder = SemanticMetricsRecorder(db_path=temp_db)

        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_semantic_metrics_timestamp'"
        )
        result = cursor.fetchone()
        conn.close()

        assert result is not None

    @pytest.mark.asyncio
    async def test_record_sample(self, temp_db, mock_cache_backend):
        """Test recording a metrics sample."""
        recorder = SemanticMetricsRecorder(db_path=temp_db, sample_interval=60)

        stats = mock_cache_backend.get_stats()
        await recorder._record_sample(stats, "text-embedding-ada-002")

        # Check that sample was recorded
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM semantic_cache_metrics")
        count = cursor.fetchone()[0]
        conn.close()

        assert count == 1

    @pytest.mark.asyncio
    async def test_record_sample_stores_correct_data(self, temp_db, mock_cache_backend):
        """Test that recorded sample contains correct data."""
        recorder = SemanticMetricsRecorder(db_path=temp_db)

        stats = mock_cache_backend.get_stats()
        await recorder._record_sample(stats, "text-embedding-3-small")

        # Retrieve the recorded data
        conn = sqlite3.connect(temp_db)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM semantic_cache_metrics LIMIT 1")
        row = cursor.fetchone()
        conn.close()

        assert row is not None
        assert row["hits"] == 10
        assert row["misses"] == 5
        assert abs(row["hit_rate"] - 0.67) < 0.01
        assert abs(row["average_similarity"] - 0.88) < 0.01
        assert abs(row["similarity_threshold"] - 0.85) < 0.01
        assert row["index_size"] == 100
        assert row["evictions"] == 2
        assert row["embedding_model"] == "text-embedding-3-small"

    @pytest.mark.asyncio
    async def test_query_timeseries_empty(self, temp_db):
        """Test querying timeseries when no data exists."""
        recorder = SemanticMetricsRecorder(db_path=temp_db)

        data = await recorder.query_timeseries()

        assert isinstance(data, list)
        assert len(data) == 0

    @pytest.mark.asyncio
    async def test_query_timeseries_returns_data(self, temp_db, mock_cache_backend):
        """Test querying timeseries returns recorded data."""
        recorder = SemanticMetricsRecorder(db_path=temp_db)

        # Record multiple samples
        stats = mock_cache_backend.get_stats()
        for i in range(5):
            stats["hits"] = 10 + i
            await recorder._record_sample(stats, "test-model")
            await asyncio.sleep(0.1)  # Small delay to ensure different timestamps

        # Query data
        data = await recorder.query_timeseries(limit=10)

        assert isinstance(data, list)
        assert len(data) == 5

        # Check that data is ordered by timestamp (newest first)
        timestamps = [d["timestamp"] for d in data]
        assert timestamps == sorted(timestamps, reverse=True)

    @pytest.mark.asyncio
    async def test_query_timeseries_respects_time_range(self, temp_db, mock_cache_backend):
        """Test querying timeseries respects start/end time range."""
        recorder = SemanticMetricsRecorder(db_path=temp_db)

        # Record samples at different times
        stats = mock_cache_backend.get_stats()
        now = int(time.time())

        # Manually insert samples with specific timestamps
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()

        for i in range(5):
            timestamp = now - (i * 600)  # 10 minute intervals
            cursor.execute(
                """
                INSERT INTO semantic_cache_metrics (
                    timestamp, hits, misses, hit_rate, average_similarity,
                    similarity_threshold, index_size, evictions, embedding_model
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (timestamp, 10, 5, 0.67, 0.88, 0.85, 100, 2, "test-model"),
            )

        conn.commit()
        conn.close()

        # Query with time range (last 30 minutes)
        start = now - 1800
        end = now
        data = await recorder.query_timeseries(start=start, end=end, limit=10)

        # Should return samples within the time range (at most 4: 0, 10, 20, 30 minutes ago)
        # Using <= to allow for boundary conditions
        assert len(data) <= 4
        assert len(data) >= 3

    @pytest.mark.asyncio
    async def test_query_timeseries_respects_limit(self, temp_db, mock_cache_backend):
        """Test querying timeseries respects limit parameter."""
        recorder = SemanticMetricsRecorder(db_path=temp_db)

        stats = mock_cache_backend.get_stats()
        for i in range(10):
            await recorder._record_sample(stats, "test-model")

        # Query with limit
        data = await recorder.query_timeseries(limit=5)

        assert len(data) == 5

    @pytest.mark.asyncio
    async def test_cleanup_old_data(self, temp_db):
        """Test cleanup of old data beyond retention period."""
        # Use very short retention period for testing (1 second)
        recorder = SemanticMetricsRecorder(
            db_path=temp_db, sample_interval=60, retention_hours=0
        )
        recorder.retention_seconds = 1  # Override to 1 second for testing

        # Insert old sample
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        old_timestamp = int(time.time()) - 5  # 5 seconds ago

        cursor.execute(
            """
            INSERT INTO semantic_cache_metrics (
                timestamp, hits, misses, hit_rate, average_similarity,
                similarity_threshold, index_size, evictions, embedding_model
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (old_timestamp, 10, 5, 0.67, 0.88, 0.85, 100, 2, "test-model"),
        )
        conn.commit()
        conn.close()

        # Run cleanup
        await recorder._cleanup_old_data()

        # Check that old data was removed
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM semantic_cache_metrics")
        count = cursor.fetchone()[0]
        conn.close()

        assert count == 0

    def test_get_stats(self, temp_db, mock_cache_backend):
        """Test getting recorder statistics."""
        recorder = SemanticMetricsRecorder(
            db_path=temp_db, sample_interval=30, retention_hours=48
        )

        stats = recorder.get_stats()

        assert "running" in stats
        assert stats["sample_interval"] == 30
        assert stats["retention_hours"] == 48
        assert "total_samples" in stats
        assert stats["total_samples"] == 0  # No samples recorded yet

    @pytest.mark.asyncio
    async def test_start_stop_sampling(self, temp_db, mock_cache_backend):
        """Test starting and stopping the sampling task."""
        recorder = SemanticMetricsRecorder(
            db_path=temp_db, sample_interval=1  # 1 second for fast testing
        )

        # Start sampling
        await recorder.start(mock_cache_backend, "test-model")
        assert recorder._running is True
        assert recorder.task is not None

        # Let it run for a bit
        await asyncio.sleep(2.5)

        # Stop sampling
        await recorder.stop()
        assert recorder._running is False

        # Check that samples were recorded
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM semantic_cache_metrics")
        count = cursor.fetchone()[0]
        conn.close()

        # Should have at least 1-2 samples
        assert count >= 1

    @pytest.mark.asyncio
    async def test_multiple_start_calls(self, temp_db, mock_cache_backend):
        """Test that multiple start calls don't create duplicate tasks."""
        recorder = SemanticMetricsRecorder(db_path=temp_db, sample_interval=10)

        await recorder.start(mock_cache_backend, "test-model")
        first_task = recorder.task

        await recorder.start(mock_cache_backend, "test-model")
        second_task = recorder.task

        # Should be the same task
        assert first_task == second_task

        await recorder.stop()

    @pytest.mark.asyncio
    async def test_sample_loop_handles_errors(self, temp_db):
        """Test that sampling loop continues after errors."""

        class ErrorCacheBackend:
            """Mock backend that raises errors."""

            def __init__(self):
                self.call_count = 0

            def get_stats(self):
                self.call_count += 1
                if self.call_count == 1:
                    raise Exception("Simulated error")
                return {
                    "hits": 10,
                    "misses": 5,
                    "hit_rate": 0.67,
                    "average_similarity": 0.88,
                    "similarity_threshold": 0.85,
                    "size": 100,
                    "evictions": 2,
                }

        recorder = SemanticMetricsRecorder(db_path=temp_db, sample_interval=1)
        error_backend = ErrorCacheBackend()

        await recorder.start(error_backend, "test-model")
        await asyncio.sleep(2.5)  # Let it sample a few times
        await recorder.stop()

        # Should have recorded at least one sample despite the first error
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM semantic_cache_metrics")
        count = cursor.fetchone()[0]
        conn.close()

        assert count >= 1
