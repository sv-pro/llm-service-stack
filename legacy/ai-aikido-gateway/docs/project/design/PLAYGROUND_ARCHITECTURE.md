# Gateway Playground Architecture

**Date:** 2025-11-08
**Status:** Design Phase
**Related:** [THREE_PATH_RESPONSES_API.md](THREE_PATH_RESPONSES_API.md)

---

## Executive Summary

The AI Aikido Gateway requires a comprehensive suite of **interactive playgrounds** to support the three-path architecture (Semantic, Syntactic, Intent) and enable users to test, tune, and understand gateway features before production deployment.

This document defines **14 specialized playgrounds** organized into 4 implementation phases, from core three-path support to advanced optimization and extensibility features.

---

## Motivation

### Current State
- Single Prompt Playground (basic testing only)
- Limited visibility into gateway internals
- No tooling for Path 3 (Intent/Template/Playbook)
- No optimization/tuning interfaces

### Desired State
- **Comprehensive testing environments** for all three paths
- **Visual debugging tools** for caching, routing, embeddings
- **Authoring interfaces** for intents, templates, playbooks
- **Optimization playgrounds** for cost, performance, accuracy tuning

### Value Proposition
Playgrounds transform the gateway from a "black box" proxy into a **transparent, tunable, and extensible platform** where users can:
- Understand how features work
- Test configurations safely
- Optimize for their specific use cases
- Build custom workflows (Path 3)

---

## Playground Inventory

### **Phase 1: Core Three-Path Support** (Weeks 1-3)

#### 1. Prompt Playground (Enhanced) 🎯
**Status:** Existing, needs Path 1 enhancements
**Purpose:** Test LLM requests with different configurations

**Current Features:**
- Send prompts to gateway
- View responses
- Basic model selection

**Enhancements Needed (Path 1 Support):**
- **Reasoning token display** in response
- Reasoning effort selector (low/medium/high)
- Reasoning type toggle (basic/advanced)
- Side-by-side cost comparison (with/without reasoning)
- Display `reasoning` content field from responses
- Tool execution metadata visualization (`output` fields)

**UI Components:**
```
┌─────────────────────────────────────────────────────────┐
│ Prompt Playground                        [Path 1 & 2]   │
├─────────────────────────────────────────────────────────┤
│ Model: [gpt-4 ▼]    Path: [Semantic (/v1/responses) ▼] │
│                                                         │
│ Reasoning: [✓] Enable    Effort: [○ Low ● Medium ○ High]│
│                                                         │
│ Prompt:                                                 │
│ ┌─────────────────────────────────────────────────┐   │
│ │ Explain quantum computing to a 10-year-old     │   │
│ │                                                 │   │
│ └─────────────────────────────────────────────────┘   │
│                                                         │
│ [Send Request]                                          │
│                                                         │
│ ─────────────────────────────────────────────────     │
│                                                         │
│ Response:                                               │
│ ┌─────────────────────────────────────────────────┐   │
│ │ Quantum computing uses quantum mechanics...     │   │
│ └─────────────────────────────────────────────────┘   │
│                                                         │
│ Reasoning (120 tokens, $0.0072):                       │
│ ┌─────────────────────────────────────────────────┐   │
│ │ First, I need to break down the concept into    │   │
│ │ simple analogies. Key points: superposition,    │   │
│ │ entanglement, qubits vs bits...                 │   │
│ └─────────────────────────────────────────────────┘   │
│                                                         │
│ Usage: Prompt: 15 | Completion: 42 | Reasoning: 120    │
│ Cost: $0.0089 (reasoning: $0.0072)                     │
│                                                         │
│ Cache: ✓ Semantic hit (similarity: 0.91, saved $0.0085)│
└─────────────────────────────────────────────────────────┘
```

**Implementation:**
- Enhance [dashboard/src/pages/Playground.jsx](../../dashboard/src/pages/Playground.jsx)
- Add reasoning controls to UI
- Parse and display reasoning tokens from response
- Add cost breakdown visualization

---

#### 2. Reasoning Playground (NEW) 🧠
**Status:** New, Path 1 differentiator
**Purpose:** Deep dive into reasoning model behavior and cost optimization

**Features:**
- **Model comparison:** Side-by-side o1-preview vs o1-mini vs gpt-4
- **Reasoning effort impact:** Show how effort affects quality and cost
- **Reasoning visualization:** Display thinking process step-by-step
- **Cost calculator:** Project costs for different reasoning configurations
- **Quality metrics:** Track answer accuracy, completeness, clarity
- **A/B testing:** Compare answers with/without reasoning

