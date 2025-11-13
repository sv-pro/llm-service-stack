# Three-Path Responses API Architecture

**Date:** 2025-11-08
**Status:** Design Phase
**Priority:** 4 (Responses API Alignment)

---

## Executive Summary

This document defines a **three-path hybrid architecture** for the AI Aikido Gateway's OpenAI compatibility layer. Rather than choosing between syntactic compatibility, semantic alignment, or custom features, we implement **all three paths in parallel**:

1. **Path 1: Semantic Gateway** - Full OpenAI Responses API compliance
2. **Path 2: Syntactic Sugar** - Legacy format compatibility for "wrong" requests
3. **Path 3: Intent Handling** - Gateway's unique value proposition

This approach provides maximum flexibility: OpenAI compatibility, backward compatibility, and differentiated features—all in one unified architecture.

---

## Motivation

### The Dilemma

The OpenAI Responses API introduces a new paradigm:
- Structured reasoning metadata (`usage.reasoning_tokens`)
- Tool execution transparency (`output` field)
- Structured output support (`structured_outputs`)
- Cleaner separation of concerns

We face three strategic options:
- **Syntactic**: Simple shim, minimal changes, quick compatibility
- **Semantic**: Full compliance, proper metadata, future-proof
- **Hybrid**: Intelligent routing, best of both worlds

### The Solution: All Three Paths

Rather than choosing, we implement **three distinct paths**:

| Path | Endpoint | Purpose | Target Audience |
|------|----------|---------|-----------------|
| **1. Semantic** | `/v1/responses` | Full OpenAI compliance | Users wanting latest OpenAI features |
| **2. Syntactic** | `/v1/chat/completions` | Legacy compatibility | Existing integrations, "wrong" requests |
| **3. Intent** | `/v1/intents` | Custom gateway features | Users leveraging Intent→Template→Playbook |

This architecture:
- ✅ Follows OpenAI official guidance (Path 1)
- ✅ Maintains backward compatibility (Path 2)
- ✅ Preserves unique differentiation (Path 3)
- ✅ No exclusions, no compromises

---

## Architecture Overview

```
                    ┌─────────────────────────────────┐
                    │   Incoming Request              │
                    └─────────────┬───────────────────┘
                                  │
                    ┌─────────────▼───────────────────┐
                    │   Request Router                │
                    │   (Endpoint + Header Detection) │
                    └─────────────┬───────────────────┘
                                  │
                ┌─────────────────┼─────────────────┐
                │                 │                 │
        ┌───────▼──────┐  ┌──────▼──────┐  ┌──────▼──────┐
        │ Path 1       │  │ Path 2      │  │ Path 3      │
        │ Semantic     │  │ Syntactic   │  │ Intent      │
        │ /v1/responses│  │ /v1/chat/*  │  │ /v1/intents │
        └───────┬──────┘  └──────┬──────┘  └──────┬──────┘
                │                 │                 │
                └────────┬────────┴────────┬────────┘
                         │                 │
              ┌──────────▼─────────────────▼──────────┐
              │   Shared Infrastructure               │
              │   - Plugin System                     │
              │   - Semantic Cache                    │
              │   - Cost Tracking                     │
              │   - Logging/Telemetry                 │
              └───────────────────────────────────────┘
```

---

## Path 1: Semantic Gateway (OpenAI Responses API)

### Purpose
Full compliance with OpenAI's official Responses API specification.

### Endpoint
```
POST /v1/responses
```

### Request Format
Follows OpenAI's new specification exactly:
```json
{
  "model": "gpt-4",
  "messages": [
    {"role": "user", "content": "Explain quantum computing"}
  ],
  "reasoning": {
    "type": "basic",
    "reasoning_effort": "medium"
  },
  "tools": [...],
  "structured_outputs": {...}
}
```

### Response Format
```json
{
  "id": "resp_abc123",
  "object": "chat.completion",
  "created": 1699891234,
  "model": "gpt-4",
  "choices": [{
    "index": 0,
    "message": {
      "role": "assistant",
      "content": "Quantum computing is...",
      "reasoning": "Let me break this down...",
      "tool_calls": [...]
    },
    "finish_reason": "stop"
  }],
  "usage": {
    "prompt_tokens": 15,
    "completion_tokens": 42,
    "reasoning_tokens": 120,
    "total_tokens": 177
  }
}
```

### Key Features
1. **Reasoning Token Tracking**
   - Separate `reasoning_tokens` field in usage
   - Cost calculation: reasoning tokens may have different pricing
   - Transparency into model's thinking process

2. **Tool Execution Metadata**
   - `output` field for each tool call result
   - Cleaner tool interaction tracking
   - Better debugging and observability

3. **Structured Output Support**
   - JSON schema validation
   - Guaranteed format compliance
   - Type-safe responses

4. **Reasoning Effort Control**
   - `reasoning_effort`: "low" | "medium" | "high"
   - Trade-off between cost and quality
   - Future o1/o3 model support

