# AI Aikido Gateway — Unified Roadmap

This roadmap merges the original **Legacy** and **Upcoming** stages into a single, continuous sequence of evolution — from a simple LLM proxy to a fully dynamic, intent-driven Gateway (IntentHub).  
Each stage can be implemented and demoed independently.

---

## 🧩 Evolution Stages

### 0. Verbatim Cache (initial state)
**Goal:** basic caching by `(model, prompt)`  
- Proxy all LLM calls through Gateway.  
- Store responses verbatim with cost tracking.  
- Dashboard: requests, hit/miss, cost per query.

---

### 1. Semantic Cache and Normalization
**Goal:** smarter reuse of results across similar prompts.  
- Add embedding-based semantic cache (threshold configurable).  
- Normalize prompts (trim system parts, unify formatting).  
- Dashboard: hit rate improvement, latency metrics.

---

### 2. Playbook-Lite (Single-Step Templates)
**Goal:** move from “hardcoded prompt” → reusable template.  
- Introduce playbook registry (`playbook@v1`, `playbook@v2`).  
- Add slot substitution for dynamic inputs.  
- Enable switching playbook versions without redeploying the app.  
- Keep verbatim + semantic cache underneath.

---

### 3. Multi-Step Playbooks & Capability Registry
**Goal:** orchestrate multiple tools (LLM + MCP + API).  
- Define registry of tools/capabilities with input/output schemas.  
- Execute multi-step flows: `collect → transform → compose`.  
- Add budget/policy enforcement (`budget_usd_max`, `providers_allow`).  
- Produce artifacts (CSV, MD, JSON).

---

### 4. Intent Routing and Triggers
**Goal:** automatic or explicit selection of playbook.  
- Cluster similar prompts via embeddings.  
- Auto-trigger matching playbook by similarity.  
- Support explicit routing by `playbook_ref` or `intent_ref`.  
- Add **hint modes:** `bind`, `prefer`, `avoid`, `suggest`.

---

### 5. Feedback Loop
**Goal:** gather human feedback and enable learning.  
- Endpoint `/v1/feedback` for marking responses (correct / incorrect / partial).  
- Include metadata: request_id, triggered_intent, expected_intent, notes.  
- Dashboard review mode for corrections and statistics.  
- Store all feedback for later tuning and analytics.

---

### 6. Intent Builder v1 (Manual)
**Goal:** enable power-users to design playbooks directly.  
- Web form or CLI for: name → slots → steps → test → publish.  
- Validate step input/output compatibility.  
- Save as `playbook@vX` in registry.  
- Allow quick draft creation (“new intent in 2 minutes”).

---

### 7. Shadow Mode / A-B Testing
**Goal:** safe experimentation.  
- Deploy new playbook versions in **shadow mode** (log only).  
- Compare metrics (cost, latency, quality).  
- Switch or rollback instantly.

---

### 8. Learning & Self-Tuning
**Goal:** use feedback and statistics to improve routing.  
- Batch processor aggregates feedback data.  
- Auto-adjust thresholds, merge/split clusters.  
- Suggest corrections for mis-routed prompts.  
- Manual review before apply.

---

### 9. Auto-Builder (Proposed Playbooks)
**Goal:** system generates draft playbooks for new clusters.  
- Detect stable prompt clusters (n≥K).  
- Synthesize skeleton workflows from tool registry.  
- Dry-run evaluation (cost, latency, coverage).  
- Present as proposal: “Approve / Edit / Reject”.

---

### 10. Meaning Graph (Intent Network)
**Goal:** represent semantic relationships between intents.  
- Map relations: `similar`, `refines`, `flows_to`, `contradicts`.  
- Visualize intent graph in dashboard.  
- Use relationships to improve routing and Builder suggestions.

---

## 🧠 MVP Scope (Hackathon Target)
**Target features for first public demo:**
1. One registered MCP (custom capability).
2. Two playbooks (e.g. `cost.report@v1`, `incident.triage@v1`).
3. Dual trigger modes (explicit + embedding-based).
4. Minimal Intent Builder v0 (create/edit playbook via UI).
5. Dashboard showing cost, latency, cache stats, artifacts.

---

## 🧭 Next Steps After MVP
- Shadow-mode and feedback integration (Stage 7 + 5).  
- Auto-learning (Stage 8).  
- Auto-Builder prototype (Stage 9).  
- Graph visualization (Stage 10).  
- Public documentation + GitHub Pages site.

---

**Summary:**  
> The Gateway evolves from a simple LLM proxy into an open, extensible framework —  
> a “constructor for intelligent systems,” where developers can plug in new capabilities, define intents, and build their own ChatGPT-like assistants with full control over structure, cost, and behavior.

