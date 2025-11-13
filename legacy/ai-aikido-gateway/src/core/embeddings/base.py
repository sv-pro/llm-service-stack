"""Base embedding provider interface."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class EmbeddingResult:
    """Represents an embedding vector plus accounting metadata."""

    vector: List[float]
    prompt_tokens: int = 0
    cost: float = 0.0
    model: Optional[str] = None
    latency_ms: Optional[float] = None


class EmbeddingProvider(ABC):
    """Abstract base class for embedding providers."""

    @abstractmethod
    async def embed(self, text: str) -> EmbeddingResult:
        """Generate embedding vector for the given text."""

    @abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[EmbeddingResult]:
        """Generate embedding vectors for multiple texts."""

    @property
    @abstractmethod
    def dimension(self) -> int:
        """Return the dimension of embedding vectors."""

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return the name of the embedding model."""