### Implementation Strategy

#### Phase 1: Core Response Structure
```python
# src/api/models.py

class ReasoningConfig(BaseModel):
    type: Literal["basic", "advanced"] = "basic"
    reasoning_effort: Literal["low", "medium", "high"] = "medium"

class ResponseRequest(BaseModel):
    model: str
    messages: List[ChatMessage]
    reasoning: Optional[ReasoningConfig] = None
    tools: Optional[List[Tool]] = None
    structured_outputs: Optional[Dict[str, Any]] = None
    # ... other OpenAI parameters

class ResponseUsage(BaseModel):
    prompt_tokens: int
    completion_tokens: int
    reasoning_tokens: Optional[int] = None
    total_tokens: int

class ResponseMessage(BaseModel):
    role: str
    content: Optional[str] = None
    reasoning: Optional[str] = None  # New field
    tool_calls: Optional[List[ToolCall]] = None

class ResponseChoice(BaseModel):
    index: int
    message: ResponseMessage
    finish_reason: str

class ResponseObject(BaseModel):
    id: str
    object: Literal["chat.completion"] = "chat.completion"
    created: int
    model: str
    choices: List[ResponseChoice]
    usage: ResponseUsage
```

#### Phase 2: Reasoning Token Extraction
```python
# src/core/responses.py

async def extract_reasoning_tokens(
    response: Dict[str, Any],
    model: str
) -> Optional[int]:
    """
    Extract reasoning token count from provider response.

    For models like o1/o3:
    - Parse usage.reasoning_tokens if available
    - Estimate from response metadata
    - Fall back to None if not supported
    """
    if "usage" in response and "reasoning_tokens" in response["usage"]:
        return response["usage"]["reasoning_tokens"]

    # Model-specific extraction
    if model.startswith("o1") or model.startswith("o3"):
        # OpenAI reasoning models have explicit tracking
        return response.get("usage", {}).get("completion_tokens_details", {}).get("reasoning_tokens")

    return None
```

#### Phase 3: Route Handler
```python
# src/api/routes.py

@app.post("/v1/responses")
async def responses_endpoint(
    request: ResponseRequest,
    request_id: str = Depends(generate_request_id),
) -> ResponseObject:
    """
    OpenAI Responses API endpoint (semantic gateway).
    Full compliance with official specification.
    """
    ctx = RequestContext(
        request_id=request_id,
        request=request,
        endpoint_type="responses"  # New field to distinguish paths
    )

    # Plugin lifecycle: before_request
    for plugin in get_active_plugins():
        await plugin.before_request(ctx)

    # Forward to provider
    response = await forward_to_provider(ctx)

    # Extract reasoning tokens
    reasoning_tokens = await extract_reasoning_tokens(response, request.model)

    # Build ResponseObject
    response_obj = ResponseObject(
        id=response["id"],
        created=response["created"],
        model=response["model"],
        choices=[
            ResponseChoice(
                index=choice["index"],
                message=ResponseMessage(
                    role=choice["message"]["role"],
                    content=choice["message"].get("content"),
                    reasoning=choice["message"].get("reasoning"),
                    tool_calls=choice["message"].get("tool_calls"),
                ),
                finish_reason=choice["finish_reason"],
            )
            for choice in response["choices"]
        ],
        usage=ResponseUsage(
            prompt_tokens=response["usage"]["prompt_tokens"],
            completion_tokens=response["usage"]["completion_tokens"],
            reasoning_tokens=reasoning_tokens,
            total_tokens=response["usage"]["total_tokens"],
        ),
    )

    ctx.response = response_obj

    # Plugin lifecycle: after_response
    for plugin in get_active_plugins():
        await plugin.after_response(ctx)

    return response_obj
```

### Testing Strategy

```python
# tests/api/test_responses_endpoint.py

async def test_responses_basic():
    """Test basic Responses API request."""
    request = {
        "model": "gpt-4",
        "messages": [{"role": "user", "content": "Hello"}]
    }
    response = await client.post("/v1/responses", json=request)
    assert response.status_code == 200
    data = response.json()
    assert data["object"] == "chat.completion"
    assert "usage" in data
    assert "total_tokens" in data["usage"]

async def test_responses_reasoning_tokens():
    """Test reasoning token tracking."""
    request = {
        "model": "o1-preview",
        "messages": [{"role": "user", "content": "Complex problem"}],
        "reasoning": {"type": "advanced", "reasoning_effort": "high"}
    }
    response = await client.post("/v1/responses", json=request)
    data = response.json()
    assert data["usage"]["reasoning_tokens"] is not None
    assert data["usage"]["reasoning_tokens"] > 0

async def test_responses_with_tools():
    """Test tool execution metadata."""
    request = {
        "model": "gpt-4",
        "messages": [{"role": "user", "content": "What's the weather?"}],
        "tools": [{"type": "function", "function": {...}}]
    }
    response = await client.post("/v1/responses", json=request)
    data = response.json()
    if data["choices"][0]["message"].get("tool_calls"):
        for tool_call in data["choices"][0]["message"]["tool_calls"]:
            assert "output" in tool_call  # New field in Responses API
```

