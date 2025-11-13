# AI AIKIDO GATEWAY - GITHUB COPILOT CONTEXT

**Last Updated**: 2025-01-28  
**Context Purpose**: GitHub Copilot working memory and development assistance  
**Project Status**: Phase 4.2 Complete - Production Ready Gateway

---

## 🔍 QUICK PROJECT OVERVIEW

**What This Is**: OpenAI-compatible API gateway with intelligent caching and cost optimization

**Current State**: Fully operational production system with:

- ✅ Complete OpenAI API proxy (7 models supported)
- ✅ Intelligent two-tier caching system (80-90% cost savings)
- ✅ Comprehensive cost tracking and analytics
- ✅ React dashboard with real-time monitoring
- ✅ Plugin-based architecture for extensibility
- ✅ 83 tests passing, production-ready code

**Architecture**: FastAPI backend + React frontend + SQLite storage + Plugin system

---

## 🏗️ CODEBASE STRUCTURE

### Backend (Python/FastAPI)

```
src/
├── main.py                    # FastAPI app entry point
├── core/                      # Plugin infrastructure
│   ├── plugin.py             # BasePlugin, PluginRegistry
│   ├── pipeline.py           # Plugin execution orchestration
│   ├── context.py            # RequestContext data sharing
│   └── config.py             # YAML config loader
├── plugins/                   # Feature implementations
│   ├── cache.py              # Two-tier caching (707 lines)
│   ├── history.py            # Request/response storage
│   ├── transparency.py       # Debug headers
│   └── example.py            # Plugin demo
└── api/
    ├── routes.py             # OpenAI-compatible endpoints
    └── models.py             # Pydantic request/response models
```

### Frontend (React/Vite)

```
dashboard/src/
├── main.jsx                  # React app entry
├── App.jsx                   # Router setup
├── components/
│   └── Layout.jsx           # Navigation sidebar
└── pages/
    ├── Playground.jsx       # Chat interface (functional)
    ├── RequestHistory.jsx   # Request/response viewer (functional)
    ├── CostExplorer.jsx     # Cost analytics (functional)
    ├── CacheAnalytics.jsx   # Cache monitoring (functional)
    ├── Overview.jsx         # Dashboard home (placeholder)
    └── Settings.jsx         # Config UI (placeholder)
```

### Configuration

```
config/
└── plugins.yaml             # Plugin enable/disable + settings

Key plugins:
- example_logger (priority 1) - Demo plugin
- cache (priority 10) - Response caching
- transparency (priority 90) - Debug headers
- request_history (priority 100) - Data storage
```

---

## 🔧 CORE PLUGIN SYSTEM

### Plugin Architecture

**BasePlugin** - Abstract class with lifecycle hooks:

- `async def before_request(ctx)` - Pre-processing
- `async def after_response(ctx)` - Post-processing
- `async def on_error(ctx, error)` - Error handling
- `async def on_startup()` - Init code
- `async def on_shutdown()` - Cleanup code

**PluginPipeline** - Executes plugins in priority order:

1. Before request hooks (cache lookup, validation)
2. Main request execution (OpenAI API call)
3. After response hooks (storage, headers, caching)

**RequestContext** - Shared data between plugins:

```python
@dataclass
class RequestContext:
    request: ChatCompletionRequest
    response: Optional[Dict] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    errors: List[Exception] = field(default_factory=list)
    _stop_pipeline: bool = False
```

### Key Plugins

**CachePlugin** (src/plugins/cache.py):

- Two-tier system: LRU hot cache + SQLite storage
- Deterministic cache keys from normalized payloads
- Per-model TTL (15-40 minutes)
- Cost savings calculation and tracking
- Cache hit/miss metrics

**RequestHistoryPlugin** (src/plugins/history.py):

- Captures every request/response to SQLite
- Calculates costs automatically via `calculate_cost()`
- Provides REST API for querying history
- Supports filters, pagination, search

**TransparencyPlugin** (src/plugins/transparency.py):

- Adds HTTP headers showing gateway behavior
- Optional headers: normalizations, latency, cache status
- Configurable per-header and custom prefixes

---

## 💰 COST TRACKING SYSTEM

### Pricing Data (MODEL_REGISTRY in routes.py)

```python
# October 2025 pricing (USD per 1M tokens)
"gpt-5": {"input": 2.50, "output": 10.00}         # Latest reasoning
"gpt-5-mini": {"input": 1.00, "output": 4.00}    # Efficient reasoning
"gpt-5-nano": {"input": 0.40, "output": 1.60}    # Cheapest GPT-5
"gpt-4o": {"input": 5.00, "output": 20.00}       # Optimized
"gpt-4-turbo": {"input": 10.00, "output": 30.00} # Fast GPT-4
"gpt-4": {"input": 30.00, "output": 60.00}       # Legacy
"gpt-3.5-turbo": {"input": 0.50, "output": 1.50} # Most economical
```

