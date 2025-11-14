import pytest

from src.core.cache.semantic import SemanticCacheBackend


@pytest.mark.asyncio
async def test_semantic_backend_skips_mismatched_metadata():
    backend = SemanticCacheBackend(
        dimension=3,
        similarity_threshold=0.5,
        search_limit=5,
    )

    await backend.set([1.0, 0.0, 0.0], {"id": "a"}, {"model": "gpt-3.5"})
    await backend.set([0.0, 1.0, 0.0], {"id": "b"}, {"model": "gpt-4"})

    result = await backend.get([0.0, 1.0, 0.0], {"model": "gpt-4"})

    assert result is not None
    response, similarity = result
    assert response["id"] == "b"
    assert similarity > 0.9


@pytest.mark.asyncio
async def test_semantic_backend_checks_multiple_candidates():
    backend = SemanticCacheBackend(
        dimension=2,
        similarity_threshold=0.8,
        search_limit=2,
    )

    base_vec = [0.99, 0.1]
    await backend.set(base_vec, {"id": "wrong"}, {"model": "gpt-3.5"})
    await backend.set(base_vec, {"id": "right"}, {"model": "gpt-4"})

    hit = await backend.get(base_vec, {"model": "gpt-4"})
    assert hit is not None
    assert hit[0]["id"] == "right"
