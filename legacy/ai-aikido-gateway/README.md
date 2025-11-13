# AI Aikido Gateway - Unified Dashboard 🥋

**OpenAI-compatible API proxy with intelligent routing, caching, and cost optimization.**

**New!** Unified React dashboard - one app for testing, monitoring, and optimization.

## 🚀 Quick Start (Unified Dashboard)

### Prerequisites

- Python 3.11+ with pyenv
- Node.js 18+ and npm
- OpenAI API Key (set in `.env`)

### Start Everything (One Command)

```bash
# Start gateway + unified dashboard
./scripts/start_unified_dashboard.sh
```

**Access Points:**

- 🎮 **Dashboard**: http://localhost:3000 (Main interface)
- 🚀 **Gateway API**: http://localhost:8000
- 📚 **API Docs**: http://localhost:8000/docs

### Dashboard Screens

1. **🎮 Playground** - Test requests interactively ✅
2. **📊 Overview** - Cost optimization insights (Coming Soon)
3. **💰 Cost Explorer** - Detailed analytics (Coming Soon)
4. **📋 Request History** - View and search all requests ✅
5. **⚡ Cache Analytics** - Performance metrics (Coming Soon)
6. **⚙️ Settings** - Configuration (Coming Soon)

### Re^Re Loop Demo Telemetry

The Re^Re demo on the dashboard listens to a WebSocket stream that is emitted by the gateway. To enable it locally:

1. **Run Redis for telemetry fan-out.**
   - When using `docker compose`, the new `redis` service starts automatically.
   - If you are running everything directly on your host, start Redis yourself:
     ```bash
     docker run -d --name aikido-redis -p 6379:6379 redis:7
     ```
2. **Update your `.env`:**
   ```bash
   RE_RE_DEMO_ENABLED=true
   RE_RE_TELEMETRY_REDIS_URL=redis://localhost:6379/0  # optional
   RE_RE_TELEMETRY_CHANNEL=re-re.telemetry            # optional
   ```
3. **Restart the gateway** so the telemetry emitter and `/ws/re-re/{execution_id}` route are enabled.

After this, the Re^Re demo’s “Start Demo” button will stream live workflow events and the comparison tools will be able to load historical executions.

### Docker Service Groups

| Group | Services | Purpose |
|-------|----------|---------|
| **Application** | `gateway`, `dashboard` | Frequently rebuilt during development. Use `make docker-redeploy`. |
| **Infrastructure** | `embeddings`, `qdrant`, `redis` | Longer-lived data services. Use `make docker-redeploy-infra` when you need to rebuild them. |

The standard `make docker-up` command starts every service. During iterative work, prefer `make docker-redeploy` (fast app-only refresh) and only touch the infra containers when you actually change embeddings/Qdrant/Redis images.

## Alternative: Manual Setup

### Option A: Using Makefile (Recommended)

```bash
# 1. Setup everything (one command)
make setup

# 2. Edit .env and add your API keys
# ANTHROPIC_API_KEY=sk-ant-your-key-here
# OPENAI_API_KEY=sk-your-key-here

# 3. Start the gateway with hot reload
make start-reload

# 4. Run tests
make test
```

See all available commands with `make help`.

### Option B: Manual Setup

#### 1. Setup (One Command)

```bash
./scripts/setup.sh
```

This will:

- Create a Python 3.11 virtual environment with pyenv
- Install all dependencies
- Create `.env` file from template

#### 2. Configure API Keys

Edit `.env` and add your API keys:

```bash
ANTHROPIC_API_KEY=sk-ant-your-key-here
OPENAI_API_KEY=sk-your-key-here
```

#### 3. Run the Gateway

```bash
uvicorn src.main:app --reload
```

Visit:

- API: http://localhost:8000
- Docs: http://localhost:8000/docs
- Health: http://localhost:8000/health

#### 4. Run Tests

```bash
pytest
```

## 📚 Project Docs

### Core Documentation (Updated 2025-11-06)

- **[Status & Next Steps](docs/project/STATUS.md)** — Current implementation status, what's working, immediate next steps
- **[Roadmap & Planning](docs/project/ROADMAP.md)** — Complete evolution plan from cache to IntentHub (Phases 0-10)
- **[Vision](docs/project/design/VISION.md)** — Long-term strategic direction and principles
- **[Consolidation Summary](docs/project/CONSOLIDATION_SUMMARY.md)** — Documentation unification guide

### Technical Documentation

- **[Architecture](docs/development/ARCHITECTURE.md)** — Plugin-first design and system architecture
- **[Testing Guide](docs/development/TESTING.md)** — Test suite and QA processes
- **[Codebase Analysis](CODEBASE_ANALYSIS.md)** — Complete technical deep-dive (960 lines)
- **[Quick Start](docs/project/quick_start/CONTEXT.md)** — Daily context and reboot guide

## Project Status

📍 **Current Phase**: Phases 0-5 Complete ✅ | Phase 6 Starting (Semantic Cache)