**UI Components:**
```
┌─────────────────────────────────────────────────────────┐
│ Reasoning Playground                         [Path 1]   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ Compare Reasoning Configurations:                       │
│                                                         │
│ ┌─────────────────────┬─────────────────────┐         │
│ │ Config A            │ Config B            │         │
│ │                     │                     │         │
│ │ Model: o1-preview   │ Model: gpt-4        │         │
│ │ Reasoning: High     │ Reasoning: None     │         │
│ │                     │                     │         │
│ │ Cost: $0.0145       │ Cost: $0.0018       │         │
│ │ Time: 3.2s          │ Time: 1.1s          │         │
│ │ Reasoning: 1500 tok │ Reasoning: N/A      │         │
│ │                     │                     │         │
│ │ Response:           │ Response:           │         │
│ │ [Detailed answer]   │ [Quick answer]      │         │
│ │                     │                     │         │
│ │ Quality: ⭐⭐⭐⭐⭐    │ Quality: ⭐⭐⭐       │         │
│ └─────────────────────┴─────────────────────┘         │
│                                                         │
│ Cost/Quality Tradeoff:                                  │
│ ┌─────────────────────────────────────────────────┐   │
│ │     Quality │                                   │   │
│ │     ⭐⭐⭐⭐⭐  │    ● Config A (o1-preview/high)  │   │
│ │     ⭐⭐⭐⭐    │                                   │   │
│ │     ⭐⭐⭐     │         ● Config B (gpt-4/none)  │   │
│ │     ⭐⭐      │                                   │   │
│ │     ⭐       │                                   │   │
│ │             └───────────────────────────────────│   │
│ │              $0.001   $0.005   $0.010   $0.015  │   │
│ │                        Cost per request         │   │
│ └─────────────────────────────────────────────────┘   │
│                                                         │
│ Recommendation: Use Config A for complex reasoning,    │
│                 Config B for simple factual queries    │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Implementation:**
- Create [dashboard/src/pages/ReasoningPlayground.jsx](../../dashboard/src/pages/ReasoningPlayground.jsx)
- Add side-by-side comparison UI
- Integrate with `/v1/responses` endpoint (Path 1)
- Build cost/quality visualization components
- Add quality rating interface

---

#### 3. Intent Playground (NEW) 🎯
**Status:** New, Path 3 core feature
**Purpose:** Test intent resolution and semantic matching

**Features:**
- **Intent input:** Natural language intent string
- **Resolution results:** Show matched templates with confidence scores
- **Top-N matches:** Display similarity scores for alternative matches
- **Parameter extraction:** Show extracted parameters from intent
- **Embedding visualization:** Show intent embedding vector
- **Template preview:** View matched template details
- **Execution link:** Quick link to execute in Playbook Playground

**UI Components:**
```
┌─────────────────────────────────────────────────────────┐
│ Intent Playground                            [Path 3]   │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ Intent Input:                                           │
│ ┌─────────────────────────────────────────────────┐   │
│ │ analyze security logs from last 24 hours        │   │
│ └─────────────────────────────────────────────────┘   │
│                                                         │
│ Parameters (Optional):                                  │
│ ┌─────────────────────────────────────────────────┐   │
│ │ {                                               │   │
│ │   "timeframe": "24h",                           │   │
│ │   "severity": "high"                            │   │
│ │ }                                               │   │
│ └─────────────────────────────────────────────────┘   │
│                                                         │
│ [Test Intent Resolution]                                │
│                                                         │
│ ─────────────────────────────────────────────────     │
│                                                         │
│ Resolution Results:                                     │
│ ┌─────────────────────────────────────────────────┐   │
│ │ ✓ Intent Resolved                               │   │
│ │                                                 │   │
│ │ Matched Template: SecurityLogAnalysis           │   │
│ │ Confidence: 0.92                                │   │
│ │ Embedding Similarity: 0.89                      │   │
│ │ Resolution Time: 12ms                           │   │
│ │                                                 │   │
│ │ Top 5 Matches:                                  │   │
│ │   1. SecurityLogAnalysis     (0.92) ✓ Selected │   │
│ │   2. AnomalyDetection        (0.73)            │   │
│ │   3. SystemHealthCheck       (0.68)            │   │
│ │   4. UserActivityReport      (0.45)            │   │
│ │   5. PerformanceMonitoring   (0.38)            │   │
│ │                                                 │   │
│ │ Extracted Parameters:                           │   │
│ │   • timeframe: "24h" (from intent text)        │   │
│ │   • severity: "high" (from parameters)         │   │
│ │   • log_source: "all" (default)                │   │
│ │                                                 │   │
│ │ [View Template] [Execute Playbook] [Debug]     │   │
│ └─────────────────────────────────────────────────┘   │
│                                                         │
│ Embedding Vector (384D):                                │
│ [0.12, -0.05, 0.31, ..., 0.08] [Copy] [Visualize]     │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Implementation:**
- Create [dashboard/src/pages/IntentPlayground.jsx](../../dashboard/src/pages/IntentPlayground.jsx)
- Add intent resolution API call to `/v1/intents/resolve` (new endpoint)
- Display similarity scores and rankings
- Add parameter extraction visualization
- Link to Template and Playbook playgrounds

