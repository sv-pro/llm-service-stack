"""Main FastAPI application for LLM Gateway."""

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
import litellm
from datetime import datetime

from .config import settings
from .database import init_db, get_db
from .models import UsageLog
from .cache import CacheManager
from .cost_tracker import CostTracker

app = FastAPI(
    title="LLM Gateway Service",
    description="OpenAI-compatible LLM gateway with routing, caching, and cost tracking",
    version="0.1.0"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
cache_manager = CacheManager()
cost_tracker = CostTracker()


@app.on_event("startup")
async def startup_event():
    """Initialize database and components on startup."""
    init_db()
    litellm.set_verbose = settings.LITELLM_VERBOSE


@app.get("/")
async def root():
    """Health check endpoint."""
    return {
        "service": "LLM Gateway",
        "version": "0.1.0",
        "status": "running"
    }


@app.get("/v1/models")
async def list_models():
    """List available models (OpenAI-compatible endpoint)."""
    models = [
        {"id": "gpt-4", "object": "model", "owned_by": "openai"},
        {"id": "gpt-3.5-turbo", "object": "model", "owned_by": "openai"},
        {"id": "claude-2", "object": "model", "owned_by": "anthropic"},
    ]
    return {"object": "list", "data": models}


# Request/Response models for OpenAI-compatible API
class Message(BaseModel):
    role: str
    content: str


class ChatCompletionRequest(BaseModel):
    model: str
    messages: List[Message]
    temperature: Optional[float] = 0.7
    max_tokens: Optional[int] = None
    stream: Optional[bool] = False


@app.post("/v1/chat/completions")
async def chat_completions(request: ChatCompletionRequest):
    """
    OpenAI-compatible chat completion endpoint.
    Routes requests through LiteLLM with caching and cost tracking.
    """
    # Check cache
    cache_key = cache_manager.generate_key(request.model_dump())
    cached_response = await cache_manager.get(cache_key)
    if cached_response:
        return cached_response
    
    try:
        # Route through LiteLLM
        messages = [msg.model_dump() for msg in request.messages]
        response = await litellm.acompletion(
            model=request.model,
            messages=messages,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            stream=request.stream
        )
        
        # Track costs
        cost = cost_tracker.calculate_cost(request.model, response)
        
        # Log usage (would save to database)
        usage_log = {
            "model": request.model,
            "tokens": response.get("usage", {}).get("total_tokens", 0),
            "cost": cost,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Cache response
        await cache_manager.set(cache_key, response)
        
        return response
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/v1/usage/stats")
async def get_usage_stats():
    """Get usage statistics and cost tracking."""
    stats = cost_tracker.get_stats()
    return stats


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
