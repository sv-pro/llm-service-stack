"""Caching layer for LLM responses with verbatim and semantic caching."""

import hashlib
import json
import numpy as np
from typing import Optional, Any, Dict, List, Tuple
import redis.asyncio as redis

from .config import settings


async def generate_embedding(text: str) -> Optional[List[float]]:
    """
    Generate embedding for semantic search using OpenAI.
    Standalone function that can be used by cache, template store, etc.
    """
    try:
        import litellm
        response = await litellm.aembedding(
            model="text-embedding-3-small",  # Use the newer, cheaper model
            input=[text]
        )
        return response['data'][0]['embedding']
    except Exception as e:
        print(f"Embedding generation error: {e}")
        return None


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
        """Generate embedding for semantic search using OpenAI (calls shared function)."""
        return await generate_embedding(text)

    def _cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors."""
        try:
            v1 = np.array(vec1)
            v2 = np.array(vec2)
            return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))
        except Exception as e:
            print(f"Cosine similarity error: {e}")
            return 0.0

    def _extract_cache_scope(self, request_data: dict) -> Dict[str, Any]:
        """
        Extract the "affordances" that should scope the semantic cache.

        Philosophy: The endpoint's affordances (parameters that materially affect
        the response) should determine cache key scope.

        Returns scope dict with:
        - model: Explicit model if specified (critical - different models = different responses)
        - temperature_bucket: Bucketed temp (deterministic vs creative)
        - endpoint_type: Derived from request structure
        """
        scope = {}

        # Model: ALWAYS include if specified (most critical scope)
        if 'model' in request_data:
            scope['model'] = request_data['model']

        # Temperature: Bucket into ranges (affect response randomness)
        # <0.3 = deterministic, 0.3-0.7 = balanced, >0.7 = creative
        temp = request_data.get('temperature', 0.7)
        if temp < 0.3:
            scope['temperature_bucket'] = 'deterministic'
        elif temp <= 0.7:
            scope['temperature_bucket'] = 'balanced'
        else:
            scope['temperature_bucket'] = 'creative'

        # Top_p: Only scope if explicitly set to non-default
        if 'top_p' in request_data and request_data['top_p'] != 1.0:
            scope['top_p_custom'] = True

        # Max tokens: Scope by magnitude (affects response length)
        if 'max_tokens' in request_data:
            max_tok = request_data['max_tokens']
            if max_tok < 500:
                scope['length'] = 'short'
            elif max_tok < 2000:
                scope['length'] = 'medium'
            else:
                scope['length'] = 'long'

        # Detect endpoint type by request structure
        # (Different endpoints have different capabilities)
        if 'response_format' in request_data:
            scope['endpoint'] = 'structured'  # JSON mode
        elif any(msg.get('role') == 'system' for msg in request_data.get('messages', [])):
            scope['endpoint'] = 'chat'
        else:
            scope['endpoint'] = 'completion'

        return scope

    def _scopes_compatible(self, scope1: Dict[str, Any], scope2: Dict[str, Any]) -> bool:
        """
        Check if two cache scopes are compatible for semantic matching.

        Philosophy: Only return cached responses that were generated with
        compatible affordances (model, temperature range, etc.)
        """
        # Model MUST match (critical!)
        if scope1.get('model') != scope2.get('model'):
            return False

        # Temperature bucket should match
        if scope1.get('temperature_bucket') != scope2.get('temperature_bucket'):
            return False

        # If one has custom top_p, both should
        if scope1.get('top_p_custom') != scope2.get('top_p_custom'):
            return False

        # Length expectation should be compatible
        # (Allow medium to match short/long, but not short vs long)
        len1 = scope1.get('length', 'medium')
        len2 = scope2.get('length', 'medium')
        if len1 == 'medium' or len2 == 'medium' or len1 == len2:
            pass  # Compatible
        else:
            return False  # short vs long = incompatible

        # Endpoint type should match
        if scope1.get('endpoint') != scope2.get('endpoint'):
            return False

        return True

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
        try:
            cache_key = self.generate_key(request_data)
            cached = await self.get(cache_key)
            if cached:
                return cached, "verbatim", 1.0
        except Exception as e:
            print(f"Verbatim cache error (non-fatal): {e}")
            # Continue to try semantic cache

        # 2. Try semantic cache if enabled
        if not self.semantic_enabled or cache_control == "verbatim-only":
            return None, "api", None

        try:
            client = await self._get_client()
            if not client:
                # Redis not available, skip semantic cache
                return None, "api", None

            # Extract prompt text and generate embedding
            prompt_text = self._extract_prompt_text(request_data)
            if not prompt_text:
                return None, "api", None

            current_embedding = await self._generate_embedding(prompt_text)
            if not current_embedding:
                # Embedding generation failed, skip semantic cache
                print("Semantic cache: Embedding generation failed, skipping")
                return None, "api", None

            # Extract cache scope (model, temperature, etc.)
            current_scope = self._extract_cache_scope(request_data)

            # Search for similar embeddings in cache with compatible scope
            # Use Redis sorted sets or scan for semantic cache entries
            semantic_key_pattern = "llm:semantic:*"
            best_match = None
            best_similarity = 0.0
            scanned_count = 0
            scope_filtered_count = 0

            async for key in client.scan_iter(match=semantic_key_pattern):
                try:
                    scanned_count += 1
                    cached_data = await client.get(key)
                    if not cached_data:
                        continue

                    cached_item = json.loads(cached_data)
                    cached_embedding = cached_item.get('embedding')
                    if not cached_embedding:
                        continue

                    # Check scope compatibility BEFORE computing similarity
                    # This is the key fix: only compare embeddings for compatible scopes
                    cached_scope = cached_item.get('scope', {})
                    if not self._scopes_compatible(current_scope, cached_scope):
                        scope_filtered_count += 1
                        continue  # Skip incompatible cached items

                    # Calculate similarity
                    similarity = self._cosine_similarity(current_embedding, cached_embedding)

                    # Update best match if this is better
                    if similarity > best_similarity and similarity >= threshold:
                        best_similarity = similarity
                        best_match = cached_item.get('response')

                except Exception as e:
                    print(f"Error checking semantic cache entry {key}: {e}")
                    continue

            # Debug logging
            if scanned_count > 0:
                print(f"Semantic cache: scanned {scanned_count} entries, filtered {scope_filtered_count} by scope")

            if best_match and best_similarity >= threshold:
                return best_match, "semantic", best_similarity

            # No match found
            return None, "api", None

        except Exception as e:
            print(f"Semantic cache search warning (non-fatal): {e}")
            # Return API miss instead of failing the request
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
                try:
                    client = await self._get_client()
                    if not client:
                        # Redis not available, skip semantic cache but don't fail
                        return True

                    # Extract prompt and generate embedding
                    prompt_text = self._extract_prompt_text(request_data)
                    if not prompt_text:
                        return True  # Still return True since verbatim cache was set

                    embedding = await self._generate_embedding(prompt_text)
                    if not embedding:
                        return True  # Still return True since verbatim cache was set

                    # Extract scope (model, temperature bucket, etc.)
                    scope = self._extract_cache_scope(request_data)

                    # Store semantic cache entry WITH SCOPE
                    semantic_key = f"llm:semantic:{cache_key}"
                    semantic_data = {
                        'embedding': embedding,
                        'response': response,
                        'prompt': prompt_text,
                        'model': request_data.get('model', 'unknown'),  # Legacy field
                        'scope': scope  # NEW: Stores all affordances for matching
                    }

                    await client.setex(
                        semantic_key,
                        cache_ttl,
                        json.dumps(semantic_data)
                    )
                except Exception as semantic_error:
                    # Log semantic cache error but don't fail the request
                    print(f"Semantic cache storage warning (non-fatal): {semantic_error}")
                    # Return True since verbatim cache was still set
                    return True

            return True

        except Exception as e:
            print(f"Cache set error: {e}")
            return False
