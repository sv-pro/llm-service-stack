"""
Tests for the Request History Plugin

Tests storage, retrieval, and querying of request history.
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime

from src.plugins.history import RequestHistoryPlugin
from src.core.context import RequestContext
from src.api.models import ChatCompletionRequest, ChatMessage


@pytest.fixture
def temp_db():
    """Create a temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_history.db"
        yield db_path


@pytest.fixture
async def history_plugin(temp_db):
    """Create a history plugin instance for testing."""
    plugin = RequestHistoryPlugin(
        name="history",
        config={"db_path": str(temp_db)}
    )
    await plugin.on_startup()
    yield plugin
    await plugin.on_shutdown()


@pytest.mark.asyncio
async def test_plugin_startup_creates_database(temp_db):
    """Test that plugin startup creates the database file."""
    assert not temp_db.exists()
    
    plugin = RequestHistoryPlugin(
        name="history",
        config={"db_path": str(temp_db)}
    )
    
    await plugin.on_startup()
    
    assert temp_db.exists()
    
    await plugin.on_shutdown()


@pytest.mark.asyncio
async def test_store_request_basic(history_plugin):
    """Test storing a basic request/response."""
    # Create a request context
    request = ChatCompletionRequest(
        model="gpt-3.5-turbo",
        messages=[
            ChatMessage(role="user", content="Hello, world!")
        ]
    )
    
    response = {
        "id": "chatcmpl-123",
        "choices": [{
            "message": {"role": "assistant", "content": "Hello! How can I help you?"},
            "finish_reason": "stop"
        }],
        "usage": {
            "prompt_tokens": 10,
            "completion_tokens": 8,
            "total_tokens": 18
        },
        "model": "gpt-3.5-turbo"
    }
    
    ctx = RequestContext(
        request=request,
        response=response,
        metadata={"latency_ms": 1234, "cached": False}
    )
    
    # Store the request
    await history_plugin.after_response(ctx)
    
    # Retrieve and verify
    requests = history_plugin.get_requests(limit=10)
    assert len(requests) == 1
    
    stored = requests[0]
    assert stored["model"] == "gpt-3.5-turbo"
    assert stored["prompt_tokens"] == 10
    assert stored["completion_tokens"] == 8
    assert stored["total_tokens"] == 18
    assert stored["latency_ms"] == 1234
    assert stored["cached"] == 0
    assert stored["embedding_cost"] == 0.0
    assert stored["total_cost"] == stored["estimated_cost"]
    assert "Hello, world!" in stored["messages"]
    assert "Hello! How can I help you?" in stored["response_text"]
    assert stored["cache_type"] == "api"


@pytest.mark.asyncio
async def test_store_cached_request(history_plugin):
    """Test storing a cached request."""
    request = ChatCompletionRequest(
        model="gpt-4",
        messages=[ChatMessage(role="user", content="What is 2+2?")]
    )
    
    response = {
        "choices": [{
            "message": {"role": "assistant", "content": "4"},
            "finish_reason": "stop"
        }],
        "usage": {"prompt_tokens": 5, "completion_tokens": 1, "total_tokens": 6}
    }
    
    ctx = RequestContext(
        request=request,
        response=response,
        metadata={
            "latency_ms": 15,
            "cached": True,
            "cache_key": "cache_key_123",
            "cache_type": "verbatim",
        }
    )
    
    await history_plugin.after_response(ctx)
    
    requests = history_plugin.get_requests(limit=10)
    assert len(requests) == 1
    assert requests[0]["cached"] == 1
    assert requests[0]["cache_key"] == "cache_key_123"
    assert requests[0]["latency_ms"] == 15  # Should be fast
    assert requests[0]["cache_type"] == "verbatim"


@pytest.mark.asyncio
async def test_filter_by_model(history_plugin):
    """Test filtering requests by model."""
    # Store multiple requests with different models
    for model in ["gpt-3.5-turbo", "gpt-4", "gpt-3.5-turbo"]:
        request = ChatCompletionRequest(
            model=model,
            messages=[ChatMessage(role="user", content=f"Test with {model}")]
        )
        ctx = RequestContext(request=request, response={}, metadata={})
        await history_plugin.after_response(ctx)
    
    # Filter by GPT-3.5
    results = history_plugin.get_requests(model="gpt-3.5-turbo")
    assert len(results) == 2
    assert all(r["model"] == "gpt-3.5-turbo" for r in results)
    
    # Filter by GPT-4
    results = history_plugin.get_requests(model="gpt-4")
    assert len(results) == 1
    assert results[0]["model"] == "gpt-4"


@pytest.mark.asyncio
async def test_filter_by_cached(history_plugin):
    """Test filtering by cached status."""
    # Store cached and non-cached requests
    for i, cached in enumerate([True, False, True, False, True]):
        request = ChatCompletionRequest(
            model="gpt-3.5-turbo",
            messages=[ChatMessage(role="user", content=f"Request {i}")]
        )
        ctx = RequestContext(
            request=request,
            response={},
            metadata={"cached": cached}
        )
        await history_plugin.after_response(ctx)
    
    # Filter cached only
    cached_results = history_plugin.get_requests(cached=True)
    assert len(cached_results) == 3
    assert all(r["cached"] == 1 for r in cached_results)
    
    # Filter non-cached only
    non_cached_results = history_plugin.get_requests(cached=False)
    assert len(non_cached_results) == 2
    assert all(r["cached"] == 0 for r in non_cached_results)


