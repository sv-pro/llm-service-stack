# AI Aikido Gateway – Unified Roadmap & Plan

**Last Updated:** 2025-11-08
**Audience:** Core engineering & product (solo developer)
**Status:** Phases 0-6 Complete | Phases 7-12 Planned

---

## Vision & North Star

> **To build a Reflective Intelligence Platform where agents don't just execute — they learn.** Through the **Re^Re (Reflective Reasoning)** loop — Reason → Act → Reflect → Re-reason → ∞ — every interaction becomes a learning opportunity. **This is not just ReAct (Reason + Act). This is Re^Re: continuous evolution through reflection.**

The Gateway transcends its origins as an LLM proxy to become an open, extensible framework for building intelligent systems that improve themselves. Developers can plug in capabilities, define intents, orchestrate multi-step workflows, and build their own ChatGPT-like assistants with full control over structure, cost, and behavior — while the system learns from every execution.

### Three-Path Architecture

The platform implements a "no compromises" hybrid architecture with three parallel API paths:

1. **Path 1 (Semantic):** `/v1/responses` - Full OpenAI Responses API compliance with reasoning tokens
2. **Path 2 (Syntactic):** `/v1/chat/completions` - Legacy compatibility with internal reasoning tracking
3. **Path 3 (Intent):** `/v1/intents` - Custom gateway feature for Intent→Template→Playbook execution

All paths share unified caching, cost tracking, and plugin infrastructure. See [THREE_PATH_RESPONSES_API.md](design/THREE_PATH_RESPONSES_API.md) for details.

---

## Evolution Path: Reflective Intelligence Journey

The roadmap follows the **Re^Re (Reflective Reasoning)** loop, where each phase builds on the previous one, enabling the system to Reason, Act, Reflect, and Re-reason continuously. Each stage can be implemented and demoed independently, providing incremental value and validation points.

### Cumulative Impact Table

| Phase | Focus | Cost Reduction | Control | Learning | Status |
|-------|-------|----------------|---------|----------|--------|
| 0 — Verbatim Cache | Gateway infrastructure | ~10% | Medium | 0% | ✅ Complete |
| 1 — Semantic Cache & Normalization | Improved reuse | ~85% | High | 10% | ✅ Complete |
| 2 — Playbook-Lite | Template execution | ~87% | High | 15% | 🔄 In Progress |
| 3 — Multi-Step Playbooks | Workflow orchestration | ~90% | Full | 25% | 📋 Designed |
| 4 — Intent Routing | Semantic intent resolution | ~92% | Full | 35% | 📋 Designed |
| 5 — Feedback Loop | Outcome evaluation | ~93% | Full | 50% | 📋 Planned |
| 6 — Intent Builder v1 | Self-service authoring | ~94% | Full | 55% | 📋 Designed |
| 7 — Shadow Mode / A-B Testing | Safe experimentation | ~95% | Full | 65% | 📋 Planned |
| 8 — Learning & Self-Tuning | Adaptive optimization | ~96% | Full | 75% | 📋 Planned |
| 9 — Auto-Builder | Playbook synthesis | ~97% | Full | 85% | 🔮 Vision |
| 10 — Meaning Graph | Semantic relationships | ~97% | Full | 90% | 🔮 Vision |
| 11 — Federation / A2A | Multi-gateway network | ~98% | Full | 95% | 🔮 Vision |
| 12 — Edge Reasoning | Distributed intelligence | ~98% | Full | 98% | 🔮 Vision |

---

## Reflective Demonstrations (Priorities 3 & 4) ✅

### Re^Re Loop Demo (Priority 3 — Visual Dashboard Demos)

**Goal:** Expose the Reason → Act → Reflect → Re-reason cycle as an interactive dashboard experience so stakeholders can witness the platform’s learning journey.

**Delivered:**
- **Telemetry pipeline:** `WorkflowEvent` emitter, LangGraph nodes streaming per-phase events, history snapshots persisted, and optional Redis pub/sub via `RE_RE_DEMO_ENABLED`.
- **Dashboard UI:** `/rere-demo` route with `ReReTimeline`, BudgetGauge, ExecutionControls, timeline slider, comparison mode, artifact viewer, reflection notes drawer, and the `useTelemetry` hook integrating websocket telemetry.
- **Backend support:** Replay endpoints, `/re-re/executions/compare`, WebSocket broadcasts with live state, delta cards, playback scrubber, and export utilities for state snapshots.
- **Infrastructure:** App/infra container split speeds `make docker-redeploy`, Redis container with health checks, documented env vars for websocket URLs + Redis connections, and propagation checks proving the demo runs inside Docker with telemetry streaming.
- **Supporting demos:** Playbook Playground, Tool Registry Explorer, Workflow Visualizer, Request History, and Monitoring Widgets (cache hit rate, budget monitor, quality analytics) all feed from the same telemetry fabric.

**Success Criteria:** Telemetry stream + UI + replay operate end-to-end (live or replay), at least three visual demo pages ship, monitoring widgets reflect cache/budget/quality trends, and Docker deployment streams telemetry via Redis.

### Retrospective Publishing (Priority 4 — Reflective Storytelling)

**Goal:** Publish a 15-article retrospective series that chronicles the architectural evolution, cites real code + commit IDs, and reuses artifacts from `docs/retrospective/`.

**Approach:**
1. **Phase 1 (Weeks 1-2):** Analyze git history, tag phase boundaries, and capture problem/context/solution/impact notes.
2. **Phase 2 (Weeks 3-4):** Turn those notes into outlines plus a pilot article (“Building an LLM Gateway: Why and How”).
3. **Phase 3 (Weeks 5-12):** Draft two polished articles per week with diagrams, code snippets, and commit references, stored under `docs/retrospective/articles/` and `docs/retrospective/code_examples/`.
4. **Phase 4 (Week 13+):** Publish bi-weekly on Dev.to with a GitHub Pages mirror and promote the series across developer communities.