---

## Path 2: Syntactic Sugar (Legacy Compatibility)

### Purpose
Maintain compatibility with existing `/v1/chat/completions` integrations. Handle "wrong" requests gracefully.

### Endpoint
```
POST /v1/chat/completions
```

### Request Format
Standard OpenAI Chat Completions format:
```json
{
  "model": "gpt-4",
  "messages": [
    {"role": "user", "content": "Hello"}
  ],
  "temperature": 0.7,
  "max_tokens": 150
}
```

### Response Format
Standard Chat Completions response (no reasoning fields):
```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1699891234,
  "model": "gpt-4",
  "choices": [{
    "index": 0,
    "message": {
      "role": "assistant",
      "content": "Hello! How can I help you?"
    },
    "finish_reason": "stop"
  }],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 9,
    "total_tokens": 19
  }
}
```

### Key Features

1. **Backward Compatibility**
   - Existing integrations work without changes
   - No breaking API changes
   - Gradual migration path to `/v1/responses`

2. **Internal Modernization**
   - Convert to ResponseRequest internally
   - Track reasoning tokens if available
   - Store in metadata but don't expose in response

3. **Upgrade Path**
   - Response header: `X-Upgrade-Available: /v1/responses`
   - Documentation links in response metadata
   - Smooth migration guidance

### Implementation Strategy

```python
# src/api/routes.py

@app.post("/v1/chat/completions")
async def chat_completions_endpoint(
    request: ChatCompletionRequest,
    request_id: str = Depends(generate_request_id),
) -> ChatCompletionResponse:
    """
    OpenAI Chat Completions endpoint (syntactic sugar).
    Maintains backward compatibility with legacy format.
    """
    ctx = RequestContext(
        request_id=request_id,
        request=request,
        endpoint_type="chat_completions"  # Distinguish from responses
    )

    # Internal: Check if this could benefit from Responses API
    if _should_suggest_upgrade(request):
        ctx.metadata["upgrade_suggestion"] = "/v1/responses"

    # Plugin lifecycle
    for plugin in get_active_plugins():
        await plugin.before_request(ctx)

    # Forward to provider
    response = await forward_to_provider(ctx)

    # Internal: Track reasoning tokens if available (don't expose)
    reasoning_tokens = await extract_reasoning_tokens(response, request.model)
    if reasoning_tokens:
        ctx.metadata["internal_reasoning_tokens"] = reasoning_tokens
        # Cost tracking plugins can use this metadata

    # Build standard Chat Completions response
    response_obj = ChatCompletionResponse(
        id=response["id"],
        created=response["created"],
        model=response["model"],
        choices=[...],
        usage=Usage(
            prompt_tokens=response["usage"]["prompt_tokens"],
            completion_tokens=response["usage"]["completion_tokens"],
            total_tokens=response["usage"]["total_tokens"],
            # NOTE: No reasoning_tokens in public response
        ),
    )

    ctx.response = response_obj

    # Plugin lifecycle
    for plugin in get_active_plugins():
        await plugin.after_response(ctx)

    # Optional: Add upgrade suggestion header
    if ctx.metadata.get("upgrade_suggestion"):
        response.headers["X-Upgrade-Available"] = "/v1/responses"

    return response_obj

def _should_suggest_upgrade(request: ChatCompletionRequest) -> bool:
    """
    Determine if request would benefit from Responses API.
    """
    # Models with reasoning capabilities
    if request.model.startswith("o1") or request.model.startswith("o3"):
        return True

    # Tool-heavy requests
    if request.tools and len(request.tools) > 2:
        return True

    # Structured output requests
    if request.response_format and request.response_format.get("type") == "json_schema":
        return True

    return False
```

### Testing Strategy

```python
# tests/api/test_chat_completions_legacy.py

async def test_legacy_format_unchanged():
    """Ensure existing integrations work without changes."""
    request = {
        "model": "gpt-4",
        "messages": [{"role": "user", "content": "Hello"}]
    }
    response = await client.post("/v1/chat/completions", json=request)
    assert response.status_code == 200
    data = response.json()

    # Standard format, no new fields
    assert "reasoning_tokens" not in data["usage"]
    assert "reasoning" not in data["choices"][0]["message"]

async def test_upgrade_suggestion_header():
    """Test upgrade suggestion for reasoning models."""
    request = {
        "model": "o1-preview",
        "messages": [{"role": "user", "content": "Complex task"}]
    }
    response = await client.post("/v1/chat/completions", json=request)
    assert response.headers.get("X-Upgrade-Available") == "/v1/responses"

async def test_internal_reasoning_tracking():
    """Test that reasoning tokens are tracked internally."""
    # This would require inspecting telemetry/logs
    # Reasoning tokens captured but not exposed in response
    pass
```

