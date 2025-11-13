"""
Tests for Cache Plugin
"""

import pytest
import time
import tempfile
from pathlib import Path
from datetime import datetime, timezone

from src.plugins.cache import CachePlugin, LRUCache
from src.core.context import RequestContext
from src.api.models import ChatCompletionRequest, ChatMessage, ChatCompletionResponse


class TestLRUCache:
    """Test LRU cache implementation"""

    def test_cache_basic_operations(self):
        """Test basic get/set operations"""
        cache = LRUCache(max_size=3)

        # Set values
        cache.set("key1", {"data": "value1"}, ttl_seconds=3600)
        cache.set("key2", {"data": "value2"}, ttl_seconds=3600)

        # Get values
        entry1 = cache.get("key1")
        entry2 = cache.get("key2")

        assert entry1 is not None
        assert entry1["data"] == "value1"
        assert entry2 is not None
        assert entry2["data"] == "value2"
        assert cache.get("key3") is None  # Not in cache

    def test_cache_lru_eviction(self):
        """Test LRU eviction when max size reached"""
        cache = LRUCache(max_size=3)

        # Fill cache
        cache.set("key1", {"data": "value1"}, ttl_seconds=3600)
        cache.set("key2", {"data": "value2"}, ttl_seconds=3600)
        cache.set("key3", {"data": "value3"}, ttl_seconds=3600)

        # All should be present
        assert cache.get("key1") is not None
        assert cache.get("key2") is not None
        assert cache.get("key3") is not None

        # Add one more (should evict key1 as least recently used)
        cache.set("key4", {"data": "value4"}, ttl_seconds=3600)

        assert cache.get("key1") is None  # Evicted
        assert cache.get("key2") is not None
        assert cache.get("key3") is not None
        assert cache.get("key4") is not None

    def test_cache_lru_access_order(self):
        """Test that accessing an item makes it most recent"""
        cache = LRUCache(max_size=3)

        cache.set("key1", {"data": "value1"}, ttl_seconds=3600)
        cache.set("key2", {"data": "value2"}, ttl_seconds=3600)
        cache.set("key3", {"data": "value3"}, ttl_seconds=3600)

        # Access key1 to make it most recent
        cache.get("key1")

        # Add key4 (should evict key2, not key1)
        cache.set("key4", {"data": "value4"}, ttl_seconds=3600)

        assert cache.get("key1") is not None  # Still present (was accessed)
        assert cache.get("key2") is None  # Evicted
        assert cache.get("key3") is not None
        assert cache.get("key4") is not None

    def test_cache_ttl_expiration(self):
        """Test TTL expiration"""
        cache = LRUCache(max_size=10)

        cache.set("key1", {"data": "value1"}, ttl_seconds=1)  # 1 second TTL

        # Should be present immediately
        assert cache.get("key1") is not None

        # Wait for expiration
        time.sleep(1.1)

        # Should be expired
        assert cache.get("key1") is None

    def test_cache_clear(self):
        """Test cache clearing"""
        cache = LRUCache(max_size=10)

        cache.set("key1", {"data": "value1"}, ttl_seconds=3600)
        cache.set("key2", {"data": "value2"}, ttl_seconds=3600)

        assert cache.get("key1") is not None

        cache.clear()

        assert cache.get("key1") is None
        assert cache.get("key2") is None
        assert len(cache) == 0


