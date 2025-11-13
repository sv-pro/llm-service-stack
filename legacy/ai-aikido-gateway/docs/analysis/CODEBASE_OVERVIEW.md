# AI Aikido Gateway - Codebase Overview

**Generated:** November 6, 2025  
**Analysis Type:** Comprehensive codebase structure and architecture review  
**Status:** ✅ Production-Ready (Phases 1-5 Complete)

## Quick Navigation

### 📋 Documentation Files
- **[CODEBASE_ANALYSIS.md](CODEBASE_ANALYSIS.md)** - Detailed 960-line technical analysis
  - Source code organization
  - Plugin architecture & implementations
  - API routes and models
  - Configuration structure
  - Test coverage breakdown
  - Dashboard implementation
  - Architectural patterns
  - Implementation status vs roadmap
  - Code quality metrics
  - Key gaps and future work

- **[VISUAL_OVERVIEW.txt](VISUAL_OVERVIEW.txt)** - ASCII visual summary
  - Architecture diagrams
  - Plugin pipeline diagram
  - Component breakdown
  - Model registry
  - Features & capabilities checklist
  - Testing breakdown
  - Quality metrics table
  - Next priorities

### 📁 Project Structure

```
ai-aikido-gateway/
├── src/                          # Python source code (~4,300 LOC)
│   ├── api/                      # HTTP API layer
│   │   ├── routes.py            # OpenAI-compatible endpoints (1,100 LOC)
│   │   ├── models.py            # Pydantic models
│   │   ├── auth.py              # Gateway key validation
│   │   ├── middleware.py        # Request tracing
│   │   └── exceptions.py        # Custom errors
│   ├── core/                     # Core engine
│   │   ├── config.py            # Configuration loading (450 LOC)
│   │   ├── pipeline.py          # Plugin orchestration (265 LOC)
│   │   ├── plugin.py            # Base plugin interface (270 LOC)
│   │   ├── context.py           # Request context
│   │   └── logging.py           # Structured logging
│   ├── plugins/                  # Plugin implementations (6 plugins)
│   │   ├── cache.py            # Two-tier caching (400 LOC)
│   │   ├── history.py          # Request history (350 LOC)
│   │   ├── openai_proxy.py     # OpenAI proxy (300 LOC)
│   │   ├── anthropic_proxy.py  # Anthropic proxy (300 LOC)
│   │   ├── transparency.py     # Debug headers (150 LOC)
│   │   └── example.py          # Demo plugin (50 LOC)
│   └── main.py                  # FastAPI app (200 LOC)
│
├── dashboard/                    # React 18 + Vite dashboard (173MB)
│   ├── src/
│   │   ├── App.jsx             # Main router
│   │   ├── pages/
│   │   │   ├── Playground.jsx      # ✅ Request tester
│   │   │   ├── RequestHistory.jsx  # ✅ Request log viewer
│   │   │   ├── Overview.jsx        # 🟡 Cost trends (planned)
│   │   │   ├── CostExplorer.jsx    # 🟡 Cost analytics (planned)
│   │   │   ├── CacheAnalytics.jsx  # 🟡 Cache metrics (planned)
│   │   │   └── Settings.jsx        # 🟡 Configuration (planned)
│   │   └── components/
│   └── tests/                  # Playwright E2E tests
│
├── tests/                        # Python test suite (188 tests, 12 modules)
│   ├── test_api.py             # Endpoint tests
│   ├── test_cache.py           # Cache plugin tests
│   ├── test_history_plugin.py  # History tests
│   ├── test_end_to_end.py      # Full pipeline tests
│   ├── test_guard_rails.py     # Provider validation tests
│   ├── test_plugin_system.py   # Framework tests
│   ├── test_config_extensions.py
│   ├── test_cost_calculation.py
│   ├── test_main.py
│   ├── test_proxy_load_balancing.py
│   ├── test_transparency_plugin.py
│   └── conftest.py             # Pytest fixtures
│
├── config/                       # Configuration files
│   ├── plugins.yaml            # Plugin enable/disable + priority
│   ├── tenants.sample.yml      # Multi-tenant template
│   └── billing.sample.yml      # Cost alert thresholds
│
├── deployment/                   # Docker & deployment
│   ├── Dockerfile.gateway
│   ├── Dockerfile.dashboard
│   ├── docker-compose.yml      # Development
│   ├── docker-compose.prod.yml # Production
│   └── render.yaml             # Cloud deployment
│
├── docs/                         # 20+ documentation pages
│   ├── project/                # Project planning
│   │   ├── ROADMAP.md         # Phases 0-9 roadmap
│   │   ├── NEXT_STEPS.md      # Actionable tasks
│   │   ├── PROJECT_STATUS.md  # Implementation status
│   │   └── design/            # Architecture designs
│   ├── development/            # Development guides
│   │   ├── ARCHITECTURE.md    # System design
│   │   ├── TESTING.md         # Test strategy
│   │   └── TRANSPARENCY_PLUGIN.md
│   └── deployment/             # Deployment guides
│       ├── DOCKER_DEPLOYMENT.md
│       ├── DEPLOYMENT.md
│       └── PRE_DEPLOY_CHECKLIST.md
│
└── scripts/                      # Utility scripts
    ├── setup.sh                # Initial setup
    ├── docker.sh               # Docker helpers
    └── [others]
```