---

## Path 3: Intent Handling (Custom Gateway)

### Purpose
Gateway's unique value proposition: Intent→Template→Playbook execution with semantic understanding.

### Endpoint
```
POST /v1/intents
```

### Request Format
Intent-based request (gateway-specific):
```json
{
  "intent": "analyze_security_logs",
  "parameters": {
    "timeframe": "last_24h",
    "severity": "high"
  },
  "context": {
    "user_id": "usr_123",
    "session_id": "sess_456"
  }
}
```

### Response Format
Intent execution result with playbook metadata:
```json
{
  "id": "intent_abc123",
  "object": "intent.execution",
  "created": 1699891234,
  "intent": "analyze_security_logs",
  "status": "completed",
  "result": {
    "summary": "Found 3 critical security events",
    "details": {...},
    "recommendations": [...]
  },
  "execution": {
    "template_id": "tmpl_security_analysis",
    "playbook_id": "pb_log_analysis",
    "steps_executed": 5,
    "duration_ms": 1234
  },
  "usage": {
    "llm_calls": 2,
    "total_tokens": 450,
    "cache_hits": 1,
    "cost_usd": 0.0023
  }
}
```

### Key Features

1. **Semantic Intent Recognition**
   - Natural language intent mapping
   - Parameter extraction from context
   - Intent→Template resolution

2. **Playbook Execution**
   - Multi-step workflows
   - Tool orchestration
   - State management

3. **Enhanced Observability**
   - Step-by-step execution trace
   - Cost breakdown by step
   - Cache hit attribution

4. **Gateway Differentiation**
   - Not an OpenAI feature
   - Unique selling proposition
   - Advanced use cases

### Implementation Strategy

```python
# src/api/models.py

class IntentRequest(BaseModel):
    intent: str
    parameters: Dict[str, Any] = {}
    context: Dict[str, Any] = {}

class IntentExecution(BaseModel):
    template_id: str
    playbook_id: str
    steps_executed: int
    duration_ms: int
    trace: Optional[List[Dict[str, Any]]] = None

class IntentUsage(BaseModel):
    llm_calls: int
    total_tokens: int
    cache_hits: int
    cost_usd: float

class IntentResponse(BaseModel):
    id: str
    object: Literal["intent.execution"] = "intent.execution"
    created: int
    intent: str
    status: Literal["completed", "failed", "partial"]
    result: Dict[str, Any]
    execution: IntentExecution
    usage: IntentUsage
    error: Optional[str] = None
```

```python
# src/api/routes.py

@app.post("/v1/intents")
async def intents_endpoint(
    request: IntentRequest,
    request_id: str = Depends(generate_request_id),
) -> IntentResponse:
    """
    Intent execution endpoint (custom gateway feature).
    Maps intents to templates and executes playbooks.
    """
    ctx = IntentContext(
        request_id=request_id,
        intent=request.intent,
        parameters=request.parameters,
        context=request.context,
    )

    # Intent resolution
    template = await resolve_intent_to_template(request.intent)
    playbook = await load_playbook(template.playbook_id)

    # Execute playbook
    start_time = time.time()
    result = await execute_playbook(playbook, ctx)
    duration_ms = int((time.time() - start_time) * 1000)

    # Collect usage metrics
    usage = IntentUsage(
        llm_calls=ctx.metrics["llm_calls"],
        total_tokens=ctx.metrics["total_tokens"],
        cache_hits=ctx.metrics["cache_hits"],
        cost_usd=ctx.metrics["total_cost"],
    )

    return IntentResponse(
        id=f"intent_{request_id}",
        created=int(time.time()),
        intent=request.intent,
        status=result.status,
        result=result.data,
        execution=IntentExecution(
            template_id=template.id,
            playbook_id=playbook.id,
            steps_executed=len(result.steps),
            duration_ms=duration_ms,
            trace=result.trace if ctx.debug else None,
        ),
        usage=usage,
        error=result.error if result.status == "failed" else None,
    )
```

### Example: Intent Resolution

```python
# src/core/intents.py

class IntentResolver:
    """
    Resolves natural language intents to templates using semantic matching.
    """

    def __init__(self, embedding_provider, template_db):
        self.embedding_provider = embedding_provider
        self.template_db = template_db

    async def resolve(self, intent: str) -> Template:
        """
        Resolve intent string to template using semantic search.

        Examples:
        - "analyze security logs" → SecurityLogAnalysisTemplate
        - "summarize weekly reports" → WeeklySummaryTemplate
        - "detect anomalies in metrics" → AnomalyDetectionTemplate
        """
        # Embed intent
        intent_embedding = await self.embedding_provider.embed(intent)

        # Semantic search over template descriptions
        matches = await self.template_db.search(
            query_vector=intent_embedding,
            limit=5,
            similarity_threshold=0.75,
        )

        if not matches:
            raise IntentNotFoundError(f"No template found for intent: {intent}")

        # Return best match
        return matches[0].template
```

