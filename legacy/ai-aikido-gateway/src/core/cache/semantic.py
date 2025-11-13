"""Semantic cache backend using FAISS for vector similarity search."""

import json
import logging
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

try:
    import faiss
    import numpy as np
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False

logger = logging.getLogger(__name__)


@dataclass
class CachedItem:
    """Represents a cached response with metadata."""

    embedding: List[float]
    response: Any
    timestamp: float
    metadata: Dict[str, Any]


class SemanticCacheBackend:
    """FAISS-based semantic cache for similarity search.

    This cache stores embeddings and finds similar prompts using
    cosine similarity. When a similar prompt is found above the
    threshold, the cached response is returned.

    Args:
        dimension: Embedding vector dimension (default: 1536 for OpenAI)
        similarity_threshold: Minimum similarity score (0.0-1.0)
        max_entries: Maximum number of cached items
        ttl_seconds: Time-to-live for cache entries (0 = no expiration)

    Raises:
        ImportError: If faiss-cpu package is not installed
    """

    def __init__(
        self,
        dimension: int = 1536,
        similarity_threshold: float = 0.85,
        max_entries: int = 10000,
        ttl_seconds: int = 3600,
        search_limit: int = 5,
    ):
        if not FAISS_AVAILABLE:
            raise ImportError(
                "faiss-cpu package is required for semantic cache. "
                "Install with: pip install faiss-cpu"
            )

        self.dimension = dimension
        self.similarity_threshold = similarity_threshold
        self.max_entries = max_entries
        self.ttl_seconds = ttl_seconds
        self.search_limit = max(1, search_limit)

        # Initialize FAISS index for cosine similarity
        # We use IndexFlatIP (inner product) after L2 normalization
        self.index = faiss.IndexFlatIP(dimension)

        # Store cached items parallel to FAISS index
        self.items: List[CachedItem] = []

        # Statistics
        self.stats = {
            "hits": 0,
            "misses": 0,
            "total_similarity_scores": 0.0,
            "evictions": 0
        }

        logger.info(
            f"Initialized semantic cache: dimension={dimension}, "
            f"threshold={similarity_threshold}, max_entries={max_entries}"
        )

    def _normalize_vector(self, vector: List[float]) -> np.ndarray:
        """Normalize vector for cosine similarity using inner product.

        Args:
            vector: Input embedding vector

        Returns:
            Normalized numpy array
        """
        vec = np.array(vector, dtype=np.float32).reshape(1, -1)
        norm = np.linalg.norm(vec)
        if norm > 0:
            vec = vec / norm
        return vec

    def _evict_if_needed(self):
        """Evict oldest entries if cache is full."""
        while len(self.items) >= self.max_entries:
            # Remove oldest (first) item
            self.items.pop(0)
            self.stats["evictions"] += 1

            # Rebuild FAISS index (there's no efficient remove in IndexFlat)
            self._rebuild_index()

            logger.debug(f"Evicted oldest entry, cache size: {len(self.items)}")

    def _rebuild_index(self):
        """Rebuild FAISS index from current items."""
        self.index.reset()

        if self.items:
            embeddings = np.array(
                [self._normalize_vector(item.embedding)[0] for item in self.items],
                dtype=np.float32
            )
            self.index.add(embeddings)

        logger.debug(f"Rebuilt FAISS index with {len(self.items)} items")

    def _is_expired(self, item: CachedItem) -> bool:
        """Check if cache item has expired.

        Args:
            item: Cached item to check

        Returns:
            True if expired, False otherwise
        """
        if self.ttl_seconds <= 0:
            return False

        age = time.time() - item.timestamp
        return age > self.ttl_seconds

    def _clean_expired(self):
        """Remove expired entries from cache."""
        if self.ttl_seconds <= 0:
            return

        before_count = len(self.items)
        self.items = [item for item in self.items if not self._is_expired(item)]

        if len(self.items) < before_count:
            self._rebuild_index()
            logger.debug(
                f"Cleaned {before_count - len(self.items)} expired entries"
            )

    def _filter_candidates(
        self,
        candidates: List[Tuple[int, float]],
        metadata: Optional[Dict[str, Any]],
        min_similarity: Optional[float] = None,
    ) -> List[Tuple[CachedItem, float]]:
        """Helper to filter FAISS search results."""
        results: List[Tuple[CachedItem, float]] = []
        for idx, similarity in candidates:
            item = self.items[idx]
            if self._is_expired(item):
                continue
            if metadata:
                mismatch = False
                for key, value in metadata.items():
                    if item.metadata.get(key) != value:
                        mismatch = True
                        break
                if mismatch:
                    continue
            if min_similarity is not None and similarity < min_similarity:
                continue
            results.append((item, similarity))
        return results[: len(candidates)]

    def _search_indices(
        self,
        embedding: List[float],
        limit: int,
    ) -> List[Tuple[int, float]]:
        """Search FAISS index and return (index, similarity) tuples."""
        if len(self.items) == 0:
            return []

        query_vec = self._normalize_vector(embedding)
        k = min(limit, len(self.items))
        similarities, indices = self.index.search(query_vec, k)
        results: List[Tuple[int, float]] = []
        for sim, idx in zip(similarities[0], indices[0]):
            if idx == -1:
                continue
            results.append((int(idx), float(sim)))
        return results

    async def get(
        self,
        embedding: List[float],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Optional[Tuple[Any, float]]:
        """Search for similar cached response and enforce threshold."""
        self._clean_expired()

        indices = self._search_indices(embedding, self.search_limit)
        if not indices:
            self.stats["misses"] += 1
            return None

        filtered = self._filter_candidates(indices, metadata, self.similarity_threshold)
        if not filtered:
            self.stats["misses"] += 1
            return None

        item, similarity_score = filtered[0]

        self.stats["hits"] += 1
        self.stats["total_similarity_scores"] += similarity_score

        logger.info(
            f"Semantic cache HIT: similarity={similarity_score:.3f}, "
            f"model={item.metadata.get('model', 'unknown')}"
        )

        return (item.response, similarity_score)

    async def search_candidates(
        self,
        embedding: List[float],
        metadata: Optional[Dict[str, Any]] = None,
        limit: int = 3,
        include_below_threshold: bool = True,
    ) -> List[Dict[str, Any]]:
        """Return top candidates for diagnostics/visualization."""
        self._clean_expired()

        indices = self._search_indices(embedding, max(limit, 1))
        if not indices:
            return []

        min_similarity = None if include_below_threshold else self.similarity_threshold
        filtered = self._filter_candidates(indices, metadata, min_similarity)

        formatted: List[Dict[str, Any]] = []
        for item, similarity in filtered[:limit]:
            formatted.append(
                {
                    "similarity": similarity,
                    "prompt_text": item.metadata.get("prompt_text"),
                    "model": item.metadata.get("model"),
                    "timestamp": item.metadata.get("timestamp"),
                    "metadata": item.metadata,
                }
            )
        return formatted

    def list_entries(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Return the most recent cache entries for inspection."""
        self._clean_expired()
        entries: List[Dict[str, Any]] = []
        for item in reversed(self.items[-limit:]):
            entries.append(
                {
                    "prompt_text": item.metadata.get("prompt_text"),
                    "model": item.metadata.get("model"),
                    "timestamp": item.metadata.get("timestamp"),
                    "metadata": item.metadata,
                }
            )
        return entries

    async def set(
        self,
        embedding: List[float],
        response: Any,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Store response in semantic cache.

        Args:
            embedding: Embedding vector for the prompt
            response: Response to cache
            metadata: Optional metadata (e.g., model name, cost)
        """
        # Evict if needed
        self._evict_if_needed()

        # Create cached item
        item = CachedItem(
            embedding=embedding,
            response=response,
            timestamp=time.time(),
            metadata=metadata or {}
        )

        # Add to items list
        self.items.append(item)

        # Add to FAISS index
        normalized_vec = self._normalize_vector(embedding)
        self.index.add(normalized_vec)

        logger.debug(
            f"Added to semantic cache: size={len(self.items)}, "
            f"model={metadata.get('model', 'unknown') if metadata else 'unknown'}"
        )

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics.

        Returns:
            Dictionary with cache statistics
        """
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
            "size": len(self.items),
            "max_entries": self.max_entries,
            "hits": self.stats["hits"],
            "misses": self.stats["misses"],
            "hit_rate": hit_rate,
            "average_similarity": avg_similarity,
            "evictions": self.stats["evictions"],
            "similarity_threshold": self.similarity_threshold,
            "ttl_seconds": self.ttl_seconds,
            "backend": "faiss",
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
        logger.info("Updated semantic cache threshold to %.3f", self.similarity_threshold)
        return self.similarity_threshold

    def clear(self):
        """Clear all cached items."""
        self.items.clear()
        self.index.reset()
        self.stats = {
            "hits": 0,
            "misses": 0,
            "total_similarity_scores": 0.0,
            "evictions": 0
        }
        logger.info("Semantic cache cleared")
