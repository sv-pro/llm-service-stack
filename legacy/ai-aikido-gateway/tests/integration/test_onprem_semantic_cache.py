"""Integration tests for on-premise semantic cache setup.

Tests the full stack:
- SentenceTransformersProvider with embedding service
- QdrantBackend with Qdrant vector database
- SemanticCachePlugin with on-premise configuration
"""

import asyncio
import pytest

# Mark all tests in this module as integration tests
pytestmark = pytest.mark.integration


@pytest.fixture
def embedding_service_url():
    """URL of the embedding service (must be running)."""
    return "http://localhost:8001"


@pytest.fixture
def qdrant_config():
    """Qdrant configuration (must be running)."""
    return {
        "host": "localhost",
        "port": 6333,
        "collection_name": "test_semantic_cache",
    }


@pytest.mark.asyncio
async def test_sentence_transformers_provider(embedding_service_url):
    """Test SentenceTransformersProvider can generate embeddings."""
    from src.core.embeddings import SentenceTransformersProvider

    provider = SentenceTransformersProvider(
        service_url=embedding_service_url,
        model="all-MiniLM-L6-v2",
    )

    try:
        # Test single embedding
        result = await provider.embed("This is a test sentence")

        assert result is not None
        assert result.vector is not None
        assert len(result.vector) == 384  # all-MiniLM-L6-v2 dimension
        assert result.cost == 0.0  # No API cost for on-premise
        assert result.prompt_tokens == 0  # No token counting
        assert result.latency_ms > 0

        # Test consistency
        result2 = await provider.embed("This is a test sentence")
        assert result.vector == result2.vector

        # Test different text
        result3 = await provider.embed("Different sentence")
        assert result.vector != result3.vector

    finally:
        await provider.close()


@pytest.mark.asyncio
async def test_qdrant_backend_basic_operations(qdrant_config):
    """Test QdrantBackend basic CRUD operations."""
    from src.core.cache.qdrant import QdrantBackend

    backend = QdrantBackend(
        host=qdrant_config["host"],
        port=qdrant_config["port"],
        collection_name=qdrant_config["collection_name"],
        dimension=384,
        similarity_threshold=0.8,
        max_entries=100,
        ttl_seconds=3600,
    )

    try:
        # Clear any existing data
        backend.clear()

        # Test set/get
        test_embedding = [0.1] * 384
        test_response = {"text": "Hello, world!"}
        test_metadata = {"model": "test-model", "prompt_text": "test prompt"}

        await backend.set(test_embedding, test_response, test_metadata)

        # Retrieve with exact same embedding (should have high similarity)
        result = await backend.get(test_embedding, {"model": "test-model"})

        assert result is not None
        cached_response, similarity = result
        assert cached_response == test_response
        assert similarity > 0.99  # Should be very high for identical vectors

        # Test miss with different metadata
        result2 = await backend.get(test_embedding, {"model": "different-model"})
        assert result2 is None

        # Test miss with very different embedding (orthogonal direction)
        different_embedding = [0.1 if i % 2 == 0 else -0.1 for i in range(384)]
        result3 = await backend.get(different_embedding, {"model": "test-model"})
        assert result3 is None  # Should miss due to low similarity

        # Test stats
        stats = backend.get_stats()
        assert stats["size"] == 1
        assert stats["hits"] == 1
        assert stats["misses"] == 2

        # Cleanup
        backend.clear()

    finally:
        backend.close()