**Guardrails:** Writing always references real code + commit IDs, doc/implementation progress stays synchronized via STATUS/NEXT_PRIORITIES updates, and drafts land in PRs with Core Platform reviewers so publishing never blocks engineering work.

**Success Criteria:** 15 article drafts complete with code + commit links, binge-readable navigation/cross-linking established (see `docs/retrospective/articles/INDEX.md`), and a publication calendar locked before Phase 4 engineering resumes.

---

## Phase 0: Verbatim Cache ✅ Complete

**Goal:** Build production-ready gateway infrastructure with basic caching for immediate cost savings.

**Re^Re Context:** This phase establishes the foundation for observation (the first step in Reason → Act → Reflect → Re-reason). By capturing all requests and responses, we create the data substrate needed for future learning.

**Delivered:**
- FastAPI application with async/await architecture
- OpenAI-compatible `/v1/chat/completions` endpoint
- Plugin system with 6 lifecycle hooks and priority-based execution
- Structured logging with JSON formatter and correlation IDs
- Request tracing middleware with `X-Trace-Id` headers
- Auth scaffolding (gateway-issued keys + tenant registry)
- Cost alert configuration framework
- Docker deployment (dev + production configurations)
- Comprehensive test suite (188 tests)
- React dashboard foundation

**Key Files:**
- `src/main.py` - FastAPI app initialization
- `src/core/plugin.py` - Base plugin framework
- `src/core/pipeline.py` - Plugin orchestration
- `src/core/logging.py` - Structured logging
- `src/api/middleware.py` - Tracing middleware
- `src/api/auth.py` - Authentication scaffolding

**Success Criteria:**
- ✅ Staging uptime ≥99%
- ✅ All tests passing (188/188)
- ✅ Reproducible setup scripts
- ✅ Docker builds functional

---

## Phase 1: Semantic Cache & Normalization ✅ Complete

**Goal:** Improve cache reuse across similar prompts through semantic matching and standardized request payloads.

**Re^Re Context:** Semantic matching enables the system to "reason" about similarity—recognizing that two differently-phrased prompts may have the same intent. This is the first step toward intent-based reasoning.

**Delivered:**
- Two-tier cache: LRU in-memory + SQLite persistent backend
- Cache key: `hash(model + prompt + temperature + other params)`
- Model-specific TTL configuration
- LRU eviction with configurable max entries
- Cache statistics tracking (hits/misses/savings)
- Cache management API endpoints
- Bypass headers support (`X-Bypass-Cache`)

**Key Files:**
- `src/plugins/cache.py` (400 lines) - Cache plugin implementation
- `tests/test_cache.py` - Cache test suite
- `config/plugins.yaml` - Cache configuration

**Configuration:**
```yaml
- name: cache
  enabled: true
  priority: 5  # Run early in pipeline
  class: plugins.cache.CachePlugin
  config:
    backend: sqlite
    db_path: ./data/cache.db
    ttl_seconds: 3600
    max_entries: 10000
    eviction_policy: lru
    model_ttl:
      gpt-4: 7200
      gpt-3.5-turbo: 1800
```

**Success Criteria:**
- ✅ Cache hit rate >20% (measured)
- ✅ Response time <50ms for cached requests
- ✅ Immediate measurable savings (≈30%)

---

## Phase 2: Playbook-Lite (Template Execution) 🔄 In Progress

**Goal:** Make responses deterministic and governed with reusable templates (simple single-step playbooks).

**Re^Re Context:** Templates represent the "Act" phase—executing predefined patterns rather than generating new responses. This phase begins the transition from reactive (caching) to proactive (structured execution).

**Delivered:**
- Request history plugin with full metadata storage
- Cost calculation per request (predicted vs actual)
- Token usage tracking (prompt + completion)
- Model pricing registry for 10 LLM models
- SQLite persistence for request history
- Query API for historical requests

**Key Files:**
- `src/plugins/history.py` (350 lines) - History plugin
- `tests/test_history_plugin.py` - History tests
- `src/api/models.py` - Pydantic models

**Model Pricing Coverage:**
```python
# OpenAI Models
"gpt-4": {"prompt": 30.00, "completion": 60.00}
"gpt-4-turbo": {"prompt": 10.00, "completion": 30.00}
"gpt-3.5-turbo": {"prompt": 0.50, "completion": 1.50}

# Anthropic Models
"claude-3-opus-20240229": {"prompt": 15.00, "completion": 75.00}
"claude-3-sonnet-20240229": {"prompt": 3.00, "completion": 15.00}
"claude-3-haiku-20240307": {"prompt": 0.25, "completion": 1.25}
```

**Success Criteria:**
- ✅ 100% request cost tracking
- ✅ <5% variance between predicted/actual costs
- ✅ Responses reproducible and model-independent

---

## Phase 2 (Infrastructure): Aikido Dispatcher ✅ Complete

**Goal:** Intelligently route each request to the optimal provider/model.

**Re^Re Context:** The dispatcher implements the reasoning layer for provider selection—analyzing request characteristics and routing to optimal backends. This is the infrastructure that enables adaptive behavior.

**Delivered:**
- Multi-provider support via LiteLLM abstraction
- OpenAI proxy plugin with API key rotation
- Anthropic proxy plugin with fallback logic
- Provider guard rails (auto-disable when no keys)
- Retry logic with exponential backoff
- Failover between providers
- Transparency headers for routing metadata

**Key Files:**
- `src/plugins/openai_proxy.py` (300 lines) - OpenAI proxy
- `src/plugins/anthropic_proxy.py` (250 lines) - Anthropic proxy
- `src/plugins/transparency.py` - Transparency headers
- `tests/test_guard_rails.py` - Guard rail tests
- `tests/test_proxy_load_balancing.py` - Load balancing tests

**Transparency Headers:**
```http
X-Gateway-Provider: openai
X-Gateway-Model: gpt-3.5-turbo
X-Gateway-Cached: false
X-Gateway-Retries: 0
X-Trace-Id: req-abc123
```

