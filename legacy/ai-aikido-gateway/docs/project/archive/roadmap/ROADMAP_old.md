# AI Aikido Gateway – Roadmap

**Last updated:** 2025-11-02  
**Audience:** Core engineering & product (solo developer)  
**Source docs:** [`PROJECT_STATUS.md`](PROJECT_STATUS.md), [`EVOLUTION_ROADMAP.md`](EVOLUTION_ROADMAP.md), [`ROADMAP_unified.md`](ROADMAP_unified.md)

This roadmap merges the legacy phase view with the IntentHub build-up into a single sequence that starts with today’s caching gateway and ends with an adaptive, intent-driven execution layer. Each stage can land independently, providing incremental demos and validation points.

---

## Evolution Stages

### Stage 0 — Verbatim Cache (Initial State)
- **Goal** basic caching by `(model, prompt)` so all traffic runs through the gateway.
- **Key Outcomes** proxy all LLM calls, store responses verbatim with cost tracking, surface request counts, hit/miss ratios, and per-request cost in the dashboard.

### Stage 1 — Semantic Cache & Normalization
- **Goal** improve reuse across similar prompts.
- **Key Outcomes** introduce embedding-based semantic cache with configurable threshold, normalize prompts (trim system parts, canonical formatting), expand dashboard with semantic hit-rate and latency metrics.

### Stage 2 — Playbook-Lite (Single-Step Templates)
- **Goal** move from hardcoded prompts to reusable templates.
- **Key Outcomes** stand up a playbook registry with versioning (`playbook@v1`), add slot substitution for dynamic inputs, enable swapping versions without redeploying the app, keep verbatim + semantic cache layers in place.

### Stage 3 — Multi-Step Playbooks & Capability Registry
- **Goal** orchestrate multi-step workflows across tools.
- **Key Outcomes** define tool/capability registry with input/output schemas, execute flows such as `collect → transform → compose`, enforce budgets and provider policies, emit artifacts (CSV, Markdown, JSON).

### Stage 4 — Intent Routing & Triggers
- **Goal** select playbooks automatically or explicitly.
- **Key Outcomes** cluster prompts via embeddings, auto-trigger matching playbooks by similarity, support routing by `playbook_ref` or `intent_ref`, respect hint modes (`bind`, `prefer`, `avoid`, `suggest`).

### Stage 5 — Feedback Loop
- **Goal** gather feedback to guide tuning.
- **Key Outcomes** expose `/v1/feedback` for correctness votes with metadata (request ID, triggered intent, expected intent, notes), add dashboard review mode for triage, retain all feedback for analytics.

### Stage 6 — Intent Builder v1 (Manual)
- **Goal** let power-users design playbooks directly.
- **Key Outcomes** deliver UI or CLI to capture name → slots → steps → test → publish, validate step input/output compatibility, persist as `playbook@vX`, streamline “draft new intent in minutes”.

### Stage 7 — Shadow Mode / A-B Testing
- **Goal** experiment safely before promotion.
- **Key Outcomes** run new playbook versions in shadow mode (log only), compare cost/latency/quality metrics, switch or roll back instantly when ready.

### Stage 8 — Learning & Self-Tuning
- **Goal** use accumulated data to adjust routing automatically.
- **Key Outcomes** batch-process feedback, auto-adjust thresholds, merge or split clusters, suggest corrections for misrouted prompts, require human confirmation before applying changes.

### Stage 9 — Auto-Builder (Proposed Playbooks)
- **Goal** generate draft playbooks from traffic patterns.
- **Key Outcomes** detect stable prompt clusters, synthesize skeleton workflows leveraging the tool registry, dry-run and score proposals, present reviewers with Approve/Edit/Reject options.

### Stage 10 — Meaning Graph (Intent Network)
- **Goal** model relationships across intents.
- **Key Outcomes** track relations such as `similar`, `refines`, `flows_to`, `contradicts`, visualize the graph in the dashboard, use it to improve routing and Builder suggestions.

---

## MVP Scope (Hackathon Target)
1. Register at least one MCP/custom capability.
2. Ship two playable templates (`cost.report@v1`, `incident.triage@v1` as exemplars).
3. Enable dual triggers (explicit routing + embedding-based similarity).
4. Deliver Intent Builder v0 for create/edit/publish from the UI.
5. Display cost, latency, cache stats, and produced artifacts in the dashboard.

---

## After MVP
- Add shadow mode and integrate feedback ingestion (Stages 7 and 5).
- Roll out auto-learning for routing and thresholds (Stage 8).
- Prototype Auto-Builder proposals (Stage 9).
- Implement intent network visualization and graph-informed routing (Stage 10).
- Publish documentation and a GitHub Pages overview site.

---

## References
- [`PROJECT_STATUS.md`](PROJECT_STATUS.md) — live status and backlog alignment.
- [`EVOLUTION_ROADMAP.md`](EVOLUTION_ROADMAP.md) — narrative history and impact estimates.
- [`ROADMAP_unified.md`](ROADMAP_unified.md) — source outline for this document.
