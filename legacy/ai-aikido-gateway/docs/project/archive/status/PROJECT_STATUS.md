# AI Aikido Gateway – Project Status

**Last updated:** 2025-11-01  
**Maintainer:** Core Platform Team  
**Current branch:** `dev`  
**Default branch:** `dev`

---

## Executive Summary

- **Phase 1–4.2 are complete.** Foundation, plugin system, request history, cost tracking, cost explorer, transparency headers, and intelligent caching are production ready.
- **Phase 5 features merged.** LiteLLM-backed provider proxies (OpenAI + Anthropic) with telemetry and guard rails now live on `dev`; a scheduled post-merge review will confirm configuration guidance.
- **Cloud build-out paused.** Suspend all cloud deployment or infra experiments; redirect those cycles to gateway hardening and intent tooling until leadership restarts the initiative.
- **Primary focus:** monitor the proxies in shared environments, complete the guard-rail audit, finish the carryover backlog from Phase 4 (budget alerts, cache tooling), and stand up Stage 1 semantic cache foundations.

---

## Phase 5 Hardening Checklist

| Area | Status |
|------|--------|
| **LiteLLM proxy E2E tests** | Added high-level regression cases that monkeypatch `litellm.acompletion` to avoid network access. Exercises happy-path, fallback, and Anthropic flows. |
| **Transparency headers** | `X-Gateway-Retries` now surfaces retry provenance for debugging. |
| **Proxy guard rails** | OpenAI/Anthropic plugins auto-disable when no API keys exist, returning clear `ProviderNotConfigured` responses; synthetic guard-rail suite (`tests/test_guard_rails.py`) now verifies 503 outcomes and disabled plugins. |
| **Testing guide** | `docs/development/TESTING.md` documents the expanded workflow. |

**In-flight actions**

1. Validate that the end-to-end suite passes in CI (ensuring `litellm` dependency and async patches behave under Pytest).
2. ✅ 2025-11-01 guard-rail review (synthetic telemetry via pytest) logged below; follow-up tickets required only if new regressions appear.
3. Park any ongoing cloud deployment tasks; move related tickets back to the backlog and close incidental work-in-progress branches.
4. Define the multi-tenant authentication model (gateway-issued keys, optional tenant-provided provider keys, internal subnet exemptions).
5. Implement the dashboard CLI playground panel to surface the exact OpenAI-style payload (curl preview and copy button).
6. Kick off Phase 4 backlog items (budget alerts, cache invalidation tooling) immediately after the guard-rail review.
7. Bootstrap dashboard UI smoke tests using Playwright and iterate on coverage as part of the next sprint.
8. Execute Stage 1 semantic cache initiatives captured in `docs/project/NEXT_STEPS.md` (tasks 8–10) without resuming any cloud deployment work.

### Guard-rail Review Notes — 2025-11-01

- Ran `pytest tests/test_guard_rails.py` to simulate missing provider credentials; plugins auto-disabled themselves and surfaced 503 `provider_not_configured` responses with transparency headers intact.
- Verified request context metadata includes disabled plugin reasons and no cache/history side effects when guard rails trigger.
- No additional safeguards required; next telemetry check should come from real proxy traffic once environments go live.

---

## Quality & Testing

- **Automated suites**
  - `pytest tests/test_end_to_end.py` (new) – mocks LiteLLM to verify cache/history interactions and headers.
  - `pytest tests/test_guard_rails.py` (new) – enforces provider guard rails when API keys are missing, checking disabled plugins and 503 responses.
  - GitHub Actions (`.github/workflows/ci.yml`) runs the full Pytest suite on pushes/PRs targeting `dev`/`main`.
  - Legacy unit suites (83 tests) remain stable; re-run `pytest` after installing `litellm` to confirm.
- **Manual validation**
  - When running the gateway directly, supply provider API keys or monkeypatch LiteLLM; otherwise requests will hang awaiting upstream providers.
- **CI considerations**
  - Ensure `litellm` is available in CI environments.
  - SQLite-backed cache/history paths are overridden to tmp directories in tests—works in GitHub Actions as long as the filesystem is writable.

---

## Deployment & Operations Snapshot

- **Service ports**
  - Gateway API: `:8000`
  - Dashboard (Vite): `:3000`
- **Persistent data**
  - Cache DB: `/app/data/cache.db`
  - History DB: `/app/data/history.db`
- **Key Plugins (enabled)**
  - `cache` (two-tier LRU + SQLite)
  - `openai_proxy`, `anthropic_proxy` (LiteLLM)
  - `transparency`, `history`, `example_logger`

---

## Risks & Decisions