### Testing Strategy

```python
# tests/api/test_intents_endpoint.py

async def test_intent_resolution():
    """Test intent to template resolution."""
    request = {
        "intent": "analyze security logs",
        "parameters": {"timeframe": "24h"}
    }
    response = await client.post("/v1/intents", json=request)
    assert response.status_code == 200
    data = response.json()
    assert data["object"] == "intent.execution"
    assert data["execution"]["template_id"].startswith("tmpl_")

async def test_playbook_execution_trace():
    """Test execution trace capture."""
    request = {
        "intent": "summarize weekly reports",
        "context": {"debug": True}
    }
    response = await client.post("/v1/intents", json=request)
    data = response.json()
    assert data["execution"]["trace"] is not None
    assert len(data["execution"]["trace"]) > 0

async def test_intent_cost_tracking():
    """Test cost breakdown for intent execution."""
    request = {"intent": "detect anomalies"}
    response = await client.post("/v1/intents", json=request)
    data = response.json()
    assert "usage" in data
    assert data["usage"]["cost_usd"] >= 0
    assert data["usage"]["cache_hits"] >= 0
```

---

## Routing Logic

### Request Detection

The gateway uses **endpoint-based routing** with optional header flags:

```python
# src/api/router.py

class RequestRouter:
    """
    Routes incoming requests to appropriate path handler.
    """

    @staticmethod
    def detect_path(request: Request) -> Literal["responses", "chat_completions", "intents"]:
        """
        Determine which path to use based on endpoint.

        Priority:
        1. Endpoint path (highest priority)
        2. Header flags (override for testing)
        3. Content-based detection (fallback)
        """
        path = request.url.path

        # Path 1: Semantic gateway
        if path == "/v1/responses":
            return "responses"

        # Path 3: Intent handling
        if path == "/v1/intents":
            return "intents"

        # Path 2: Syntactic sugar (default)
        if path == "/v1/chat/completions":
            # Optional: Header-based override for testing
            if request.headers.get("X-Gateway-Mode") == "semantic":
                return "responses"
            return "chat_completions"

        # Unknown endpoint
        raise ValueError(f"Unknown endpoint: {path}")
```

### Request Flow Diagram

```
Request arrives
    │
    ├─→ /v1/responses → Path 1 (Semantic)
    │                   └─→ ResponseRequest → Full reasoning metadata
    │
    ├─→ /v1/chat/completions → Path 2 (Syntactic)
    │                          └─→ ChatCompletionRequest → Legacy format
    │
    └─→ /v1/intents → Path 3 (Intent)
                      └─→ IntentRequest → Playbook execution
```

---

## Shared Infrastructure

All three paths leverage **common gateway components**:

### 1. Plugin System

```python
# All paths execute plugins in the same lifecycle

for plugin in get_active_plugins():
    await plugin.before_request(ctx)
    # ... route-specific handling ...
    await plugin.after_response(ctx)
```

**Plugins work across all paths:**
- Semantic Cache: Works for all LLM calls
- Cost Tracking: Unified tracking regardless of path
- Rate Limiting: Applied consistently
- Logging: Centralized telemetry

### 2. Semantic Cache

The cache is **path-agnostic**:

```python
# Caching works the same for all paths
cache_key = await semantic_cache.generate_key(prompt)
cached_response = await semantic_cache.lookup(cache_key)

if cached_response:
    # Convert cached response to path-specific format
    if ctx.endpoint_type == "responses":
        return convert_to_response_object(cached_response)
    elif ctx.endpoint_type == "chat_completions":
        return convert_to_chat_completion(cached_response)
    elif ctx.endpoint_type == "intents":
        return convert_to_intent_response(cached_response)
```

### 3. Cost Tracking

Unified cost tracking across paths:

```python
# src/plugins/cost_tracking.py

class CostTrackingPlugin:
    async def after_response(self, ctx: RequestContext):
        """Track costs regardless of endpoint type."""
        usage = self._extract_usage(ctx)

        # Track prompt tokens
        cost = self._calculate_cost(
            model=ctx.request.model,
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens,
            reasoning_tokens=usage.get("reasoning_tokens"),  # Path 1 only
        )

        await self.db.record_cost(
            request_id=ctx.request_id,
            endpoint_type=ctx.endpoint_type,
            model=ctx.request.model,
            cost_usd=cost,
        )
```

### 4. Request Context

Unified context object with path-specific metadata:

```python
# src/core/context.py

class RequestContext:
    request_id: str
    request: Union[ResponseRequest, ChatCompletionRequest, IntentRequest]
    response: Optional[Union[ResponseObject, ChatCompletionResponse, IntentResponse]]
    endpoint_type: Literal["responses", "chat_completions", "intents"]
    metadata: Dict[str, Any]  # Path-specific data

    # Plugins can access endpoint_type to adjust behavior
```