🎯 **Implementation Status**:
- ✅ **Foundation** - FastAPI, plugins, logging, tracing (Phase 0)
- ✅ **Caching** - Two-tier cache with 38% hit rate (Phase 1)
- ✅ **Cost Tracking** - Full request history and cost analytics (Phase 2)
- ✅ **Multi-Provider** - OpenAI + Anthropic with failover (Phase 3)
- ✅ **Dashboard** - React UI with Playground and History (Phase 4)
- 🟡 **Semantic Cache** - Starting week of 2025-11-05 (Phase 5)

🎯 **Test Coverage**: 188/188 tests passing (100%)

See [STATUS.md](docs/project/STATUS.md) for detailed implementation status and [ROADMAP.md](docs/project/ROADMAP.md) for future plans.

## Architecture

**Plugin-First Design** - Every feature is a modular, composable plugin:

```
AI Aikido Gateway
├── Core Layer       → Minimal plugin infrastructure (pipeline, context, loader)
├── Plugin Layer     → Independent, composable plugins
│   ├── cost_monitor → [PRIORITY] Track costs, analytics, budgets
│   ├── cache        → Response caching (future)
│   ├── router       → Intelligent model routing (future)
│   └── proxies      → OpenAI, Anthropic API proxies
└── API Layer        → FastAPI endpoints (OpenAI-compatible)
```

**Design Principles**:

- Each plugin = one concern (single responsibility)
- Plugins composable via shared request context
- Enable/disable plugins via YAML config
- Minimal core, maximum extensibility

See [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) for comprehensive architecture design.

See [CLAUDE.md](CLAUDE.md) for development guidelines.

## Development

### Using Makefile (Recommended)

```bash
# Format code
make format

# Lint
make lint

# Type check
make type-check

# Run all quality checks
make quality

# Run tests with coverage
make test-cov

# Clean cache files
make clean
```

### Manual Commands

```bash
# Format code
black src/ tests/

# Lint
ruff check src/ tests/

# Type check
mypy src/

# Run tests with coverage
pytest --cov=src --cov-report=html
```

## Testing with the Reference Client

A simple web-based client is included to test the gateway:

### Quick Start (Both Gateway + Client)

```bash
# Start both services with one command
make demo
```

Then open <http://localhost:3000> in your browser.

### Manual Start

```bash
# Terminal 1: Start the gateway
make start-reload

# Terminal 2: Start the client
make client-start
```

The client provides:

- Simple chat interface (text box + send button)
- Model selection (GPT-3.5, GPT-4, Claude models)
- Response display with metadata
- Gateway health check

See [client/README.md](client/README.md) for more details.

## How It Works (Plugin Pipeline)

1. **Client** sends OpenAI-compatible request to gateway
2. **Plugin Pipeline** executes plugins in configured order:
   - **before_request** hooks: Pre-process, route, cache check
   - **Request execution**: Proxy to LLM provider
   - **after_response** hooks: Track costs, cache response, update metrics
3. **Response** returned to client in OpenAI format

**Example Plugin Flow** (with cost monitoring):

```
Request → CostMonitor.before_request() → Proxy.execute() →
CostMonitor.after_response() → Response
                                   ↓
                          [Store cost in database]
```

## Documentation

- [PROJECT_STATUS.md](PROJECT_STATUS.md) - Current progress and next steps
- [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md) - **Comprehensive plugin-first architecture design**
- [CLAUDE.md](CLAUDE.md) - Development guidelines and plugin development
- [AGENTS.md](AGENTS.md) - Comprehensive setup guide

## Features (Roadmap)

### Phase 2: Core Plugin System (Next)

- [ ] Base plugin class with lifecycle hooks
- [ ] Plugin pipeline for request/response processing
- [ ] Request context for sharing data between plugins
- [ ] Plugin loader from YAML configuration

### Phase 3: Cost Monitor Plugin (PRIORITY ⭐)

- [ ] Track LLM API costs per request
- [ ] SQLite storage for cost records
- [ ] Cost analytics endpoints (summary, daily, by-model)
- [ ] Budget alerts (daily/weekly/monthly)
- [ ] Export cost data to CSV/JSON

### Phase 4+: Future Plugins

- [ ] Caching plugin (in-memory, Redis)
- [ ] Router plugin (intelligent model selection)
- [ ] Rate limiter plugin
- [ ] Auth plugin (API key management)

## 📁 Project Structure

### Root Directory

```
├── src/                    # Python source code
├── tests/                  # Test suite
├── dashboard/              # React dashboard
├── config/                 # Configuration files
├── scripts/                # Utility scripts
├── deployment/             # Docker & deployment files
├── docs/                   # Documentation
│   ├── project/           # Project management docs
│   ├── development/       # Technical documentation
│   └── deployment/        # Deployment guides
├── data/                   # SQLite databases
└── README.md              # This file
```

### Key Files

- `docs/QUICKSTART.md` - Quick start guide
- `docs/project/PROJECT_STATUS.md` - Current project status
- `docs/development/ARCHITECTURE.md` - System architecture
- `deployment/docker-compose.yml` - Docker orchestration
- `scripts/start_unified_dashboard.sh` - Start everything

## License

MIT