---

### **Phase 2: Template/Playbook Creation** (Weeks 4-5)

#### 4. Template Playground (NEW) 📝
**Status:** New, Path 3 authoring
**Purpose:** Create, edit, and test prompt templates

**Features:**
- **Template editor:** Monaco editor with syntax highlighting
- **Variable slots:** Define and test template variables
- **Preview mode:** Render template with sample data
- **Version control:** Track template versions
- **Testing interface:** Test template with different inputs
- **Template library:** Browse existing templates
- **Validation:** Syntax checking and variable validation

**UI Components:**
```
┌─────────────────────────────────────────────────────────┐
│ Template Playground                          [Path 3]   │
├─────────────────────────────────────────────────────────┤
│ Template Name: [SecurityLogAnalysis_________]           │
│ Intent: [SecurityLogAnalysis ▼]                         │
│                                                         │
│ Template Editor:                                        │
│ ┌─────────────────────────────────────────────────┐   │
│ │ 1  You are a security analyst. Analyze the      │   │
│ │ 2  following logs and identify any security     │   │
│ │ 3  threats or anomalies.                        │   │
│ │ 4                                               │   │
│ │ 5  Timeframe: {{timeframe}}                     │   │
│ │ 6  Severity Filter: {{severity}}                │   │
│ │ 7  Log Source: {{log_source}}                   │   │
│ │ 8                                               │   │
│ │ 9  Logs:                                        │   │
│ │ 10 {{logs}}                                     │   │
│ │ 11                                              │   │
│ │ 12 Provide:                                     │   │
│ │ 13 1. Summary of critical events                │   │
│ │ 14 2. Detailed analysis of each threat          │   │
│ │ 15 3. Recommended actions                       │   │
│ └─────────────────────────────────────────────────┘   │
│                                                         │
│ Variables Detected: timeframe, severity, log_source,    │
│                     logs                                │
│                                                         │
│ Test Data:                                              │
│ ┌─────────────────────────────────────────────────┐   │
│ │ timeframe: "24h"                                │   │
│ │ severity: "high"                                │   │
│ │ log_source: "all"                               │   │
│ │ logs: [sample log data...]                      │   │
│ └─────────────────────────────────────────────────┘   │
│                                                         │
│ [Preview] [Test with LLM] [Save Template] [Version]    │
│                                                         │
│ Preview:                                                │
│ ┌─────────────────────────────────────────────────┐   │
│ │ You are a security analyst. Analyze the         │   │
│ │ following logs and identify any security        │   │
│ │ threats or anomalies.                           │   │
│ │                                                 │   │
│ │ Timeframe: 24h                                  │   │
│ │ Severity Filter: high                           │   │
│ │ ...                                             │   │
│ └─────────────────────────────────────────────────┘   │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Implementation:**
- Create [dashboard/src/pages/TemplatePlayground.jsx](../../dashboard/src/pages/TemplatePlayground.jsx)
- Integrate Monaco editor for template editing
- Add variable detection and highlighting
- Build template preview renderer
- Add template CRUD API endpoints

---

#### 5. Playbook Playground (NEW) 🔧
**Status:** New, Path 3 orchestration
**Purpose:** Design and test multi-step workflow execution

**Features:**
- **Visual workflow builder:** Drag-and-drop playbook designer
- **Step editor:** Configure each playbook step
- **Execution simulation:** Run playbook with test data
- **Step-by-step trace:** View execution log for each step
- **Variable flow:** Track how variables flow between steps
- **Error handling:** Define and test error recovery
- **Cost tracking:** See cost breakdown by step

**UI Components:**
```
┌─────────────────────────────────────────────────────────┐
│ Playbook Playground                          [Path 3]   │
├─────────────────────────────────────────────────────────┤
│ Playbook: [SecurityLogAnalysis__________] [Save] [Run]  │
│                                                         │
│ Workflow Designer:                                      │
│ ┌─────────────────────────────────────────────────┐   │
│ │                                                 │   │
│ │  [Start]                                        │   │
│ │     │                                           │   │
│ │     ▼                                           │   │
│ │  ┌──────────────┐                              │   │
│ │  │ 1. Fetch Logs│                              │   │
│ │  └──────┬───────┘                              │   │
│ │         │                                       │   │
│ │         ▼                                       │   │
│ │  ┌──────────────┐                              │   │
│ │  │2. Filter High│                              │   │
│ │  │   Severity   │                              │   │
│ │  └──────┬───────┘                              │   │
│ │         │                                       │   │
│ │         ▼                                       │   │
│ │  ┌──────────────┐                              │   │
│ │  │3. LLM Analyze│ ← [Edit Step]                │   │
│ │  └──────┬───────┘                              │   │
│ │         │                                       │   │
│ │         ▼                                       │   │
│ │  ┌──────────────┐                              │   │
│ │  │4. Generate   │                              │   │
│ │  │ Recommendations                              │   │
│ │  └──────┬───────┘                              │   │
│ │         │                                       │   │
│ │         ▼                                       │   │
│ │     [End]                                       │   │
│ │                                                 │   │
│ └─────────────────────────────────────────────────┘   │
│                                                         │
│ Step 3: LLM Analyze (Selected)                         │
│ ┌─────────────────────────────────────────────────┐   │
│ │ Type: LLM Call                                  │   │
│ │ Template: SecurityLogAnalysis                   │   │
│ │ Model: gpt-4                                    │   │
│ │ Input Variables: filtered_logs                  │   │
│ │ Output Variable: analysis_result                │   │
│ │ Error Handling: Retry 3x, fallback to gpt-3.5  │   │
│ │ Estimated Cost: $0.0045                         │   │
│ └─────────────────────────────────────────────────┘   │
│                                                         │
│ [Add Step] [Delete Step] [Test Execution]              │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Execution Results View:**
```
┌─────────────────────────────────────────────────────────┐
│ Execution Trace: SecurityLogAnalysis                    │
├─────────────────────────────────────────────────────────┤
│ Status: ✓ Completed | Duration: 2.4s | Cost: $0.0089   │
│                                                         │
│ Step-by-Step Results:                                   │
│                                                         │
│ ✓ 1. Fetch Logs                   120ms   $0.0000      │
│   Retrieved 1,234 log entries                           │
│                                                         │
│ ✓ 2. Filter High Severity          50ms   $0.0000      │
│   Filtered to 23 high-severity events                   │
│                                                         │
│ ✓ 3. LLM Analyze                 1800ms   $0.0045      │
│   [Cache Miss] Generated analysis                       │
│   Output: "Found 3 critical security events..."         │
│                                                         │
│ ✓ 4. Generate Recommendations     300ms   $0.0044      │
│   [Cache Hit - similarity: 0.88] Saved $0.0041          │
│   Output: 5 recommendations generated                   │
│                                                         │
│ Total: 4 steps, 2 LLM calls, 1 cache hit               │
│                                                         │
│ [View Full Output] [Save Results] [Debug Variables]    │
└─────────────────────────────────────────────────────────┘
```

