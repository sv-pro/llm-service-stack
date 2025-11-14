# Architecture Design

## Overview

AI Aikido Gateway is built on a **plugin-first architecture** where functionality is modular, composable, and configurable. The core is intentionally minimal, with all business logic implemented as plugins.

The system consists of three main components:

1. **Gateway Backend** (Python/FastAPI) - Plugin-based request processing
2. **Unified Dashboard** (React/Vite) - Testing, monitoring, and optimization UI with Playground, Request History, and analytics
3. **Plugin System** - Modular, composable functionality (history, cache, cost tracking, routing, etc.)

## Design Principles

### 1. Plugin-First
Every feature is a plugin. The core only provides:
- Plugin lifecycle management
- Request/response pipeline
- Configuration loading
- Shared context

### 2. Single Responsibility
Each plugin handles exactly one concern:
- `cost_monitor.py` → Track and analyze costs
- `cache.py` → Cache responses
- `router.py` → Route to appropriate models
- `openai_proxy.py` → Proxy to OpenAI API

### 3. Composability
Plugins work together through a shared request context:
```python
context = {
    "request": original_request,
    "response": llm_response,
    "metadata": {
        "model": "gpt-4",
        "tokens": {"prompt": 100, "completion": 50},
        "cost": 0.0075,
        "latency_ms": 1200,
        "cached": False
    }
}
```

### 4. Configuration Over Code
Enable/disable/configure plugins via YAML:
```yaml
plugins:
  - name: cost_monitor
    enabled: true
    priority: 10
    config:
      storage: sqlite
      db_path: ./data/costs.db

  - name: cache
    enabled: false  # Disabled, won't load
    priority: 5
```

## Architecture Layers

### Layer 1: Core Infrastructure

**Location**: `src/core/`

**Components**:

1. **plugin.py** - Base plugin class
```python
class BasePlugin(ABC):
    def __init__(self, config: dict): pass
    async def on_startup(self): pass
    async def on_shutdown(self): pass
    async def before_request(self, ctx: RequestContext): pass
    async def after_response(self, ctx: RequestContext): pass
    async def on_error(self, ctx: RequestContext, error: Exception): pass
```

2. **pipeline.py** - Plugin execution pipeline
```python
class PluginPipeline:
    def __init__(self, plugins: List[BasePlugin]): pass
    async def execute_before_request(self, ctx: RequestContext): pass
    async def execute_after_response(self, ctx: RequestContext): pass
    async def handle_error(self, ctx: RequestContext, error: Exception): pass
```

3. **context.py** - Shared request context
```python
@dataclass
class RequestContext:
    request_id: str
    timestamp: datetime
    request: ChatCompletionRequest
    response: Optional[ChatCompletionResponse] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    errors: List[Exception] = field(default_factory=list)
```

4. **config.py** - Configuration loader
```python
class Config:
    def load_plugins(self) -> List[PluginConfig]: pass
    def get_plugin_config(self, name: str) -> dict: pass
```

### Layer 2: Plugin Ecosystem

**Location**: `src/plugins/`

**Priority Plugin: Cost Monitor**

```python
# src/plugins/cost_monitor.py
class CostMonitorPlugin(BasePlugin):
    """
    Tracks LLM API costs per request.

    Features:
    - Calculate cost based on model pricing and token usage
    - Store cost data (SQLite/PostgreSQL)
    - Aggregate metrics (daily, weekly, monthly costs)
    - Cost alerts and budgets
    - Export cost reports
    """

    async def before_request(self, ctx: RequestContext):
        # Store request timestamp
        ctx.metadata["cost_tracking_start"] = time.time()

    async def after_response(self, ctx: RequestContext):
        # Calculate cost from response token usage
        cost = self._calculate_cost(
            model=ctx.metadata["model"],
            prompt_tokens=ctx.response.usage.prompt_tokens,
            completion_tokens=ctx.response.usage.completion_tokens
        )

        # Store in database
        await self.db.store_cost_record({
            "request_id": ctx.request_id,
            "timestamp": ctx.timestamp,
            "model": ctx.metadata["model"],
            "prompt_tokens": ctx.response.usage.prompt_tokens,
            "completion_tokens": ctx.response.usage.completion_tokens,
            "total_cost": cost,
            "latency_ms": (time.time() - ctx.metadata["cost_tracking_start"]) * 1000
        })

        # Add to context for other plugins
        ctx.metadata["cost"] = cost
```