---

## Implementation Roadmap

### Phase 1: Foundation (Week 1)

**Goal:** Request models and routing infrastructure

- [ ] Create `ResponseRequest` and `ResponseObject` models ([src/api/models.py:1](src/api/models.py#L1))
- [ ] Create `IntentRequest` and `IntentResponse` models
- [ ] Implement `RequestRouter` with path detection
- [ ] Add `endpoint_type` to `RequestContext`
- [ ] Update plugin lifecycle to handle all paths

**Deliverables:**
- Three distinct request/response model sets
- Working router with unit tests
- Documentation: API specification for each path

### Phase 2: Path 1 - Semantic Gateway (Week 2)

**Goal:** Full OpenAI Responses API compliance

- [ ] Implement `/v1/responses` endpoint
- [ ] Add reasoning token extraction logic
- [ ] Update cost calculation for reasoning tokens
- [ ] Add tool execution metadata support
- [ ] Create integration tests with mock o1 responses

**Deliverables:**
- Working `/v1/responses` endpoint
- Reasoning token cost tracking
- 20+ integration tests
- Migration guide from `/v1/chat/completions`

### Phase 3: Path 2 - Syntactic Sugar (Week 3)

**Goal:** Legacy compatibility with internal modernization

- [ ] Ensure `/v1/chat/completions` unchanged externally
- [ ] Add internal reasoning token tracking (metadata only)
- [ ] Implement upgrade suggestion logic
- [ ] Add `X-Upgrade-Available` response header
- [ ] Test backward compatibility with existing integrations

**Deliverables:**
- Zero breaking changes to existing integrations
- Internal reasoning tracking (not exposed)
- Upgrade guidance documentation
- Compatibility test suite

### Phase 4: Path 3 - Intent Handling (Week 4-5)

**Goal:** Custom gateway differentiation

- [ ] Design intent resolution system
- [ ] Implement template database with semantic search
- [ ] Create playbook execution engine
- [ ] Build `/v1/intents` endpoint
- [ ] Add execution trace capture
- [ ] Implement cost breakdown by step

**Deliverables:**
- Working intent→template→playbook pipeline
- 5+ example intents with templates
- Execution trace visualization
- Cost attribution system

### Phase 5: Integration & Testing (Week 6)

**Goal:** End-to-end validation across all paths

- [ ] Integration tests for all three paths
- [ ] Cross-path cache validation
- [ ] Unified cost tracking verification
- [ ] Performance benchmarks
- [ ] Load testing (concurrent requests across paths)

**Deliverables:**
- 100+ integration tests passing
- Performance report (latency, throughput)
- Cost accuracy validation
- Production readiness checklist

### Phase 6: Documentation & Migration (Week 7)

**Goal:** Enable users to choose appropriate path

- [ ] API documentation for all three paths
- [ ] Migration guide: Path 2 → Path 1
- [ ] Intent creation tutorial (Path 3)
- [ ] Best practices guide
- [ ] Example implementations

**Deliverables:**
- Complete API documentation
- Migration toolkit
- Intent template library
- Video tutorials

---

## Decision Matrix: Which Path to Use?

| Use Case | Recommended Path | Rationale |
|----------|------------------|-----------|
| **OpenAI drop-in replacement** | Path 1 (Responses) | Full compatibility with latest OpenAI features |
| **Existing integrations** | Path 2 (Chat Completions) | Zero code changes required |
| **Reasoning models (o1/o3)** | Path 1 (Responses) | Access to reasoning token metadata |
| **Complex tool workflows** | Path 1 (Responses) | Better tool execution transparency |
| **Structured outputs** | Path 1 (Responses) | Native JSON schema support |
| **Custom workflows** | Path 3 (Intents) | Leverage gateway's unique capabilities |
| **Domain-specific tasks** | Path 3 (Intents) | Intent→Playbook mapping |
| **Cost optimization priority** | Path 2 or 3 | Semantic cache + internal reasoning tracking |
| **Exploratory/prototyping** | Path 2 (Chat Completions) | Simplest to start with |

---

## Examples

### Example 1: Using Path 1 (Semantic Gateway)

```bash
curl -X POST http://localhost:8000/v1/responses \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -d '{
    "model": "o1-preview",
    "messages": [
      {"role": "user", "content": "Solve this complex math problem: ..."}
    ],
    "reasoning": {
      "type": "advanced",
      "reasoning_effort": "high"
    }
  }'
```

**Response:**
```json
{
  "id": "resp_abc123",
  "object": "chat.completion",
  "created": 1699891234,
  "model": "o1-preview",
  "choices": [{
    "message": {
      "role": "assistant",
      "content": "The solution is 42.",
      "reasoning": "First, I analyzed the constraints..."
    },
    "finish_reason": "stop"
  }],
  "usage": {
    "prompt_tokens": 50,
    "completion_tokens": 20,
    "reasoning_tokens": 1500,
    "total_tokens": 1570
  }
}
```

### Example 2: Using Path 2 (Syntactic Sugar)

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $OPENAI_API_KEY" \
  -d '{
    "model": "gpt-4",
    "messages": [
      {"role": "user", "content": "Hello, world!"}
    ]
  }'
```

**Response (unchanged from OpenAI):**
```json
{
  "id": "chatcmpl-abc123",
  "object": "chat.completion",
  "created": 1699891234,
  "model": "gpt-4",
  "choices": [{
    "message": {
      "role": "assistant",
      "content": "Hello! How can I assist you today?"
    },
    "finish_reason": "stop"
  }],
  "usage": {
    "prompt_tokens": 10,
    "completion_tokens": 9,
    "total_tokens": 19
  }
}
```

**Response headers:**
```
X-Upgrade-Available: /v1/responses
```

### Example 3: Using Path 3 (Intent Handling)

```bash
curl -X POST http://localhost:8000/v1/intents \
  -H "Content-Type: application/json" \
  -d '{
    "intent": "analyze security logs",
    "parameters": {
      "timeframe": "last_24h",
      "severity": "high"
    },
    "context": {
      "user_id": "usr_123"
    }
  }'
