"""Tests for semantic cache backend."""

import time

import pytest

from src.core.cache.semantic import CachedItem, SemanticCacheBackend


class TestSemanticCacheBackend:
    """Tests for FAISS-based semantic cache."""

    @pytest.fixture
    def cache(self):
        """Create cache instance."""
        return SemanticCacheBackend(
            dimension=128,  # Smaller dimension for testing
            similarity_threshold=0.85,
            max_entries=10,
            ttl_seconds=1  # Short TTL for testing
        )

    @pytest.fixture
    def sample_embedding(self):
        """Create a sample embedding vector."""
        return [0.1] * 128

    @pytest.fixture
    def similar_embedding(self):
        """Create a similar embedding (slightly different)."""
        embedding = [0.1] * 128
        embedding[0] = 0.11  # Slight difference
        return embedding

    @pytest.fixture
    def different_embedding(self):
        """Create a very different embedding."""
        # Create an embedding that's orthogonal to sample_embedding [0.1] * 128
        # Using alternating positive/negative values to ensure low cosine similarity
        return [(-1.0 if i % 2 == 0 else 1.0) for i in range(128)]

    @pytest.mark.asyncio
    async def test_cache_miss_empty(self, cache, sample_embedding):
        """Test cache miss when cache is empty."""
        result = await cache.get(sample_embedding)

        assert result is None
        assert cache.stats["misses"] == 1
        assert cache.stats["hits"] == 0

    @pytest.mark.asyncio
    async def test_cache_set_and_get(self, cache, sample_embedding):
        """Test setting and getting from cache."""
        response = {"text": "Hello, world!"}
        metadata = {"model": "gpt-3.5-turbo"}

        # Store in cache
        await cache.set(sample_embedding, response, metadata)

        # Retrieve from cache
        result = await cache.get(sample_embedding, metadata)

        assert result is not None
        cached_response, similarity = result
        assert cached_response == response
        assert similarity > 0.99  # Should be very similar to itself

    @pytest.mark.asyncio
    async def test_semantic_similarity_match(self, cache, sample_embedding, similar_embedding):
        """Test that similar embeddings match."""
        response = {"text": "Test response"}
        metadata = {"model": "gpt-4"}

        # Store with original embedding
        await cache.set(sample_embedding, response, metadata)

        # Query with similar embedding
        result = await cache.get(similar_embedding, metadata)

        assert result is not None
        cached_response, similarity = result
        assert cached_response == response
        assert similarity >= cache.similarity_threshold

    @pytest.mark.asyncio
    async def test_dissimilar_embedding_miss(self, cache, sample_embedding, different_embedding):
        """Test that dissimilar embeddings don't match."""
        response = {"text": "Test response"}

        # Store with one embedding
        await cache.set(sample_embedding, response)

        # Query with very different embedding
        result = await cache.get(different_embedding)

        assert result is None  # Similarity should be below threshold

    @pytest.mark.asyncio
    async def test_metadata_filtering(self, cache, sample_embedding):
        """Test that metadata filtering works."""
        response = {"text": "Test response"}

        # Store with specific metadata
        await cache.set(sample_embedding, response, {"model": "gpt-3.5-turbo"})

        # Query with matching metadata should work
        result = await cache.get(sample_embedding, {"model": "gpt-3.5-turbo"})
        assert result is not None

        # Query with different metadata should miss
        result = await cache.get(sample_embedding, {"model": "gpt-4"})
        assert result is None

    @pytest.mark.asyncio
    async def test_ttl_expiration(self, cache, sample_embedding):
        """Test that cache entries expire."""
        response = {"text": "Test response"}

        # Store in cache
        await cache.set(sample_embedding, response)

        # Should be retrievable immediately
        result = await cache.get(sample_embedding)
        assert result is not None

        # Wait for TTL to expire
        time.sleep(1.1)

        # Should now be expired
        result = await cache.get(sample_embedding)
        assert result is None

    @pytest.mark.asyncio
    async def test_max_entries_eviction(self, cache):
        """Test that oldest entries are evicted when max is reached."""
        # Fill cache to max
        for i in range(15):  # More than max_entries (10)
            embedding = [float(i) / 100.0] * 128
            response = {"text": f"Response {i}"}
            await cache.set(embedding, response)

        # Cache should have evicted some entries
        assert len(cache.items) == cache.max_entries
        assert cache.stats["evictions"] > 0

    @pytest.mark.asyncio
    async def test_cache_stats(self, cache, sample_embedding, different_embedding):
        """Test cache statistics."""
        response = {"text": "Test"}

        # Generate some hits and misses
        await cache.set(sample_embedding, response)
        await cache.get(sample_embedding)  # Hit
        await cache.get(different_embedding)  # Miss (truly dissimilar)

        stats = cache.get_stats()

        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["hit_rate"] == 0.5
        assert stats["size"] == 1
        assert "average_similarity" in stats

    def test_cache_clear(self, cache):
        """Test clearing the cache."""
        # Add some items
        for i in range(5):
            embedding = [float(i) / 100.0] * 128
            response = {"text": f"Response {i}"}
            cache.items.append(
                CachedItem(
                    embedding=embedding,
                    response=response,
                    timestamp=time.time(),
                    metadata={}
                )
            )

        # Clear cache
        cache.clear()

        assert len(cache.items) == 0
        assert cache.index.ntotal == 0
        assert cache.stats["hits"] == 0

    @pytest.mark.asyncio
    async def test_multiple_similar_items(self, cache):
        """Test handling multiple similar items."""
        base_embedding = [0.5] * 128
        responses = []

        # Add multiple similar items
        for i in range(5):
            embedding = base_embedding.copy()
            embedding[0] += i * 0.01  # Slight variations
            response = {"text": f"Response {i}"}
            responses.append(response)
            await cache.set(embedding, response, {"index": i})

        # Query should return the most similar
        result = await cache.get(base_embedding, {"index": 0})

        assert result is not None
        cached_response, similarity = result
        assert cached_response == responses[0]

    @pytest.mark.asyncio
    async def test_normalized_vectors(self, cache):
        """Test that vectors are properly normalized."""
        # Two vectors with different magnitudes but same direction
        embedding1 = [1.0] * 128
        embedding2 = [2.0] * 128  # Same direction, double magnitude

        response = {"text": "Test"}
        await cache.set(embedding1, response)

        # Should match due to normalization (cosine similarity)
        result = await cache.get(embedding2)

        assert result is not None
        _, similarity = result
        assert similarity > 0.99  # Should be nearly identical after normalization

    def test_update_similarity_threshold(self, cache):
        """Threshold updates should clamp between 0 and 1."""
        new_threshold = cache.update_similarity_threshold(0.9)
        assert pytest.approx(new_threshold, rel=1e-3) == 0.9
        assert cache.similarity_threshold == pytest.approx(0.9, rel=1e-3)

        with pytest.raises(ValueError):
            cache.update_similarity_threshold(1.5)

    @pytest.mark.asyncio
    async def test_search_candidates(self, cache, sample_embedding):
        """Search candidates should return prompt text metadata."""
        await cache.set(
            sample_embedding,
            {"text": "Hello"},
            metadata={"prompt_text": "user: hello world", "model": "gpt-3.5-turbo"},
        )

        candidates = await cache.search_candidates(sample_embedding, limit=3)
        assert len(candidates) == 1
        assert candidates[0]["prompt_text"] == "user: hello world"
        assert candidates[0]["model"] == "gpt-3.5-turbo"

    def test_list_entries(self, cache, sample_embedding):
        """List entries should expose prompt text."""
        cache.items.append(
            CachedItem(
                embedding=sample_embedding,
                response={"text": "hi"},
                timestamp=time.time(),
                metadata={"prompt_text": "user: hi there", "model": "gpt-3.5-turbo"},
            )
        )
        entries = cache.list_entries(limit=5)
        assert entries
        assert entries[0]["prompt_text"] == "user: hi there"
