"""Time-series metrics tracking for semantic cache."""

import asyncio
import logging
import sqlite3
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class SemanticMetricsRecorder:
    """Records semantic cache metrics to SQLite time-series database.

    This recorder periodically samples semantic cache statistics and stores
    them in a SQLite database for historical analysis and trend visualization.

    Args:
        db_path: Path to SQLite database file
        sample_interval: Seconds between samples (default: 60)
        retention_hours: Hours to retain data (default: 168 = 7 days)
    """

    def __init__(
        self,
        db_path: str = "./data/semantic_metrics.db",
        sample_interval: int = 60,
        retention_hours: int = 168,
    ):
        self.db_path = db_path
        self.sample_interval = sample_interval
        self.retention_seconds = retention_hours * 3600
        self.task: Optional[asyncio.Task] = None
        self._running = False

        # Ensure data directory exists
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        # Initialize database schema
        self._init_db()

        logger.info(
            f"Initialized semantic metrics recorder: db={db_path}, "
            f"sample_interval={sample_interval}s, retention={retention_hours}h"
        )

    def _init_db(self):
        """Initialize database schema."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Create metrics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS semantic_cache_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp INTEGER NOT NULL,
                    hits INTEGER NOT NULL,
                    misses INTEGER NOT NULL,
                    hit_rate REAL NOT NULL,
                    average_similarity REAL,
                    similarity_threshold REAL NOT NULL,
                    index_size INTEGER NOT NULL,
                    evictions INTEGER NOT NULL,
                    embedding_model TEXT NOT NULL
                )
            """)

            # Create index for efficient time-range queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_semantic_metrics_timestamp
                ON semantic_cache_metrics(timestamp)
            """)

            conn.commit()
            conn.close()

            logger.debug("Semantic metrics database schema initialized")

        except Exception as e:
            logger.error(f"Failed to initialize metrics database: {e}", exc_info=True)
            raise

    async def start(self, cache_backend: Any, embedding_model: str = "unknown"):
        """Start background sampling task.

        Args:
            cache_backend: SemanticCacheBackend instance to sample
            embedding_model: Name of embedding model for metadata
        """
        if self._running:
            logger.warning("Metrics recorder already running")
            return

        self._running = True
        self.task = asyncio.create_task(
            self._sample_loop(cache_backend, embedding_model)
        )

        logger.info("Started semantic metrics sampling task")

    async def stop(self):
        """Stop background sampling task."""
        if not self._running:
            return

        self._running = False

        if self.task:
            self.task.cancel()
            try:
                await self.task
            except asyncio.CancelledError:
                pass

        logger.info("Stopped semantic metrics sampling task")

    async def _sample_loop(self, cache_backend: Any, embedding_model: str):
        """Background loop that samples metrics at regular intervals."""
        while self._running:
            try:
                # Wait for next sample interval
                await asyncio.sleep(self.sample_interval)

                # Get current stats from cache backend
                stats = cache_backend.get_stats()

                # Record sample
                await self._record_sample(stats, embedding_model)

                # Clean up old data
                await self._cleanup_old_data()

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(
                    f"Error in metrics sampling loop: {e}",
                    exc_info=True
                )
                # Continue sampling on error

    async def _record_sample(self, stats: Dict[str, Any], embedding_model: str):
        """Insert metrics snapshot into database.

        Args:
            stats: Statistics from cache backend
            embedding_model: Name of embedding model
        """
        try:
            timestamp = int(time.time())

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                INSERT INTO semantic_cache_metrics (
                    timestamp,
                    hits,
                    misses,
                    hit_rate,
                    average_similarity,
                    similarity_threshold,
                    index_size,
                    evictions,
                    embedding_model
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                timestamp,
                stats.get("hits", 0),
                stats.get("misses", 0),
                stats.get("hit_rate", 0.0),
                stats.get("average_similarity", 0.0),
                stats.get("similarity_threshold", 0.0),
                stats.get("size", 0),
                stats.get("evictions", 0),
                embedding_model,
            ))

            conn.commit()
            conn.close()

            logger.debug(
                f"Recorded metrics sample: hit_rate={stats.get('hit_rate', 0):.3f}, "
                f"hits={stats.get('hits', 0)}, misses={stats.get('misses', 0)}"
            )

        except Exception as e:
            logger.error(f"Failed to record metrics sample: {e}", exc_info=True)

    async def _cleanup_old_data(self):
        """Remove metrics data older than retention period."""
        try:
            cutoff_time = int(time.time()) - self.retention_seconds

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute("""
                DELETE FROM semantic_cache_metrics
                WHERE timestamp < ?
            """, (cutoff_time,))

            deleted_count = cursor.rowcount

            conn.commit()
            conn.close()

            if deleted_count > 0:
                logger.debug(f"Cleaned up {deleted_count} old metric samples")

        except Exception as e:
            logger.error(f"Failed to cleanup old metrics: {e}", exc_info=True)

    async def query_timeseries(
        self,
        start: Optional[int] = None,
        end: Optional[int] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Query time-series metrics data.

        Args:
            start: Start timestamp (Unix epoch), default: 1 hour ago
            end: End timestamp (Unix epoch), default: now
            limit: Maximum number of data points to return

        Returns:
            List of metric samples ordered by timestamp (newest first)
        """
        try:
            # Default time range: last hour
            if end is None:
                end = int(time.time())
            if start is None:
                start = end - 3600  # 1 hour ago

            conn = sqlite3.connect(self.db_path)
            conn.row_factory = sqlite3.Row  # Return rows as dicts
            cursor = conn.cursor()

            cursor.execute("""
                SELECT
                    timestamp,
                    hits,
                    misses,
                    hit_rate,
                    average_similarity,
                    similarity_threshold,
                    index_size,
                    evictions,
                    embedding_model
                FROM semantic_cache_metrics
                WHERE timestamp >= ? AND timestamp <= ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (start, end, limit))

            rows = cursor.fetchall()
            conn.close()

            # Convert rows to list of dicts
            data = [
                {
                    "timestamp": row["timestamp"],
                    "hits": row["hits"],
                    "misses": row["misses"],
                    "hit_rate": row["hit_rate"],
                    "average_similarity": row["average_similarity"],
                    "similarity_threshold": row["similarity_threshold"],
                    "index_size": row["index_size"],
                    "evictions": row["evictions"],
                    "embedding_model": row["embedding_model"],
                }
                for row in rows
            ]

            logger.debug(
                f"Queried {len(data)} metric samples: "
                f"start={start}, end={end}, limit={limit}"
            )

            return data

        except Exception as e:
            logger.error(f"Failed to query timeseries data: {e}", exc_info=True)
            return []

    def get_stats(self) -> Dict[str, Any]:
        """Get recorder statistics.

        Returns:
            Dictionary with recorder status and metadata
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # Get total sample count
            cursor.execute("SELECT COUNT(*) FROM semantic_cache_metrics")
            total_samples = cursor.fetchone()[0]

            # Get latest sample timestamp
            cursor.execute("""
                SELECT timestamp FROM semantic_cache_metrics
                ORDER BY timestamp DESC LIMIT 1
            """)
            result = cursor.fetchone()
            last_sample_time = result[0] if result else None

            # Get oldest sample timestamp
            cursor.execute("""
                SELECT timestamp FROM semantic_cache_metrics
                ORDER BY timestamp ASC LIMIT 1
            """)
            result = cursor.fetchone()
            oldest_sample_time = result[0] if result else None

            conn.close()

            return {
                "running": self._running,
                "sample_interval": self.sample_interval,
                "retention_hours": self.retention_seconds // 3600,
                "total_samples": total_samples,
                "last_sample_time": last_sample_time,
                "oldest_sample_time": oldest_sample_time,
            }

        except Exception as e:
            logger.error(f"Failed to get recorder stats: {e}", exc_info=True)
            return {
                "running": self._running,
                "sample_interval": self.sample_interval,
                "retention_hours": self.retention_seconds // 3600,
            }

    def get_similarity_histogram(
        self,
        start: Optional[int] = None,
        end: Optional[int] = None,
        limit: int = 1000,
        buckets: Optional[List[float]] = None,
    ) -> Dict[str, Any]:
        """Build histogram of average similarity scores over a time window."""
        try:
            if end is None:
                end = int(time.time())
            if start is None:
                start = end - 86400  # default last 24h

            if limit < 1:
                limit = 1
            if limit > 5000:
                limit = 5000

            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT average_similarity
                FROM semantic_cache_metrics
                WHERE timestamp >= ? AND timestamp <= ?
                    AND average_similarity IS NOT NULL
                ORDER BY timestamp DESC
                LIMIT ?
                """,
                (start, end, limit),
            )
            rows = cursor.fetchall()
            conn.close()

            values = [row[0] for row in rows if row[0] is not None]
            if not values:
                return {
                    "buckets": [],
                    "total_samples": 0,
                    "range_seconds": end - start,
                }

            # Default bucket edges (0.50-1.00 focus range)
            bucket_edges = buckets or [0.0, 0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 1.01]
            histogram = []
            for idx in range(len(bucket_edges) - 1):
                low = bucket_edges[idx]
                high = bucket_edges[idx + 1]
                count = sum(1 for value in values if low <= value < high)
                label = f"{low:.2f}-{high:.2f}" if high <= 1.0 else f"{low:.2f}-1.00+"
                histogram.append(
                    {
                        "label": label,
                        "start": low,
                        "end": high,
                        "count": count,
                    }
                )

            return {
                "buckets": histogram,
                "total_samples": len(values),
                "range_seconds": end - start,
            }

        except Exception as exc:
            logger.error("Failed to build similarity histogram: %s", exc, exc_info=True)
            return {
                "buckets": [],
                "total_samples": 0,
                "range_seconds": 0,
            }