## Core Concepts

### Plugin-First Architecture

All functionality is implemented as plugins that inherit from `BasePlugin`:

1. **Plugin Lifecycle** (6 hooks):
   - `on_startup()` - Initialize resources
   - `before_request(context)` - Pre-process request
   - `after_response(context)` - Post-process response
   - `on_error(context, error)` - Handle errors
   - `on_shutdown()` - Cleanup
   - Dynamic enable/disable toggle

2. **Plugin Pipeline** - Orchestrates plugin execution:
   - Plugins execute in priority order (lower = earlier)
   - `before_request` runs ascending (cache → proxy)
   - `after_response` runs descending (history → transparency)
   - Early termination support (for cache hits)

3. **Current Plugins** (6):
   - Cache (priority 10) - Two-tier caching
   - OpenAI Proxy (priority 50) - OpenAI API forward
   - Anthropic Proxy (priority 50) - Anthropic API forward
   - Transparency (priority 90) - Debug headers
   - History (priority 100) - Request logging
   - Example Logger (priority 1) - Demo

### Request Flow

```
Request → TraceMiddleware (correlation ID)
  ↓
  → Auth validation (if enabled)
  ↓
  → Cache check (cache hit = early exit)
  ↓
  → Provider selection & parameter normalization
  ↓
  → Proxy to OpenAI or Anthropic
  ↓
  → Response enrichment (transparency headers)
  ↓
  → Request history logging & cost tracking
  ↓
  → Return response to client
```

### Configuration System

**Three-layer configuration:**

1. **Plugin Configuration** (`config/plugins.yaml`)
   - Enable/disable plugins
   - Set execution priority
   - Plugin-specific settings
   - Environment variable expansion

2. **Tenant Configuration** (`config/tenants.yml`)
   - Multi-tenant definitions
   - API key management
   - Rate limits
   - Custom metadata

3. **Billing Configuration** (`config/billing.yml`)
   - Cost alert thresholds
   - Per-tenant overrides

4. **Environment Variables** (`.env`)
   - OPENAI_API_KEY
   - ANTHROPIC_API_KEY
   - GATEWAY_LOG_LEVEL
   - etc.

## Implementation Status

### ✅ Complete (Phases 1-5)

| Phase | Feature | Status |
|-------|---------|--------|
| 1 | Plugin framework | ✅ Complete |
| 2 | Request history & cost tracking | ✅ Complete |
| 3 | Transparency, logging, auth scaffold | ✅ Complete |
| 4 | Intelligent caching, cache analytics | ✅ Complete |
| 5 | Proxy plugins, dashboard UI | ✅ Complete |

**Key Features Working:**
- 10 LLM models (7 OpenAI + 3 Anthropic)
- Two-tier caching (LRU + SQLite)
- Cost tracking with pricing data
- Request history with search/filter
- API key pool with load balancing
- Fallback chains (graceful degradation)
- Guard rails (fails fast on misconfiguration)
- Full trace correlation
- 188 passing tests
- Docker deployment
- React dashboard (Playground + History)

### 🟡 Planned (Phases 6-9)

| Phase | Feature | Status |
|-------|---------|--------|
| 6 | Semantic cache with embeddings | 🟡 Planned |
| 6 | Prompt normalization pipeline | 🟡 Planned |
| 6 | Dashboard semantic metrics | 🟡 Planned |
| 7-8 | Intent/Template/Playbook system | 🟡 Planned |
| 8 | Playbook execution engine | 🟡 Planned |
| 8 | Intent builder UI | 🟡 Planned |
| 9 | Multi-provider routing | 🟡 Planned |
| 9 | Budget enforcement | 🟡 Planned |

## Testing

**Test Suite: 188 tests across 12 modules**

- **Unit Tests** (70+) - Components in isolation
- **Integration Tests** (40+) - Pipeline interactions
- **Guard Rail Tests** (20+) - Configuration validation
- **Config Tests** (10+) - YAML loading, env expansion

**Run Tests:**
```bash
pytest                              # All tests
pytest tests/test_cache.py -v      # Specific module
pytest --cov=src --cov-report=html # With coverage
```

## Dashboard

**Implemented Pages:**
- ✅ **Playground** - Interactive request builder with curl preview
- ✅ **Request History** - Paginated log with filtering and cost breakdown

