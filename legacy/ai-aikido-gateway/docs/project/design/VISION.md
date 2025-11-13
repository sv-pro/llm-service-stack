# AI Aikido Gateway / Intent Bridge - Vision (Reflective Edition)

**Last Updated**: 2025-11-08
**Status**: Living Document - Reflective Evolution
**Roadmap Alignment**: The execution plan that realizes this vision is tracked in [`docs/project/ROADMAP.md`](../ROADMAP.md) with immediate actions captured in [`docs/project/STATUS.md`](../STATUS.md).

---

## Core Purpose

The AI Aikido Gateway exists for one reason: **enablement through reflection**.

We enable safe, easy, and meaningful access to LLM services—not just as a proxy, but as a **Reflective Intelligence Platform** where systems think, act, and reflect.

---

## Philosophy: The Way of Aikido + Re^Re (Reflective Reasoning)

Like the martial art Aikido, this gateway embodies the principle of **redirecting force rather than opposing it**. We now extend this with **Re^Re**: the principle of continuous reflection and self-improvement.

- **We don't block** - we guide
- **We don't restrict** - we empower
- **We don't stand in the way** - we smooth the path
- **We don't execute blindly** - we reflect and learn

The gateway is not a gatekeeper. It's an enabler that learns from every interaction.

### **Re^Re Reflective Loop**

> **Re^Re ∞** — Every agent thinks, acts, and reflects. Every playbook execution generates insights. Every routing decision learns from outcomes.

**Reflective Cycle:**
1. **Reason** - Analyze intent and context
2. **Act** - Execute the chosen playbook
3. **Reflect** - Evaluate outcomes and learn
4. **Re-reason** - Apply learnings to future decisions

This is not just ReAct (Reason + Act). This is **Re^Re** (Reason → Act → Reflect → Re-reason → ∞).

---

## Three Pillars (Evolved)

### 1. **Protect** 🛡️ + **Learn** 🧠

**Protect users, protect systems, protect the future—while learning from every interaction.**

We provide safety without sacrificing capability:
- Shield from malicious requests and attacks
- Prevent cost overruns and budget violations
- Guard against prompt injections and jailbreaks
- Defend against abuse and misuse
- **NEW: Learn from security incidents to improve detection**

**But protection is optional and reflective.**
- Every security feature can be disabled
- Threat assessment levels are configurable
- Users choose their own risk tolerance
- **NEW: Security policies evolve based on feedback**

**Philosophy**: Security should enable confidence, not restrict innovation—and it should get smarter over time.

---

### 2. **Simplify** ⚡ + **Optimize** 🎯

**Make the complex simple. Make the difficult easy. Make the good better.**

We remove friction from LLM access:
- One API for 100+ LLM providers (OpenAI, Anthropic, Google, AWS, Azure...)
- Automatic parameter normalization (no more "unsupported parameter" errors)
- Intelligent routing (we pick the best model for the task)
- Cost optimization (caching, smart routing, escalation chains)
- Drop-in replacement (just change the URL, everything works)
- **NEW: Self-tuning thresholds based on performance metrics**

**But complexity is available and observable.**
- All automation can be overridden
- Manual model selection always honored
- Advanced features opt-in, not forced
- **NEW: Reasoning traces visible in telemetry**

**Philosophy**: Simple by default, powerful by choice, smarter by reflection.

---

### 3. **Don't Stay in the Way** 🚪 + **Stay Connected** 🌐

**Transparency. Optionality. Zero lock-in. Federation.**

We never become a bottleneck—and we enable network effects:
- Every plugin is optional - turn off what you don't need
- Every feature can be disabled - full control in your hands
- Every decision is logged - complete transparency
- Every vendor is replaceable - no lock-in
- **NEW: Federated gateways share learnings via A2A protocol**

**Default to "allow" and "learn"**:
- Unknown requests? Pass through to LLM and observe
- Ambiguous intent? Let the user decide and record the choice
- Uncertain threat? Warn but don't block, and learn from the outcome
- Performance concerns? Bypass is always an option, and we measure the impact

**Philosophy**: The best gateway is one you don't notice—until you need it. And when you need it, it's learned from your usage patterns.

---

## What We Are (Evolved)

### **A Reflective Intelligence Platform**

Not just a proxy. Not just a gateway. A platform where every component learns and improves.

