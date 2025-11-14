"""On-premise embedding service using sentence-transformers.

This service provides a FastAPI endpoint for generating embeddings
using local sentence-transformers models, avoiding OpenAI API costs.
"""

import logging
import time
from contextlib import asynccontextmanager
from typing import List, Optional

import uvicorn
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from sentence_transformers import SentenceTransformer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global model instance (loaded on startup)
model: Optional[SentenceTransformer] = None

# Default model - fast and efficient for semantic similarity
DEFAULT_MODEL = "all-MiniLM-L6-v2"


class EmbeddingRequest(BaseModel):
    """Request model for embedding generation."""

    text: str = Field(..., description="Text to embed", min_length=1)
    model: str = Field(DEFAULT_MODEL, description="Model to use for embedding")


class EmbeddingResponse(BaseModel):
    """Response model for embedding generation."""

    embedding: List[float] = Field(..., description="Generated embedding vector")
    model: str = Field(..., description="Model used")
    dimensions: int = Field(..., description="Embedding dimensions")
    processing_time_ms: float = Field(..., description="Processing time in milliseconds")


class HealthResponse(BaseModel):
    """Health check response."""

    status: str
    model_loaded: bool
    model_name: str


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load model on startup, cleanup on shutdown."""
    global model
    logger.info(f"Loading sentence-transformer model: {DEFAULT_MODEL}")
    start = time.time()
    model = SentenceTransformer(DEFAULT_MODEL)
    logger.info(f"Model loaded in {time.time() - start:.2f}s")
    yield
    logger.info("Shutting down embedding service")
    model = None


app = FastAPI(
    title="AI Aikido Gateway - Embedding Service",
    description="On-premise embedding generation using sentence-transformers",
    version="0.1.0",
    lifespan=lifespan,
)


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    return HealthResponse(
        status="healthy" if model is not None else "degraded",
        model_loaded=model is not None,
        model_name=DEFAULT_MODEL,
    )


@app.post("/embed", response_model=EmbeddingResponse)
async def generate_embedding(request: EmbeddingRequest):
    """Generate embedding for given text.

    Args:
        request: Embedding request with text and optional model specification

    Returns:
        EmbeddingResponse with vector and metadata

    Raises:
        HTTPException: If model not loaded or embedding fails
    """
    if model is None:
        raise HTTPException(
            status_code=503,
            detail="Model not loaded - service may be starting up",
        )

    if request.model != DEFAULT_MODEL:
        raise HTTPException(
            status_code=400,
            detail=f"Only {DEFAULT_MODEL} is currently supported",
        )

    try:
        start = time.time()
        embedding = model.encode(request.text, convert_to_numpy=True)
        processing_time = (time.time() - start) * 1000

        return EmbeddingResponse(
            embedding=embedding.tolist(),
            model=request.model,
            dimensions=len(embedding),
            processing_time_ms=round(processing_time, 2),
        )
    except Exception as e:
        logger.error(f"Embedding generation failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Embedding generation failed: {str(e)}",
        )


if __name__ == "__main__":
    uvicorn.run(
        "server:app",
        host="0.0.0.0",
        port=8001,
        log_level="info",
        reload=False,
    )