**Implementation:**
- Create [dashboard/src/pages/PlaybookPlayground.jsx](../../dashboard/src/pages/PlaybookPlayground.jsx)
- Build visual workflow editor (React Flow or similar)
- Add step configuration UI
- Implement playbook execution API
- Build execution trace viewer

---

### **Phase 3: Optimization & Tuning** (Week 6)

#### 6. Semantic Cache Playground (NEW) 💾
**Status:** New, cross-path optimization
**Purpose:** Test and tune semantic cache behavior

**Features:**
- **Similarity testing:** Compare prompt similarity scores
- **Threshold tuning:** Adjust threshold and see hit rate impact
- **False positive detection:** Identify incorrect matches
- **Cache visualization:** See cached prompts in embedding space
- **Hit rate analysis:** Historical hit rate by threshold
- **Cost impact calculator:** Show savings from different thresholds

**UI Components:**
```
┌─────────────────────────────────────────────────────────┐
│ Semantic Cache Playground                   [All Paths] │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ Test Prompt Similarity:                                 │
│                                                         │
│ Prompt A:                                               │
│ ┌─────────────────────────────────────────────────┐   │
│ │ What is the capital of France?                  │   │
│ └─────────────────────────────────────────────────┘   │
│                                                         │
│ Prompt B:                                               │
│ ┌─────────────────────────────────────────────────┐   │
│ │ Tell me the capital city of France              │   │
│ └─────────────────────────────────────────────────┘   │
│                                                         │
│ [Calculate Similarity]                                  │
│                                                         │
│ Results:                                                │
│ ┌─────────────────────────────────────────────────┐   │
│ │ Cosine Similarity: 0.94                         │   │
│ │                                                 │   │
│ │ Current Threshold: 0.85 ✓ Would cache hit      │   │
│ │                                                 │   │
│ │ Test Other Thresholds:                          │   │
│ │   0.80: ✓ Hit                                   │   │
│ │   0.85: ✓ Hit (current)                         │   │
│ │   0.90: ✓ Hit                                   │   │
│ │   0.95: ✗ Miss                                  │   │
│ └─────────────────────────────────────────────────┘   │
│                                                         │
│ Threshold Impact Analysis:                              │
│ ┌─────────────────────────────────────────────────┐   │
│ │ Threshold │ Hit Rate │ False Positives │ Savings│   │
│ │─────────────────────────────────────────────────│   │
│ │   0.80    │   72%    │      3%         │  $45.2 │   │
│ │   0.85 ✓  │   68%    │      1%         │  $42.8 │   │
│ │   0.90    │   54%    │      0%         │  $34.1 │   │
│ │   0.95    │   38%    │      0%         │  $24.0 │   │
│ └─────────────────────────────────────────────────┘   │
│                                                         │
│ Recommendation: Keep 0.85 (good balance)                │
│                                                         │
│ [Update Threshold] [Run Benchmark] [View Cache]        │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Implementation:**
- Create [dashboard/src/pages/SemanticCachePlayground.jsx](../../dashboard/src/pages/SemanticCachePlayground.jsx)
- Add similarity calculation API endpoint
- Build threshold impact analyzer
- Integrate with existing cache stats API
- Add cache visualization (embedding space plot)

---

#### 7. Normalization Playground (NEW) 🔧
**Status:** New, cache optimization
**Purpose:** Test prompt normalization pipeline

**Features:**
- **Raw vs normalized:** See transformation in real-time
- **Rule toggles:** Enable/disable individual rules
- **Step-by-step view:** Watch each normalization step
- **Custom rules:** Add and test custom normalization rules
- **Hit rate impact:** See how normalization affects caching
- **Rule library:** Browse built-in normalization rules

**UI Components:**
```
┌─────────────────────────────────────────────────────────┐
│ Normalization Playground                    [All Paths] │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ Input Prompt:                                           │
│ ┌─────────────────────────────────────────────────┐   │
│ │  What's the capital of   France?  Tell me pls!  │   │
│ └─────────────────────────────────────────────────┘   │
│                                                         │
│ Normalization Rules:                                    │
│ [✓] Strip extra whitespace                              │
│ [✓] Lowercase                                           │
│ [✓] Remove punctuation                                  │
│ [✓] Expand acronyms                                     │
│ [✓] Remove filler words (pls, tell me, etc.)           │
│ [ ] Custom rule: [Add Custom Rule]                     │
│                                                         │
│ [Apply Normalization]                                   │
│                                                         │
│ Transformation Steps:                                   │
│ ┌─────────────────────────────────────────────────┐   │
│ │ Original:                                       │   │
│ │   "What's the capital of   France?  Tell me pls!"│   │
│ │                                                 │   │
│ │ Step 1: Strip whitespace                        │   │
│ │   "What's the capital of France? Tell me pls!"  │   │
│ │                                                 │   │
│ │ Step 2: Lowercase                               │   │
│ │   "what's the capital of france? tell me pls!"  │   │
│ │                                                 │   │
│ │ Step 3: Remove punctuation                      │   │
│ │   "whats the capital of france tell me pls"     │   │
│ │                                                 │   │
│ │ Step 4: Expand acronyms                         │   │
│ │   "whats the capital of france tell me pls"     │   │
│ │   (no changes)                                  │   │
│ │                                                 │   │
│ │ Step 5: Remove filler words                     │   │
│ │   "whats capital france"                        │   │
│ │                                                 │   │
│ │ Final Normalized:                               │   │
│ │   "whats capital france"                        │   │
│ └─────────────────────────────────────────────────┘   │
│                                                         │
│ Cache Lookup Test:                                      │
│ Similar cached prompts:                                 │
│   • "What is the capital of France?" (similarity: 0.96) │
│   • "France capital city?" (similarity: 0.89)           │
│                                                         │
│ ✓ Would hit cache with current configuration           │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Implementation:**
- Create [dashboard/src/pages/NormalizationPlayground.jsx](../../dashboard/src/pages/NormalizationPlayground.jsx)
- Add normalization step-by-step API endpoint
- Build rule toggle UI
- Add custom rule editor
- Show cache impact analysis

