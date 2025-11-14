# AI Aikido Gateway - Quick Onboarding

**Last Updated:** 2025-11-09
**Current Phase:** Phase 3 - Multi-Step Playbooks
**Active Branch:** `dev`
**Test Status:** 209/209 passing ✅

---

## 30-Second Context

The AI Aikido Gateway is a **Reflective Intelligence Platform** that intercepts LLM requests to add:

- **Cost tracking & caching** (Phases 0-1) ✅
- **Multi-provider routing** (Phase 2) ✅
- **Multi-step playbooks with LangGraph** (Phase 3) 🚧
  - Week 10 ✅: Tool Registry & Adapters
  - Week 11-12 🚧: Three-Path API
- **Intent-based execution** (Phase 4+) 🔮

**Re^Re Framework:** Reason → Act → Reflect → Re-reason → ∞

---

## Current Status (At a Glance)

| Metric | Value |
|--------|-------|
| **Tests** | 209/209 passing (100%) |
| **Source Files** | 50 Python files in `src/` |
| **Test Files** | 26 Python files in `tests/` |
| **Docker Services** | 4 (gateway, dashboard, embeddings, qdrant) |
| **Demo Scripts** | 3 categories in `demos/` |

---

## Active Priorities (In Order)

### ✅ Priority 1: Project Structure Cleanup (COMPLETE)
- Organized demos/, scripts/, docs/
- Clean root directory (25+ files → 14 essential files)

### 🚧 Priority 2: Documentation Cleanup (IN PROGRESS)
- Create ONBOARDING.md (this file!)
- Archive outdated docs
- Clean up progress tracking files
- Deduplicate roadmap content

### 🔜 Priority 3: Visual Dashboard Demos (NEXT)
- Playbook Playground page
- Tool Registry Explorer
- Workflow Visualizer
- Enhanced monitoring

### 🔜 Priority 4: Three-Path API Implementation (AFTER P3)
- Update `/v1/responses` for full playbook execution
- Update `/v1/chat/completions` for internal reasoning
- Create `/v1/intents` endpoint

---

## Key Files & Their Purpose

### API Layer
| File | Purpose | Lines |
|------|---------|-------|
| [src/api/routes.py](../../src/api/routes.py) | All API endpoints | 1000+ |
| [src/api/models.py](../../src/api/models.py) | Pydantic request/response models | 210 |
| [src/api/playbook_integration.py](../../src/api/playbook_integration.py) | Playbook-API bridge | 238 |

### Workflow System (Phase 3)
| File | Purpose | Lines |
|------|---------|-------|
| [src/workflows/state.py](../../src/workflows/state.py) | PlaybookState TypedDict | 142 |
| [src/workflows/nodes.py](../../src/workflows/nodes.py) | Re^Re loop nodes | 260 |
| [src/workflows/graphs.py](../../src/workflows/graphs.py) | LangGraph workflow | 71 |
| [src/workflows/executor.py](../../src/workflows/executor.py) | Execution interface | 144 |

### Tool Registry (Week 10)
| File | Purpose | Lines |
|------|---------|-------|
| [src/tools/base.py](../../src/tools/base.py) | Tool base class | 110 |
| [src/tools/registry.py](../../src/tools/registry.py) | ToolRegistry | 148 |
| [src/tools/adapters/llm.py](../../src/tools/adapters/llm.py) | LLM tool adapter | 122 |
| [src/tools/adapters/http.py](../../src/tools/adapters/http.py) | HTTP API adapter | 119 |
| [src/tools/adapters/python_function.py](../../src/tools/adapters/python_function.py) | Python function wrapper | 110 |

### Progress Tracking
| File | Purpose | When to Update |
|------|---------|----------------|
| **[CONTEXT.md](CONTEXT.md)** | Session-by-session history | After each session (append-only) |
| **[STATUS.md](../STATUS.md)** | Current snapshot | When status changes |
| **[ROADMAP.md](../ROADMAP.md)** | High-level vision | Rarely (major pivots only) |
| **ONBOARDING.md** (this file) | Quick handoff guide | Weekly or when priorities change |

---

## Recent Commits (Last 10)

```
d7c23c3 docs: update CONTEXT.md with Week 10 and Priority 1 completion
4cd5bd8 refactor: reorganize project structure (Priority 1 cleanup)
52d78de feat: add API models and playbook integration for three-path architecture
286b674 demo: add tool registry demonstration script
5451eff feat: implement tool registry and adapters (Week 10)
c31d23b Merge branch 'feature/langgraph-state-updates' into dev
2a1fb9d feat: harden LangGraph workflow guardrails
ceaf8e4 docs: save context for Phase 3 LangGraph prototype completion
1e57efe fix: resolve Docker dependency conflicts for Python 3.11 compatibility
cea8f35 fix: update LangGraph dependencies and disable checkpointing
```

---

## How to Continue Work

