"""Tests for the Transparency Plugin"""

import pytest
from src.plugins.transparency import TransparencyPlugin
from core.context import RequestContext
from src.api.models import ChatCompletionRequest, ChatMessage


@pytest.fixture
def transparency_plugin():
    """Create a transparency plugin instance"""
    config = {
        "show_normalizations": True,
        "show_model": True,
        "show_latency": True,
        "show_cache_status": True,
        "custom_prefix": "X-Gateway"
    }
    return TransparencyPlugin(name="transparency", config=config, enabled=True, priority=90)


@pytest.fixture
def request_context():
    """Create a test request context"""
    request_data = ChatCompletionRequest(
        model="gpt-5",
        messages=[ChatMessage(role="user", content="Test message")]
    )
    ctx = RequestContext(request=request_data)
    ctx.metadata["model"] = "gpt-5"
    ctx.response = {"id": "test-123", "choices": []}
    return ctx


@pytest.mark.asyncio
async def test_plugin_initialization(transparency_plugin):
    """Test that plugin initializes correctly"""
    assert transparency_plugin.name == "transparency"
    assert transparency_plugin.enabled is True
    assert transparency_plugin.priority == 90
    assert transparency_plugin.show_normalizations is True
    assert transparency_plugin.show_model is True
    assert transparency_plugin.show_latency is True
    assert transparency_plugin.show_cache_status is True


@pytest.mark.asyncio
async def test_startup_shutdown(transparency_plugin):
    """Test plugin startup and shutdown"""
    await transparency_plugin.on_startup()
    await transparency_plugin.on_shutdown()
    # Should not raise any exceptions


@pytest.mark.asyncio
async def test_adds_model_header(transparency_plugin, request_context):
    """Test that plugin adds original model header"""
    await transparency_plugin.after_response(request_context)
    
    headers = request_context.metadata.get("transparency_headers", {})
    assert "X-Gateway-Original-Model" in headers
    assert headers["X-Gateway-Original-Model"] == "gpt-5"


@pytest.mark.asyncio
async def test_adds_normalization_headers(transparency_plugin, request_context):
    """Test that plugin adds normalization headers when normalizations exist"""
    request_context.metadata["normalizations"] = [
        "Removed unsupported parameter 'temperature'",
        "Removed unsupported parameter 'top_p'"
    ]
    
    await transparency_plugin.after_response(request_context)
    
    headers = request_context.metadata.get("transparency_headers", {})
    assert "X-Gateway-Normalizations" in headers
    assert "temperature" in headers["X-Gateway-Normalizations"]
    assert "top_p" in headers["X-Gateway-Normalizations"]


@pytest.mark.asyncio
async def test_adds_latency_header(transparency_plugin, request_context):
    """Test that plugin adds latency header"""
    request_context.metadata["latency_ms"] = 1234.56
    
    await transparency_plugin.after_response(request_context)
    
    headers = request_context.metadata.get("transparency_headers", {})
    assert "X-Gateway-Latency-Ms" in headers
    assert "1234.56" in headers["X-Gateway-Latency-Ms"]


@pytest.mark.asyncio
async def test_adds_cache_hit_header(transparency_plugin, request_context):
    """Test that plugin adds cache hit header"""
    request_context.metadata["cache_hit"] = True
    
    await transparency_plugin.after_response(request_context)
    
    headers = request_context.metadata.get("transparency_headers", {})
    assert "X-Gateway-Cache-Status" in headers
    assert headers["X-Gateway-Cache-Status"] == "HIT"


@pytest.mark.asyncio
async def test_adds_cache_miss_header(transparency_plugin, request_context):
    """Test that plugin adds cache miss header"""
    request_context.metadata["cache_miss"] = True
    
    await transparency_plugin.after_response(request_context)
    
    headers = request_context.metadata.get("transparency_headers", {})
    assert "X-Gateway-Cache-Status" in headers
    assert headers["X-Gateway-Cache-Status"] == "MISS"


@pytest.mark.asyncio
async def test_custom_prefix(request_context):
    """Test that custom prefix works"""
    config = {
        "show_model": True,
        "custom_prefix": "X-Custom"
    }
    plugin = TransparencyPlugin(name="transparency", config=config)
    
    await plugin.after_response(request_context)
    
    headers = request_context.metadata.get("transparency_headers", {})
    assert "X-Custom-Original-Model" in headers


@pytest.mark.asyncio
async def test_selective_headers(request_context):
    """Test that headers can be selectively disabled"""
    config = {
        "show_normalizations": False,
        "show_model": True,
        "show_latency": False,
        "show_cache_status": False
    }
    plugin = TransparencyPlugin(name="transparency", config=config)
    
    request_context.metadata["normalizations"] = ["Some change"]
    request_context.metadata["latency_ms"] = 100
    request_context.metadata["cache_hit"] = True
    
    await plugin.after_response(request_context)
    
    headers = request_context.metadata.get("transparency_headers", {})
    
    # Only model header should be present
    assert "X-Gateway-Original-Model" in headers
    assert "X-Gateway-Normalizations" not in headers
    assert "X-Gateway-Latency-Ms" not in headers
    assert "X-Gateway-Cache-Status" not in headers


@pytest.mark.asyncio
async def test_no_response_no_headers(transparency_plugin, request_context):
    """Test that no headers are added if there's no response"""
    request_context.response = None
    
    await transparency_plugin.after_response(request_context)
    
    headers = request_context.metadata.get("transparency_headers", {})
    assert len(headers) == 0


@pytest.mark.asyncio
async def test_empty_normalizations_no_header(transparency_plugin, request_context):
    """Test that empty normalizations don't add header"""
    request_context.metadata["normalizations"] = []
    
    await transparency_plugin.after_response(request_context)
    
    headers = request_context.metadata.get("transparency_headers", {})
    assert "X-Gateway-Normalizations" not in headers


@pytest.mark.asyncio
async def test_retry_summary_header(transparency_plugin, request_context):
    """Test that retry summary header is added when metadata exists."""
    request_context.metadata["retry_summary"] = [
        {
            "provider": "openai",
            "model": "gpt-4",
            "attempts": 2,
            "failures": 1,
            "successful": True,
            "is_fallback": False,
            "key_label": "primary",
        }
    ]

    await transparency_plugin.after_response(request_context)

    headers = request_context.metadata.get("transparency_headers", {})
    assert "X-Gateway-Retries" in headers
    assert "openai:gpt-4" in headers["X-Gateway-Retries"]


@pytest.mark.asyncio
async def test_access_control_expose_headers(transparency_plugin, request_context):
    """Ensure custom headers are exposed for browser clients."""
    request_context.metadata["latency_ms"] = 42.0

    await transparency_plugin.after_response(request_context)

    headers = request_context.metadata.get("transparency_headers", {})
    expose = headers.get("Access-Control-Expose-Headers")
    assert expose is not None
    assert "X-Gateway-Original-Model" in expose
    assert "X-Gateway-Latency-Ms" in expose
