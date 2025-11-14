# Intent Architecture Vision

## Overview

This document describes the evolution from **naive prompts** to a **deterministic intent-driven system**, using **Prompt Studio as the Trojan Horse** - a familiar interface that gradually introduces structure, determinism, and observability.

**Core Principle:** Each stage adds value independently while preparing for the next. Users experience continuous improvement without disruption.

---

## Module Boundaries

### LLM Service Stack (Current Repo - v1)
**Repository:** `llm-service-stack/`

Handles all prompt-based interactions with progressive structure:
- Gateway (controlled LLM entry point)
- App Server (users, sessions, API keys)
- **Prompt Studio** (the stable facade for all stages)
- Web Chat (reference client)

**Owns:** Stages 1-5 (naive prompts → frozen artifacts)

### Intent Engine (Future Repo - v2+)
**Repository:** `intent-engine/` (separate)

Deterministic execution runtime:
- Playbook executor (DAG-based workflows)
- Intent router (automatic workflow selection)
- Policy engine (cost/model/tool constraints)

**Owns:** Stages 6-8 (playbooks → intent engine)

### Tools Gateway (Future Repo)
**Repository:** `tools-gateway/` (separate)

Tool integration layer:
- MCP server integration
- Sandboxed execution
- Tool registry and policies

**Enables:** Actions beyond text (Stage 4 from EVOLUTION.md)

---

## Evolution Stages

### Stage 1 — Naive Prompt ✅ **(Current)**

**What:** Raw, unstructured text input
**Where:** LLM Service Stack (Prompt Studio)
**Value:** Simple, immediate, no learning curve

Users write free-form prompts. Every request is unique, expensive, and not reproducible.

---

### Stage 2 — Smart Prompt 🎯 **(Next)**

**What:** LLM-generated template from naive input
**Where:** LLM Service Stack (Prompt Studio)
**Value:** Better results, teaches users good prompting

Prompt Studio offers "✨ Enhance Prompt" - uses GPT-4/Claude to improve clarity, specificity, and structure. Shows before/after comparison.

**User Experience:**
```
User types: "make a react app"
         ↓
System shows:
  Enhanced: "Create a modern React application with:
             - TypeScript for type safety
             - Component structure following...
             - Include routing setup..."

  [Use This] [Edit] [Save as Template]
```

**Why this matters:** Builds dataset for Stage 3, teaches users, introduces concept of "better prompts."

**Design doc:** `docs/design/SMART_PROMPTS.md`

---

### Stage 3 — Template Match

**What:** Semantic retrieval of existing templates
**Where:** LLM Service Stack (Prompt Studio)
**Value:** Reuse > regenerate, cost savings, consistency

Instead of regenerating every time, match user input to library of proven templates. Reuses existing semantic cache infrastructure.

**User Experience:**
```
User types: "review my python code"
         ↓
System shows:
  🔍 Similar templates found:

  ⭐ Code Review (95% match)
     Used 42 times | Avg cost: $0.002
     [Use This]
```

**Why this matters:** Massive cost reduction, quality consistency, foundation for argument extraction.

**Design doc:** `docs/design/TEMPLATES.md`

---

### Stage 4 — Argument Extraction

**What:** Fill template parameters from natural language
**Where:** LLM Service Stack (Prompt Studio)
**Value:** Structured input, validation before execution

Extract structured arguments from user prompts, validate against template specs, request missing parameters interactively.

**User Experience:**
```
Template: Code Review
         ↓
✅ Code: [extracted]
✅ Language: python
⚠️  Focus Areas: [not specified - please select]
   □ Bugs  □ Performance  □ Style
```

**Why this matters:** User intent becomes structured data. First step toward determinism.

**Design doc:** `docs/design/TEMPLATES.md#argument-extraction`

---

### Stage 5 — Freeze / Materialize 🎯

**What:** Convert template + args into immutable artifact
**Where:** LLM Service Stack (Prompt Studio)
**Value:** **First boundary of determinism** - fully reproducible