1. **Proxy configuration drift:** Guard rails now disable proxies when keys are missing, returning 503s. Ensure documentation and staging checks keep expectations clear after the scheduled review.
2. **Retry telemetry correctness:** Newly added headers rely on consistent error typing from LiteLLM; ensure edge cases (non-LiteLLM exceptions) are handled.
3. **SQLite schema drift:** Cache/history plugins mutate DB paths in tests; double-check migrations/indices for production paths after recent caching improvements.

---

## Next 2–3 Iterations

1. **Harden LiteLLM integrations**
   - Add deterministic fixtures for error pathways.
   - Complete the scheduled guard-rail review and publish follow-up actions.
2. **Finish Phase 4 backlog – Budget alerts & notifications**
   - Build atop existing cost tracking for daily/weekly/monthly thresholds.
3. **Stage 1 semantic cache & normalization**
   - Deliver the semantic cache, normalization pipeline, and dashboard metrics outlined in `docs/project/NEXT_STEPS.md` tasks 8–10.
   - Keep work local-first; no cloud deployment until leadership reopens that stream.
4. **Roadmap execution (Phase 5)**
   - Finalise proxy resilience (load balancing, quotas).
   - Introduce multi-provider routing rules once proxies are stable.
5. **Gateway multi-tenant auth**
   - Register clients with gateway-issued keys, allow opt-in provider keys, enforce quotas and disable open relay behaviour.
   - Support "private" tenants (same subnet/friendly subnets/custom headers) with relaxed rules but auditable logging.
6. **Plugin toggle controls**
   - Provide UI & admin integration to enable/disable plugins per environment with transparency about active stack.
   - Persist toggles via `config/plugins.yaml` or dedicated admin endpoints and surface status in Settings.
7. **Playground advanced request builder**
   - Let users edit system/session prompts, temperature, max tokens, headers, tools, and MCP directives.
   - Keep the curl/JSON preview in sync with every field and surface plugin/tool metadata.
8. **Dashboard UI regression coverage (Playwright)**
   - Stand up Playwright harness for navigation smoke tests.
   - Expand to Cost Explorer and Request History views once initial scaffolding lands.

---

## Roadmap – Gateway to IntentHub

### Stage 0: Baseline Hardening (≈1 week)
- **Objectives** instrument structured logging, tracing, auth, and normalized cache schema to support future metrics.
- **Backend Deliverables** cost tracking per provider, config-driven secrets, alert hooks for budget anomalies.
- **Frontend Deliverables** richer dashboard cards (per-model charts, cache timeline) and cost-cap settings.
- **Success Criteria** staging uptime ≥99%, dashboards refresh in ≤5s, reproducible setup scripts.
- **Dependencies** current gateway foundation; anchors metrics for later stages.

| Task | Modules / Files | Notes |
|------|-----------------|-------|
| Structured logging & correlation IDs | `src/core/logging.py`, `src/main.py`, `src/core/pipeline.py` | Replace basic logging config with JSON formatter and include request correlation metadata across pipeline execution. |
| Request tracing middleware | `src/api/middleware.py`, `src/api/routes.py`, `tests/test_end_to_end.py` | Inject middleware to stamp trace IDs, bind logging context, return `X-Trace-Id`, and assert header presence in tests. |
| Auth scaffolding & config | `src/api/auth.py`, `src/api/models.py`, `config/tenants.sample.yml` | Introduce gateway-issued key model, config loader, and stub validation routine. |
| Cost alert configuration | `src/core/config.py`, `config/billing.sample.yml`, `/v1/settings` | Extend config to store alert thresholds and surface them via the settings endpoint. |

### Stage 1: Intent & Template Models (≈1–1.5 weeks)
- **Objectives** persist the Intent→Template→Playbook→Execution hierarchy.
- **Backend Deliverables** relational schema, CRUD APIs, embedding store integration for similarity lookup.
- **Frontend Deliverables** Intents admin list with create/edit and prompt-tagging from cache history.
- **Success Criteria** validation-covered APIs, UI edits persisted, integration tests green.
- **Dependencies** Stage 0 telemetry for future reporting; required ahead of execution engine.

### Stage 2: Playbook Execution Engine v1 (≈2–3 weeks)
- **Objectives** orchestrate multi-step workflows with tool registry, budgets, and versioning.
- **Backend Deliverables** DAG/sequence executor, tool adapters (LLM, HTTP, MCP stub), execution logs, `playbook@vN` support.
- **Frontend Deliverables** dashboard timelines showing execution metrics, cost per step, and rollback controls.
- **Success Criteria** multi-step runs with retries stay within budgets, ≥90% unit coverage on orchestrator, rollback tested.
- **Dependencies** Stage 1 models; foundation for builder UX and routing.