**Success Criteria:**
- ✅ Automatic routing to optimal provider
- ✅ Budget, quota, and policy enforcement
- ✅ Graceful degradation on provider failures

---

## Phase 2 (Infrastructure): Intent Observatory ✅ Complete

**Goal:** Observe repeated and expensive intents to guide optimization.

**Re^Re Context:** The Observatory embodies the "Reflect" phase—collecting metrics, analyzing patterns, and surfacing insights that inform future decisions. This is where the system begins to learn from its behavior.

**Delivered:**
- Request history with embedding-based clustering (planned)
- Cost tracking per request with metadata labels
- React dashboard with Playground and Request History
- Interactive admin dashboard
- Health check integration
- Metadata extraction from custom headers

**Key Files:**
- `dashboard/src/` - React dashboard (Vite + React)
- `dashboard/src/pages/Playground.jsx` - Chat interface
- `dashboard/src/pages/RequestHistory.jsx` - History viewer
- `tests/test_cost_calculation.py` - Cost tracking tests

**Dashboard Features:**
- Model selection (10 models supported)
- Real-time response display
- Request metadata viewer (latency, tokens, cost)
- Request history table with filtering
- Health check indicator

**Metadata Labels:**
```python
# Custom headers for tracking
X-Aikido-App: mobile-app
X-Aikido-User: user-123
X-Aikido-Environment: production
X-Aikido-Version: 1.2.3
```

**Success Criteria:**
- ✅ Logging all requests with clustering
- ✅ Metrics: `cost_total × repeat_count` per intent cluster
- ✅ Interactive admin dashboard
- ✅ Human-in-the-loop improvement cycle

**Outcome:**
Operators see where the system leaks money and can formalize new executable templates to eliminate recurring LLM calls (promotion to "old generation" in garbage collection).

---

## Phase 1 (Detail): Semantic Cache & Normalization ✅ Complete

**Timeline:** Delivered week of 2025‑11‑07 (≈2 weeks)
**Goal:** Improve cache reuse across similar prompts through semantic matching and standardized request payloads.

**Re^Re Context:** Detailed implementation of Phase 1—this is where semantic reasoning begins. The system learns to recognize similar intents even when expressed differently.

**Delivered:**
1. **Semantic Cache Plugin**
   - FAISS-backed cosine similarity search with OpenAI embeddings
   - Configurable thresholds/TTLs, metadata filters, and LRU+SQLite persistence
   - Transparent retry summary hydration on cache hits for downstream plugins

2. **Prompt Normalization Pipeline**
   - Trim/whitespace/tool canonicalization + temperature rounding rules
   - Runs at priority 4 ahead of both cache layers with full unit coverage

3. **Operational Plumbing**
   - `core.config` import aliasing for tests/fixtures
   - 42 new tests (140 total) spanning embeddings, normalization, semantic cache, and E2E retries
   - Working context mirrored at `/context.md` for quick restores

**Follow-Up (Phase 5 Adoption):**
- Dashboard semantic metrics panel + API counters (in progress)
- Performance benchmarking/threshold tuning on production traces

**Reference Implementation:**
```python
# Embedding provider interface
src/core/embeddings/base.py
src/core/embeddings/openai.py

# Semantic cache
src/plugins/semantic_cache.py
src/core/cache/semantic.py

# Normalization pipeline
src/core/normalization/pipeline.py
src/core/normalization/rules.py

# Dashboard extensions (in progress)
dashboard/src/components/cache/SemanticStatsPanel.*
dashboard/src/store/cacheMetrics.ts
```

**Configuration:**
```yaml
- name: semantic_cache
  enabled: false  # Enable once OPENAI_API_KEY for embeddings is configured
  priority: 6
  class: plugins.semantic_cache.SemanticCachePlugin
  config:
    embedding_provider: openai
    similarity_threshold: 0.85
    max_cache_entries: 5000
    vector_store: faiss
    fallback_to_verbatim: true
```

**Success Criteria:**
- Cache hit rate improvement ≥20%
- Semantic lookup latency <100ms
- Dashboard shows semantic metrics
- Configurable threshold persistence

---

## Phase 1 (Detail): On-Premise Embeddings & Vector Database ✅ Complete

**Timeline:** Delivered 2025-11-07/08 (2 days)
**Goal:** Deploy zero-cost, high-performance on-premise embedding service and validate with comprehensive benchmarks.

**Re^Re Context:** On-premise embeddings enable the system to reason about similarity at zero marginal cost, making the Re^Re loop sustainable at scale. Fast embedding generation (10ms vs 500ms) accelerates the learning cycle.

**Delivered:**

1. **SentenceTransformersProvider** (`src/core/embeddings/sentence_transformers.py` - 204 lines)
   - HTTP client to embedding service
   - Connection pooling with httpx
   - Automatic retries with exponential backoff
   - **$0 cost** vs OpenAI's $0.0001/1K tokens

2. **QdrantBackend** (`src/core/cache/qdrant.py` - 420 lines)
   - Persistent vector storage (survives restarts)
   - Cosine similarity with metadata filtering
   - TTL expiration and LRU eviction
   - Scalable to millions of vectors

3. **Embedding Service** (`src/services/embeddings/server.py` - 137 lines)
   - FastAPI service with sentence-transformers
   - Model: all-MiniLM-L6-v2 (384 dimensions)
   - ~10ms processing time per embedding
   - Health check and generation endpoints

4. **Docker Orchestration** (`deployment/docker-compose.yml`)
   - Added `embeddings` service (port 8001)
   - Added `qdrant` service (ports 6333/6334)
   - Added `qdrant-storage` persistent volume

5. **Comprehensive Benchmarks** ([BENCHMARK_RESULTS.md](implementation/BENCHMARK_RESULTS.md))
   - Tested 4 similarity thresholds (0.80-0.95)
   - **60x speedup confirmed:** 10ms avg vs 500-800ms (OpenAI)
   - **100% cost savings:** $0 vs $0.0001/1K tokens
   - **Recommendation:** 0.85 threshold for production