**Future Plugins**:

- **cache.py** - Response caching
- **router.py** - Intelligent model routing based on complexity
- **openai_proxy.py** - OpenAI API proxy
- **anthropic_proxy.py** - Anthropic API proxy
- **rate_limiter.py** - Rate limiting per user/API key
- **auth.py** - Authentication and API key management

### Layer 3: API Layer

**Location**: `src/api/`

**Request Flow**:

```
Client Request
    ↓
FastAPI Endpoint (/v1/chat/completions)
    ↓
Middleware (creates RequestContext)
    ↓
Pipeline.execute_before_request()
    ↓ (plugins run in priority order)
    ├─ CostMonitor.before_request()
    ├─ Cache.before_request()  [check cache]
    └─ Router.before_request()  [select model]
    ↓
Proxy Plugin (execute LLM request)
    ↓
Pipeline.execute_after_response()
    ↓ (plugins run in reverse priority)
    ├─ Router.after_response()
    ├─ Cache.after_response()  [store in cache]
    └─ CostMonitor.after_response()  [track cost]
    ↓
Response to Client
```

## Data Flow

### Request Context Lifecycle

1. **Creation**: Middleware creates RequestContext with request data
2. **Enhancement**: Plugins add metadata during before_request hooks
3. **Execution**: Proxy plugin executes LLM request, adds response
4. **Processing**: Plugins process response in after_response hooks
5. **Cleanup**: Context discarded after response sent

### Plugin Priority Order

Plugins execute in priority order (lower number = higher priority):

**Before Request** (ascending order):
```
1. Auth (priority: 1) - Validate API key
2. RateLimiter (priority: 5) - Check rate limits
3. Cache (priority: 10) - Check cache hit
4. Router (priority: 20) - Select model
5. CostMonitor (priority: 30) - Start tracking
```

**After Response** (descending order):
```
1. CostMonitor (priority: 30) - Calculate & store cost
2. Router (priority: 20) - Log routing decision
3. Cache (priority: 10) - Store response
4. RateLimiter (priority: 5) - Update counters
5. Auth (priority: 1) - Log request
```

## Configuration Schema

### plugins.yaml

```yaml
# Plugin configuration
plugins:
  # Cost monitoring (PRIORITY)
  - name: cost_monitor
    enabled: true
    priority: 30
    class: plugins.cost_monitor.CostMonitorPlugin
    config:
      storage_backend: sqlite  # sqlite | postgresql | memory
      db_path: ./data/costs.db
      pricing:
        # USD per 1M tokens
        gpt-4:
          prompt: 30.00
          completion: 60.00
        gpt-4-turbo:
          prompt: 10.00
          completion: 30.00
        claude-3-opus:
          prompt: 15.00
          completion: 75.00
        claude-3-sonnet:
          prompt: 3.00
          completion: 15.00
        claude-3-haiku:
          prompt: 0.25
          completion: 1.25
      alerts:
        daily_budget: 100.00  # USD
        weekly_budget: 500.00
        monthly_budget: 2000.00

  # OpenAI proxy
  - name: openai_proxy
    enabled: true
    priority: 50
    class: plugins.openai_proxy.OpenAIProxyPlugin
    config:
      api_key: ${OPENAI_API_KEY}
      timeout: 60

  # Anthropic proxy
  - name: anthropic_proxy
    enabled: true
    priority: 50
    class: plugins.anthropic_proxy.AnthropicProxyPlugin
    config:
      api_key: ${ANTHROPIC_API_KEY}
      timeout: 60

  # Future: Caching (disabled for now)
  - name: cache
    enabled: false
    priority: 10
    class: plugins.cache.CachePlugin
    config:
      backend: redis
      ttl: 3600

  # Future: Router (disabled for now)
  - name: router
    enabled: false
    priority: 20
    class: plugins.router.RouterPlugin
    config:
      default_cheap_model: claude-3-haiku
      default_expensive_model: gpt-4-turbo
```