@pytest.mark.asyncio
async def test_qdrant_backend_similarity_search(qdrant_config):
    """Test QdrantBackend similarity search with multiple entries."""
    from src.core.cache.qdrant import QdrantBackend
    import math

    backend = QdrantBackend(
        host=qdrant_config["host"],
        port=qdrant_config["port"],
        collection_name=qdrant_config["collection_name"],
        dimension=384,
        similarity_threshold=0.7,
    )

    try:
        backend.clear()

        # Add multiple entries with varying similarity
        embeddings = []
        for i in range(5):
            # Create embeddings with varying directions (not just magnitude)
            # Each vector emphasizes different dimensions
            embedding = []
            for j in range(384):
                # Create patterns that vary by index
                if j < (i + 1) * 76:  # Different cutoff for each vector
                    embedding.append(0.1)
                else:
                    embedding.append(-0.1 if j % 2 == i % 2 else 0.05)

            # Normalize to unit length for proper cosine similarity
            norm = math.sqrt(sum(x**2 for x in embedding))
            embedding = [x / norm for x in embedding]
            embeddings.append(embedding)

            await backend.set(
                embedding,
                {"response": f"Response {i}"},
                {"model": "test", "prompt_text": f"prompt {i}"},
            )

        # Search for candidates
        query_embedding = embeddings[0]
        candidates = await backend.search_candidates(
            query_embedding,
            metadata={"model": "test"},
            limit=3,
            include_below_threshold=True,
        )

        assert len(candidates) <= 3
        assert candidates[0]["similarity"] > candidates[-1]["similarity"]  # Sorted
        assert all("prompt_text" in c for c in candidates)

        # Cleanup
        backend.clear()

    finally:
        backend.close()


@pytest.mark.asyncio
async def test_full_onprem_semantic_cache_integration(embedding_service_url, qdrant_config):
    """Test full integration of embedding service + Qdrant + semantic cache plugin."""
    from src.plugins.semantic_cache import SemanticCachePlugin
    from src.core.context import RequestContext
    from src.api.models import ChatCompletionRequest, ChatMessage

    config = {
        "embedding_provider": "sentence_transformers",
        "embedding_service_url": embedding_service_url,
        "embedding_model": "all-MiniLM-L6-v2",
        "cache_backend": "qdrant",
        "qdrant_host": qdrant_config["host"],
        "qdrant_port": qdrant_config["port"],
        "qdrant_collection": qdrant_config["collection_name"],
        "similarity_threshold": 0.85,
        "max_cache_entries": 100,
        "ttl_seconds": 3600,
        "enable_timeseries": False,  # Disable for test
    }

    plugin = SemanticCachePlugin(
        name="semantic_cache",
        config=config,
        enabled=True,
        priority=6,
    )

    try:
        # Clear cache
        plugin.cache_backend.clear()

        # Create test context with proper Pydantic models
        request1 = ChatCompletionRequest(
            model="gpt-4",
            messages=[ChatMessage(role="user", content="What is the capital of France?")],
        )
        ctx = RequestContext(
            request_id="test-001",
            request=request1,
        )

        # First request - cache miss
        await plugin.before_request(ctx)

        # Simulate response
        ctx.response = {
            "choices": [{"message": {"content": "Paris"}}],
            "model": "gpt-4",
        }

        await plugin.after_response(ctx)

        # Second identical request - should hit cache
        request2 = ChatCompletionRequest(
            model="gpt-4",
            messages=[ChatMessage(role="user", content="What is the capital of France?")],
        )
        ctx2 = RequestContext(
            request_id="test-002",
            request=request2,
        )

        await plugin.before_request(ctx2)

        # Should have cached response
        assert ctx2.response is not None
        assert ctx2.metadata.get("cache_hit") is True
        assert ctx2.response["choices"][0]["message"]["content"] == "Paris"

        # Get stats
        stats = plugin.cache_backend.get_stats()
        assert stats["hits"] >= 1
        assert stats["size"] >= 1

        # Cleanup
        plugin.cache_backend.clear()

    finally:
        if hasattr(plugin.embedding_provider, "close"):
            await plugin.embedding_provider.close()
        plugin.cache_backend.close()


if __name__ == "__main__":
    # Run tests manually (requires services to be running)
    print("Running on-premise semantic cache integration tests...")
    print("Ensure embedding service (port 8001) and Qdrant (port 6333) are running!")

    asyncio.run(test_sentence_transformers_provider("http://localhost:8001"))
    print("✓ SentenceTransformersProvider test passed")

    qdrant_cfg = {"host": "localhost", "port": 6333, "collection_name": "test_semantic_cache"}
    asyncio.run(test_qdrant_backend_basic_operations(qdrant_cfg))
    print("✓ QdrantBackend basic operations test passed")

    asyncio.run(test_qdrant_backend_similarity_search(qdrant_cfg))
    print("✓ QdrantBackend similarity search test passed")

    asyncio.run(test_full_onprem_semantic_cache_integration("http://localhost:8001", qdrant_cfg))
    print("✓ Full integration test passed")

    print("\nAll tests passed!")
