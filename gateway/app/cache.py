"""Caching layer for LLM responses."""

import hashlib
import json
from typing import Optional, Any
import redis.asyncio as redis

from .config import settings


class CacheManager:
    """Redis-based cache manager for LLM responses."""
    
    def __init__(self):
        self.enabled = settings.CACHE_ENABLED
        self.ttl = settings.CACHE_TTL
        self.redis_client = None
    
    async def _get_client(self):
        """Get or create Redis client."""
        if not self.redis_client and self.enabled:
            try:
                self.redis_client = await redis.from_url(
                    settings.REDIS_URL,
                    encoding="utf-8",
                    decode_responses=True
                )
            except Exception as e:
                print(f"Redis connection failed: {e}")
                self.enabled = False
        return self.redis_client
    
    def generate_key(self, request_data: dict) -> str:
        """Generate cache key from request data."""
        # Create deterministic hash of request
        request_str = json.dumps(request_data, sort_keys=True)
        return f"llm:cache:{hashlib.sha256(request_str.encode()).hexdigest()}"
    
    async def get(self, key: str) -> Optional[Any]:
        """Get cached response."""
        if not self.enabled:
            return None
        
        try:
            client = await self._get_client()
            if client:
                cached = await client.get(key)
                if cached:
                    return json.loads(cached)
        except Exception as e:
            print(f"Cache get error: {e}")
        
        return None
    
    async def set(self, key: str, value: Any) -> bool:
        """Set cached response."""
        if not self.enabled:
            return False
        
        try:
            client = await self._get_client()
            if client:
                await client.setex(
                    key,
                    self.ttl,
                    json.dumps(value)
                )
                return True
        except Exception as e:
            print(f"Cache set error: {e}")
        
        return False