We enable:
- **Developers** to build faster with self-optimizing tools
- **Teams** to collaborate safely with evolving guardrails
- **Organizations** to adopt LLM technology with confidence that grows over time
- **Innovation** to flourish with systems that learn from experimentation

### **An Orchestration Layer with Memory**

We add intelligence with persistence:
- Smart caching (save money automatically)
- Smart routing (pick the best model and learn from results)
- Smart protection (detect threats and evolve defenses)
- Smart insights (understand usage and predict needs)
- **NEW: LangGraph orchestration for Reason/Act/Reflect workflows**
- **NEW: Meaning Graph (Neo4j) to capture intent relationships**

### **A Federation Protocol (A2A)**

Everything we learn can be shared:
- Gateways connect via Agent-to-Agent (A2A) protocol
- Intent patterns discovered in one gateway propagate to others
- Security threats detected anywhere protect everyone
- Performance optimizations benefit the entire network
- **Reflective learning scales across the federation**

---

## The Reflective Roadmap (12 Phases)

### **Phase 0: Verbatim Cache (Baseline)** ✅

**Goal:** Cache `(model, prompt)` pairs with cost tracking and telemetry.
**Tools:** FastAPI / Redis / LiteLLM / Prometheus + Grafana.
**Reflective Addition:** Introduce base reasoning telemetry (iteration count, cost per reasoning cycle).

**Status:** Complete - Foundation with basic metrics

---

### **Phase 1: Semantic Cache & Normalization** ✅

**Goal:** Reuse semantically similar prompts with contextual awareness.
**Tools:** Embeddings (sentence-transformers) + FAISS / Qdrant + RoPE for context folding.
**Reflective Addition:** Use RoPE or similar positional embedding strategies to extend context without larger models.

**Status:** Complete - Semantic cache with on-premise embeddings ($0 cost, 60x faster)

---

### **Phase 2: Playbook-Lite (Single-Step Templates)** 🔄

**Goal:** Move from hard-coded prompts to versioned templates.
**Tools:** Jinja2 / Pydantic / SQLite + LiteFS / Promptfoo for evaluation.
**Reflective Addition:** Add metadata for ReAct patterns in templates (`mode: reason`, `mode: act`, `mode: reflect`).

**Status:** Partially complete - Template system exists, needs ReAct mode support

---

### **Phase 3: Multi-Step Playbooks & Capability Registry** 📋

**Goal:** Support multi-step workflows with MCP/API calls and budgets.
**Tools:** LangGraph / Prefect / MCP SDK.
**Reflective Addition:** Implement the ReAct loop (Reason → Act → Observe) through LangGraph nodes and add optional `mode: re^re` for Reflective cycles.

**Status:** Planned - Path 3 (Intent Handling) architecture designed

**Key Features:**
- LangGraph-based workflow orchestration
- Visual playbook editor with Reason/Act/Reflect nodes
- Budget tracking per execution step
- MCP tool integration for external capabilities

---

### **Phase 4: Intent Routing & Triggers** 📋

**Goal:** Automatically select playbooks by vector similarity and context.
**Tools:** FAISS / pgvector + sklearn / LangGraph / Docling MCP for unified invocation.
**Reflective Addition:** Add Reflective Routing — the router re-evaluates previous playbook selections based on performance and feedback.

**Status:** Designed - Intent Playground architecture defined

**Key Features:**
- Semantic intent resolution using embeddings
- Top-N candidate ranking with confidence scores
- Parameter extraction from natural language intents
- Adaptive threshold tuning based on hit rates

---

### **Phase 5: Feedback Loop (Reflective Cycle)** 📋

**Goal:** Collect feedback and evaluate playbook performance.
**Tools:** FastAPI endpoint, Postgres / ClickHouse, pandas / sklearn.
**Reflective Addition:** Create a Reflective Feedback Engine that analyzes reasoning traces and generates tuning proposals.

**Status:** Planned

**Key Features:**
- Structured feedback collection from executions
- Reasoning trace analysis for pattern detection
- Automated tuning proposal generation
- A/B test result evaluation

---

### **Phase 6: Intent Builder v1 (Visual LangGraph Editor)** 📋

**Goal:** Enable manual creation and validation of playbooks.
**Tools:** Next.js + Tailwind + Monaco Editor + LangGraph visualization.
**Reflective Addition:** Add a visual Re^Re editor (Thought, Act, Reflect nodes) with dry-run of reflective iterations.