```

**Response:**
```json
{
  "id": "intent_abc123",
  "object": "intent.execution",
  "created": 1699891234,
  "intent": "analyze_security_logs",
  "status": "completed",
  "result": {
    "summary": "Found 3 critical security events in the last 24 hours",
    "events": [
      {"id": "evt_001", "severity": "critical", "description": "..."},
      {"id": "evt_002", "severity": "high", "description": "..."},
      {"id": "evt_003", "severity": "high", "description": "..."}
    ],
    "recommendations": [
      "Immediately investigate evt_001",
      "Review access logs for suspicious patterns",
      "Enable additional monitoring for affected systems"
    ]
  },
  "execution": {
    "template_id": "tmpl_security_analysis",
    "playbook_id": "pb_log_analysis",
    "steps_executed": 5,
    "duration_ms": 2340,
    "trace": [
      {"step": 1, "action": "fetch_logs", "duration_ms": 120},
      {"step": 2, "action": "filter_by_severity", "duration_ms": 50},
      {"step": 3, "action": "llm_analysis", "duration_ms": 1800, "cache_hit": false},
      {"step": 4, "action": "generate_recommendations", "duration_ms": 300, "cache_hit": true},
      {"step": 5, "action": "format_response", "duration_ms": 70}
    ]
  },
  "usage": {
    "llm_calls": 2,
    "total_tokens": 3450,
    "cache_hits": 1,
    "cost_usd": 0.0089
  }
}
```

---

## Migration Path

### For Existing Users (Path 2 → Path 1)

1. **No immediate action required** - Path 2 continues to work
2. **Optional upgrade** - When ready, switch endpoint:
   ```diff
   - POST /v1/chat/completions
   + POST /v1/responses
   ```
3. **Benefit from new features**:
   - Reasoning token visibility
   - Better tool execution tracking
   - Structured output guarantees

### For New Users

**Decision tree:**
1. **Do you need custom workflows?** → Use Path 3 (Intents)
2. **Do you use reasoning models (o1/o3)?** → Use Path 1 (Responses)
3. **Standard chat/completion?** → Start with Path 2, migrate to Path 1 later

---

## Monitoring & Observability

### Key Metrics by Path

| Metric | Path 1 | Path 2 | Path 3 |
|--------|--------|--------|--------|
| **Requests/sec** | ✓ | ✓ | ✓ |
| **Avg latency** | ✓ | ✓ | ✓ (by step) |
| **Cache hit rate** | ✓ | ✓ | ✓ |
| **Cost per request** | ✓ (with reasoning) | ✓ | ✓ (by step) |
| **Reasoning tokens** | ✓ (exposed) | ✓ (internal) | ✓ (if LLM used) |
| **Error rate** | ✓ | ✓ | ✓ |
| **Upgrade suggestions** | N/A | ✓ | N/A |
| **Intent resolution time** | N/A | N/A | ✓ |
| **Playbook execution steps** | N/A | N/A | ✓ |

### Dashboard Enhancements

```
┌─────────────────────────────────────────────────────────┐
│ AI Aikido Gateway - Multi-Path Analytics               │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  Requests by Path (Last 24h)                           │
│  ┌──────────────────────────────────────────────────┐  │
│  │ Path 1 (Responses):       1,234 req  (15%)      │  │
│  │ Path 2 (Chat Completions): 6,789 req  (82%)     │  │
│  │ Path 3 (Intents):           245 req   (3%)      │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  Avg Latency by Path                                   │
│  ┌──────────────────────────────────────────────────┐  │
│  │ Path 1: 245ms  [████████░░] 89th percentile     │  │
│  │ Path 2: 180ms  [██████░░░░] 92nd percentile     │  │
│  │ Path 3: 1.2s   [████████████] 95th percentile   │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  Cost Breakdown                                        │
│  ┌──────────────────────────────────────────────────┐  │
│  │ Total: $45.67                                    │  │
│  │   Path 1: $12.34 (27%) - Reasoning: $8.90       │  │
│  │   Path 2: $28.90 (63%)                           │  │
│  │   Path 3: $4.43  (10%) - Playbooks: 245         │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
│  Cache Hit Rate by Path                                │
│  ┌──────────────────────────────────────────────────┐  │
│  │ Path 1: 72% [███████████████████░░░░]           │  │
│  │ Path 2: 68% [█████████████████░░░░░]            │  │
│  │ Path 3: 45% [███████████░░░░░░░░░░] (step-lvl)  │  │
│  └──────────────────────────────────────────────────┘  │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## Security Considerations