6. **Integration Tests** (`tests/integration/test_onprem_semantic_cache.py` - 273 lines)
   - SentenceTransformersProvider embedding generation
   - QdrantBackend CRUD operations
   - Full semantic cache plugin integration
   - **187/187 tests passing** (was 178/181)

7. **Semantic Metrics Surfacing**
   - `/v1/cache/semantic/stats` endpoint with histogram, cost summary, transparency metadata
   - React dashboard histogram + ledger tiles + refreshed threshold slider UX
   - Expanded test suite for API + UI polling

8. **Qdrant Default + Auto Fallback**
   - `config/plugins.yaml` now points semantic cache at Qdrant with FAISS fallback & env overrides
   - Plugin stats expose backend + fallback reason; new unit tests cover failure path

9. **Responses API Shim**
   - `/v1/responses` endpoint + `ResponsesRequest` model map OpenAI Responses payloads into chat completions
   - Adds new test coverage to ensure parity + validation

**Performance Metrics:**
- **Embedding latency:** 10ms avg (vs 500-800ms OpenAI) - **60x faster**
- **Cache lookup:** <1ms (virtually instant)
- **Cost per embedding:** $0.00 (vs $0.0001/1K tokens)
- **Hit rate:** 86.7% with default test prompts
- **Throughput:** ~100 embeddings/sec

**Configuration Modes:**
1. OpenAI + FAISS (default, simple)
2. SentenceTransformers + Qdrant (recommended, $0 costs + persistent)
3. SentenceTransformers + FAISS ($0 embeddings, testing)
4. OpenAI + Qdrant (persistent with API)

**Success Criteria:**
- ✅ $0 embedding costs confirmed
- ✅ 60x speedup validated with benchmarks
- ✅ Production recommendations documented (threshold: 0.85, TTL: 1h, size: 5K)
- ✅ Integration tests passing with real service
- ✅ Docker services orchestrated and healthy
- ✅ Semantic metrics surfaced in API + dashboard
- ✅ `/v1/responses` shim available for OpenAI alignment

**Commits:**
- `2cc1f7f` - Prototype embedding service
- `66d18a9` - Full on-premise solution
- `f4404e6` - Critical performance fixes (pipeline stop bug)
- `cbef27b` - Test fixes
- `788bc23` - Benchmark validation & documentation

---

## Phase 3: Multi-Step Playbooks 📋 Designed

**Timeline:** 2-3 weeks
**Goal:** Orchestrate multi-step workflows with LangGraph, tool registry, and budget enforcement.

**Re^Re Context:** Multi-step playbooks implement the full Reason → Act cycle iteratively. Each step reasons about the next action based on previous results, creating a chain of deliberate execution.

**Planned Features:**
1. **LangGraph Workflow Engine**
   - State graph definition for Reason → Act cycles
   - Conditional branching based on step outcomes
   - Tool execution nodes with retry logic
   - Budget tracking per execution path
   - Parallel execution support for independent steps

2. **Tool Registry & MCP Integration**
   - LLM tool adapter (call models as tools)
   - HTTP API tool adapter (REST/GraphQL endpoints)
   - MCP (Model Context Protocol) integration
   - Custom tool registration interface
   - Input/output schema validation

3. **Three-Path API Implementation**
   - `/v1/responses` - Full OpenAI Responses API (reasoning tokens, tool outputs)
   - `/v1/chat/completions` - Syntactic compatibility (internal reasoning tracking)
   - `/v1/intents` - Intent-driven execution (playbook orchestration)
   - Shared caching and cost infrastructure

4. **Execution Persistence**
   - Playbook execution logs with step-by-step telemetry
   - Artifact generation (CSV, MD, JSON outputs)
   - Rollback support for failed executions
   - Execution timeline visualization

**LangGraph Playbook Example:**
```python
from langgraph.graph import StateGraph

# Define playbook state
class PlaybookState(TypedDict):
    intent: str
    context: Dict[str, Any]
    steps_completed: List[str]
    artifacts: List[Dict]
    budget_used: float

# Create workflow graph
workflow = StateGraph(PlaybookState)

# Add nodes (Reason → Act → Reflect)
workflow.add_node("analyze_intent", analyze_intent_node)
workflow.add_node("execute_tool", execute_tool_node)
workflow.add_node("evaluate_result", evaluate_result_node)
workflow.add_node("decide_next", decide_next_node)

# Add edges with conditionals
workflow.add_edge("analyze_intent", "execute_tool")
workflow.add_edge("execute_tool", "evaluate_result")
workflow.add_conditional_edges(
    "evaluate_result",
    should_continue,
    {"continue": "decide_next", "complete": END}
)
```

**Success Criteria:**
- LangGraph workflows execute successfully
- Tool registry supports 5+ tool types
- Three-path API implementation complete
- Budget enforcement tested
- Rollback functional

---

## Phase 4: Intent Routing 📋 Designed

**Timeline:** 1-2 weeks
**Goal:** Enable semantic intent resolution to automatically match user requests to playbooks.

**Re^Re Context:** Intent routing is the "Reason" phase—analyzing incoming requests to understand their semantic meaning and routing them to appropriate playbooks. This enables the system to classify and respond to novel phrasings of known intents.

**Planned Features:**
1. **Intent Models & Storage**
   - Intent registry with embeddings
   - SQLite persistence for intent definitions
   - Template-to-playbook mappings
   - Version tracking and metadata

2. **Semantic Intent Matching**
   - Vector similarity search against intent embeddings
   - Confidence thresholds for automatic routing
   - Fallback to LLM when confidence is low
   - Multi-intent detection support

3. **Intent Resolution API**
   - `/v1/intents/resolve` - Match request to intent
   - `/v1/intents` - CRUD operations for intent management
   - Metadata filters (user, app, environment)
   - Dry-run mode for testing