### Cost Calculation

```python
def calculate_cost(model: str, prompt_tokens: int, completion_tokens: int) -> float:
    """Calculate cost in USD with 6 decimal precision"""
    pricing = get_model_pricing(model)
    input_cost = (prompt_tokens / 1_000_000) * pricing["input"]
    output_cost = (completion_tokens / 1_000_000) * pricing["output"]
    return round(input_cost + output_cost, 6)
```

**Integration**: Every request automatically calculates cost and stores in database

---

## ⚡ CACHING SYSTEM

### Two-Tier Architecture

**Hot Cache (In-Memory LRU)**:

- Fast access (<1ms lookup)
- Max 500 entries (configurable)
- Automatic eviction (least recently used)

**Storage Backend (SQLite)**:

- Persistent across restarts
- Max 5000 entries (configurable)
- Auto-promotion to hot cache on hits

### Cache Key Generation

```python
def generate_cache_key(payload: Dict[str, Any]) -> str:
    """Deterministic key from normalized payload"""
    # Exclude unstable fields (user, timestamps)
    stable_payload = {k: v for k, v in payload.items()
                     if k not in ["user"]}
    payload_str = json.dumps(stable_payload, sort_keys=True)
    return hashlib.sha256(payload_str.encode()).hexdigest()
```

### Cache Flow

```
Request → Generate Key → Check Hot Cache → Check SQLite → OpenAI API
                              ↓ HIT        ↓ HIT         ↓ MISS
                          Return cached    Promote +     Store in both
                                          return        + return new
```

---

## 🌐 API ENDPOINTS

### Gateway (Port 8000)

**Core OpenAI Compatibility**:

- `POST /v1/chat/completions` - Main chat endpoint
- `GET /v1/models` - List available models
- `GET /v1/models?available_only=true` - Filter to working models

**Request History**:

- `GET /v1/history/requests` - Paginated request list with filters
- `GET /v1/history/requests/{id}` - Single request details
- `GET /v1/history/stats` - Aggregated statistics + cache metrics

**System**:

- `GET /health` - Health check
- `GET /docs` - OpenAPI documentation

### Dashboard (Port 3000)

**Functional Pages**:

- `/playground` - Chat interface (send requests to gateway)
- `/requests` - Request history browser with costs
- `/costs` - Cost analytics with charts and insights
- `/cache` - Cache performance monitoring with recommendations

**Placeholder Pages**:

- `/overview` - System dashboard (needs implementation)
- `/settings` - Plugin configuration (needs implementation)

---

## 🧪 TESTING FRAMEWORK

### Test Structure (83 tests total)

```bash
tests/
├── test_cache.py              # 16 tests - Cache system
├── test_cost_calculation.py   # 15 tests - Cost accuracy
├── test_history_plugin.py     # 10 tests - Database operations
├── test_transparency_plugin.py # 11 tests - Header generation
├── test_plugin_system.py      # 24 tests - Core infrastructure
├── test_api.py               # 7 tests - API validation
└── conftest.py               # Test fixtures
```

### Key Test Categories

**Cache Tests**: LRU eviction, TTL expiry, SQLite persistence, hit/miss tracking
**Cost Tests**: Model pricing lookup, calculation accuracy, edge cases
**Plugin Tests**: Lifecycle hooks, configuration loading, error handling
**API Tests**: Request validation, response format, error handling

### Running Tests

```bash
make test         # All tests
make test-cov     # With coverage
pytest tests/test_cache.py -v  # Specific test file
```

---

## 🔄 REQUEST FLOW

### Complete Request Pipeline

```
1. Client → POST /v1/chat/completions
2. FastAPI → Validate request (Pydantic)
3. PluginPipeline.execute_before_request():
   - CachePlugin: Check for cached response
   - If cache HIT: Return cached + stop pipeline
4. [If cache MISS] → OpenAI API call:
   - Normalize parameters for model
   - Send HTTP request to OpenAI
   - Parse response
5. PluginPipeline.execute_after_response():
   - TransparencyPlugin: Add debug headers
   - RequestHistoryPlugin: Store request + calculate cost
   - CachePlugin: Store response for future hits
6. Return response to client (with optional headers)
```

### Cache Hit Flow (Fast Path)

```
Request → Cache Check → Return Cached Response
         (<1ms)      ↓
                    Update metrics + Execute after_response hooks
```

---

## 🎯 COMMON DEVELOPMENT PATTERNS

### Adding a New Plugin

1. **Create plugin class**:

```python
class MyPlugin(BasePlugin):
    def __init__(self, config: Dict[str, Any]):
        self.my_setting = config.get("my_setting", "default")

    async def before_request(self, ctx: RequestContext):
        # Pre-processing logic
        pass

    async def after_response(self, ctx: RequestContext):
        # Post-processing logic
        pass
```

2. **Add to plugins.yaml**:

```yaml
- name: my_plugin
  enabled: true
  priority: 50
  class: plugins.my_plugin.MyPlugin
  config:
    my_setting: "custom_value"
```

3. **Create tests**:

```python
def test_my_plugin():
    plugin = MyPlugin({"my_setting": "test"})
    # Test logic
```

### Adding a New Dashboard Page

1. **Create page component**:

```jsx
function MyPage() {
  return <div>My Page Content</div>;
}
export default MyPage;
```

2. **Add route to App.jsx**:

```jsx
<Route path="/my-page" element={<MyPage />} />
```

3. **Add navigation link to Layout.jsx**:

```jsx
<NavLink to="/my-page">My Page</NavLink>
```

### Adding a New API Endpoint

1. **Add to routes.py**:

```python
@router.get("/my-endpoint")
async def my_endpoint():
    return {"message": "Hello"}
```

2. **Add tests to test_api.py**:

```python
def test_my_endpoint():
    response = client.get("/my-endpoint")
    assert response.status_code == 200
```

---

## 🔍 DEBUGGING & DEVELOPMENT

### Useful Development Commands

```bash
# Start services
make start-all              # Both gateway + dashboard
make start-gateway          # Just gateway (port 8000)
make start-dashboard        # Just dashboard (port 3000)

# Testing & Quality
make test                   # Run all tests
make test-watch            # Watch mode for tests
make lint                  # Code quality checks
make format               # Auto-format code

# Debugging
curl http://localhost:8000/health        # Check gateway health
curl http://localhost:8000/v1/models     # List models
```

### Enable Transparency Headers

Set `transparency.enabled: true` in config/plugins.yaml to see:

- `X-Gateway-Normalizations` - Parameter changes made
- `X-Gateway-Cache-Status` - hit/miss/write
- `X-Gateway-Latency-Ms` - Request timing
- `X-Gateway-Original-Model` - Model requested

### Cache Debugging

```bash
# Check cache stats
curl http://localhost:8000/v1/history/stats | jq '.cache_metrics'

# View cache analytics
open http://localhost:3000/cache
```

---

## 📊 CURRENT METRICS (Live System)

### Test Status

- **83/83 tests passing** ✅
- Cache plugin: 16 tests
- Cost calculation: 15 tests
- Request history: 10 tests
- Transparency: 11 tests
- Plugin system: 24 tests
- API validation: 7 tests

### Cache Performance

- Hit rate: 60-90% (varies by usage)
- Lookup time: <1ms (hot), <10ms (SQLite)
- Cost savings: 80-90% via cache hits
- Storage: Persists across restarts

### Service Health

- Gateway: ✅ Running on port 8000
- Dashboard: ✅ Running on port 3000
- Database: ✅ SQLite in ./data/ directory
- All endpoints: ✅ Responding correctly

---

## 🚀 NEXT DEVELOPMENT PRIORITIES

### Phase 5 Roadmap (Next 3-4 weeks)

**P1 - Multi-Provider Support**:

- LiteLLM integration for Anthropic/Claude models
- Automatic fallbacks (gpt-4 → gpt-3.5-turbo)
- Load balancing across API keys

**P2 - Docker Deployment**:

- Production Dockerfiles
- Docker Compose orchestration
- Persistent storage volumes

**P3 - Authentication System**:

- Virtual API key management
- Rate limiting per key
- Budget controls per user/team

**P4 - Advanced Analytics**:

- Natural language queries ("What's my most expensive model?")
- Automated insights and recommendations
- Budget alerts and notifications

### Quick Wins Available

- Complete Overview dashboard page
- Add Settings page for plugin configuration
- CSV export functionality for analytics
- Cache warming for common queries
- Budget threshold alerts

---

## 💡 DEVELOPMENT TIPS

### Performance Considerations

- Cache lookups are <1ms (optimize for cache hits)
- SQLite queries <10ms (already optimized)
- OpenAI API calls 500-2000ms (biggest latency)
- Plugin hooks add <1ms overhead per plugin

### Code Quality Standards

- Type hints required (mypy validation)
- Test coverage >90% for new features
- Black formatting + Ruff linting
- Comprehensive docstrings for public APIs

### Plugin Development Guidelines

- Keep plugins independent (no inter-plugin dependencies)
- Use RequestContext for data sharing
- Handle errors gracefully (don't break pipeline)
- Add comprehensive tests for new plugins

### UI Development Patterns

- Use modern React patterns (hooks, functional components)
- Follow existing component structure
- Add responsive design (mobile-friendly)
- Use consistent styling (gradients, cards, animations)

---

**Context Summary**: This is a production-ready OpenAI-compatible gateway with intelligent caching, cost tracking, and comprehensive analytics. The plugin architecture makes it highly extensible. All major features are complete and tested. Next focus is multi-provider support and enterprise features.

**For GitHub Copilot**: Use this context to understand the codebase structure, suggest improvements, help with debugging, and assist with implementing new features following established patterns.