### 1. Quick Context Restore (5 minutes)
1. Read this file (you're here!) ✅
2. Check [STATUS.md](../STATUS.md) for detailed current state
3. Review last 2-3 sessions in [CONTEXT.md](CONTEXT.md) (sections 32-35)
4. Check active todos in current session

### 2. Environment Setup
```bash
# Clone and enter directory
cd /home/dev/code/playground/ai/ai-aikido-gateway

# Check status
git status
git log -5

# Verify tests
pytest tests/ -v

# Start Docker services
make docker-redeploy
```

### 3. Run a Demo (Quick Validation)
```bash
# Tool Registry demo (Week 10)
python demos/tool_registry/demo_tool_registry.py

# LangGraph workflow demo
python demos/langgraph/demo_langgraph.py

# Semantic cache demo
bash demos/semantic_cache/demo_semantic_cache.sh
```

---

## Recovery Commands

### If Docker is broken:
```bash
make docker-redeploy          # Full rebuild
docker ps                     # Check services
docker logs gateway           # Debug gateway
docker logs dashboard         # Debug dashboard
```

### If tests are failing:
```bash
pytest tests/ -v --tb=short   # Run with short traceback
pytest tests/ -x              # Stop on first failure
pytest tests/test_X.py -v    # Run specific test file
```

### If imports are broken:
```bash
# Ensure you're in project root
pwd  # Should be: /home/dev/code/playground/ai/ai-aikido-gateway

# Run with PYTHONPATH
PYTHONPATH=$PWD python demos/tool_registry/demo_tool_registry.py
```

---

## Common Tasks

### Add a new test:
1. Create test file in `tests/` or `tests/integration/`
2. Import modules: `from src.module import Class`
3. Use `@pytest.mark.asyncio` for async tests
4. Run: `pytest tests/test_yourfile.py -v`

### Add a new tool adapter:
1. Create file in `src/tools/adapters/`
2. Inherit from `Tool` base class
3. Implement `async def execute(self, input_data) -> ToolResult`
4. Register in `src/tools/adapters/__init__.py`
5. Write tests in `tests/test_tool_registry.py`

### Add a new API endpoint:
1. Add route in `src/api/routes.py`
2. Create Pydantic models in `src/api/models.py`
3. Write integration test in `tests/test_api.py`
4. Update OpenAPI docs (automatic via FastAPI)

### Update documentation:
1. **Session history:** Append to [CONTEXT.md](CONTEXT.md)
2. **Current status:** Update [STATUS.md](../STATUS.md)
3. **This guide:** Update ONBOARDING.md when priorities change
4. **Commit:** Use descriptive commit messages

---

## Architecture Quick Reference

### Request Flow
```
Client Request
    ↓
FastAPI Routes (src/api/routes.py)
    ↓
Plugin Pipeline (before_request)
    ↓
Semantic Cache Check
    ↓
LLM Proxy (OpenAI/Anthropic)
    ↓
Plugin Pipeline (after_response)
    ↓
Cost Tracking
    ↓
History Storage
    ↓
Client Response
```

### Playbook Execution Flow (Phase 3)
```
API Endpoint
    ↓
execute_playbook_for_api() [playbook_integration.py]
    ↓
execute_playbook() [executor.py]
    ↓
LangGraph StateGraph [graphs.py]
    ↓
Re^Re Loop:
  1. analyze_intent (REASON)
  2. execute_tool (ACT)
  3. evaluate_result (REFLECT)
  4. decide_next (RE-REASON)
    ↓
Return PlaybookState with artifacts
```

---

## What to Work on Next?

Based on current priorities:

**Immediate (Today):**
- Complete Priority 2: Documentation cleanup
- Archive outdated docs in `docs/project/archive/`
- Clean up NEXT_PRIORITIES.md

**This Week:**
- Priority 3: Visual dashboard demos
- Create Playbook Playground page
- Add workflow visualizer

**Next Week:**
- Three-Path API endpoints
- `/v1/responses`, `/v1/chat/completions`, `/v1/intents`
- Integration tests for all three paths

---

## Need Help?

### Documentation
- **Quick Start:** [README.md](../../../README.md)
- **Architecture:** [docs/development/ARCHITECTURE.md](../../development/ARCHITECTURE.md)
- **Testing:** [docs/development/TESTING.md](../../development/TESTING.md)
- **Deployment:** [docs/deployment/DEPLOYMENT.md](../../deployment/DEPLOYMENT.md)

### Key Concepts
- **Re^Re Framework:** [docs/project/design/VISION.md](../design/VISION.md)
- **Roadmap:** [docs/project/ROADMAP.md](../ROADMAP.md)
- **Phase 3 Plan:** [docs/project/implementation/PHASE_3_IMPLEMENTATION_PLAN.md](../implementation/PHASE_3_IMPLEMENTATION_PLAN.md)

### Ask Questions
- Check recent commit messages for context
- Review CONTEXT.md for session history
- Look at test files for usage examples
- Run demos to see features in action

---

**Remember:** This file is your **starting point** for any new session. Read it first, then dive into specifics as needed.

**Last Session:** Completed Week 10 (Tool Registry), Priority 1 (Project Cleanup), started Priority 2 (Doc Cleanup)