## Cost Monitor Plugin Details

### Database Schema

```sql
-- SQLite schema for cost tracking
CREATE TABLE cost_records (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    request_id TEXT NOT NULL,
    timestamp DATETIME NOT NULL,
    model TEXT NOT NULL,
    prompt_tokens INTEGER NOT NULL,
    completion_tokens INTEGER NOT NULL,
    total_tokens INTEGER NOT NULL,
    prompt_cost REAL NOT NULL,
    completion_cost REAL NOT NULL,
    total_cost REAL NOT NULL,
    latency_ms INTEGER,
    user_id TEXT,  -- Future: multi-user support
    tags TEXT  -- JSON array for custom tags
);

CREATE INDEX idx_timestamp ON cost_records(timestamp);
CREATE INDEX idx_model ON cost_records(model);
CREATE INDEX idx_user_id ON cost_records(user_id);
```

### Cost Monitor API Endpoints

```python
# New endpoints for cost analytics
GET  /v1/costs/summary          # Overall cost summary
GET  /v1/costs/daily            # Daily breakdown
GET  /v1/costs/by-model         # Cost by model
GET  /v1/costs/records          # Detailed records (paginated)
POST /v1/costs/export           # Export CSV/JSON
```

### Cost Calculation

```python
def calculate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """Calculate cost in USD based on model pricing"""
    pricing = self.config["pricing"].get(model)
    if not pricing:
        # Default pricing if model not configured
        pricing = {"prompt": 1.00, "completion": 2.00}

    # Pricing is per 1M tokens, convert to per-token
    prompt_cost = (prompt_tokens / 1_000_000) * pricing["prompt"]
    completion_cost = (completion_tokens / 1_000_000) * pricing["completion"]

    return prompt_cost + completion_cost
```

## Benefits of This Architecture

### 1. **Modularity**
- Add new features without modifying core
- Test plugins in isolation
- Disable expensive features in development

### 2. **Flexibility**
- Enable only what you need
- Configure per-environment (dev, staging, prod)
- Swap implementations (SQLite → PostgreSQL)

### 3. **Extensibility**
- Third-party plugins possible
- Custom business logic as plugins
- Easy to add new LLM providers

### 4. **Maintainability**
- Small, focused modules
- Clear separation of concerns
- Easy to reason about

### 5. **Performance**
- Disabled plugins have zero overhead
- Async execution throughout
- Plugins can run in parallel (future enhancement)

## Development Phases (Revised)

### Phase 2: Core Plugin System (NEXT)
- Implement `BasePlugin` class
- Implement `PluginPipeline`
- Implement `RequestContext`
- Create plugin loader from YAML config
- Add plugin middleware to FastAPI
- Write tests for plugin system

### Phase 3: Cost Monitor Plugin (PRIORITY)
- Implement `CostMonitorPlugin`
- Add SQLite storage backend
- Implement cost calculation with pricing table
- Create cost analytics endpoints
- Add budget alerts
- Write comprehensive tests

### Phase 4: Basic Proxy Plugins
- Implement `OpenAIProxyPlugin`
- Implement `AnthropicProxyPlugin`
- Add error handling and retries
- Test end-to-end flow

### Phase 5: Future Plugins (After Cost Monitor Works)
- Cache plugin
- Router plugin (intelligent model selection)
- Rate limiter plugin
- Auth plugin

## Migration Path

This new architecture is compatible with Phase 1:
- FastAPI app already exists
- Can build plugin system alongside existing code
- Incremental migration, no big rewrite
- Start with cost monitoring, add features over time