class TestCachePlugin:
    """Test CachePlugin"""

    @pytest.fixture
    def plugin(self):
        """Create cache plugin instance with memory backend"""
        config = {
            "backend": "memory",
            "default_ttl_seconds": 3600,
            "max_entries": 100,
        }
        return CachePlugin(name="cache", config=config, enabled=True, priority=10)

    @pytest.fixture
    def sqlite_plugin(self):
        """Create cache plugin with SQLite backend"""
        temp_db = tempfile.NamedTemporaryFile(delete=False, suffix=".db")
        config = {
            "backend": "sqlite",
            "db_path": temp_db.name,
            "default_ttl_seconds": 3600,
            "max_storage_entries": 100,
            "max_memory_entries": 10,
        }
        plugin = CachePlugin(name="cache", config=config, enabled=True, priority=10)
        yield plugin
        # Cleanup
        if plugin.sqlite_backend:
            plugin.sqlite_backend.close()
        Path(temp_db.name).unlink(missing_ok=True)

    @pytest.fixture
    def request_context(self):
        """Create a sample request context"""
        request = ChatCompletionRequest(
            model="gpt-3.5-turbo",
            messages=[
                ChatMessage(role="user", content="Hello, how are you?")
            ],
        )
        return RequestContext(
            request_id="test-123",
            timestamp=datetime.now(timezone.utc),
            request=request,
        )

    @pytest.mark.asyncio
    async def test_plugin_initialization(self, plugin):
        """Test plugin initializes correctly"""
        await plugin.on_startup()
        assert plugin.hot_cache is not None
        assert plugin.hot_cache.max_size == 100
        assert plugin.default_ttl == 3600

    @pytest.mark.asyncio
    async def test_sqlite_plugin_initialization(self, sqlite_plugin):
        """Test SQLite plugin initializes correctly"""
        await sqlite_plugin.on_startup()
        assert sqlite_plugin.sqlite_backend is not None
        assert sqlite_plugin.hot_cache is not None
        assert sqlite_plugin.hot_cache.max_size == 10
        assert sqlite_plugin.default_ttl == 3600

    @pytest.mark.asyncio
    async def test_cache_key_generation(self, plugin, request_context):
        """Test cache key generation"""
        await plugin.on_startup()

        # Generate cache key
        await plugin.before_request(request_context)
        key1 = request_context.get_metadata("cache_key")

        # Generate again for same request
        ctx2 = RequestContext(
            request_id="test-456",
            timestamp=datetime.now(timezone.utc),
            request=request_context.request,
        )
        await plugin.before_request(ctx2)
        key2 = ctx2.get_metadata("cache_key")

        # Same request should generate same key
        assert key1 == key2
        assert isinstance(key1, str)
        assert len(key1) == 64  # SHA256 hex digest

    @pytest.mark.asyncio
    async def test_cache_key_different_messages(self, plugin):
        """Test that different messages generate different keys"""
        await plugin.on_startup()

        ctx1 = RequestContext(
            request_id="test-1",
            timestamp=datetime.now(timezone.utc),
            request=ChatCompletionRequest(
                model="gpt-3.5-turbo",
                messages=[ChatMessage(role="user", content="Hello")]
            ),
        )

        ctx2 = RequestContext(
            request_id="test-2",
            timestamp=datetime.now(timezone.utc),
            request=ChatCompletionRequest(
                model="gpt-3.5-turbo",
                messages=[ChatMessage(role="user", content="Goodbye")]
            ),
        )

        await plugin.before_request(ctx1)
        await plugin.before_request(ctx2)

        key1 = ctx1.get_metadata("cache_key")
        key2 = ctx2.get_metadata("cache_key")

        assert key1 != key2

    @pytest.mark.asyncio
    async def test_cache_key_different_models(self, plugin):
        """Test that different models generate different keys"""
        await plugin.on_startup()

        ctx1 = RequestContext(
            request_id="test-1",
            timestamp=datetime.now(timezone.utc),
            request=ChatCompletionRequest(
                model="gpt-3.5-turbo",
                messages=[ChatMessage(role="user", content="Hello")]
            ),
        )

        ctx2 = RequestContext(
            request_id="test-2",
            timestamp=datetime.now(timezone.utc),
            request=ChatCompletionRequest(
                model="gpt-4",
                messages=[ChatMessage(role="user", content="Hello")]
            ),
        )

        await plugin.before_request(ctx1)
        await plugin.before_request(ctx2)

        key1 = ctx1.get_metadata("cache_key")
        key2 = ctx2.get_metadata("cache_key")

        assert key1 != key2

    @pytest.mark.asyncio
    async def test_cache_miss_on_first_request(self, plugin, request_context):
        """Test cache miss on first request"""
        await plugin.on_startup()
        await plugin.before_request(request_context)

        assert request_context.get_metadata("cache_hit") is False
        assert request_context.response is None
        assert request_context.stopped is False

    @pytest.mark.asyncio
    async def test_cache_stores_response(self, plugin, request_context):
        """Test that response is stored in cache"""
        await plugin.on_startup()

        # Simulate no cache hit
        await plugin.before_request(request_context)

        # Simulate API response with usage tokens
        request_context.response = {
            "id": "test-response",
            "model": "gpt-3.5-turbo",
            "choices": [{"message": {"content": "I'm doing well!"}}],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15,
            }
        }

        # Store in cache
        await plugin.after_response(request_context)

        # Check metrics
        stats = plugin.get_cache_stats()
        assert stats["writes"] == 1
        assert stats["hot_cache_size"] == 1

    @pytest.mark.asyncio
    async def test_cache_hit_on_duplicate_request(self, plugin):
        """Test cache hit on duplicate request"""
        await plugin.on_startup()

        # First request
        ctx1 = RequestContext(
            request_id="test-1",
            timestamp=datetime.now(timezone.utc),
            request=ChatCompletionRequest(
                model="gpt-3.5-turbo",
                messages=[ChatMessage(role="user", content="Hello")]
            ),
        )

        await plugin.before_request(ctx1)
        assert ctx1.get_metadata("cache_hit") is False

        # Simulate response with usage
        ctx1.response = {
            "id": "test-response",
            "model": "gpt-3.5-turbo",
            "choices": [{"message": {"content": "Hi there!"}}],
            "usage": {
                "prompt_tokens": 5,
                "completion_tokens": 3,
                "total_tokens": 8,
            }
        }
        await plugin.after_response(ctx1)

        # Second identical request
        ctx2 = RequestContext(
            request_id="test-2",
            timestamp=datetime.now(timezone.utc),
            request=ChatCompletionRequest(
                model="gpt-3.5-turbo",
                messages=[ChatMessage(role="user", content="Hello")]
            ),
        )

        await plugin.before_request(ctx2)

        # Should be cache hit
        assert ctx2.get_metadata("cache_hit") is True
        assert ctx2.response is not None
        assert ctx2.response["choices"][0]["message"]["content"] == "Hi there!"
        assert ctx2.stopped is True  # Should stop pipeline

    @pytest.mark.asyncio
    async def test_cache_not_stored_on_error(self, plugin, request_context):
        """Test that responses with errors are not cached"""
        await plugin.on_startup()

        await plugin.before_request(request_context)

        # Simulate API response with error
        request_context.response = {"error": {"message": "Something went wrong"}}
        request_context.errors.append(Exception("API Error"))

        # Try to store in cache
        await plugin.after_response(request_context)

        # Should not be cached
        stats = plugin.get_cache_stats()
        assert stats["writes"] == 0

    @pytest.mark.asyncio
    async def test_cache_stats(self, plugin):
        """Test cache statistics"""
        await plugin.on_startup()

        stats = plugin.get_cache_stats()

        assert "hits" in stats
        assert "misses" in stats
        assert "hit_rate" in stats
        assert "lookups" in stats
        assert "writes" in stats
        assert "estimated_savings" in stats
        assert "backend" in stats
        assert stats["backend"] == "memory"

    @pytest.mark.asyncio
    async def test_sqlite_backend_stores_and_retrieves(self, sqlite_plugin):
        """Test SQLite backend storage and retrieval"""
        await sqlite_plugin.on_startup()

        # First request - cache miss
        ctx1 = RequestContext(
            request_id="test-1",
            timestamp=datetime.now(timezone.utc),
            request=ChatCompletionRequest(
                model="gpt-3.5-turbo",
                messages=[ChatMessage(role="user", content="Hello SQLite")]
            ),
        )

        await sqlite_plugin.before_request(ctx1)
        assert ctx1.get_metadata("cache_hit") is False

        # Simulate response
        ctx1.response = {
            "id": "test-response",
            "model": "gpt-3.5-turbo",
            "choices": [{"message": {"content": "SQLite works!"}}],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 5,
                "total_tokens": 15,
            }
        }
        await sqlite_plugin.after_response(ctx1)

        # Clear hot cache to force SQLite lookup
        if sqlite_plugin.hot_cache:
            sqlite_plugin.hot_cache.clear()

        # Second request - should hit SQLite cache
        ctx2 = RequestContext(
            request_id="test-2",
            timestamp=datetime.now(timezone.utc),
            request=ChatCompletionRequest(
                model="gpt-3.5-turbo",
                messages=[ChatMessage(role="user", content="Hello SQLite")]
            ),
        )

        await sqlite_plugin.before_request(ctx2)

        # Should be cache hit from SQLite
        assert ctx2.get_metadata("cache_hit") is True
        assert ctx2.response is not None
        assert ctx2.response["choices"][0]["message"]["content"] == "SQLite works!"
        assert ctx2.stopped is True