Prompt is frozen, no further LLM interpretation. Can be executed identically multiple times, shared, versioned, audited.

**User Experience:**
```
Request Frozen ✅
Frozen ID: req_abc123
Template: Code Review v2.3

[View Artifact] [Execute] [Share]

📊 Estimates:
   Cost: ~$0.0023
   Success Rate: 95%
```

**Why this matters:** **Determinism begins here.** Execution is now reproducible, auditable, cost-predictable.

**Design doc:** `docs/design/FROZEN_REQUESTS.md`

---

### Stage 6 — Playbook Generation 🔜

**What:** Multi-step executable workflows (DAG)
**Where:** Intent Engine (separate repo)
**Value:** Complex tasks, tool integration, step-by-step execution

Convert frozen requests into deterministic workflows with multiple steps, conditional logic, tool calls, error handling.

**Conceptual Example:**
```yaml
playbook: full_code_review
steps:
  - static_analysis (tool call)
  - llm_review (frozen template)
  - suggest_fixes (frozen template)
  - apply_fixes (tool call, conditional)
```

**Why this matters:** Enables complex workflows beyond single LLM calls. Foundation for true automation.

**Design doc:** `docs/design/PLAYBOOKS.md`

---

### Stage 7 — Intent Detection 🔜

**What:** Automatic workflow selection from intent
**Where:** Intent Engine (separate repo)
**Value:** Zero configuration - just describe intent

System detects intent category, selects best workflow, extracts arguments automatically.

**Conceptual Example:**
```
User: "review my python code"
         ↓
System:
  🎯 Detected: code_review
  Selected: full_code_review playbook
  Est: $0.012, ~6s

  [Confirm & Run]
```

**Why this matters:** Prompts become UI only. Execution is deterministic under the hood.

**Design doc:** `docs/design/INTENT_ENGINE.md`

---

### Stage 8 — Intent Engine Runtime 🔜

**What:** Full policy-driven execution environment
**Where:** Intent Engine (separate repo)
**Value:** Autonomous, observable, cost-controlled

Complete runtime with:
- Policy engine (model selection, cost limits)
- Playbook executor (DAG runtime)
- Full observability (traces, costs, latency)
- Error handling and fallbacks

**Why this matters:** System operates autonomously within defined policies. Fully observable and auditable.

**Design doc:** `docs/design/INTENT_ENGINE.md`

---

### Stage 9 — Self-Improvement Loop 🌟

**What:** System learns from execution patterns
**Where:** Intent Engine (separate repo)
**Value:** Continuous optimization
**Status:** Long-term / conceptual only

System analyzes logs to suggest:
- Better model selections
- Optimized cache thresholds
- Cost reductions
- Failure pattern fixes

**Bounded by:** Human approval for major changes, simulation testing, rollback capability.

**Note:** This is a long-term vision, not committed scope for v1/v2.

**Design doc:** `docs/design/LEARNING_SYSTEM.md` (future)

---

## The Determinism Storyline

Each stage increases determinism:

| Stage | Determinism Level | Why |
|-------|------------------|-----|
| 1 | None | Free text, LLM interprets fresh each time |
| 2 | Low | Enhanced prompt is more consistent, but still text |
| 3 | Medium | Template reuse means similar inputs → similar outputs |
| 4 | Higher | Structured arguments reduce ambiguity |
| 5 | **High** | **Frozen = no reinterpretation, fully reproducible** |
| 6 | **Full** | **DAG execution, predictable flow** |
| 7-8 | **Complete** | **Prompts are UI, execution is deterministic** |

**Key Insight:** Stage 5 (Freeze) is the **first strong boundary** where prompts become artifacts. Stage 6 (Playbooks) makes execution fully deterministic.

---

## Prompt Studio: The Stable Facade

Throughout all stages, **Prompt Studio remains the user interface**:

- **Stage 1-2:** Looks like a playground with helpful enhancements
- **Stage 3-4:** Adds template suggestions and argument forms
- **Stage 5:** Adds freeze/materialize capability
- **Stage 6-8:** Becomes the frontend for Intent Engine