---

#### 8. Cost Simulator (NEW) 💰
**Status:** New, business value
**Purpose:** Project costs for different configurations

**Features:**
- **Traffic pattern input:** Define expected request volumes
- **Configuration comparison:** Compare different setups
- **Path cost breakdown:** See costs per path (1, 2, 3)
- **Cache impact modeling:** Estimate savings from caching
- **Reasoning cost projection:** o1/o3 model cost forecasting
- **ROI calculator:** Show gateway savings vs direct API use
- **Export reports:** Generate cost reports for stakeholders

**UI Components:**
```
┌─────────────────────────────────────────────────────────┐
│ Cost Simulator                              [All Paths] │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ Traffic Pattern:                                        │
│ ┌─────────────────────────────────────────────────┐   │
│ │ Daily Requests: [10,000________]                │   │
│ │                                                 │   │
│ │ Path Distribution:                              │   │
│ │   Path 1 (Responses):    20% [====░░░░░░░░░░]  │   │
│ │   Path 2 (Chat):         70% [==============░░] │   │
│ │   Path 3 (Intents):      10% [==░░░░░░░░░░░░]  │   │
│ │                                                 │   │
│ │ Model Distribution:                             │   │
│ │   GPT-4:                 60% [============░░░░] │   │
│ │   GPT-3.5:               30% [======░░░░░░░░░░] │   │
│ │   o1-preview:            10% [==░░░░░░░░░░░░░░] │   │
│ │                                                 │   │
│ │ Avg Tokens per Request:  500                    │   │
│ └─────────────────────────────────────────────────┘   │
│                                                         │
│ Cache Configuration:                                    │
│ [✓] Verbatim cache (estimated hit rate: 15%)           │
│ [✓] Semantic cache (estimated hit rate: 50%)           │
│                                                         │
│ [Calculate Costs]                                       │
│                                                         │
│ ─────────────────────────────────────────────────     │
│                                                         │
│ Monthly Cost Projection:                                │
│                                                         │
│ ┌─────────────────────────────────────────────────┐   │
│ │ Scenario              │ Cost/Month │ Savings    │   │
│ │───────────────────────────────────────────────│   │
│ │ Direct OpenAI API     │  $4,500    │  —         │   │
│ │ Gateway (no cache)    │  $4,500    │  $0        │   │
│ │ Gateway (verbatim)    │  $3,825    │  $675      │   │
│ │ Gateway (semantic)    │  $2,475    │  $2,025    │   │
│ │ Gateway (both caches) │  $2,025    │  $2,475    │   │
│ └─────────────────────────────────────────────────┘   │
│                                                         │
│ Cost Breakdown (Gateway with both caches):              │
│ ┌─────────────────────────────────────────────────┐   │
│ │ LLM Calls:              $1,950 (43% of baseline)│   │
│ │ Embeddings (on-prem):       $0 ($0 cost!)       │   │
│ │ Infrastructure:           $75 (Docker services) │   │
│ │ Total:                 $2,025                   │   │
│ │                                                 │   │
│ │ ROI: 55% cost reduction                         │   │
│ └─────────────────────────────────────────────────┘   │
│                                                         │
│ Reasoning Model Impact (o1-preview):                    │
│ Without reasoning tracking: $450/month hidden cost      │
│ With Path 1 (full tracking): $450/month visible         │
│ Optimization potential: Switch 50% to gpt-4 = -$225     │
│                                                         │
│ [Export Report] [Share Link] [Save Scenario]           │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

**Implementation:**
- Create [dashboard/src/pages/CostSimulator.jsx](../../dashboard/src/pages/CostSimulator.jsx)
- Build cost calculation engine
- Add traffic pattern input forms
- Create cost comparison visualizations
- Add report export functionality

---

### **Phase 4: Advanced Features** (Future)

#### 9. Embedding Playground (Power Users) 🧬
**Purpose:** Visualize and compare embeddings
**Features:** Vector visualization, similarity heatmaps, model comparison

#### 10. Tool/Function Calling Playground 🔨
**Purpose:** Test function calling workflows
**Features:** Define functions, test calls, multi-turn conversations

#### 11. Routing Playground 🚦
**Purpose:** Test dispatcher routing logic
**Features:** Routing rules editor, provider comparison, load testing

#### 12. A/B Testing Playground 🧪
**Purpose:** Compare configurations side-by-side
**Features:** Split-screen comparison, statistical analysis, winner selection

#### 13. Plugin Playground 🔌
**Purpose:** Test custom plugins in isolation
**Features:** Plugin upload, lifecycle testing, performance profiling

#### 14. Structured Output Playground 📋
**Purpose:** Test JSON schema validation
**Features:** Schema editor, validation testing, format conversion

---

## Dashboard Navigation Structure

```
AI Aikido Gateway
├─ 📊 Overview (home)
│
├─ 🎮 Playgrounds ▼
│  ├─ Prompt (Path 1 & 2)              [Enhanced]
│  ├─ Reasoning (Path 1)               [Phase 1] 🆕
│  ├─ Intent (Path 3)                  [Phase 1] 🆕
│  ├─ Template (Path 3)                [Phase 2] 🆕
│  ├─ Playbook (Path 3)                [Phase 2] 🆕
│  ├─ Semantic Cache                   [Phase 3] 🆕
│  ├─ Normalization                    [Phase 3] 🆕
│  ├─ Cost Simulator                   [Phase 3] 🆕
│  ├─ Embeddings                       [Phase 4] 🆕
│  ├─ Tools/Functions                  [Phase 4] 🆕
│  ├─ Routing                          [Phase 4] 🆕
│  ├─ A/B Testing                      [Phase 4] 🆕
│  ├─ Plugins                          [Phase 4] 🆕
│  └─ Structured Outputs               [Phase 4] 🆕
│
├─ 📈 Analytics ▼
│  ├─ Request History (existing)
│  ├─ Cache Analytics (existing)
│  ├─ Cost Dashboard                   [New]
│  ├─ Performance Metrics              [New]
│  └─ Intent Analytics                 [New]
│
├─ ⚙️  Configuration ▼
│  ├─ Plugins
│  ├─ Models
│  ├─ Intents                          [New]
│  ├─ Templates                        [New]
│  └─ Playbooks                        [New]
│
└─ 🔧 Settings
```

---

## Implementation Roadmap

### **Phase 1: Core Three-Path Support** (Weeks 1-3)
**Goal:** Enable testing and validation for all three paths

**Deliverables:**
1. **Prompt Playground Enhancement** (Week 1)
   - Add reasoning token display
   - Add reasoning controls (effort, type)
   - Add cost breakdown with reasoning
   - **Estimate:** 3 days

2. **Reasoning Playground** (Week 1-2)
   - Build side-by-side comparison UI
   - Integrate with `/v1/responses` endpoint
   - Add cost/quality visualization
   - **Estimate:** 5 days

3. **Intent Playground** (Week 2-3)
   - Create intent resolution UI
   - Build top-N matches display
   - Add parameter extraction visualization
   - Link to template/playbook playgrounds
   - **Estimate:** 5 days

**Success Criteria:**
- Users can test reasoning models and see cost impact
- Intent resolution works with visual feedback
- All three paths have testing interfaces

---

### **Phase 2: Template/Playbook Creation** (Weeks 4-5)
**Goal:** Enable Path 3 workflow authoring

**Deliverables:**
1. **Template Playground** (Week 4)
   - Monaco editor integration
   - Variable detection and preview
   - Template CRUD operations
   - **Estimate:** 5 days

2. **Playbook Playground** (Week 5)
   - Visual workflow builder
   - Step configuration UI
   - Execution trace viewer
   - Cost tracking by step
   - **Estimate:** 7 days

**Success Criteria:**
- Users can create and test templates
- Playbooks can be designed and executed visually
- Execution traces provide debugging insight

---

### **Phase 3: Optimization & Tuning** (Week 6)
**Goal:** Enable cache and cost optimization

**Deliverables:**
1. **Semantic Cache Playground** (Week 6, days 1-2)
   - Similarity testing UI
   - Threshold impact analyzer
   - Cache visualization
   - **Estimate:** 2 days

2. **Normalization Playground** (Week 6, days 3-4)
   - Step-by-step transformation view
   - Rule toggle UI
   - Cache impact testing
   - **Estimate:** 2 days

3. **Cost Simulator** (Week 6, days 5-7)
   - Traffic pattern input
   - Cost calculation engine
   - Scenario comparison
   - **Estimate:** 3 days

**Success Criteria:**
- Users can tune cache for their workload
- Cost projections help justify gateway ROI
- Normalization rules improve hit rates

---

### **Phase 4: Advanced Features** (Future)
**Goal:** Power user features and extensibility

**Deliverables:**
- Embedding Playground (visualization)
- Tool/Function Calling Playground (complex workflows)
- Routing Playground (dispatcher tuning)
- A/B Testing Playground (experimentation)
- Plugin Playground (custom extensions)
- Structured Output Playground (schema validation)

**Timeline:** To be determined based on user demand

---

## Technical Architecture

### **Frontend Structure**
```
dashboard/src/
├─ pages/
│  ├─ Playground.jsx (existing, enhance)
│  ├─ ReasoningPlayground.jsx (new)
│  ├─ IntentPlayground.jsx (new)
│  ├─ TemplatePlayground.jsx (new)
│  ├─ PlaybookPlayground.jsx (new)
│  ├─ SemanticCachePlayground.jsx (new)
│  ├─ NormalizationPlayground.jsx (new)
│  └─ CostSimulator.jsx (new)
│
├─ components/
│  ├─ playgrounds/
│  │  ├─ ReasoningComparison.jsx
│  │  ├─ IntentResolver.jsx
│  │  ├─ TemplateEditor.jsx (Monaco integration)
│  │  ├─ PlaybookBuilder.jsx (React Flow integration)
│  │  ├─ SimilarityTester.jsx
│  │  └─ CostProjection.jsx
│  │
│  └─ shared/
│     ├─ CodeEditor.jsx (Monaco wrapper)
│     ├─ JsonEditor.jsx
│     └─ WorkflowCanvas.jsx
│
└─ api/
   └─ playgrounds.js (API client for playground endpoints)