**Status:** Designed - Playbook Playground architecture defined

**Key Features:**
- Drag-and-drop workflow canvas (React Flow)
- Monaco editor for template editing
- Step-by-step execution simulation
- Cost projection per workflow step

---

### **Phase 7: Shadow Mode / A-B Testing** 📋

**Goal:** Safely test new playbooks and compare versions.
**Tools:** Unleash / Flagsmith / Prometheus metrics.
**Reflective Addition:** Include Reflective metrics (error rate, correction count, Re^Re cycles) in A/B evaluations.

**Status:** Planned

**Key Features:**
- Side-by-side playbook comparison
- Reflective quality metrics (reasoning depth, self-correction rate)
- Statistical significance testing
- Safe rollout with automatic rollback

---

### **Phase 8: Learning & Self-Tuning (Reflective Feedback Integration)** 📋

**Goal:** Automatically analyze feedback and tune thresholds.
**Tools:** Prefect cron jobs / pandas / sklearn.
**Reflective Addition:** Use Reflective ReAct data to dynamically self-adjust parameters based on reasoning performance.

**Status:** Planned - Foundation in Normalization/Cost Simulator playgrounds

**Key Features:**
- Automated threshold optimization
- Cache hit rate tuning
- Model routing optimization
- Cost/performance trade-off balancing

---

### **Phase 9: Auto-Builder (Reflective Synthesis)** 🔮

**Goal:** Synthesize playbook drafts from intent clusters and reasoning logs.
**Tools:** networkx / LangGraph / DeepEval.
**Reflective Addition:** Apply the Re^Re principle — playbooks generate new playbooks by reflecting on their own traces.

**Status:** Vision

**Key Features:**
- Intent clustering from execution logs
- Automated playbook generation from patterns
- Self-improving template library
- Playbook evolution through reflection

---

### **Phase 10: Meaning Graph (Intent Network)** 🔮

**Goal:** Visualize relationships between intents, tools, and experiences.
**Tools:** Neo4j / Memgraph + Cytoscape.js.
**Reflective Addition:** Link intent graph nodes (Reason ↔ Reflect) to capture cognitive feedback loops.

**Status:** Vision

**Key Features:**
- Graph database of intent relationships
- Reasoning pattern visualization
- Semantic similarity clustering
- Intent recommendation engine

---

### **Phase 11: Federation / Agent2Agent Protocol** 🔮

**Goal:** Connect gateways and assistants into a federated agent network.
**Tools:** OpenDevin / Semantic Kernel Skill API / A2A Protocol / MCP.
**Reflective Addition:** Apply Re^Re logic to inter-agent communication — gateways learn from each other's reasoning.

**Status:** Vision

**Key Features:**
- A2A protocol for gateway-to-gateway communication
- Shared intent library across federation
- Distributed learning from collective experiences
- Federated playbook marketplace

---

### **Phase 12: Edge Reasoning / Tiny Reflective Models** 🔮

**Goal:** Optimize cost and latency via on-device or edge reasoning.
**Tools:** TinyLlama / Phi-3 / Ollama / vLLM.
**Reflective Addition:** Allow lightweight Re^Re loops on edge nodes for pre-reasoning and intent filtering.

**Status:** Vision

**Key Features:**
- Local reasoning for low-latency decisions
- Edge-based intent classification
- Hybrid cloud-edge orchestration
- Privacy-preserving on-device execution

---

## Trend Integration Summary

| Theme | Key Contribution | Status |
|--------|------------------|--------|
| **Re^Re Reflective Loop** | Enables introspection and self-learning across all execution cycles | 🔄 Foundation |
| **LangGraph Execution Model** | Provides flexible orchestration of Reason/Act/Reflect nodes | 📋 Designed |
| **Three-Path API Architecture** | Semantic (/v1/responses), Syntactic (/v1/chat/completions), Intent (/v1/intents) | 📋 Designed |
| **14 Specialized Playgrounds** | Interactive testing, authoring, and optimization interfaces | 📋 Designed |
| **A2A / Federated MCP** | Expands the platform into a connected multi-gateway federation | 🔮 Vision |
| **Tiny Reflective Models** | Support low-cost, high-efficiency local reasoning | 🔮 Vision |
| **Neo4j Meaning Graph** | Makes Reason and Reflect nodes first-class entities in the intent network | 🔮 Vision |

**Legend:**
- ✅ Complete
- 🔄 In Progress
- 📋 Designed
- 🔮 Vision