Users never see "Intent Engine" directly. They see gradual UX improvements in a familiar tool.

**The Trojan Horse Strategy:**
1. Users come for better prompts (Stage 2)
2. Stay for template convenience (Stage 3)
3. Discover structured inputs (Stage 4)
4. Adopt frozen artifacts for reproducibility (Stage 5)
5. Use complex workflows without realizing architecture changed (Stage 6-8)

The meta-prompt default ("Generate a prompt for building a modern React application") seeds this evolution by teaching prompt engineering as a skill.

---

## Implementation Roadmap

### Phase 1: Enhanced Prompting (v1.1)
**Timeline:** 2-4 weeks
**Scope:** Stages 1-2
**Repository:** llm-service-stack/

- [x] Stage 1: Current playground (done)
- [ ] Stage 2: Smart Prompt feature
  - "Enhance Prompt" button
  - Before/after comparison
  - Save enhanced prompts
  - Build dataset for templates

### Phase 2: Templates & Arguments (v1.2)
**Timeline:** 4-6 weeks
**Scope:** Stages 3-4
**Repository:** llm-service-stack/

- [ ] Stage 3: Template library
  - Semantic template matching
  - Template statistics (usage, cost, success)
  - Template sharing
- [ ] Stage 4: Argument extraction
  - Interactive argument forms
  - Validation
  - Auto-extraction from prompts

### Phase 3: Deterministic Artifacts (v1.3)
**Timeline:** 2-3 weeks
**Scope:** Stage 5
**Repository:** llm-service-stack/

- [ ] Stage 5: Freeze/materialize
  - Frozen request API
  - Artifact storage
  - Deterministic execution
  - Sharing and replay

### Phase 4: Intent Engine (v2.0)
**Timeline:** 8-12 weeks
**Scope:** Stages 6-8
**Repository:** intent-engine/ (new)

- [ ] Stage 6: Playbook runtime
- [ ] Stage 7: Intent detection
- [ ] Stage 8: Full policy engine

### Phase 5: Learning (v3.0+)
**Timeline:** TBD (long-term)
**Scope:** Stage 9
**Repository:** intent-engine/

- [ ] Conceptual design only
- [ ] Not committed for v1/v2

---

## Success Metrics

### Technical
- **Cost Reduction:** 40-60% through caching and optimization
- **Cache Hit Rate:** >50% for common patterns
- **Template Reuse:** >70% of requests match templates
- **Execution Success:** >95%

### User
- **Time to Value:** <30s from idea to result
- **Learning Curve:** <5min for new users
- **Satisfaction:** >4.5/5 rating

### Business
- **Cost per Request:** Decreasing over time (learning effect)
- **Request Volume:** Increasing (easier = more usage)

---

## Why This Works

1. **Gradual Evolution** - Each stage adds value independently
2. **Stable Facade** - Prompt Studio remains familiar
3. **Data Flywheel** - More usage → better templates → better suggestions
4. **Cost-Aware** - Optimization built in from Stage 1
5. **Observable** - Full visibility at every stage
6. **Deterministic** - Reproducible, auditable, trustworthy
7. **Modular** - LLM Stack and Intent Engine can evolve separately

---

## Related Documentation

- [LLM Service Stack Overview](LLM_SERVICE_STACK.md)
- [Evolution Stages](EVOLUTION.md)
- [Project Guide (CLAUDE.md)](../CLAUDE.md)
- [Troubleshooting](TROUBLESHOOTING.md)

## Design Documents

- [Smart Prompts Design](design/SMART_PROMPTS.md) - Stage 2
- [Templates Design](design/TEMPLATES.md) - Stages 3-4
- [Frozen Requests Design](design/FROZEN_REQUESTS.md) - Stage 5
- [Playbooks Design](design/PLAYBOOKS.md) - Stage 6
- [Intent Engine Design](design/INTENT_ENGINE.md) - Stages 7-8