```

### **Backend API Endpoints**

```python
# Path 1: Reasoning
POST   /v1/responses                    # Full OpenAI Responses API
GET    /v1/responses/models             # List reasoning models
GET    /v1/responses/cost-estimate      # Estimate reasoning costs

# Path 3: Intent Resolution
POST   /v1/intents                      # Execute intent
POST   /v1/intents/resolve              # Resolve intent to template
GET    /v1/intents                      # List all intents
POST   /v1/intents/{id}/test            # Test intent with sample data

# Path 3: Templates
GET    /v1/templates                    # List templates
POST   /v1/templates                    # Create template
GET    /v1/templates/{id}               # Get template
PUT    /v1/templates/{id}               # Update template
DELETE /v1/templates/{id}               # Delete template
POST   /v1/templates/{id}/preview       # Preview with data
POST   /v1/templates/{id}/test          # Test with LLM

# Path 3: Playbooks
GET    /v1/playbooks                    # List playbooks
POST   /v1/playbooks                    # Create playbook
GET    /v1/playbooks/{id}               # Get playbook
PUT    /v1/playbooks/{id}               # Update playbook
DELETE /v1/playbooks/{id}               # Delete playbook
POST   /v1/playbooks/{id}/execute       # Execute playbook
GET    /v1/playbooks/{id}/executions    # List executions
GET    /v1/playbooks/executions/{exec_id}/trace  # Get execution trace