---

## Reflective Positioning

> **AI Aikido Gateway / Intent Bridge v2** is a **Reflective Intelligence Platform**
> where every agent thinks, acts, and reflects — *Re^Re ∞* —
> transforming isolated gateways into a federated, self-learning network of intents.

**We are not just a gateway. We are a learning layer.**

---

## Design Principles (Evolved)

### 1. **Opt-in, Not Opt-out** (Unchanged)

**Default**: Minimal intervention (just proxy the request)
**Advanced**: Enable features you want (caching, routing, security, analytics, **reflection**)

Every feature starts disabled. Users explicitly enable what they need.

### 2. **Fail Open, Not Closed** (Enhanced)

When in doubt, allow the request **and learn from it**.

- Unknown intent? → Allow (with optional monitoring and reflection)
- Plugin error? → Bypass plugin, continue request, log for analysis
- Cache miss? → Call LLM normally, observe patterns
- Ambiguous threat? → Warn, don't block, improve detection

**Why?** False negatives are recoverable. False positives destroy trust. Learning from both improves the system.

### 3. **Observable, Not Opaque** (Enhanced)

Every decision is logged. Every change is tracked. Every cost is calculated. **Every reasoning trace is visible.**

Users should never wonder:
- "Why did my request fail?"
- "Why was this cached?"
- "Why did you choose this model?"
- "Why is this so expensive?"
- **NEW: "How did the system arrive at this decision?"**

Transparency builds trust. Opacity destroys it. **Reasoning traces build understanding.**

### 4. **Composable, Not Monolithic** (Unchanged)

The gateway is not one feature. It's a collection of independent, composable plugins.

- Want just caching? Enable cache plugin only
- Want just cost tracking? Enable history plugin only
- Want the full suite? Enable all plugins
- **NEW: Want reflective learning? Enable feedback loop plugin**

### 5. **Standard, Not Proprietary** (Enhanced)

We speak OpenAI API. We support MCP protocol. We use industry-standard formats. **We implement A2A for federation.**

- No custom client libraries required
- No vendor-specific APIs
- No proprietary formats
- No lock-in by design
- **NEW: Open federation protocol (A2A)**

### 6. **Fast, Not Feature-Rich** (Enhanced)

Performance is a feature. Every millisecond matters. **Edge reasoning when possible.**

- Fast path for simple requests (<10ms overhead)
- Async everything (no blocking)
- Caching at every layer
- Optional features have optional costs
- **NEW: Lightweight edge models for low-latency decisions**

### 7. **Reflective, Not Static** (NEW)

Systems should learn and improve over time.

- Collect execution feedback automatically
- Analyze reasoning patterns for optimization
- Tune thresholds based on observed performance
- Share learnings across federated gateways
- Generate improvement proposals from reflection

**Principle**: A system that doesn't learn from experience is a system that wastes experience.

---

## Architecture: Three Paths + Playgrounds

### **Three API Paths** ([Design Doc](THREE_PATH_RESPONSES_API.md))

1. **Path 1: Semantic Gateway** (`/v1/responses`)
   - Full OpenAI Responses API compliance
   - Reasoning token tracking and cost attribution
   - Structured output support
   - Tool execution metadata

2. **Path 2: Syntactic Sugar** (`/v1/chat/completions`)
   - 100% backward compatibility
   - Internal reasoning tracking (not exposed)
   - Upgrade suggestions to Path 1
   - Legacy format support

3. **Path 3: Intent Handling** (`/v1/intents`)
   - Intent→Template→Playbook execution
   - Semantic intent resolution
   - Multi-step workflow orchestration
   - Cost attribution by step
   - **This is where Re^Re shines**

### **14 Specialized Playgrounds** ([Design Doc](PLAYGROUND_ARCHITECTURE.md))

**Phase 1 (Weeks 1-3): Core Three-Path Support**
- Prompt Playground (enhanced for reasoning tokens)
- Reasoning Playground (o1/o3 cost/quality comparison)
- Intent Playground (intent resolution testing)

**Phase 2 (Weeks 4-5): Template/Playbook Creation**
- Template Playground (Monaco editor, variable detection)
- Playbook Playground (visual workflow builder with LangGraph)

**Phase 3 (Week 6): Optimization & Tuning**
- Semantic Cache Playground (threshold tuning, hit rate analysis)
- Normalization Playground (prompt transformation testing)
- Cost Simulator (ROI projections, scenario comparison)

