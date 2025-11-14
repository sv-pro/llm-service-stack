"""Semantic cache backend using Qdrant for persistent vector storage."""

import json
import logging
import time
import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

try:
    from qdrant_client import QdrantClient
    from qdrant_client.models import (
        Distance,
        VectorParams,
        PointStruct,
        Filter,
        FieldCondition,
        MatchValue,
    )
    QDRANT_AVAILABLE = True
except ImportError:
    QDRANT_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class CachedItem:
    """Represents a cached response with metadata."""

    embedding: List[float]
    response: Any
    timestamp: float
    metadata: Dict[str, Any]


class QdrantBackend:
    """Qdrant-based semantic cache for persistent vector similarity search.

    This cache stores embeddings in Qdrant and finds similar prompts using
    cosine similarity. Unlike FAISS, Qdrant provides persistent storage
    and efficient filtered search.

    Args:
        host: Qdrant server host (default: localhost)
        port: Qdrant server port (default: 6333)
        collection_name: Name of the Qdrant collection (default: semantic_cache)
        dimension: Embedding vector dimension (default: 384 for all-MiniLM-L6-v2)
        similarity_threshold: Minimum similarity score (0.0-1.0)
        max_entries: Maximum number of cached items (0 = unlimited)
        ttl_seconds: Time-to-live for cache entries (0 = no expiration)

    Raises:
        ImportError: If qdrant-client package is not installed
        Exception: If connection to Qdrant fails
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 6333,
        collection_name: str = "semantic_cache",
        dimension: int = 384,
        similarity_threshold: float = 0.85,
        max_entries: int = 0,  # 0 = unlimited
        ttl_seconds: int = 3600,
        search_limit: int = 5,
    ):
        if not QDRANT_AVAILABLE:
            raise ImportError(
                "qdrant-client package is required for Qdrant backend. "
                "Install with: pip install qdrant-client"
            )

        self.host = host
        self.port = port
        self.collection_name = collection_name
        self.dimension = dimension
        self.similarity_threshold = similarity_threshold
        self.max_entries = max_entries
        self.ttl_seconds = ttl_seconds
        self.search_limit = max(1, search_limit)

        # Initialize Qdrant client
        try:
            self.client = QdrantClient(host=host, port=port)
            self._ensure_collection()
            logger.info(
                f"Initialized Qdrant backend: {host}:{port}/{collection_name}, "
                f"dimension={dimension}, threshold={similarity_threshold}"
            )
        except Exception as e:
            logger.error(f"Failed to connect to Qdrant at {host}:{port}: {e}")
            raise

        # Statistics (in-memory only, reset on restart)
        self.stats = {
            "hits": 0,
            "misses": 0,
            "total_similarity_scores": 0.0,
            "evictions": 0
        }

    def _ensure_collection(self):
        """Create collection if it doesn't exist."""
        collections = self.client.get_collections().collections
        collection_names = [c.name for c in collections]

        if self.collection_name not in collection_names:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(
                    size=self.dimension,
                    distance=Distance.COSINE,
                ),
            )
            logger.info(f"Created Qdrant collection: {self.collection_name}")
        else:
            logger.debug(f"Using existing Qdrant collection: {self.collection_name}")

    def _is_expired(self, timestamp: float) -> bool:
        """Check if cache item has expired.

        Args:
            timestamp: Unix timestamp of cached item

        Returns:
            True if expired, False otherwise
        """
        if self.ttl_seconds <= 0:
            return False

        age = time.time() - timestamp
        return age > self.ttl_seconds

    async def _clean_expired(self):
        """Remove expired entries from Qdrant."""
        if self.ttl_seconds <= 0:
            return

        # Calculate expiration timestamp
        expiration_time = time.time() - self.ttl_seconds

        # Delete expired points
        try:
            # Qdrant doesn't have direct "delete by filter" for numeric ranges in older versions
            # So we scroll through and delete individually
            # In production, you might want to use a scheduled cleanup job
            points, _ = self.client.scroll(
                collection_name=self.collection_name,
                limit=10000,  # Adjust based on your needs
            )

            expired_ids = []
            for point in points:
                if point.payload and point.payload.get("timestamp", 0) < expiration_time:
                    expired_ids.append(point.id)

            if expired_ids:
                self.client.delete(
                    collection_name=self.collection_name,
                    points_selector=expired_ids,
                )
                logger.debug(f"Cleaned {len(expired_ids)} expired entries from Qdrant")
        except Exception as e:
            logger.warning(f"Error cleaning expired entries: {e}")

    async def _evict_if_needed(self):
        """Evict oldest entries if cache exceeds max_entries."""
        if self.max_entries <= 0:
            return  # Unlimited

        try:
            count = self.client.count(collection_name=self.collection_name).count

            if count >= self.max_entries:
                # Get oldest entries
                points, _ = self.client.scroll(
                    collection_name=self.collection_name,
                    limit=count - self.max_entries + 1,
                    order_by="timestamp",  # Requires Qdrant 1.7+
                )

                # Sort by timestamp and delete oldest
                sorted_points = sorted(
                    points,
                    key=lambda p: p.payload.get("timestamp", 0) if p.payload else 0
                )

                to_delete = sorted_points[:len(sorted_points) - self.max_entries + 1]
                delete_ids = [p.id for p in to_delete]

                if delete_ids:
                    self.client.delete(
                        collection_name=self.collection_name,
                        points_selector=delete_ids,
                    )
                    self.stats["evictions"] += len(delete_ids)
                    logger.debug(f"Evicted {len(delete_ids)} oldest entries")
        except Exception as e:
            logger.warning(f"Error during eviction: {e}")

    async def get(
        self,
        embedding: List[float],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Tuple[Any, float]]:
        """Search for similar cached response and enforce threshold.

        Args:
            embedding: Query embedding vector
            metadata: Optional metadata filters (e.g., {"model": "gpt-4"})

        Returns:
            Tuple of (response, similarity_score) if found, None otherwise
        """
        await self._clean_expired()

        try:
            # Build filter if metadata provided
            query_filter = None
            if metadata:
                conditions = []
                for key, value in metadata.items():
                    conditions.append(
                        FieldCondition(
                            key=f"metadata.{key}",
                            match=MatchValue(value=value)
                        )
                    )
                if conditions:
                    query_filter = Filter(must=conditions)

            # Search for similar vectors
            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=embedding,
                limit=self.search_limit,
                score_threshold=None,
                query_filter=query_filter,
            )

            if not results:
                self.stats["misses"] += 1
                return None

            for result in results:
                if not result.payload:
                    continue
                if self._is_expired(result.payload.get("timestamp", 0)):
                    continue
                similarity_score = result.score
                if similarity_score < self.similarity_threshold:
                    continue

                response = result.payload.get("response")

                self.stats["hits"] += 1
                self.stats["total_similarity_scores"] += similarity_score

                logger.info(
                    "Semantic cache HIT: similarity=%.3f, model=%s",
                    similarity_score,
                    result.payload.get("metadata", {}).get("model", "unknown"),
                )

                return (response, similarity_score)

            self.stats["misses"] += 1
            return None

        except Exception as e:
            logger.error(f"Error searching Qdrant cache: {e}")
            self.stats["misses"] += 1
            return None

    async def search_candidates(
        self,
        embedding: List[float],
        metadata: Optional[Dict[str, Any]] = None,
        limit: int = 3,
        include_below_threshold: bool = True,
    ) -> List[Dict[str, Any]]:
        """Return top candidates for diagnostics/visualization.

        Args:
            embedding: Query embedding vector
            metadata: Optional metadata filters
            limit: Maximum number of candidates to return
            include_below_threshold: Include results below similarity threshold

        Returns:
            List of candidate dictionaries with similarity and metadata
        """
        await self._clean_expired()

        try:
            # Build filter if metadata provided
            query_filter = None
            if metadata:
                conditions = []
                for key, value in metadata.items():
                    conditions.append(
                        FieldCondition(
                            key=f"metadata.{key}",
                            match=MatchValue(value=value)
                        )
                    )
                if conditions:
                    query_filter = Filter(must=conditions)

            # Search without threshold if including below threshold results
            score_threshold = None if include_below_threshold else self.similarity_threshold

            results = self.client.search(
                collection_name=self.collection_name,
                query_vector=embedding,
                limit=limit,
                score_threshold=score_threshold,
                query_filter=query_filter,
            )

            # Format results
            formatted = []
            for result in results:
                if result.payload and not self._is_expired(result.payload.get("timestamp", 0)):
                    formatted.append({
                        "similarity": result.score,
                        "prompt_text": result.payload.get("metadata", {}).get("prompt_text"),
                        "model": result.payload.get("metadata", {}).get("model"),
                        "timestamp": result.payload.get("timestamp"),
                        "metadata": result.payload.get("metadata", {}),
                    })

            return formatted

        except Exception as e:
            logger.error(f"Error searching candidates in Qdrant: {e}")
            return []

    def list_entries(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Return the most recent cache entries for inspection.

        Args:
            limit: Maximum number of entries to return

        Returns:
            List of entry dictionaries
        """
        try:
            points, _ = self.client.scroll(
                collection_name=self.collection_name,
                limit=limit,
            )

            # Sort by timestamp descending
            sorted_points = sorted(
                points,
                key=lambda p: p.payload.get("timestamp", 0) if p.payload else 0,
                reverse=True
            )

            entries = []
            for point in sorted_points:
                if point.payload:
                    metadata = point.payload.get("metadata", {})
                    entries.append({
                        "prompt_text": metadata.get("prompt_text"),
                        "model": metadata.get("model"),
                        "timestamp": point.payload.get("timestamp"),
                        "metadata": metadata,
                    })

            return entries

        except Exception as e:
            logger.error(f"Error listing Qdrant entries: {e}")
            return []

    async def set(
        self,
        embedding: List[float],
        response: Any,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Store response in Qdrant cache.

        Args:
            embedding: Embedding vector for the prompt
            response: Response to cache
            metadata: Optional metadata (e.g., model name, cost)
        """
        await self._evict_if_needed()

        try:
            # Generate unique ID
            point_id = str(uuid.uuid4())

            # Create point with payload
            point = PointStruct(
                id=point_id,
                vector=embedding,
                payload={
                    "response": response,
                    "timestamp": time.time(),
                    "metadata": metadata or {},
                }
            )

            # Upsert to Qdrant
            self.client.upsert(
                collection_name=self.collection_name,
                points=[point],
            )

            logger.debug(
                f"Added to Qdrant cache: id={point_id}, "
                f"model={metadata.get('model', 'unknown') if metadata else 'unknown'}"
            )

        except Exception as e:
            logger.error(f"Error adding to Qdrant cache: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
        try:
            count = self.client.count(collection_name=self.collection_name).count
        except Exception as e:
            logger.error(f"Error getting collection count: {e}")
            count = 0

        total_requests = self.stats["hits"] + self.stats["misses"]
        hit_rate = (
            self.stats["hits"] / total_requests if total_requests > 0 else 0.0
        )
        avg_similarity = (
            self.stats["total_similarity_scores"] / self.stats["hits"]
            if self.stats["hits"] > 0
            else 0.0
        )

        return {
            "size": count,
            "max_entries": self.max_entries if self.max_entries > 0 else "unlimited",
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "hit_rate": hit_rate,
            "average_similarity": avg_similarity,
            "evictions": self.stats["evictions"],
            "similarity_threshold": self.similarity_threshold,
            "ttl_seconds": self.ttl_seconds,
            "backend": "qdrant",
        }

    def update_similarity_threshold(self, new_threshold: float) -> float:
        """Update similarity threshold used for cache hits.

        Args:
            new_threshold: Threshold between 0.0 and 1.0

        Returns:
            The updated threshold value
        """
        if not 0.0 <= new_threshold <= 1.0:
            raise ValueError("Similarity threshold must be between 0.0 and 1.0")

        self.similarity_threshold = float(new_threshold)
        logger.info("Updated Qdrant cache threshold to %.3f", self.similarity_threshold)
        return self.similarity_threshold

    def clear(self):
        """Clear all cached items."""
        try:
            # Delete the collection and recreate it
            self.client.delete_collection(collection_name=self.collection_name)
            self._ensure_collection()

            self.stats = {
                "hits": 0,
                "misses": 0,
                "total_similarity_scores": 0.0,
                "evictions": 0
            }
            logger.info(f"Qdrant cache cleared: {self.collection_name}")

        except Exception as e:
            logger.error(f"Error clearing Qdrant cache: {e}")

    def close(self):
        """Close Qdrant client connection."""
        try:
            self.client.close()
            logger.debug("Qdrant client connection closed")
        except Exception as e:
            logger.warning(f"Error closing Qdrant client: {e}")
