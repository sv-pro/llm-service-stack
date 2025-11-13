"""Main FastAPI application for LLM Gateway."""

from fastapi import FastAPI, HTTPException, Depends, Header
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
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
    expose_headers=["X-Gateway-Cache-Status", "X-Gateway-Cache-Type", "X-Gateway-Cache-Similarity"],
)

# Initialize components
cache_manager = CacheManager()
cost_tracker = CostTracker()


def check_vendor_availability() -> Dict[str, bool]:
    """Check which vendors have valid API keys configured."""
    vendors = {
        'openai': bool(settings.OPENAI_API_KEY and settings.OPENAI_API_KEY.strip()),
        'anthropic': bool(settings.ANTHROPIC_API_KEY and settings.ANTHROPIC_API_KEY.strip()),
        'ollama': ollama_checker.available
    }
    return vendors


@app.on_event("startup")
async def startup_event():
    """Initialize database and components on startup."""
    import os

    init_db()
    litellm.set_verbose = settings.LITELLM_VERBOSE

    # Set API keys in environment for LiteLLM
    if settings.OPENAI_API_KEY:
        os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY
    if settings.ANTHROPIC_API_KEY:
        os.environ["ANTHROPIC_API_KEY"] = settings.ANTHROPIC_API_KEY

    # Check Ollama availability
    await check_ollama_on_startup()

    # Configure Ollama API base if available
    if ollama_checker.available:
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
    """
    List available models with metadata (vendor, type, endpoint, availability).

    Model types:
    - simple: Standard chat models (use /v1/chat/completions)
    - reasoning: Advanced reasoning models (use /v1/responses for full features, or /v1/chat/completions for compatibility)

    Availability:
    - Models are marked unavailable if vendor API key is missing
    - Ollama models are only available if downloaded locally
    """
    # Check which vendors have valid API keys
    vendor_availability = check_vendor_availability()

    models = [
        # OpenAI Models
        {
            "id": "gpt-4",
            "object": "model",
            "owned_by": "openai",
            "vendor": "openai",
            "type": "simple",
            "endpoint": "chat",
            "available": vendor_availability['openai'],
            "unavailable_reason": None if vendor_availability['openai'] else "API key not configured"
        },
        {
            "id": "gpt-4-turbo",
            "object": "model",
            "owned_by": "openai",
            "vendor": "openai",
            "type": "simple",
            "endpoint": "chat",
            "available": vendor_availability['openai'],
            "unavailable_reason": None if vendor_availability['openai'] else "API key not configured"
        },
        {
            "id": "gpt-3.5-turbo",
            "object": "model",
            "owned_by": "openai",
            "vendor": "openai",
            "type": "simple",
            "endpoint": "chat",
            "available": vendor_availability['openai'],
            "unavailable_reason": None if vendor_availability['openai'] else "API key not configured"
        },
        {
            "id": "o1-preview",
            "object": "model",
            "owned_by": "openai",
            "vendor": "openai",
            "type": "reasoning",
            "endpoint": "responses",
            "available": vendor_availability['openai'],
            "unavailable_reason": None if vendor_availability['openai'] else "API key not configured"
        },
        {
            "id": "o1-mini",
            "object": "model",
            "owned_by": "openai",
            "vendor": "openai",
            "type": "reasoning",
            "endpoint": "responses",
            "available": vendor_availability['openai'],
            "unavailable_reason": None if vendor_availability['openai'] else "API key not configured"
        },
        {
            "id": "gpt-5-preview",
            "object": "model",
            "owned_by": "openai",
            "vendor": "openai",
            "type": "reasoning",
            "endpoint": "responses",
            "available": vendor_availability['openai'],
            "unavailable_reason": None if vendor_availability['openai'] else "API key not configured"
        },
        {
            "id": "gpt-5",
            "object": "model",
            "owned_by": "openai",
            "vendor": "openai",
            "type": "reasoning",
            "endpoint": "responses",
            "available": vendor_availability['openai'],
            "unavailable_reason": None if vendor_availability['openai'] else "API key not configured"
        },
        # Anthropic Models
        {
            "id": "claude-3-opus-20240229",
            "object": "model",
            "owned_by": "anthropic",
            "vendor": "anthropic",
            "type": "simple",
            "endpoint": "messages",
            "available": vendor_availability['anthropic'],
            "unavailable_reason": None if vendor_availability['anthropic'] else "API key not configured"
        },
        {
            "id": "claude-3-sonnet-20240229",
            "object": "model",
            "owned_by": "anthropic",
            "vendor": "anthropic",
            "type": "simple",
            "endpoint": "messages",
            "available": vendor_availability['anthropic'],
            "unavailable_reason": None if vendor_availability['anthropic'] else "API key not configured"
        },
        {
            "id": "claude-3-haiku-20240307",
            "object": "model",
            "owned_by": "anthropic",
            "vendor": "anthropic",
            "type": "simple",
            "endpoint": "messages",
            "available": vendor_availability['anthropic'],
            "unavailable_reason": None if vendor_availability['anthropic'] else "API key not configured"
        },
        {
            "id": "claude-2.1",
            "object": "model",
            "owned_by": "anthropic",
            "vendor": "anthropic",
            "type": "simple",
            "endpoint": "messages",
            "available": vendor_availability['anthropic'],
            "unavailable_reason": None if vendor_availability['anthropic'] else "API key not configured"
        },
    ]

    # Add Ollama models (only downloaded ones are available)
    if ollama_checker.available and ollama_checker.installed_models:
        for model_name in ollama_checker.installed_models:
            # Use Ollama prefix for LiteLLM routing
            models.append({
                "id": f"ollama/{model_name}",
                "object": "model",
                "owned_by": "ollama",
                "vendor": "ollama",
                "type": "simple",
                "endpoint": "chat",
                "available": True,  # If in installed_models list, it's downloaded
                "unavailable_reason": None
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


# Request/Response models for Responses API (GPT-5, reasoning models)
class ReasoningConfig(BaseModel):
    effort: Optional[str] = "low"  # "minimal" | "low" | "medium" | "high"
    type: Optional[str] = "basic"  # "basic" | "extended"


class ResponsesRequest(BaseModel):
    model: str
    input: Any  # Can be string or messages array
    reasoning: Optional[ReasoningConfig] = None
    max_output_tokens: Optional[int] = None
    temperature: Optional[float] = None  # May be ignored for reasoning models
    stream: Optional[bool] = False


@app.post("/v1/chat/completions")
async def chat_completions(
    request: ChatCompletionRequest,
    db = Depends(get_db),
    x_cache_control: Optional[str] = Header(None, alias="X-Cache-Control"),
    x_cache_ttl: Optional[int] = Header(None, alias="X-Cache-TTL"),
    x_cache_similarity_threshold: Optional[float] = Header(None, alias="X-Cache-Similarity-Threshold")
):
    """
    OpenAI-compatible chat completion endpoint with semantic caching.
    Routes requests through LiteLLM with caching and cost tracking.

    Custom Headers:
    - X-Cache-Control: "no-cache", "auto", "verbatim-only" (default: "auto")
    - X-Cache-TTL: Custom cache TTL in seconds
    - X-Cache-Similarity-Threshold: Minimum similarity for semantic match (0.0-1.0, default: 0.85)
    """
    start_time = datetime.utcnow()

    # Parse cache control
    cache_control = (x_cache_control or "auto").lower()
    cache_ttl = x_cache_ttl
    similarity_threshold = x_cache_similarity_threshold

    # Check cache with semantic support
    request_data = request.model_dump()
    cached_response, cache_type, similarity = await cache_manager.get_with_semantic(
        request_data,
        similarity_threshold=similarity_threshold,
        cache_control=cache_control
    )

    if cached_response:
        # Log cache hit
        _save_usage_log(db, request, cached_response, 0, cache_hit=True)

        # Add custom headers to indicate cache status
        headers = {
            "X-Gateway-Cache-Status": "HIT",
            "X-Gateway-Cache-Type": cache_type,
        }
        if similarity is not None:
            headers["X-Gateway-Cache-Similarity"] = f"{similarity:.3f}"

        return JSONResponse(content=cached_response, headers=headers)

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

        # Convert LiteLLM response to dict (properly handle Pydantic models)
        if hasattr(response, 'model_dump'):
            # Pydantic v2 - recursively converts nested models
            response_dict = response.model_dump()
        elif hasattr(response, 'dict'):
            # Pydantic v1 - recursively converts nested models
            response_dict = response.dict()
        else:
            # Fallback: JSON round-trip for any remaining serialization issues
            import json as json_lib
            response_dict = json_lib.loads(json_lib.dumps(response, default=str))

        # Track costs
        cost = cost_tracker.calculate_cost(request.model, response_dict)

        # Save usage log to database
        _save_usage_log(db, request, response_dict, latency_ms, cache_hit=False, cost=cost)

        # Cache response with semantic indexing
        await cache_manager.set_with_semantic(request_data, response_dict, ttl=cache_ttl)

        # Add headers for cache miss
        headers = {
            "X-Gateway-Cache-Status": "MISS",
            "X-Gateway-Cache-Type": "api",
        }

        return JSONResponse(content=response_dict, headers=headers)

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/v1/responses")
async def responses_api(request: ResponsesRequest, db = Depends(get_db)):
    """
    OpenAI Responses API endpoint for reasoning models (GPT-5, o1, etc.).
    Supports reasoning.effort, max_output_tokens, and returns reasoning_tokens in usage.
    """
    start_time = datetime.utcnow()

    # Convert input to messages format if it's a string
    if isinstance(request.input, str):
        messages = [{"role": "user", "content": request.input}]
    elif isinstance(request.input, list):
        # Assume it's already in messages format
        messages = [msg if isinstance(msg, dict) else msg.model_dump() for msg in request.input]
    else:
        raise HTTPException(status_code=400, detail="Input must be a string or messages array")

    # Check cache (using messages format for consistency)
    cache_data = {
        "model": request.model,
        "messages": messages,
        "reasoning": request.reasoning.model_dump() if request.reasoning else None,
        "max_output_tokens": request.max_output_tokens,
    }
    cache_key = cache_manager.generate_key(cache_data)
    cached_response = await cache_manager.get(cache_key)
    cache_hit = cached_response is not None

    if cached_response:
        # Log cache hit
        # Note: We'll need a separate logging function for responses API
        return cached_response

    try:
        # Prepare request for LiteLLM
        # Note: LiteLLM may not directly support Responses API yet, so we'll use chat completions
        # and add metadata for reasoning tracking
        litellm_kwargs = {
            "model": request.model,
            "messages": messages,
            "max_tokens": request.max_output_tokens,
            "stream": request.stream
        }

        # For reasoning models, we might want to add special handling
        # LiteLLM handles o1 and reasoning models automatically
        if request.reasoning and request.reasoning.effort:
            # Store reasoning config in metadata (LiteLLM may use this in the future)
            litellm_kwargs["metadata"] = {
                "reasoning_effort": request.reasoning.effort,
                "reasoning_type": request.reasoning.type or "basic"
            }

        # Route through LiteLLM
        response = await litellm.acompletion(**litellm_kwargs)

        # Calculate latency
        latency_ms = (datetime.utcnow() - start_time).total_seconds() * 1000

        # Convert LiteLLM response to dict (properly handle Pydantic models)
        if hasattr(response, 'model_dump'):
            # Pydantic v2 - recursively converts nested models
            response_dict = response.model_dump()
        elif hasattr(response, 'dict'):
            # Pydantic v1 - recursively converts nested models
            response_dict = response.dict()
        else:
            # Fallback: JSON round-trip for any remaining serialization issues
            import json as json_lib
            response_dict = json_lib.loads(json_lib.dumps(response, default=str))

        # Track costs (reasoning models may have different pricing)
        cost = cost_tracker.calculate_cost(request.model, response_dict)

        # Transform response to Responses API format
        # Add reasoning_tokens tracking if available
        usage = response_dict.get("usage", {})
        if "reasoning_tokens" not in usage and request.model in ["gpt-5", "gpt-5-preview", "gpt-5-mini", "o1-preview", "o1-mini"]:
            # Estimate reasoning tokens (in production, this should come from the API)
            # For now, we'll use a simple heuristic
            usage["reasoning_tokens"] = 0  # Will be populated by OpenAI's API

        # Create Responses API formatted response
        responses_response = {
            "id": response_dict.get("id", "resp_" + str(int(datetime.utcnow().timestamp()))),
            "object": "chat.completion",
            "created": response_dict.get("created", int(datetime.utcnow().timestamp())),
            "model": request.model,
            "choices": response_dict.get("choices", []),
            "usage": usage
        }

        # Save usage log (convert to chat completion format for logging)
        chat_request = ChatCompletionRequest(
            model=request.model,
            messages=[Message(role=msg["role"], content=msg["content"]) for msg in messages],
            max_tokens=request.max_output_tokens
        )
        _save_usage_log(db, chat_request, responses_response, latency_ms, cache_hit=False, cost=cost)

        # Cache response
        await cache_manager.set(cache_key, responses_response)

        return responses_response

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