@pytest.mark.asyncio
async def test_filter_by_cache_type(history_plugin):
    """Ensure filtering by cache type works."""
    scenarios = [
        (True, "verbatim"),
        (True, "semantic"),
        (False, "api"),
    ]
    for cached, cache_type in scenarios:
        request = ChatCompletionRequest(
            model="gpt-3.5-turbo",
            messages=[ChatMessage(role="user", content=f"{cache_type} request")]
        )
        ctx = RequestContext(
            request=request,
            response={},
            metadata={"cached": cached, "cache_type": cache_type}
        )
        await history_plugin.after_response(ctx)

    semantic = history_plugin.get_requests(cache_type="semantic")
    assert len(semantic) == 1
    assert semantic[0]["cache_type"] == "semantic"

    api_calls = history_plugin.get_requests(cache_type="api")
    assert all(r["cache_type"] == "api" for r in api_calls)


@pytest.mark.asyncio
async def test_search_in_messages(history_plugin):
    """Test searching in messages and responses."""
    # Store requests with different content
    messages_content = [
        "Tell me about Python",
        "Explain JavaScript",
        "What is Python used for?"
    ]
    
    for content in messages_content:
        request = ChatCompletionRequest(
            model="gpt-3.5-turbo",
            messages=[ChatMessage(role="user", content=content)]
        )
        ctx = RequestContext(request=request, response={}, metadata={})
        await history_plugin.after_response(ctx)
    
    # Search for "Python"
    results = history_plugin.get_requests(search="Python")
    assert len(results) == 2
    
    # Search for "JavaScript"
    results = history_plugin.get_requests(search="JavaScript")
    assert len(results) == 1


@pytest.mark.asyncio
async def test_pagination(history_plugin):
    """Test pagination with limit and offset."""
    # Store 10 requests
    for i in range(10):
        request = ChatCompletionRequest(
            model="gpt-3.5-turbo",
            messages=[ChatMessage(role="user", content=f"Request {i}")]
        )
        ctx = RequestContext(request=request, response={}, metadata={})
        await history_plugin.after_response(ctx)
    
    # Get first page (5 items)
    page1 = history_plugin.get_requests(limit=5, offset=0)
    assert len(page1) == 5
    
    # Get second page (5 items)
    page2 = history_plugin.get_requests(limit=5, offset=5)
    assert len(page2) == 5
    
    # Verify no overlap
    page1_ids = {r["id"] for r in page1}
    page2_ids = {r["id"] for r in page2}
    assert len(page1_ids & page2_ids) == 0


@pytest.mark.asyncio
async def test_get_request_by_id(history_plugin):
    """Test retrieving a single request by ID."""
    request = ChatCompletionRequest(
        model="gpt-4",
        messages=[ChatMessage(role="user", content="Unique request")]
    )
    ctx = RequestContext(request=request, response={}, metadata={})
    await history_plugin.after_response(ctx)
    
    # Get all requests to find the ID
    requests = history_plugin.get_requests(limit=1)
    request_id = requests[0]["request_id"]
    
    # Retrieve by ID
    retrieved = history_plugin.get_request_by_id(request_id)
    assert retrieved is not None
    assert retrieved["request_id"] == request_id
    assert "Unique request" in retrieved["messages"]


@pytest.mark.asyncio
async def test_get_stats(history_plugin):
    """Test getting summary statistics."""
    # Store varied requests
    for i in range(5):
        request = ChatCompletionRequest(
            model="gpt-3.5-turbo" if i % 2 == 0 else "gpt-4",
            messages=[ChatMessage(role="user", content=f"Request {i}")]
        )
        ctx = RequestContext(
            request=request,
            response={"usage": {"total_tokens": 100}},
            metadata={"latency_ms": 1000 + i * 100, "cached": i % 2 == 0}
        )
        await history_plugin.after_response(ctx)
    
    stats = history_plugin.get_stats()
    
    assert stats["total_requests"] == 5
    assert stats["cached_requests"] == 3  # Indices 0, 2, 4
    assert stats["total_tokens"] == 500  # 5 * 100
    assert stats["unique_models"] == 2  # gpt-3.5-turbo and gpt-4
    assert stats["avg_latency_ms"] > 1000  # Average should be around 1200


@pytest.mark.asyncio
async def test_history_persists_cost_summary(history_plugin):
    """Verify cost ledger data flows into history table."""
    request = ChatCompletionRequest(
        model="gpt-3.5-turbo",
        messages=[ChatMessage(role="user", content="Track my costs")],
    )
    response = {
        "choices": [
            {
                "message": {"role": "assistant", "content": "Done"},
                "finish_reason": "stop",
            }
        ],
        "usage": {"prompt_tokens": 12, "completion_tokens": 4, "total_tokens": 16},
        "model": "gpt-3.5-turbo",
    }
    ctx = RequestContext(request=request, response=response, metadata={"latency_ms": 42})
    ctx.add_cost_entry(
        {
            "type": "completion",
            "cost": 0.003,
            "prompt_tokens": 12,
            "completion_tokens": 4,
            "model": "gpt-3.5-turbo",
        }
    )
    ctx.add_cost_entry(
        {
            "type": "embedding",
            "cost": 0.0001,
            "prompt_tokens": 12,
            "model": "text-embedding-3-small",
        }
    )

    await history_plugin.after_response(ctx)
    stored = history_plugin.get_requests(limit=1)[0]

    assert stored["embedding_tokens"] == 12
    assert stored["embedding_cost"] == pytest.approx(0.0001)
    assert stored["total_cost"] == pytest.approx(0.0031)


@pytest.mark.asyncio
async def test_error_handling(history_plugin):
    """Test that plugin handles errors gracefully."""
    # Create an invalid context (missing required fields)
    ctx = RequestContext(request={}, response=None, metadata={})
    
    # Should not raise an exception
    await history_plugin.after_response(ctx)
    
    # Verify request was not stored (or stored with nulls)
    requests = history_plugin.get_requests()
    # The plugin should handle this gracefully
