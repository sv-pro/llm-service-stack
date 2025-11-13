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
from .ollama_checker import check_ollama_on_startup, ollama_checker

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

    # Check Ollama availability
    await check_ollama_on_startup()

    # Configure Ollama API base if available
    if ollama_checker.available:
        import os
        os.environ["OLLAMA_API_BASE"] = settings.OLLAMA_API_BASE


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
        {"id": "gpt-4-turbo", "object": "model", "owned_by": "openai"},
        {"id": "gpt-3.5-turbo", "object": "model", "owned_by": "openai"},
        {"id": "claude-3-opus-20240229", "object": "model", "owned_by": "anthropic"},
        {"id": "claude-3-sonnet-20240229", "object": "model", "owned_by": "anthropic"},
        {"id": "claude-2", "object": "model", "owned_by": "anthropic"},
    ]

    # Add Ollama models if available
    if ollama_checker.available and ollama_checker.installed_models:
        for model_name in ollama_checker.installed_models:
            # Use Ollama prefix for LiteLLM routing
            models.append({
                "id": f"ollama/{model_name}",
                "object": "model",
                "owned_by": "ollama"
            })

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
async def chat_completions(request: ChatCompletionRequest, db = Depends(get_db)):
    """
    OpenAI-compatible chat completion endpoint.
    Routes requests through LiteLLM with caching and cost tracking.
    """
    start_time = datetime.utcnow()

    # Check cache
    cache_key = cache_manager.generate_key(request.model_dump())
    cached_response = await cache_manager.get(cache_key)
    cache_hit = cached_response is not None

    if cached_response:
        # Log cache hit
        _save_usage_log(db, request, cached_response, 0, cache_hit=True)
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

        # Calculate latency
        latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        # Track costs
        cost = cost_tracker.calculate_cost(request.model, response)

        # Save usage log to database
        _save_usage_log(db, request, response, latency_ms, cache_hit=False, cost=cost)

        # Cache response
        await cache_manager.set(cache_key, response)

        return response

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def _save_usage_log(db, request: ChatCompletionRequest, response: dict, latency_ms: float, cache_hit: bool = False, cost: float = None):
    """Save usage log to database."""
    try:
        usage = response.get("usage", {})

        # Extract provider from model name
        provider = "unknown"
        if request.model.startswith("gpt"):
            provider = "openai"
        elif request.model.startswith("claude"):
            provider = "anthropic"
        elif request.model.startswith("ollama/"):
            provider = "ollama"

        # Calculate cost if not provided
        if cost is None:
            cost = cost_tracker.calculate_cost(request.model, response)

        usage_log = UsageLog(
            timestamp=datetime.utcnow(),
            model=request.model,
            provider=provider,
            prompt_tokens=usage.get("prompt_tokens", 0),
            completion_tokens=usage.get("completion_tokens", 0),
            total_tokens=usage.get("total_tokens", 0),
            cost=cost,
            latency_ms=latency_ms,
            cache_hit=1 if cache_hit else 0,
            request_data=request.model_dump(),
            response_data={"choices": response.get("choices", [])} if not cache_hit else None
        )

        db.add(usage_log)
        db.commit()
        db.refresh(usage_log)

    except Exception as e:
        print(f"Error saving usage log: {e}")
        db.rollback()
        # Don't fail the request if logging fails


@app.get("/v1/usage/stats")
async def get_usage_stats():
    """Get usage statistics and cost tracking."""
    stats = cost_tracker.get_stats()
    return stats


@app.get("/v1/usage/logs")
async def get_usage_logs(
    limit: int = 100,
    offset: int = 0,
    model: Optional[str] = None,
    db = Depends(get_db)
):
    """Get usage logs from the database with optional filtering."""
    try:
        query = db.query(UsageLog)

        # Filter by model if specified
        if model:
            query = query.filter(UsageLog.model == model)

        # Get total count for pagination
        total = query.count()

        # Apply pagination and order by timestamp descending
        logs = query.order_by(UsageLog.timestamp.desc()).offset(offset).limit(limit).all()

        # Convert to dict for JSON response
        logs_data = []
        for log in logs:
            logs_data.append({
                "id": log.id,
                "timestamp": log.timestamp.isoformat() if log.timestamp else None,
                "model": log.model,
                "provider": log.provider,
                "prompt_tokens": log.prompt_tokens,
                "completion_tokens": log.completion_tokens,
                "total_tokens": log.total_tokens,
                "cost": log.cost,
                "latency_ms": log.latency_ms,
                "user_id": log.user_id,
                "api_key_id": log.api_key_id,
                "cache_hit": bool(log.cache_hit),
            })

        return {
            "logs": logs_data,
            "total": total,
            "limit": limit,
            "offset": offset,
        }
    except Exception as e:
        print(f"Error fetching usage logs: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch usage logs")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