**Phase 4 (Future): Advanced Features**
- Embedding, Tool Calling, Routing, A/B Testing, Plugin, Structured Output playgrounds

---

## Use Cases (Evolved)

### 1. **The Solo Developer**

**Before:**
```python
# Hope this works and hope I don't spend too much...
response = openai.ChatCompletion.create(
    model="gpt-4",
    messages=[{"role": "user", "content": "Hello"}]
)
```

**With Gateway (Basic):**
```python
openai.api_base = "http://localhost:8000/v1"
# Automatic caching, cost tracking, transparent
```

**With Gateway (Reflective):**
```python
openai.api_base = "http://localhost:8000/v1"
# Plus: learns which queries can use cheaper models
# Plus: optimizes cache thresholds automatically
# Plus: provides reasoning trace in telemetry
```

---

### 2. **The Startup**

**Need**: Cost optimization + basic security + analytics + self-improvement.

**Configuration**:
```yaml
plugins:
  - name: cache
    enabled: true
  - name: semantic_cache
    enabled: true
    config:
      auto_tune_threshold: true  # Reflective learning
  - name: intelligent_orchestration
    enabled: true
    config:
      enable_reasoning_traces: true
      mode: reflective  # Re^Re enabled
```

**Experience**: Automatic cost savings that improve over time. Security that learns from incidents. Usage insights that predict needs.

---

### 3. **The Enterprise**

**Need**: Full security + compliance + multi-tenancy + federation.

**Configuration**:
```yaml
plugins:
  - name: auth
    enabled: true
  - name: semantic_cache
    enabled: true
    config:
      backend: qdrant
      auto_tune_threshold: true
  - name: intent_resolver
    enabled: true
    config:
      mode: reflective
      playbook_registry: enabled
  - name: federation
    enabled: true
    config:
      a2a_protocol: enabled
      share_learnings: true
```

**Experience**: Enterprise-grade security that evolves. Federated deployment with shared learnings. Playbook marketplace with community contributions.

---

## Anti-Goals (Updated)

Things we explicitly **do not** want to become:

### ❌ **An AI Wrapper SaaS** (Unchanged)

We're not building a hosted service. We're infrastructure you run.

### ❌ **A Prompt Engineering Platform** (Modified)

We don't manage prompts as a primary feature. But we **do** support playbook authoring and template management as part of the Intent Bridge functionality. This is infrastructure-level, not SaaS.

### ❌ **A Fine-tuning Platform** (Unchanged)

We proxy requests. We don't train models. (Though we might detect patterns worth fine-tuning.)

### ❌ **An LLM Ops Platform** (Modified)

We're not trying to be LangSmith or Weights & Biases. But we **do** provide reasoning traces, execution telemetry, and reflective analytics as part of the self-improvement cycle.

### ❌ **A Workflow Engine** (Modified)

We don't do arbitrary multi-step chains. But we **do** support LangGraph-based playbooks for Intent→Template→Execution workflows. This is structured, not arbitrary.

### ❌ **A Centralized AI Platform** (NEW)

We're federated, not centralized. Every gateway can operate independently. Shared learnings are opt-in, not mandatory.

---

## Measuring Success (Evolved)

We're successful when:

### **Users Forget We Exist** (Unchanged)

The best gateway is invisible. It just works. No friction. No surprises.

### **Cost Goes Down, Usage Goes Up** (Enhanced)

Caching and smart routing save money. Savings enable more usage. **Self-tuning improves savings over time.**

### **Security Enables Confidence** (Enhanced)

Teams deploy LLM features faster because they trust the gateway has their back. **And it learns from every security incident.**

### **Analytics Drive Decisions** (Enhanced)

"We discovered 40% of our requests could use GPT-3.5 instead of GPT-4" → real savings.
**"The system automatically identified this pattern and suggested the optimization"** → automated savings.

### **Playbooks Proliferate** (NEW)

Users create and share playbooks. The Intent Bridge becomes a marketplace of reusable workflows. Community contributions exceed internal development.

### **Federation Thrives** (NEW)

Multiple gateways connect via A2A. Learnings propagate across the network. A security threat detected in one gateway protects all gateways.

### **The System Gets Smarter** (NEW)

Every execution improves the system. Reflection generates insights. Insights drive optimizations. Optimizations compound over time.