### Path-Specific Risks

| Path | Risk | Mitigation |
|------|------|-----------|
| **Path 1** | Reasoning token leakage | Audit logging, access controls |
| **Path 2** | Header injection attacks | Input validation on `X-Gateway-Mode` |
| **Path 3** | Intent injection | Sanitize intent strings, whitelist templates |

### Unified Security

- **Authentication**: Same API key validation across all paths
- **Rate limiting**: Unified rate limiter (requests/min per path)
- **Input validation**: Pydantic models enforce schemas
- **Audit logging**: All requests logged with path metadata

---

## Success Criteria

### Phase 1-2 (Paths 1 & 2)
- [ ] `/v1/responses` endpoint passes 20+ integration tests
- [ ] `/v1/chat/completions` maintains 100% backward compatibility
- [ ] Reasoning token tracking works for o1/o3 models
- [ ] Cost calculation includes reasoning tokens
- [ ] Migration guide published

### Phase 3-4 (Path 3)
- [ ] Intent resolution achieves >85% accuracy
- [ ] 10+ production-ready intent templates
- [ ] Playbook execution <2s P95 latency
- [ ] Cost attribution accurate to 1%

### Phase 5-6 (Integration)
- [ ] All three paths share cache (verified via tests)
- [ ] Unified cost tracking across paths
- [ ] Dashboard shows per-path metrics
- [ ] 200+ total integration tests passing
- [ ] Production deployment successful

---

## References

- [OpenAI Responses API Migration Guide](https://platform.openai.com/docs/guides/migrate-to-responses)
- [OpenAI Responses API Reference](https://platform.openai.com/docs/api-reference/responses)
- [Playground Architecture](./PLAYGROUND_ARCHITECTURE.md) - Testing and authoring interfaces for all three paths
- [Semantic Cache Implementation](./ONPREM_EMBEDDING_VECTOR_DB.md)
- [Project Status](../STATUS.md)
- [Next Priorities](../NEXT_PRIORITIES.md)

---

## Appendix A: Configuration

### Enabling Paths

```yaml
# config/plugins.yaml

gateway:
  endpoints:
    # Path 1: Semantic gateway
    responses:
      enabled: true
      path: /v1/responses

    # Path 2: Syntactic sugar
    chat_completions:
      enabled: true
      path: /v1/chat/completions
      suggest_upgrades: true  # Enable X-Upgrade-Available header

    # Path 3: Intent handling
    intents:
      enabled: true  # Set to false to disable custom features
      path: /v1/intents
      intent_resolution:
        similarity_threshold: 0.75
        max_candidates: 5
```

### Feature Flags

```yaml
features:
  reasoning_token_tracking: true      # Enable for Paths 1 & 2
  tool_execution_metadata: true       # Enable for Path 1
  intent_resolution: true             # Enable for Path 3
  playbook_execution_trace: true      # Enable debug traces for Path 3
  upgrade_suggestions: true           # Enable for Path 2
```

---

## Appendix B: Cost Comparison

### Reasoning Token Costs (Path 1 vs Path 2)

| Model | Standard Completion | Reasoning Token | Path 1 Visibility | Path 2 Visibility |
|-------|---------------------|-----------------|-------------------|-------------------|
| o1-preview | $15/1M tokens | $60/1M tokens | ✓ Exposed | ✓ Internal only |
| o1-mini | $3/1M tokens | $12/1M tokens | ✓ Exposed | ✓ Internal only |
| gpt-4 | $30/1M tokens | N/A | N/A | N/A |

**Example calculation (Path 1):**
```
Prompt tokens:     100 × $15/1M  = $0.0015
Completion tokens: 50 × $15/1M   = $0.00075
Reasoning tokens:  2000 × $60/1M = $0.12

Total: $0.12225 (vs $0.00225 without reasoning)
```

**Path 2 behavior:** Reasoning tokens tracked internally for cost accuracy but not exposed in API response.

---

**END OF DOCUMENT**