4. **14 Specialized Playgrounds**
   - Phase 1: Prompt, Reasoning, Intent playgrounds
   - Phase 2: Template, Playbook playgrounds
   - Phase 3: Semantic Cache, Normalization, Cost Simulator
   - Phase 4: Feedback, Version Compare, A/B Test, etc.
   - See [PLAYGROUND_ARCHITECTURE.md](design/PLAYGROUND_ARCHITECTURE.md)

**Intent Resolution Example:**
```python
# User request arrives
request = "analyze security logs from last 24 hours"

# Generate embedding
embedding = await embedding_service.embed(request)

# Search intent registry
matches = await intent_store.search(
    embedding=embedding,
    threshold=0.85,
    limit=5
)

# Top match
intent = matches[0]  # SecurityLogAnalysis
confidence = matches[0].score  # 0.92

# Route to playbook
playbook = await playbook_store.get_by_intent(intent.id)
result = await execute_playbook(playbook, context={"timeframe": "24h"})
```

**Success Criteria:**
- Intent resolution accuracy >85%
- Vector search latency <50ms
- CRUD APIs fully tested
- Playgrounds implemented (Phase 1-2 at minimum)

---

## Phase 5: Feedback Loop 📋 Planned

**Timeline:** 1-2 weeks
**Goal:** Capture and analyze execution outcomes to enable learning and optimization.

**Re^Re Context:** The Feedback Loop is the "Reflect" phase—evaluating whether executions met their goals and capturing signals for improvement. This is where the system begins to learn from its actions.

**Planned Features:**
1. **Outcome Evaluation**
   - Success/failure classification for executions
   - Quality scoring (manual or automated)
   - User satisfaction signals (thumbs up/down)
   - Goal completion tracking

2. **Feedback Collection**
   - Inline feedback UI in dashboard
   - API endpoints for programmatic feedback
   - Execution replay with annotations
   - Feedback metadata (user, timestamp, context)

3. **Learning Signals**
   - Low-confidence intent resolutions
   - High-cost executions
   - Failed playbook steps
   - User corrections and overrides

4. **Feedback Analytics**
   - Aggregated quality metrics per playbook
   - Intent resolution accuracy trends
   - Cost vs quality tradeoff analysis
   - Improvement opportunity detection

**Feedback Collection Example:**
```python
# After execution completes
execution_result = await execute_playbook(playbook_id, context)

# User provides feedback
feedback = FeedbackSignal(
    execution_id=execution_result.id,
    rating=4,  # 1-5 stars
    met_goal=True,
    user_comments="Good analysis but missed edge case",
    corrections={"timeframe": "48h"}  # User override
)

await feedback_store.record(feedback)

# System learns from feedback
if feedback.rating < 3:
    await flag_for_review(execution_result.playbook_id)
```

**Success Criteria:**
- Feedback captured for 80%+ executions
- Analytics dashboard shows trends
- Low-quality playbooks flagged automatically
- Feedback loop latency <1 day

---

## Phase 6: Intent Builder v1 📋 Designed

**Timeline:** 2 weeks
**Goal:** Empower users to author intents, templates, and playbooks through visual interfaces.

**Re^Re Context:** The Intent Builder enables humans to codify their reasoning into reusable playbooks. This is where human expertise becomes automated intelligence—translating domain knowledge into executable workflows.

**Planned Features:**
1. **Playbook Playground (Visual Builder)**
   - React Flow canvas for workflow design
   - Drag-and-drop nodes (Reason, Act, Reflect steps)
   - Visual connection editor
   - Real-time validation
   - Export to LangGraph

2. **Template Playground (Monaco Editor)**
   - Syntax highlighting for templates
   - Slot variable autocomplete
   - Preview rendering with test data
   - Version diff viewer
   - Template library browser

3. **Intent Playground (Resolution Testing)**
   - Test intent matching with sample inputs
   - Confidence threshold tuning
   - Top-K results visualization
   - Embedding similarity heatmap
   - Batch testing support

4. **Draft→Validate→Test→Publish Wizard**
   - Step-by-step creation flow
   - Schema validation
   - Dry-run execution with cost estimates
   - Version tagging and approval
   - Audit trail

**Visual Playbook Builder UI:**
```
┌─────────────────────────────────────────────────────────┐
│ Playbook Builder: SecurityLogAnalysis v2               │
├─────────────────────────────────────────────────────────┤
│  [Intent] → [Parse Time] → [Query DB] → [Analyze] → [Report]
│     ↓                          ↓           ↓
│  embedding               tool:http    tool:llm
│                                            ↓
│                                      [Reflect: Quality Check]
│                                            ↓
│                                    [Re-reason: Suggest Actions]
└─────────────────────────────────────────────────────────┘
```

**Success Criteria:**
- All 14 playgrounds implemented (Phases 1-2 minimum)
- Users can create playbooks without code
- Dry-run testing functional
- Published playbooks execute correctly

---

## Phase 7: Shadow Mode / A-B Testing 📋 Planned

**Timeline:** 1.5-2 weeks
**Goal:** Safely experiment with new playbooks by running them in parallel with production without impacting users.

**Re^Re Context:** Shadow Mode enables safe "Re-reason" cycles—testing new approaches alongside existing ones, comparing outcomes, and promoting winners. This is experimentation without risk.

**Planned Features:**
1. **Parallel Execution Harness**
   - Execute production + shadow playbook simultaneously
   - Return production result to user immediately
   - Log shadow execution for analysis
   - Zero impact on user experience
   - Configurable traffic sampling (e.g., 10% shadow)

2. **Comparative Metrics**
   - Cost comparison (production vs shadow)
   - Latency comparison
   - Quality scoring (automated + human feedback)
   - Error rate tracking
   - Confidence interval calculations

3. **Promotion Workflow**
   - Gradual rollout (0% → 10% → 50% → 100%)
   - Automated promotion criteria (cost < X, quality > Y)
   - Instant rollback capability
   - Feature flags for A/B testing
   - Canary deployment support