# Optimization: Semantic Cache
POST   /v1/cache/semantic/similarity    # Calculate prompt similarity
POST   /v1/cache/semantic/test-threshold # Test threshold impact
GET    /v1/cache/semantic/visualization # Get cache visualization data

# Optimization: Normalization
POST   /v1/normalization/test           # Test normalization pipeline
GET    /v1/normalization/rules          # List normalization rules
POST   /v1/normalization/rules          # Add custom rule
DELETE /v1/normalization/rules/{id}     # Delete rule

# Optimization: Cost
POST   /v1/cost/simulate                # Simulate costs
GET    /v1/cost/report                  # Generate cost report
```

---

## Success Metrics

### **Phase 1 Success Metrics:**
- [ ] Users can test reasoning models and see token breakdown
- [ ] Intent resolution accuracy >85%
- [ ] All three paths have functional testing playgrounds

### **Phase 2 Success Metrics:**
- [ ] 10+ templates created in Template Playground
- [ ] 5+ playbooks designed and tested
- [ ] Template library with common use cases

### **Phase 3 Success Metrics:**
- [ ] Users optimize cache threshold using Semantic Cache Playground
- [ ] Cost Simulator shows clear ROI (>30% savings)
- [ ] Normalization rules improve hit rate by >10%

### **Phase 4 Success Metrics:**
- [ ] Power users adopt advanced playgrounds
- [ ] Custom plugins tested in Plugin Playground
- [ ] A/B testing drives configuration improvements

---

## Open Questions

1. **Monaco Editor Licensing:** Confirm MIT license compatible with project
2. **React Flow vs Custom:** Use React Flow for playbook builder or build custom?
3. **Embedding Visualization:** Use t-SNE, PCA, or UMAP for 2D projection?
4. **Real-time Updates:** WebSocket for live playground execution updates?
5. **Shared Playgrounds:** Enable sharing playground configurations between users?
6. **Template Marketplace:** Should there be a public template/playbook marketplace?

---

## Related Documents

- [THREE_PATH_RESPONSES_API.md](THREE_PATH_RESPONSES_API.md) - Three-path architecture design
- [PHASE_7_INTENT_MODELS.md](PHASE_7_INTENT_MODELS.md) - Intent/Template/Playbook data models (to be created)
- [BENCHMARK_RESULTS.md](../implementation/BENCHMARK_RESULTS.md) - Performance benchmarks
- [STATUS.md](../STATUS.md) - Project status

---

**END OF DOCUMENT**
