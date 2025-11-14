"""OpenAI embedding provider implementation."""

import asyncio
import logging
import time
from typing import List, Optional

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

from src.core.costs import calculate_embedding_cost

from .base import EmbeddingProvider, EmbeddingResult

logger = logging.getLogger(__name__)


class OpenAIEmbeddingProvider(EmbeddingProvider):
    """OpenAI embedding provider using text-embedding-ada-002.

    This provider uses OpenAI's embedding API to generate
    1536-dimensional vectors for semantic similarity.

    Args:
        api_key: OpenAI API key
        model: Embedding model name (default: text-embedding-ada-002)
        max_retries: Maximum number of retries on failure
        timeout: Request timeout in seconds

    Raises:
        ImportError: If openai package is not installed
        ValueError: If API key is not provided
    """

    def __init__(
        self,
        api_key: str,
        model: str = "text-embedding-ada-002",
        max_retries: int = 3,
        timeout: float = 30.0
    ):
        if not OPENAI_AVAILABLE:
            raise ImportError(
                "openai package is required for OpenAI embeddings. "
                "Install with: pip install openai"
            )

        if not api_key:
            raise ValueError("OpenAI API key is required")

        self._api_key = api_key
        self._model = model
        self._max_retries = max_retries
        self._timeout = timeout
        self._client = openai.AsyncOpenAI(api_key=api_key, timeout=timeout)

        # Model dimensions
        self._dimensions = {
            "text-embedding-ada-002": 1536,
            "text-embedding-3-small": 1536,
            "text-embedding-3-large": 3072,
        }

    @property
    def dimension(self) -> int:
        """Return embedding dimension."""
        return self._dimensions.get(self._model, 1536)

    @property
    def model_name(self) -> str:
        """Return model name."""
        return self._model

    async def embed(self, text: str) -> EmbeddingResult:
        """Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            Embedding vector as list of floats

        Raises:
            Exception: If API call fails after retries
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for embedding, returning zero vector")
            return EmbeddingResult(vector=[0.0] * self.dimension, model=self._model)

        for attempt in range(self._max_retries):
            try:
                start = time.time()
                response = await self._client.embeddings.create(
                    model=self._model,
                    input=text
                )
                embedding = response.data[0].embedding
                latency_ms = (time.time() - start) * 1000
                prompt_tokens = getattr(getattr(response, "usage", None), "total_tokens", 0) or 0
                cost = calculate_embedding_cost(self._model, prompt_tokens)
                logger.debug(
                    f"Generated embedding for text (length={len(text)}, "
                    f"dimension={len(embedding)})"
                )
                return EmbeddingResult(
                    vector=embedding,
                    prompt_tokens=prompt_tokens,
                    cost=cost,
                    model=self._model,
                    latency_ms=latency_ms,
                )

            except openai.APIError as e:
                logger.error(f"OpenAI API error on attempt {attempt + 1}: {e}")
                if attempt < self._max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
                    raise

            except openai.RateLimitError as e:
                logger.warning(f"Rate limit hit on attempt {attempt + 1}: {e}")
                if attempt < self._max_retries - 1:
                    await asyncio.sleep(5 * (attempt + 1))  # Longer backoff for rate limits
                else:
                    raise

            except Exception as e:
                logger.error(f"Unexpected error generating embedding: {e}")
                raise

    async def embed_batch(self, texts: List[str]) -> List[EmbeddingResult]:
        """Generate embeddings for multiple texts.

        OpenAI API supports batch embeddings, which is more efficient
        than making individual requests.

        Args:
            texts: List of texts to embed

        Returns:
            List of embedding vectors

        Raises:
            Exception: If API call fails after retries
        """
        if not texts:
            return []

        # Filter out empty texts but maintain indices
        non_empty_texts = [t for t in texts if t and t.strip()]

        if not non_empty_texts:
            logger.warning("All texts empty, returning zero vectors")
            return [
                EmbeddingResult(vector=[0.0] * self.dimension, model=self._model)
                for _ in texts
            ]

        for attempt in range(self._max_retries):
            try:
                response = await self._client.embeddings.create(
                    model=self._model,
                    input=non_empty_texts
                )

                embeddings = [item.embedding for item in response.data]
                usage = getattr(response, "usage", None)
                total_tokens = getattr(usage, "total_tokens", 0) or 0

                logger.debug(
                    f"Generated {len(embeddings)} embeddings "
                    f"(dimension={self.dimension})"
                )

                # Reconstruct full list with zero vectors for empty texts
                result = []
                non_empty_idx = 0
                per_entry_tokens = total_tokens // len(non_empty_texts) if non_empty_texts else 0
                per_entry_cost = calculate_embedding_cost(self._model, per_entry_tokens)
                for text in texts:
                    if text and text.strip():
                        result.append(
                            EmbeddingResult(
                                vector=embeddings[non_empty_idx],
                                prompt_tokens=per_entry_tokens,
                                cost=per_entry_cost,
                                model=self._model,
                            )
                        )
                        non_empty_idx += 1
                    else:
                        result.append(
                            EmbeddingResult(
                                vector=[0.0] * self.dimension,
                                model=self._model,
                            )
                        )

                return result

            except openai.APIError as e:
                logger.error(f"OpenAI API error on batch attempt {attempt + 1}: {e}")
                if attempt < self._max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                else:
                    raise

            except openai.RateLimitError as e:
                logger.warning(f"Rate limit hit on batch attempt {attempt + 1}: {e}")
                if attempt < self._max_retries - 1:
                    await asyncio.sleep(5 * (attempt + 1))
                else:
                    raise

            except Exception as e:
                logger.error(f"Unexpected error in batch embedding: {e}")
                raise