### Stage 3: Intent Builder UX (≈2 weeks)
- **Objectives** empower power-users to author playbooks without code deploys.
- **Backend Deliverables** validation, dry-run, and publish endpoints updating playbook state with audit trails.
- **Frontend Deliverables** Draft→Validate→Test→Publish wizard, diff viewer, inline tool documentation.
- **Success Criteria** author can design, dry-run, and publish from UI; audit log captures lifecycle; usability review passes.
- **Dependencies** Stage 2 execution APIs.

### Stage 4: Semantic & Verbatim Cache (≈1 week)
- **Objectives** add embedding-aware cache with per-intent policies and observability.
- **Backend Deliverables** similarity threshold configuration, hit/miss latency metrics, per-intent overrides.
- **Frontend Deliverables** charts for semantic vs verbatim hit rate, tuning controls.
- **Success Criteria** measured hit-rate lift (target ≥20%), thresholds persisted, metrics surfaced.
- **Dependencies** Stage 1 embeddings store; Stage 2 execution logging.

### Stage 5: Feedback Loop & Review (≈1–1.5 weeks)
- **Objectives** close the loop with runtime feedback ingestion and review workflow.
- **Backend Deliverables** `/v1/feedback` endpoint, storage linked to executions, periodic review summaries.
- **Frontend Deliverables** feedback triage console with threshold/cluster adjustments.
- **Success Criteria** feedback-to-resolution tracked, reviewers complete triage, alerts available.
- **Dependencies** Stages 1–4 data; informs routing and auto-builder.

### Stage 6: Intent Routing Engine (≈2 weeks)
- **Objectives** route traffic via embeddings clusters and explicit rules.
- **Backend Deliverables** clustering service, policy engine supporting `bind/prefer/avoid/suggest`, fallback strategy.
- **Frontend Deliverables** routing configuration panel, heatmaps, manual override tools.
- **Success Criteria** routing accuracy benchmark met, overrides respected, latency overhead <10%.
- **Dependencies** Stage 4 embeddings + Stage 5 feedback insights; enables experimentation.

### Stage 7: Shadow Mode & A/B Testing (≈1.5–2 weeks)
- **Objectives** safely evaluate new playbooks before promotion.
- **Backend Deliverables** parallel execution harness, comparative metrics, activation/rollback API.
- **Frontend Deliverables** experiment dashboard, promotion toggles, health indicators.
- **Success Criteria** shadow runs incur <20% overhead, promotion workflow tested end-to-end.
- **Dependencies** Stages 3 and 6 for playbook authoring and routing.

### Stage 8: Auto-Builder R&D (≈3+ weeks, ongoing)
- **Objectives** synthesize draft playbooks from clustered prompts for human approval.
- **Backend Deliverables** analytics job generating proposals, safeguards against hallucination, review queue APIs.
- **Frontend Deliverables** proposal inbox with diff viewer and acceptance flow.
- **Success Criteria** ≥60% accepted after edits, monitoring detects drift, governance in place.
- **Dependencies** Mature feedback and routing signals from Stages 5–7.

### MVP v1 Scope
- Intent→Template→Playbook→Execution data model with CRUD.
- Playbook Execution Engine v1 with budgets, tool registry, and version rollback.
- Intent Builder through Publish stage with dry-run validation.
- Dual-layer cache metrics in dashboard.
- Feedback ingestion endpoint and review UI.
- Routing by explicit `playbook_ref` plus similarity fallback scaffolding.
- Shadow mode toggles scaffolded even if inactive; end-to-end author→execute→feedback tests in CI.

### Snapshot – Current Roadmap Alignment
- Phase 1–4.2 work corresponds to legacy Stages 1–4 (Cost Shield → Intent Observatory) and is reflected in production features listed earlier in this status report.
- Active backlog aligns with Roadmap Stage 0 preliminaries (cost alerts, cache tooling) and the transitional pieces of Stage 3 (builder UX) and Stage 4 (cache analytics UI).
- Upcoming multi-tenant auth, routing intelligence, and Intent Builder UX map directly to the IntentHub Stage 1–3 milestones in [`ROADMAP.md`](ROADMAP.md).
- Autonomous Plan Induction and Auto-Builder efforts remain future-state and depend on finishing the feedback loop and routing engine in later stages.

---

## Reference

- Quick start / daily context: `CONTEXT.md`
- Roadmap & milestones: `docs/project/ROADMAP.md`
- Long-term vision: `docs/project/VISION.md`
- Detailed testing guidance: `docs/development/TESTING.md`
