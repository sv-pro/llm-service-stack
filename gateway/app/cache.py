"""Caching layer for LLM responses with verbatim and semantic caching."""

import hashlib
import json
import numpy as np
from typing import Optional, Any, Dict, List, Tuple
import redis.asyncio as redis

from .config import settings


class CacheManager:
    """Redis-based cache manager with verbatim and semantic caching."""

    def __init__(self):
        self.enabled = settings.CACHE_ENABLED
        self.ttl = settings.CACHE_TTL
        self.redis_client = None
        self.semantic_enabled = True  # Enable semantic cache by default
        self.similarity_threshold = 0.85  # Default threshold for semantic match
        self.embedding_model = "text-embedding-ada-002"  # OpenAI embedding model
    
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

    async def _generate_embedding(self, text: str) -> Optional[List[float]]:
        """Generate embedding for semantic search using OpenAI."""
        try:
            import litellm
            response = await litellm.aembedding(
                model=self.embedding_model,
                input=[text]
            )
            return response['data'][0]['embedding']
        except Exception as e:
            print(f"Embedding generation error: {e}")
            return None

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        try:
            v1 = np.array(vec1)
            v2 = np.array(vec2)
            return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))
        except Exception as e:
            print(f"Cosine similarity error: {e}")
            return 0.0

    def _extract_prompt_text(self, request_data: dict) -> str:
        """Extract the main prompt text from request data for embedding."""
        messages = request_data.get('messages', [])
        if not messages:
            return ""
        # Concatenate all user messages
        prompt_parts = []
        for msg in messages:
            if isinstance(msg, dict):
                role = msg.get('role', '')
                content = msg.get('content', '')
                if role == 'user':
                    prompt_parts.append(content)
        return " ".join(prompt_parts)
    
    async def get(self, key: str) -> Optional[Any]:
        """Get cached response (verbatim only)."""
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

    async def get_with_semantic(
        self,
        request_data: dict,
        similarity_threshold: Optional[float] = None,
        cache_control: str = "auto"
    ) -> Tuple[Optional[Any], str, Optional[float]]:
        """
        Get cached response with semantic matching support.

        Returns:
            Tuple of (cached_response, cache_type, similarity_score)
            cache_type: "verbatim", "semantic", or "api" (miss)
        """
        if not self.enabled or cache_control == "no-cache":
            return None, "api", None

        threshold = similarity_threshold or self.similarity_threshold

        # 1. Try verbatim cache first (exact match)
        cache_key = self.generate_key(request_data)
        cached = await self.get(cache_key)
        if cached:
            return cached, "verbatim", 1.0

        # 2. Try semantic cache if enabled
        if not self.semantic_enabled or cache_control == "verbatim-only":
            return None, "api", None

        try:
            client = await self._get_client()
            if not client:
                return None, "api", None

            # Extract prompt text and generate embedding
            prompt_text = self._extract_prompt_text(request_data)
            if not prompt_text:
                return None, "api", None

            current_embedding = await self._generate_embedding(prompt_text)
            if not current_embedding:
                return None, "api", None

            # Search for similar embeddings in cache
            # Use Redis sorted sets or scan for semantic cache entries
            semantic_key_pattern = "llm:semantic:*"
            best_match = None
            best_similarity = 0.0

            async for key in client.scan_iter(match=semantic_key_pattern):
                try:
                    cached_data = await client.get(key)
                    if not cached_data:
                        continue

                    cached_item = json.loads(cached_data)
                    cached_embedding = cached_item.get('embedding')
                    if not cached_embedding:
                        continue

                    # Calculate similarity
                    similarity = self._cosine_similarity(current_embedding, cached_embedding)

                    # Update best match if this is better
                    if similarity > best_similarity and similarity >= threshold:
                        best_similarity = similarity
                        best_match = cached_item.get('response')

                except Exception as e:
                    print(f"Error checking semantic cache entry {key}: {e}")
                    continue

            if best_match and best_similarity >= threshold:
                return best_match, "semantic", best_similarity

            # No match found
            return None, "api", None

        except Exception as e:
            print(f"Semantic cache search error: {e}")
            return None, "api", None
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set cached response."""
        if not self.enabled:
            return False

        try:
            client = await self._get_client()
            if client:
                cache_ttl = ttl or self.ttl
                await client.setex(
                    key,
                    cache_ttl,
                    json.dumps(value)
                )
                return True
        except Exception as e:
            print(f"Cache set error: {e}")

        return False

    async def set_with_semantic(
        self,
        request_data: dict,
        response: Any,
        ttl: Optional[int] = None
    ) -> bool:
        """
        Set cached response with semantic cache entry.
        Stores both verbatim and semantic cache entries.
        """
        if not self.enabled:
            return False

        cache_ttl = ttl or self.ttl

        try:
            # 1. Store verbatim cache (exact match)
            cache_key = self.generate_key(request_data)
            await self.set(cache_key, response, cache_ttl)

            # 2. Store semantic cache if enabled
            if self.semantic_enabled:
                client = await self._get_client()
                if not client:
                    return False

                # Extract prompt and generate embedding
                prompt_text = self._extract_prompt_text(request_data)
                if not prompt_text:
                    return True  # Still return True since verbatim cache was set

                embedding = await self._generate_embedding(prompt_text)
                if not embedding:
                    return True  # Still return True since verbatim cache was set

                # Store semantic cache entry
                semantic_key = f"llm:semantic:{cache_key}"
                semantic_data = {
                    'embedding': embedding,
                    'response': response,
                    'prompt': prompt_text,
                    'model': request_data.get('model', 'unknown')
                }

                await client.setex(
                    semantic_key,
                    cache_ttl,
                    json.dumps(semantic_data)
                )

            return True

        except Exception as e:
            print(f"Cache set with semantic error: {e}")
            return False