4. **Experiment Dashboard**
   - Side-by-side metric visualization
   - Statistical significance indicators
   - Promotion/rollback controls
   - Experiment history timeline

**Shadow Mode Example:**
```python
# Request arrives
async def handle_request(request):
    # Execute production playbook (return to user)
    production_result = await execute_playbook(
        playbook_id="security_analysis_v1",
        context=request
    )

    # Execute shadow playbook (log only, don't return)
    if should_run_shadow(request):
        asyncio.create_task(
            execute_shadow_and_compare(
                shadow_playbook_id="security_analysis_v2",
                context=request,
                production_result=production_result
            )
        )

    return production_result
```

**Success Criteria:**
- Shadow execution overhead <20ms
- A/B test statistical significance detection
- Automated promotion workflows functional
- Rollback completes in <30 seconds

---

## Phase 8: Learning & Self-Tuning 📋 Planned

**Timeline:** 2-3 weeks
**Goal:** Enable the system to automatically optimize playbooks based on accumulated feedback and execution data.

**Re^Re Context:** This phase closes the Re^Re loop—the system now "Re-reasons" automatically, using feedback to tune thresholds, adjust routing, and optimize execution patterns without human intervention.

**Planned Features:**
1. **Adaptive Threshold Tuning**
   - Automatic similarity threshold optimization
   - Confidence score calibration
   - Budget allocation optimization
   - Provider selection learning

2. **Playbook Optimization**
   - Step reordering based on success patterns
   - Tool substitution recommendations
   - Prompt refinement suggestions
   - Cost reduction opportunities

3. **Intent Drift Detection**
   - Monitor semantic drift in user requests
   - Detect new intent clusters
   - Flag outdated playbooks
   - Suggest intent splits/merges

4. **Self-Healing**
   - Automatic retry strategy adjustment
   - Fallback path learning
   - Error pattern recognition
   - Proactive maintenance alerts

**Learning Example:**
```python
# System observes pattern
pattern = await analyzer.detect_pattern(
    executions=recent_executions,
    time_window="7d"
)

# Pattern: Intent X resolved at 0.85 threshold but users correct 30% of time
if pattern.correction_rate > 0.2:
    # Automatically increase threshold
    await intent_config.update_threshold(
        intent_id=pattern.intent_id,
        new_threshold=0.90,
        reason="High correction rate detected"
    )

    # Log for audit
    await audit_log.record(
        action="threshold_auto_tuned",
        details=pattern.to_dict()
    )
```

**Success Criteria:**
- Automatic threshold tuning improves accuracy by 10%+
- Cost reduction of 5-10% through optimization
- Drift detection flags issues within 48 hours
- Self-healing reduces manual intervention by 50%

---

## Phase 9: Auto-Builder 🔮 Vision

**Timeline:** 3+ weeks (R&D)
**Goal:** Automatically synthesize draft playbooks from observed traffic patterns and propose them for human approval.

**Re^Re Context:** The Auto-Builder represents emergent intelligence—the system now creates its own playbooks by observing patterns, reasoning about solutions, and proposing new automations. This is the pinnacle of the Re^Re loop.

**Planned Features:**
1. **Cluster Detection**
   - Identify stable prompt clusters (n≥10 similar requests)
   - Traffic pattern analysis
   - Intent gap detection (requests not matching any intent)
   - Cost/frequency prioritization

2. **Workflow Synthesis**
   - LLM-powered playbook generation from examples
   - Tool registry analysis and recommendation
   - Step dependency inference
   - Budget estimation based on historical data

3. **Proposal Queue**
   - Draft playbook generation with confidence scores
   - Dry-run evaluation on historical requests
   - Cost/quality/coverage projections
   - Human review interface

4. **Approval & Registration**
   - Approve/Edit/Reject workflow
   - Side-by-side comparison with manual alternatives
   - Automatic registration after approval
   - Continuous monitoring post-deployment

**Auto-Builder Logic:**
```python
# Detect opportunity
clusters = await detect_intent_gaps(
    min_count=10,
    time_window="30d",
    cost_threshold_usd=100
)

for cluster in clusters:
    # Synthesize playbook using LLM
    draft = await llm.synthesize_playbook(
        example_prompts=cluster.samples,
        available_tools=tool_registry.list(),
        constraints={"max_steps": 5, "max_cost": 0.50}
    )

    # Validate and score
    score = await validator.evaluate(
        playbook=draft,
        test_inputs=cluster.validation_set
    )

    # Submit if promising
    if score.quality > 0.7 and score.cost_savings > 50:
        await proposal_queue.submit(draft, score, cluster.metadata)
```

**Success Criteria:**
- Auto-generated playbooks have 60%+ approval rate after edits
- System proposes 1-2 new playbooks per week
- No hallucinations or unsafe operations
- Cost savings ROI > 10x development effort

---

## Phase 10: Meaning Graph 🔮 Vision

**Timeline:** 4+ weeks (R&D)
**Goal:** Build a semantic knowledge graph of intents, entities, and relationships using Neo4j/Memgraph.

**Re^Re Context:** The Meaning Graph transcends vector similarity to understand relationships—knowing that "SecurityLogAnalysis" relates to "IncidentResponse" and "ThreatDetection" enables richer reasoning and cross-domain learning.

**Planned Features:**
1. **Neo4j/Memgraph Integration**
   - Intent nodes with embeddings and metadata
   - Tool nodes with capability descriptions
   - Execution nodes with outcomes
   - Relationship edges (triggers, requires, similar_to, caused_by)

2. **Semantic Relationship Mining**
   - Co-occurrence analysis (intents often used together)
   - Causal relationships (Intent A triggers Intent B)
   - Prerequisite detection (Intent X requires Intent Y)
   - Similarity clusters (Intent families)

3. **Graph-Powered Reasoning**
   - Multi-hop intent resolution
   - Contextual playbook selection
   - Related intent suggestions
   - Workflow composition from subgraphs

