"""Sentence-transformers embedding provider for on-premise embeddings."""

import asyncio
import logging
import time
from typing import List

import httpx

from .base import EmbeddingProvider, EmbeddingResult

logger = logging.getLogger(__name__)


class SentenceTransformersProvider(EmbeddingProvider):
    """On-premise embedding provider using sentence-transformers service.

    This provider connects to a local embedding service running
    sentence-transformers models (default: all-MiniLM-L6-v2).
    No API costs or rate limits.

    Args:
        service_url: URL of the embedding service (default: http://localhost:8001)
        model: Model name (default: all-MiniLM-L6-v2)
        max_retries: Maximum number of retries on failure
        timeout: Request timeout in seconds

    Raises:
        ValueError: If service_url is not provided
    """

    def __init__(
        self,
        service_url: str = "http://localhost:8001",
        model: str = "all-MiniLM-L6-v2",
        max_retries: int = 3,
        timeout: float = 30.0
    ):
        if not service_url:
            raise ValueError("service_url is required")

        self._service_url = service_url.rstrip("/")
        self._model = model
        self._max_retries = max_retries
        self._timeout = timeout

        # Model dimensions
        self._dimensions = {
            "all-MiniLM-L6-v2": 384,
            "all-mpnet-base-v2": 768,
            "all-MiniLM-L12-v2": 384,
        }

        # HTTP client with connection pooling
        self._client = httpx.AsyncClient(
            timeout=httpx.Timeout(timeout),
            limits=httpx.Limits(
                max_keepalive_connections=10,
                max_connections=20,
            ),
        )

    async def close(self):
        """Close the HTTP client."""
        await self._client.aclose()

    @property
    def dimension(self) -> int:
        """Return embedding dimension."""
        return self._dimensions.get(self._model, 384)

    @property
    def model_name(self) -> str:
        """Return model name."""
        return self._model

    async def embed(self, text: str) -> EmbeddingResult:
        """Generate embedding for a single text.

        Args:
            text: Text to embed

        Returns:
            EmbeddingResult with vector and metadata

        Raises:
            Exception: If service call fails after retries
        """
        if not text or not text.strip():
            logger.warning("Empty text provided for embedding, returning zero vector")
            return EmbeddingResult(vector=[0.0] * self.dimension, model=self._model)

        for attempt in range(self._max_retries):
            try:
                start = time.time()
                response = await self._client.post(
                    f"{self._service_url}/embed",
                    json={
                        "text": text,
                        "model": self._model,
                    },
                )
                response.raise_for_status()

                data = response.json()
                embedding = data["embedding"]
                processing_time = data.get("processing_time_ms", 0)

                # Calculate total latency (network + processing)
                total_latency_ms = (time.time() - start) * 1000

                logger.debug(
                    f"Generated embedding for text (length={len(text)}, "
                    f"dimension={len(embedding)}, "
                    f"processing={processing_time:.2f}ms, "
                    f"total={total_latency_ms:.2f}ms)"
                )

                return EmbeddingResult(
                    vector=embedding,
                    prompt_tokens=0,  # No token cost for on-premise
                    cost=0.0,  # No API cost
                    model=self._model,
                    latency_ms=total_latency_ms,
                )

            except httpx.HTTPStatusError as e:
                logger.error(
                    f"HTTP error on attempt {attempt + 1}: "
                    f"{e.response.status_code} - {e.response.text}"
                )
                if attempt < self._max_retries - 1:
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
                    raise Exception(
                        f"Embedding service error: {e.response.status_code} - {e.response.text}"
                    )

            except httpx.TimeoutException as e:
                logger.warning(f"Timeout on attempt {attempt + 1}: {e}")
                if attempt < self._max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                else:
                    raise Exception(f"Embedding service timeout after {self._max_retries} attempts")

            except httpx.RequestError as e:
                logger.error(f"Request error on attempt {attempt + 1}: {e}")
                if attempt < self._max_retries - 1:
                    await asyncio.sleep(2 ** attempt)
                else:
                    raise Exception(f"Embedding service connection error: {e}")

            except Exception as e:
                logger.error(f"Unexpected error generating embedding: {e}")
                raise

    async def embed_batch(self, texts: List[str]) -> List[EmbeddingResult]:
        """Generate embeddings for multiple texts.

        Currently processes texts sequentially. Could be optimized
        with concurrent requests or batch endpoint in the future.

        Args:
            texts: List of texts to embed

        Returns:
            List of EmbeddingResult objects

        Raises:
            Exception: If service calls fail after retries
        """
        if not texts:
            return []

        # Filter out empty texts but maintain indices
        results = []
        for text in texts:
            if text and text.strip():
                result = await self.embed(text)
                results.append(result)
            else:
                results.append(
                    EmbeddingResult(
                        vector=[0.0] * self.dimension,
                        model=self._model,
                    )
                )

        logger.debug(f"Generated {len(results)} embeddings (dimension={self.dimension})")
        return results