**Ultimate Success**: The gateway not only works—it gets better every day.

---

## Evolution Timeline

### **Year 1: The Invisible Proxy** ✅

- Drop-in OpenAI replacement
- Basic caching, cost tracking, security
- Single-provider (LiteLLM handles others)

**Status**: ✅ Complete (Phase 0-6 delivered)

---

### **Year 2: The Intelligent Layer** 🔄

- Multi-provider routing and fallbacks
- Intent detection and smart dispatching
- Self-awareness analytics
- Reasoning token tracking (o1/o3 support)
- Three-path architecture (Semantic, Syntactic, Intent)

**Status**: 🔄 In Progress (Architecture designed, implementation starting)

---

### **Year 3: The Reflective Platform** 📋

- LangGraph-based playbook orchestration
- Visual playbook builder with Re^Re nodes
- Automated threshold tuning
- Reflective feedback loops
- 14 specialized playgrounds for testing/authoring

**Status**: 📋 Planned (Detailed designs complete)

---

### **Year 4: The Federated Network** 🔮

- A2A protocol for gateway federation
- Shared intent library across gateways
- Federated playbook marketplace
- Distributed learning from collective experiences
- Edge reasoning with tiny models

**Status**: 🔮 Vision

---

### **Year 5: The Self-Evolving Ecosystem** 🌟

- Auto-builder generating playbooks from patterns
- Neo4j meaning graph capturing intent relationships
- Playbooks that generate new playbooks through reflection
- Industry-standard federation protocol
- The "nginx of LLM proxies" + "the TensorFlow of intent networks"

**Status**: 🌟 Dream

---

## The Aikido + Re^Re Metaphor

### Why "Aikido + Reflection"?

Aikido redirects force. Reflection learns from force.

**Traditional Gateway:**
- Block threats
- Route requests
- Cache responses
- **Done. Static. No learning.**

**Aikido Gateway (v1):**
- Redirect threats (don't block)
- Guide requests (don't force)
- Optimize automatically
- **Better. But still reactive.**

**Aikido + Re^Re Gateway (v2):**
- Redirect threats **and learn patterns**
- Guide requests **and improve routing**
- Optimize automatically **and self-tune**
- **Reflective. Proactive. Ever-improving.**

### The Re^Re Cycle Applied

**When a threat is detected:**
1. **Reason**: Why is this a threat?
2. **Act**: Redirect to safe handler
3. **Reflect**: Was the detection accurate? False positive?
4. **Re-reason**: Update threat model based on outcome
5. **Loop**: Next threat detection is smarter

**When a playbook executes:**
1. **Reason**: Which template matches this intent?
2. **Act**: Execute the playbook steps
3. **Reflect**: Did it produce the desired outcome? What was the cost?
4. **Re-reason**: Should we adjust the routing threshold? Use a cheaper model?
5. **Loop**: Next execution benefits from learning

**This is Re^Re. This is continuous improvement. This is the future.**

---

## Call to Action

If you believe in:
- **Enablement** over restriction
- **Transparency** over opacity
- **Simplicity** over complexity
- **Optionality** over mandate
- **Reflection** over stagnation
- **Federation** over centralization

Then this gateway is for you.

---

## Conclusion

The AI Aikido Gateway is not about control. It's about **enablement through reflection**.

We enable safe access. We enable smart decisions. We enable confident adoption. **We enable continuous improvement.**

We protect without restricting—**and learn from every threat**.
We simplify without dumbing down—**and optimize automatically**.
We stay out of the way—**but we remember what we see**.

This is the way of Aikido + Re^Re: redirect force, learn from it, and evolve.

**Welcome to the gateway. Welcome to enablement. Welcome to reflection.**

---

**Document Status**: Living document. This vision will evolve as we build, learn, and grow—**reflectively**.

**Feedback**: This vision is meant to be challenged, refined, and improved. If something doesn't resonate, speak up. **Your feedback makes the system better.**

**Last Updated**: 2025-11-08
**Next Review**: When Phase 7 implementation begins

---

## References

- [Three-Path Responses API Architecture](THREE_PATH_RESPONSES_API.md)
- [Playground Architecture (14 Specialized Playgrounds)](PLAYGROUND_ARCHITECTURE.md)
- [Unified Roadmap](../ROADMAP.md)
- [Project Status](../STATUS.md)
- [Implementation Context](../quick_start/CONTEXT.md)