**Planned Pages:**
- 🟡 **Overview** - Cost trends and optimization insights
- 🟡 **Cost Explorer** - Detailed cost analytics
- 🟡 **Cache Analytics** - Cache effectiveness metrics
- 🟡 **Settings** - Configuration management

**Ports:**
- Gateway: 8000
- Dashboard: 3000

## Key Design Patterns

1. **Plugin-First** - All concerns (caching, routing, tracking) as plugins
2. **Two-Tier Caching** - Memory (LRU) + disk (SQLite) for speed + persistence
3. **Context Communication** - RequestContext flows through pipeline
4. **Configuration-Driven** - YAML + dynamic class loading = runtime flexibility
5. **Guard Rails** - Fail fast with helpful errors
6. **Request Normalization** - Model-specific parameter handling
7. **Correlation IDs** - Trace requests through async code
8. **Fallback Chains** - Graceful degradation on provider errors
9. **API Key Pooling** - Round-robin load balancing

## API Endpoints

**OpenAI-Compatible:**
- `POST /v1/chat/completions` - Chat completion (compatible with OpenAI SDK)
- `GET /v1/models` - List available models

**History & Analytics:**
- `GET /v1/history/requests` - Request log with filters
- `GET /v1/history/requests/{id}` - Single request details
- `GET /v1/history/stats` - Aggregate statistics

**Configuration:**
- `GET /v1/settings` - Cost alert thresholds
- `GET /plugins` - Plugin status

**Health:**
- `GET /health` - Service status
- `GET /` - API info

## Code Quality

- **Type Safety:** Pydantic models + type hints throughout
- **Documentation:** Comprehensive docstrings + 20+ guides
- **Testing:** 188 tests (unit + integration + E2E)
- **Logging:** Structured JSON with correlation IDs
- **Observability:** Transparency headers, audit trail
- **Async:** Full async/await with proper context management

## Deployment

**Local Development:**
```bash
make setup              # Initial setup
make start-reload       # Dev server with hot reload
make start-all         # Gateway + dashboard
```

**Docker:**
```bash
make docker-build      # Build images
make docker-up         # Start stack
make docker-redeploy   # Rebuild and restart
```

**Production:**
- See `deployment/docker-compose.prod.yml`
- Health checks configured
- Structured logging
- Error monitoring ready

## Dependencies

**Production:**
- FastAPI (HTTP framework)
- Pydantic (data validation)
- SQLite (caching & history)
- LiteLLM (provider abstraction)
- Uvicorn (ASGI server)

**Development:**
- pytest (testing)
- black (formatting)
- ruff (linting)
- mypy (type checking)

**Dashboard:**
- React 18
- Vite
- Playwright (E2E testing)

## Key Files to Understand

1. **src/main.py** - App initialization, plugin loading, lifespan
2. **src/api/routes.py** - OpenAI-compatible endpoints, model registry
3. **src/core/pipeline.py** - Plugin orchestration
4. **src/core/plugin.py** - Base plugin interface
5. **src/core/config.py** - Configuration loading
6. **src/plugins/cache.py** - Two-tier caching implementation
7. **src/plugins/history.py** - Request history & cost tracking
8. **config/plugins.yaml** - Plugin configuration

## Quick Start

1. **Clone & Setup:**
   ```bash
   make setup
   ```

2. **Configure API Keys:**
   ```bash
   edit .env
   ```

3. **Start Services:**
   ```bash
   make start-all  # Gateway + Dashboard
   ```

4. **Access:**
   - Dashboard: http://localhost:3000
   - API: http://localhost:8000
   - Docs: http://localhost:8000/docs

## Documentation Map

For detailed information, see:

- **Understanding the architecture:** [CODEBASE_ANALYSIS.md](CODEBASE_ANALYSIS.md) Section 7
- **Plugin system:** [CODEBASE_ANALYSIS.md](CODEBASE_ANALYSIS.md) Section 2
- **API endpoints:** [CODEBASE_ANALYSIS.md](CODEBASE_ANALYSIS.md) Section 3
- **Testing:** [CODEBASE_ANALYSIS.md](CODEBASE_ANALYSIS.md) Section 5
- **Roadmap:** docs/project/ROADMAP.md
- **Status:** docs/project/PROJECT_STATUS.md
- **Next steps:** docs/project/NEXT_STEPS.md

## Support

For questions or issues:
1. Check the detailed analysis: CODEBASE_ANALYSIS.md
2. Review the roadmap: docs/project/ROADMAP.md
3. See status updates: docs/project/PROJECT_STATUS.md
4. Check development docs: docs/development/

---

**Last Updated:** November 6, 2025  
**Analysis Confidence:** High - Comprehensive codebase review complete  
**Recommended Reading Order:** VISUAL_OVERVIEW.txt → CODEBASE_OVERVIEW.md (this file) → CODEBASE_ANALYSIS.md