4. **Learning Propagation**
   - Feedback flows through graph edges
   - Similar intents benefit from each other's learning
   - Graph embeddings for intent similarity
   - Anomaly detection via graph structure

**Graph Query Example:**
```cypher
// Find related intents for cross-learning
MATCH (i1:Intent {name: "SecurityLogAnalysis"})
MATCH (i1)-[:SIMILAR_TO|TRIGGERS|REQUIRES*1..2]-(i2:Intent)
WHERE i2.success_rate > 0.8
RETURN i2.name, i2.playbook_id, i2.success_rate
ORDER BY i2.success_rate DESC
LIMIT 5

// Propagate feedback improvements
MATCH (i1:Intent)-[r:SIMILAR_TO {similarity: >0.9}]-(i2:Intent)
WHERE i1.recent_feedback_improvement > 0.1
SET i2.needs_review = true
```

**Success Criteria:**
- Graph contains 100+ intents with 500+ relationships
- Multi-hop queries complete in <100ms
- Graph-powered recommendations improve accuracy by 15%
- Relationship mining discovers 10+ non-obvious connections

---

## Phase 11: Federation / A2A 🔮 Vision

**Timeline:** 4+ weeks (R&D)
**Goal:** Enable multiple gateway instances to federate, sharing intents, playbooks, and learnings via Agent-to-Agent (A2A) protocol.

**Re^Re Context:** Federation enables collective intelligence—multiple gateways learn together, sharing successful patterns and distributing the Re^Re loop across a network. What one learns, all benefit from.

**Planned Features:**
1. **A2A Protocol Implementation**
   - Gateway discovery and registration
   - Trust and authentication between gateways
   - Intent/playbook sharing protocol
   - Federated vector search

2. **Selective Sharing**
   - Privacy-preserving federation
   - Configurable sharing policies (public/private intents)
   - Differential privacy for sensitive patterns
   - Opt-in/opt-out controls

3. **Federated Learning**
   - Aggregate feedback across gateways
   - Distributed threshold tuning
   - Playbook quality signals from network
   - Anomaly detection via federated patterns

4. **Network Intelligence**
   - Gateway reputation scoring
   - Intent marketplace (optional)
   - Collaborative filtering for playbooks
   - Distributed rate limiting and load balancing

**A2A Protocol Example:**
```python
# Gateway A shares new high-quality intent
async def share_intent(intent: Intent):
    message = A2AMessage(
        type="intent_share",
        sender_id=gateway.id,
        payload={
            "intent": intent.to_dict(),
            "quality_score": 0.95,
            "usage_count": 1000,
            "anonymized_feedback": intent.feedback_summary()
        },
        signature=sign(message, gateway.private_key)
    )

    await federation.broadcast(message, channels=["public"])

# Gateway B receives and evaluates
async def on_intent_received(message: A2AMessage):
    if verify_signature(message):
        intent = Intent.from_dict(message.payload["intent"])

        # Evaluate relevance
        if intent.quality_score > 0.9 and is_relevant(intent):
            await intent_store.import_federated(intent, source=message.sender_id)
```

**Success Criteria:**
- 3+ gateways successfully federated
- Intent sharing reduces cold-start time by 80%
- Federated learning improves accuracy by 5-10%
- Zero privacy breaches or unauthorized access

---

## Phase 12: Edge Reasoning 🔮 Vision

**Timeline:** 4+ weeks (R&D)
**Goal:** Deploy tiny reasoning models at the edge for ultra-low latency, local intent resolution, and offline capabilities.

**Re^Re Context:** Edge Reasoning brings the Re^Re loop to the edge—enabling local reasoning with tiny models (Phi, Gemma), falling back to cloud only when needed. This is distributed intelligence with millisecond latency.

**Planned Features:**
1. **Tiny Model Deployment**
   - Phi-3-mini (3.8B) for intent classification
   - Gemma-2B for simple reasoning tasks
   - Quantized models (4-bit) for resource constraints
   - ONNX runtime for cross-platform support

2. **Edge-Cloud Orchestration**
   - Local-first architecture (resolve at edge when possible)
   - Confidence-based fallback to cloud
   - Async sync of learnings from cloud
   - Offline mode with degraded capabilities

3. **Progressive Reasoning**
   - Level 1: Edge model (0-50ms, simple intents)
   - Level 2: Gateway model (50-200ms, complex intents)
   - Level 3: Cloud model (200ms+, novel/difficult)
   - Automatic level selection based on confidence

4. **Edge Learning**
   - On-device fine-tuning (LoRA adapters)
   - Federated learning from edge to cloud
   - Privacy-preserving local personalization
   - Model compression and distillation

**Edge Deployment Architecture:**
```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  Mobile App │────▶│ Edge Gateway │────▶│ Cloud       │
│  (Browser)  │     │ (Phi-3 mini) │     │ (Full Model)│
└─────────────┘     └──────────────┘     └─────────────┘
                          │
                          ├─ Confidence > 0.90 → Return
                          ├─ Confidence 0.70-0.90 → Fallback
                          └─ Confidence < 0.70 → Cloud

Latency: 10-50ms         Latency: 50-200ms      Latency: 200-500ms
Cost: $0                 Cost: ~$0.001          Cost: ~$0.01
```

**Success Criteria:**
- Edge resolution handles 70%+ of requests
- P95 latency <50ms for edge-resolved requests
- Edge model accuracy >85% on common intents
- Fallback to cloud seamless and transparent

---

## MVP v1 Scope (Hackathon Target)

**Target:** First public demo with minimal but complete feature set

**Included:**
1. ✅ One registered MCP/custom capability
2. ✅ Two playable templates (`cost.report@v1`, `incident.triage@v1` as exemplars)
3. ✅ Dual trigger modes (explicit routing + embedding-based similarity)
4. ✅ Minimal Intent Builder v0 (create/edit playbook via UI)
5. ✅ Dashboard showing cost, latency, cache stats, and artifacts

**Timeline:** 4-6 weeks from Phase 5 start

---

## Implementation Priorities

### Sprint 1-4: Foundation Complete ✅ (Weeks 1-8)
- ✅ Phase 0: Verbatim Cache (infrastructure + basic caching)
- ✅ Phase 1: Semantic Cache & Normalization (on-premise embeddings, 60x faster)
- ✅ Phase 2 (Infrastructure): Aikido Dispatcher + Intent Observatory
- 🔄 Phase 2: Playbook-Lite (template execution, in progress)

### Sprint 5-6: Three-Path API 📋 (Weeks 9-12)
- 📋 Phase 3: Multi-Step Playbooks (LangGraph, tool registry, budget enforcement)
  - Week 9-10: LangGraph integration + tool registry
  - Week 11-12: Three-path API implementation (`/v1/responses`, `/v1/chat/completions`, `/v1/intents`)

### Sprint 7-8: Intent System 📋 (Weeks 13-16)
- 📋 Phase 4: Intent Routing (semantic matching, resolution API)
  - Week 13-14: Intent models, vector search, resolution logic
  - Week 15-16: Playgrounds Phase 1-2 (Prompt, Reasoning, Intent, Template, Playbook)

### Sprint 9-10: Feedback & Builder 📋 (Weeks 17-20)
- 📋 Phase 5: Feedback Loop (outcome evaluation, learning signals)
  - Week 17-18: Feedback collection + analytics
- 📋 Phase 6: Intent Builder v1 (visual workflow builder)
  - Week 19-20: React Flow playbook builder, Monaco template editor

### Sprint 11-12: Experimentation & Learning 📋 (Weeks 21-24)
- 📋 Phase 7: Shadow Mode / A-B Testing (parallel execution, promotion workflow)
  - Week 21-22: Shadow harness + comparative metrics
- 📋 Phase 8: Learning & Self-Tuning (adaptive optimization, drift detection)
  - Week 23-24: Threshold tuning, playbook optimization, self-healing

### Sprint 13+: Advanced Intelligence 🔮 (R&D)
- 🔮 Phase 9: Auto-Builder (playbook synthesis from traffic patterns)
- 🔮 Phase 10: Meaning Graph (Neo4j knowledge graph, relationship mining)
- 🔮 Phase 11: Federation / A2A (multi-gateway network, collective intelligence)
- 🔮 Phase 12: Edge Reasoning (Phi-3, Gemma, local inference, <50ms latency)

---

## Success Metrics

### Phase 0-2 Complete ✅
- ✅ Verbatim cache hit rate: 38% (target: >20%)
- ✅ Semantic cache improvement: +20% lift (target: +20%)
- ✅ Embedding latency: 10ms (vs 500ms OpenAI) — **60x faster**
- ✅ Embedding cost: $0 (vs $0.0001/1K tokens) — **100% savings**
- ✅ Test coverage: 187/187 passing (target: 100%)
- ✅ API response time: <2s (target: <3s)
- ✅ Dashboard uptime: 99%+ (target: 99%+)

### Phase 3-4 Planned 📋 (Three-Path API + Intent Routing)
- Intent resolution accuracy: >85% (target: >85%)
- Intent matching latency: <50ms (target: <100ms)
- Playbook execution success rate: >90% (target: >90%)
- Three-path API parity: 100% (all paths functional)
- Cost reduction: ~90% (target: ~70%)

### Phase 5-6 Planned 📋 (Feedback + Builder)
- Feedback capture rate: >80% of executions (target: >80%)
- Playground adoption: All 14 playgrounds implemented (Phase 1-2 minimum)
- Visual playbook authoring: 100% of playbooks creatable via UI (target: 80%)
- User satisfaction: >4/5 stars (target: >4/5)

### Phase 7-8 Planned 📋 (Shadow Mode + Learning)
- Shadow execution overhead: <20ms (target: <50ms)
- A/B test confidence: >95% statistical significance (target: >95%)
- Auto-tuning accuracy improvement: +10% (target: +10%)
- Self-healing intervention reduction: 50% (target: 50%)

### Phase 9-12 Vision 🔮 (Advanced Intelligence)
- Auto-builder approval rate: >60% after edits (target: >60%)
- Meaning graph relationships: 500+ edges (target: 500+)
- Federated learning accuracy lift: +5-10% (target: +5%)
- Edge resolution rate: >70% (target: >70%)
- Edge P95 latency: <50ms (target: <50ms)

---

## References

- **Project Status:** [STATUS.md](STATUS.md) - Current implementation status and next steps
- **Vision Document:** [VISION.md](design/VISION.md) - Long-term strategic direction
- **Architecture:** [ARCHITECTURE.md](../development/ARCHITECTURE.md) - Technical design details
- **Testing Guide:** [TESTING.md](../development/TESTING.md) - Test suite and QA process
- **Codebase Analysis:** [/CODEBASE_ANALYSIS.md](/CODEBASE_ANALYSIS.md) - Deep dive into implementation

---

## Document History

- **2025-11-08:** Updated to Reflective Edition with Re^Re (Reflective Reasoning) framework
  - Restructured to 12-phase roadmap (was 11 phases)
  - Added Re^Re Context sections to all phases
  - Added Phases 8-12: Learning & Self-Tuning, Auto-Builder, Meaning Graph, Federation/A2A, Edge Reasoning
  - Integrated three-path API architecture (Semantic, Syntactic, Intent)
  - Updated success metrics to reflect new phase structure
  - Aligned with VISION.md Reflective Edition
- **2025-11-06:** Created unified roadmap consolidating ROADMAP.md, ROADMAP_unified.md, EVOLUTION_ROADMAP.md, and ROADMAP_CACHE_ANALYTICS.md
- **2025-11-02:** Previous roadmap updates
- **2025-10-27:** Initial roadmap versions

---

**Maintained by:** Core Platform Team
**Last Review:** 2025-11-08
