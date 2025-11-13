# Architecture Vision: Intent-Based + Meta-Cognitive System

## Overview

This document describes the strategic evolution of the LLM Service Stack from a naive prompt-based system to a fully structured, intent-driven architecture with meta-cognitive capabilities.

**Core Principle:** Use **Prompt Studio** as the Trojan Horse - a user-facing experimental ground that gradually introduces structure, determinism, and observability while maintaining an intuitive interface.

---

## From Prompts to Intents — Evolution Path

This progression moves from unstructured text to deterministic execution, adding structure and observability at each stage.

### Stage 1 — Naive Prompt ✅ **(Current State)**

**Description:** Raw, unstructured user prompts.

**Characteristics:**
- Free-form text input
- No metadata or structure
- No arguments or parameters beyond model settings
- Every request is unique and expensive
- Results not reproducible
- No reuse or learning

**Current Implementation:**
- Prompt Studio accepts system + user message
- Direct pass-through to LLM
- Manual parameter configuration (temperature, max_tokens)
- Basic caching (semantic matching provides primitive template matching)

**What works:**
- Simple, intuitive for users
- No learning curve
- Immediate results

**Limitations:**
- No reuse of patterns
- High costs (every similar request hits API)
- No observability of intent
- Cannot optimize or improve over time

---

### Stage 2 — Smart Prompt (LLM-Generated Template)

**Description:** System generates refined prompts from naive ones.

**Characteristics:**
- LLM rewrites user request into clearer, safer, more complete prompt
- Still text-based, but more deterministic
- Closer to instruction blocks
- Similar to Anthropic's "metaprompt" or "Generate Prompt" feature

**Value Proposition:**
- Improves prompt quality automatically
- Teaches users better prompting through examples
- Creates a facade for later intent extraction
- Builds foundation for template library

**Implementation Plan:**

```typescript
// Prompt Studio: New "Smart Prompt" feature
interface SmartPrompt {
  original: string;           // User's naive prompt
  enhanced: string;           // LLM-generated improvement
  reasoning: string;          // Why it was improved
  suggestions: string[];      // Additional improvements
  metadata: {
    intent_category?: string; // Detected intent (seed for Stage 7)
    task_type?: string;       // Classification: creative, analytical, code, etc.
    clarity_score?: number;   // 0-1 score of prompt clarity
  };
}
```

**Gateway Endpoint:**
```python
@app.post("/v1/prompts/enhance")
async def enhance_prompt(request: EnhancePromptRequest):
    """
    Use a reasoning model (GPT-4, Claude, o1) to improve a naive prompt.
    Returns enhanced version with metadata.
    """
    # Use metaprompt to analyze and improve
    # Extract intent signals
    # Store in prompt library for Stage 3
```

**Prompt Studio UI:**
```
┌─────────────────────────────────┐
│ Original Prompt                 │
│ [User's text]                   │
│                                 │
│ [✨ Generate Smart Prompt]      │
└─────────────────────────────────┘
         ↓
┌─────────────────────────────────┐
│ Smart Prompt                    │
│ [Enhanced version]              │
│                                 │
│ Improvements:                   │
│ • Added context about...        │
│ • Clarified expected format...  │
│ • Specified constraints...      │
│                                 │
│ [Use This] [Edit] [Save as     │
│                    Template]    │
└─────────────────────────────────┘
```

**Benefits:**
- Immediate user value (better results)
- Collects data for template building (Stage 3)
- Introduces concept of structured prompts
- Foundation for intent detection (Stage 7)

---

### Stage 3 — Template Match (Semantic Retrieval)

**Description:** Reuse existing templates instead of rewriting every time.

**Characteristics:**
- User prompt → embedding
- Semantic matching against template library
- Templates describe structure, args, expected output
- Enables reuse and predictability
- Reduces costs (fewer enhancement calls)

**Current Foundation:**
✅ Semantic cache already does embedding + cosine similarity
✅ Infrastructure exists, just needs purpose shift

**Evolution:**

```python
# Current: Semantic Cache
# Purpose: Match requests to cached responses
cache_key = hash(request)
embedding = get_embedding(request.messages)
similar_cache = find_similar(embedding, threshold=0.85)

# Stage 3: Template Library
# Purpose: Match requests to reusable templates
template_embedding = get_embedding(user_prompt)
matched_template = find_template(embedding, threshold=0.80)

# Template structure
{
  "id": "template_001",
  "name": "Code Review Request",
  "description": "Analyze code for bugs, style, performance",
  "embedding": [...],  # Precomputed
  "smart_prompt": "You are an expert code reviewer. Analyze the following code for:\n1. Bugs and edge cases\n2. Performance issues...",
  "required_args": ["code", "language"],
  "optional_args": ["focus_areas", "style_guide"],
  "output_format": "markdown",
  "usage_count": 42,
  "avg_cost": 0.0023,
  "avg_latency": 1200,
  "success_rate": 0.95
}
```

**Prompt Studio UI Evolution:**

```
┌──────────────────────────────────────┐
│ 🔍 Similar templates found:          │
│                                      │
│ ⭐ Code Review (95% match)           │
│    Used 42 times | Avg cost: $0.002 │
│    [Use This]                        │
│                                      │
│ 📝 Code Analysis (87% match)         │
│    Used 12 times | Avg cost: $0.003 │
│    [Use This]                        │
│                                      │
│ [Write from scratch]                 │
└──────────────────────────────────────┘
```

**Gateway Changes:**

```python
# New endpoint
@app.post("/v1/prompts/match")
async def match_template(request: MatchRequest):
    """
    Find best matching template for a user prompt.
    Returns ranked list of templates with similarity scores.
    """
    embedding = await generate_embedding(request.prompt)
    templates = await template_store.find_similar(embedding, top_k=5)
    return templates

# New storage
class TemplateStore:
    """Manages template library with semantic search."""
    def save(self, template: Template) -> str
    def find_similar(self, embedding: List[float], top_k: int) -> List[Template]
    def get_stats(self, template_id: str) -> TemplateStats
    def update_metrics(self, template_id: str, cost: float, latency: float, success: bool)
```

**Benefits:**
- Massive cost savings (reuse > regenerate)
- Quality consistency
- Performance metrics per template
- User learns what works
- Foundation for argument extraction (Stage 4)

---

### Stage 4 — Argument Extraction

**Description:** Fill template parameters from user input.

**Characteristics:**
- Extract structured arguments from natural language
- Validate against template specification
- Request missing parameters interactively
- Output structured object: `{template_id, args}`

**Template with Arguments:**

```yaml
template_id: code_review_001
name: "Code Review Request"

required_args:
  - name: code
    type: string
    description: "Code to review"
    validation: "non-empty, max 10k chars"

  - name: language
    type: enum
    values: [python, javascript, typescript, go, rust, java]
    description: "Programming language"

optional_args:
  - name: focus_areas
    type: array[string]
    values: [bugs, performance, style, security, testing]
    default: [bugs, performance, style]
    description: "Specific areas to focus on"

  - name: style_guide
    type: string
    description: "URL or name of style guide to follow"

output_format:
  type: markdown
  sections: [summary, critical_issues, suggestions, score]
```

**Argument Extraction Process:**

```python
@app.post("/v1/prompts/extract-args")
async def extract_arguments(request: ExtractArgsRequest):
    """
    Given a template and user prompt, extract argument values.
    Uses LLM to parse natural language into structured args.
    """
    template = await template_store.get(request.template_id)

    # Use LLM to extract structured data
    extraction_prompt = f"""
    Template: {template.name}
    Required arguments: {template.required_args}
    Optional arguments: {template.optional_args}

    User request: "{request.user_prompt}"

    Extract the argument values from the user request.
    Return JSON with extracted values.
    If required arguments are missing, set them to null.
    """

    extracted = await llm_extract(extraction_prompt)

    # Validate
    missing = validate_args(extracted, template)

    if missing:
        return {
            "status": "incomplete",
            "extracted": extracted,
            "missing": missing,
            "prompt_user": f"Please provide: {', '.join(missing)}"
        }

    return {
        "status": "complete",
        "template_id": template.id,
        "args": extracted
    }
```

**Prompt Studio UI - Interactive Filling:**

```
┌──────────────────────────────────────┐
│ Template: Code Review Request        │
├──────────────────────────────────────┤
│ ✅ Code: [Extracted from prompt]     │
│ ✅ Language: python                  │
│ ⚠️  Focus Areas: [Not specified]     │
│    □ Bugs  □ Performance  □ Style    │
│    □ Security  □ Testing             │
│ ℹ️  Style Guide: [Optional]          │
│    [                              ]  │
│                                      │
│ [Run Code Review]                    │
└──────────────────────────────────────┘
```

**Benefits:**
- User intent captured as structured data
- Can validate before execution
- Can estimate cost accurately
- Foundation for deterministic execution (Stage 5-6)
- Enables automation (Stage 7)

---

### Stage 5 — Freeze / Materialize

**Description:** Convert Smart Prompt + Template + Args into deterministic "frozen" block.

**Characteristics:**
- Prompt is frozen (immutable)
- No further reinterpretation by LLM
- Fully reproducible
- Stored as YAML/JSON/code
- Versionable artifact

**Frozen Execution Block:**

```yaml
# frozen_request_abc123.yaml
version: 1.0
created_at: 2025-01-13T10:30:00Z
frozen_by: user_456

# Template reference
template:
  id: code_review_001
  version: 2.3
  name: "Code Review Request"

# Extracted arguments
arguments:
  code: |
    def calculate_total(items):
      return sum(item.price for item in items)
  language: python
  focus_areas: [bugs, performance, security]
  style_guide: "PEP 8"

# Execution parameters
execution:
  model: gpt-4
  temperature: 0.3
  max_tokens: 2000
  cache_mode: auto
  cache_ttl: 3600

# Materialized prompt (frozen)
materialized_prompt:
  system: |
    You are an expert Python code reviewer following PEP 8 guidelines.
    Focus on: bugs, performance, and security.

    Output format:
    ## Summary
    [Brief overview]

    ## Critical Issues
    [List any critical problems]

    ## Suggestions
    [Improvement suggestions]

    ## Score
    [Overall quality score: 1-10]

  user: |
    Review this Python code:

    ```python
    def calculate_total(items):
      return sum(item.price for item in items)
    ```

# Metadata
metadata:
  estimated_cost: 0.0023
  estimated_latency: 1200
  template_usage_count: 43
  template_success_rate: 0.95
```

**Gateway Changes:**

```python
@app.post("/v1/requests/freeze")
async def freeze_request(request: FreezeRequest):
    """
    Create immutable execution artifact from template + args.
    Returns frozen request that can be executed deterministically.
    """
    template = await template_store.get(request.template_id)

    # Materialize the prompt
    materialized = template.render(request.args)

    # Create frozen artifact
    frozen = FrozenRequest(
        template_id=request.template_id,
        template_version=template.version,
        arguments=request.args,
        execution_params=request.execution_params,
        materialized_prompt=materialized,
        metadata=await get_execution_estimates(template.id)
    )

    # Store
    frozen_id = await frozen_store.save(frozen)

    return {
        "frozen_id": frozen_id,
        "artifact_url": f"/v1/frozen/{frozen_id}",
        "estimated_cost": frozen.metadata.estimated_cost,
        "can_execute": True
    }

@app.post("/v1/frozen/{frozen_id}/execute")
async def execute_frozen(frozen_id: str):
    """
    Execute a frozen request deterministically.
    No prompt interpretation needed - just execute.
    """
    frozen = await frozen_store.get(frozen_id)

    # Execute exactly as specified
    response = await litellm.acompletion(
        model=frozen.execution.model,
        messages=[
            {"role": "system", "content": frozen.materialized_prompt.system},
            {"role": "user", "content": frozen.materialized_prompt.user}
        ],
        temperature=frozen.execution.temperature,
        max_tokens=frozen.execution.max_tokens
    )

    # Log execution against frozen artifact
    await execution_log.record(frozen_id, response)

    return response
```

**Prompt Studio UI:**

```
┌──────────────────────────────────────┐
│ Request Frozen ✅                     │
│                                      │
│ Frozen ID: req_abc123               │
│ Version: 1.0                         │
│ Template: Code Review v2.3           │
│                                      │
│ [View Artifact] [Execute] [Share]   │
│                                      │
│ 📊 Estimates:                        │
│    Cost: ~$0.0023                    │
│    Latency: ~1.2s                    │
│    Success Rate: 95%                 │
└──────────────────────────────────────┘
```

**Benefits:**
- **Reproducibility:** Exact same prompt every time
- **Auditability:** Full trace of how prompt was constructed
- **Versioning:** Can track changes over time
- **Sharing:** Send frozen artifact to colleagues
- **Cost Control:** Know exact cost before execution
- **Testing:** Can replay with different models/params
- **Foundation for playbooks** (Stage 6)

---

### Stage 6 — Playbook Generation (Executable)

**Description:** Convert frozen template into multi-step executable workflow.

**Characteristics:**
- Step-by-step actions
- Deterministic workflow (DAG)
- Supports tool/MCP calls
- Conditional logic
- Error handling
- Versionable, auditable artifacts

**Playbook Structure:**

```yaml
# playbook_code_review_full.yaml
playbook_id: code_review_full_001
version: 1.0
name: "Full Code Review with Fixes"

inputs:
  - name: code
    type: string
  - name: language
    type: enum
  - name: apply_fixes
    type: boolean
    default: false

steps:
  - id: analyze
    name: "Static Analysis"
    type: tool_call
    tool: "code_analyzer"
    inputs:
      code: ${inputs.code}
      language: ${inputs.language}
    outputs:
      - issues
      - metrics

  - id: llm_review
    name: "LLM Code Review"
    type: llm_call
    template: code_review_001
    inputs:
      code: ${inputs.code}
      language: ${inputs.language}
      static_analysis: ${steps.analyze.outputs.issues}
    outputs:
      - review_text
      - severity_score

  - id: suggest_fixes
    name: "Generate Fix Suggestions"
    type: llm_call
    condition: ${steps.llm_review.outputs.severity_score} > 5
    template: code_fix_001
    inputs:
      code: ${inputs.code}
      review: ${steps.llm_review.outputs.review_text}
    outputs:
      - fixed_code
      - explanation

  - id: apply_fixes
    name: "Apply Fixes"
    type: tool_call
    condition: ${inputs.apply_fixes} == true
    tool: "file_writer"
    inputs:
      content: ${steps.suggest_fixes.outputs.fixed_code}
      path: ${inputs.file_path}

outputs:
  review: ${steps.llm_review.outputs.review_text}
  severity: ${steps.llm_review.outputs.severity_score}
  fixes: ${steps.suggest_fixes.outputs.fixed_code}
  applied: ${steps.apply_fixes.success}

error_handling:
  - on_step_failure: analyze
    action: continue_with_llm_only
  - on_step_failure: apply_fixes
    action: rollback_and_notify

metadata:
  estimated_cost_range: [0.005, 0.015]
  estimated_latency_range: [2000, 8000]
  success_rate: 0.89
```

**Execution Engine:**

```python
class PlaybookEngine:
    """Executes playbooks as deterministic DAGs."""

    async def execute(self, playbook_id: str, inputs: Dict) -> PlaybookResult:
        playbook = await playbook_store.get(playbook_id)
        context = ExecutionContext(inputs=inputs)

        for step in playbook.steps:
            # Check condition
            if step.condition and not evaluate(step.condition, context):
                continue

            # Execute step
            try:
                if step.type == "llm_call":
                    result = await self.execute_llm_step(step, context)
                elif step.type == "tool_call":
                    result = await self.execute_tool_step(step, context)

                # Store outputs in context
                context.set_step_outputs(step.id, result)

                # Log step execution
                await execution_log.record_step(step.id, result)

            except Exception as e:
                # Handle error based on policy
                await self.handle_error(playbook, step, e, context)

        # Return final outputs
        return PlaybookResult(
            playbook_id=playbook_id,
            outputs=context.get_outputs(playbook.outputs),
            steps_executed=context.steps,
            total_cost=context.total_cost,
            total_latency=context.total_latency
        )
```

**Gateway Endpoints:**

```python
@app.post("/v1/playbooks/create")
async def create_playbook(request: CreatePlaybookRequest):
    """Create a new playbook from templates and tools."""
    pass

@app.get("/v1/playbooks/{playbook_id}")
async def get_playbook(playbook_id: str):
    """Retrieve playbook definition."""
    pass

@app.post("/v1/playbooks/{playbook_id}/execute")
async def execute_playbook(playbook_id: str, inputs: Dict):
    """Execute a playbook with given inputs."""
    engine = PlaybookEngine()
    result = await engine.execute(playbook_id, inputs)
    return result

@app.get("/v1/playbooks/{playbook_id}/simulate")
async def simulate_playbook(playbook_id: str, inputs: Dict):
    """Dry-run: estimate cost, latency, steps without executing."""
    pass
```

**Prompt Studio Evolution:**

```
┌────────────────────────────────────────┐
│ Playbook: Full Code Review             │
├────────────────────────────────────────┤
│ Steps:                                 │
│ 1. ✓ Static Analysis       (50ms)     │
│ 2. ⏳ LLM Review           (running)   │
│ 3. ⏸  Fix Suggestions      (pending)   │
│ 4. ⏸  Apply Fixes          (pending)   │
│                                        │
│ Progress: ████████░░░░░░ 40%           │
│                                        │
│ Cost so far: $0.003 / ~$0.012         │
│ Time elapsed: 2.1s / ~6.5s            │
│                                        │
│ [Pause] [Cancel] [View Logs]          │
└────────────────────────────────────────┘
```

**Benefits:**
- **Complex workflows:** Multi-step reasoning + actions
- **Tool integration:** Call external tools/APIs/MCP servers
- **Observable:** See each step's inputs/outputs
- **Debuggable:** Replay individual steps
- **Cost efficient:** Skip unnecessary steps
- **Reusable:** Playbook library grows over time

---

### Stage 7 — Intent Detection

**Description:** System detects user intent and automatically selects workflow.

**Characteristics:**
- Intent category classification
- Template/playbook family selection
- Automatic argument extraction
- Policy application
- No manual template search needed

**Intent Taxonomy:**

```yaml
intents:
  code:
    - code_review
    - code_generation
    - code_debugging
    - code_refactoring
    - code_explanation

  content:
    - content_writing
    - content_editing
    - content_summarization
    - content_translation

  analysis:
    - data_analysis
    - text_analysis
    - sentiment_analysis
    - comparison

  reasoning:
    - problem_solving
    - decision_making
    - planning
    - research
```

**Intent Detection Flow:**

```python
class IntentEngine:
    """Detects user intent and routes to appropriate workflow."""

    async def detect_intent(self, user_message: str) -> Intent:
        """
        Use fast classifier model to detect intent category.
        Falls back to LLM for ambiguous cases.
        """
        # Fast path: embedding-based classification
        embedding = await generate_embedding(user_message)
        intent_match = await intent_classifier.classify(embedding)

        if intent_match.confidence > 0.9:
            return intent_match.intent

        # Slow path: LLM-based classification
        intent = await llm_classify_intent(user_message)

        # Learn from this for fast path
        await intent_classifier.train(embedding, intent)

        return intent

    async def route_request(self, user_message: str) -> WorkflowPlan:
        """
        Detect intent, select workflow, extract args, return plan.
        """
        # 1. Detect intent
        intent = await self.detect_intent(user_message)

        # 2. Get applicable templates/playbooks
        candidates = await workflow_store.get_by_intent(intent)

        # 3. Rank by historical performance
        ranked = rank_workflows(candidates, user_history, intent)

        # 4. Select best match
        workflow = ranked[0]

        # 5. Extract arguments
        args = await extract_arguments(user_message, workflow)

        # 6. Apply policies (cost limits, model selection, etc.)
        execution_plan = await apply_policies(workflow, args, user_policies)

        return WorkflowPlan(
            intent=intent,
            workflow=workflow,
            arguments=args,
            execution_plan=execution_plan,
            estimated_cost=execution_plan.cost,
            estimated_latency=execution_plan.latency
        )
```

**Gateway Endpoint:**

```python
@app.post("/v1/intents/execute")
async def execute_intent(request: IntentRequest):
    """
    High-level API: send natural language, system handles everything.

    This is the "magic" endpoint that hides all complexity.
    """
    # Detect intent and plan workflow
    plan = await intent_engine.route_request(request.message)

    # Ask for confirmation if cost exceeds threshold
    if plan.estimated_cost > request.max_auto_cost:
        return {
            "status": "confirmation_required",
            "plan": plan,
            "message": f"This will cost ~${plan.estimated_cost:.4f}. Confirm?"
        }

    # Execute workflow
    result = await playbook_engine.execute(
        plan.workflow.id,
        plan.arguments
    )

    # Log for learning
    await intent_log.record(
        intent=plan.intent,
        workflow=plan.workflow.id,
        success=result.success,
        cost=result.cost,
        latency=result.latency,
        user_feedback=None  # To be filled later
    )

    return result
```

**Prompt Studio UI - Intent Mode:**

```
┌────────────────────────────────────────┐
│ 💬 Just tell me what you want         │
├────────────────────────────────────────┤
│ [Review my Python code for bugs]      │
│                                        │
│ [Send]                                 │
└────────────────────────────────────────┘
         ↓
┌────────────────────────────────────────┐
│ 🎯 Detected Intent: code_review        │
│                                        │
│ Selected Workflow:                     │
│ "Full Code Review with Fixes"          │
│                                        │
│ Plan:                                  │
│ 1. Static analysis                     │
│ 2. LLM review (gpt-4)                  │
│ 3. Fix suggestions                     │
│                                        │
│ Estimated: $0.012, ~6s                 │
│                                        │
│ [Confirm & Execute] [Adjust] [Cancel] │
└────────────────────────────────────────┘
```

**Benefits:**
- **Zero configuration:** User just describes intent
- **Automatic optimization:** System picks best workflow
- **Learns over time:** Gets better with usage
- **Cost predictable:** Estimates before execution
- **Transparent:** Shows reasoning, allows adjustment

---

### Stage 8 — Intent Engine (Runtime)

**Description:** Full structured execution environment with policies, registry, observability.

**Components:**

```
┌─────────────────────────────────────────────┐
│          Intent Engine Runtime              │
├─────────────────────────────────────────────┤
│                                             │
│  ┌──────────────┐  ┌──────────────┐        │
│  │  Intent      │  │  Workflow    │        │
│  │  Classifier  │→│  Router      │        │
│  └──────────────┘  └──────────────┘        │
│         ↓                 ↓                 │
│  ┌──────────────┐  ┌──────────────┐        │
│  │  Policy      │  │  Playbook    │        │
│  │  Engine      │→│  Executor    │        │
│  └──────────────┘  └──────────────┘        │
│         ↓                 ↓                 │
│  ┌──────────────┐  ┌──────────────┐        │
│  │  Cost        │  │  Execution   │        │
│  │  Predictor   │  │  Logger      │        │
│  └──────────────┘  └──────────────┘        │
│                        ↓                    │
│               ┌──────────────┐              │
│               │  Learning    │              │
│               │  System      │              │
│               └──────────────┘              │
│                                             │
└─────────────────────────────────────────────┘
```

**Policy Engine:**

```yaml
# policies.yaml
policies:
  cost_limits:
    - scope: user
      max_per_request: 0.10
      max_per_day: 5.00
      max_per_month: 50.00

    - scope: intent
      code_review:
        preferred_model: gpt-4
        max_cost: 0.05
      content_writing:
        preferred_model: gpt-3.5-turbo
        max_cost: 0.02

  model_selection:
    - intent: code_review
      conditions:
        - if: file_size < 1000
          use: gpt-3.5-turbo
        - if: file_size >= 1000
          use: gpt-4

    - intent: reasoning_task
      use: o1-preview
      fallback: gpt-4

  caching:
    - intent: code_review
      semantic_threshold: 0.90  # High - code changes matter

    - intent: content_summarization
      semantic_threshold: 0.75  # Lower - summaries are flexible

  execution:
    - max_concurrent_requests: 10
    - timeout_ms: 30000
    - retry_on_failure: 3
    - fallback_model: gpt-3.5-turbo
```

**Execution Logger:**

```python
class ExecutionLogger:
    """Comprehensive logging for observability and learning."""

    async def log_execution(self, execution: Execution):
        """
        Store full execution trace with all metadata.
        Used for debugging, billing, and learning.
        """
        log_entry = {
            "execution_id": execution.id,
            "timestamp": datetime.utcnow(),

            # Intent
            "intent": execution.intent,
            "user_message": execution.original_message,

            # Workflow
            "workflow_id": execution.workflow.id,
            "workflow_version": execution.workflow.version,

            # Execution trace
            "steps": [
                {
                    "step_id": step.id,
                    "type": step.type,
                    "inputs": step.inputs,
                    "outputs": step.outputs,
                    "cost": step.cost,
                    "latency_ms": step.latency,
                    "model": step.model,
                    "cache_hit": step.cache_hit
                }
                for step in execution.steps
            ],

            # Outcomes
            "success": execution.success,
            "error": execution.error if not execution.success else None,
            "total_cost": execution.total_cost,
            "total_latency": execution.total_latency,

            # User feedback (added later)
            "user_rating": None,
            "user_feedback": None,

            # Metadata
            "policies_applied": execution.policies,
            "cache_effectiveness": execution.cache_stats
        }

        await execution_store.save(log_entry)

        # Update metrics
        await metrics.update(
            intent=execution.intent,
            workflow=execution.workflow.id,
            cost=execution.total_cost,
            latency=execution.total_latency,
            success=execution.success
        )
```

**Cost Predictor:**

```python
class CostPredictor:
    """Predicts execution cost before running."""

    async def predict(self, plan: WorkflowPlan) -> CostEstimate:
        """
        Estimate cost based on:
        - Workflow steps
        - Historical data
        - Model pricing
        - Cache hit probability
        """
        base_cost = 0

        for step in plan.workflow.steps:
            if step.type == "llm_call":
                # Get historical stats for this step
                stats = await self.get_step_stats(step.id)

                # Estimate tokens
                avg_tokens = stats.avg_prompt_tokens + stats.avg_completion_tokens

                # Model cost
                model_cost = get_model_cost(step.model, avg_tokens)

                # Cache probability
                cache_prob = await self.estimate_cache_hit_probability(step, plan.arguments)

                # Expected cost = (1 - cache_prob) * model_cost
                step_cost = (1 - cache_prob) * model_cost

                base_cost += step_cost

        return CostEstimate(
            min=base_cost * 0.8,
            expected=base_cost,
            max=base_cost * 1.5,
            confidence=0.85,
            breakdown=[...],
            cache_assumptions={...}
        )
```

**Gateway Endpoints:**

```python
# Intent execution (main API)
@app.post("/v1/intents/execute")

# Policy management
@app.get("/v1/policies")
@app.put("/v1/policies/{policy_id}")

# Workflow/playbook management
@app.get("/v1/workflows")
@app.post("/v1/workflows")
@app.get("/v1/workflows/{workflow_id}")
@app.put("/v1/workflows/{workflow_id}")

# Execution history and logs
@app.get("/v1/executions")
@app.get("/v1/executions/{execution_id}")
@app.get("/v1/executions/{execution_id}/trace")

# Analytics
@app.get("/v1/analytics/costs")
@app.get("/v1/analytics/intents")
@app.get("/v1/analytics/workflows")

# Learning
@app.post("/v1/executions/{execution_id}/feedback")
@app.get("/v1/recommendations")
```

**Benefits:**
- **Fully autonomous:** User just states intent
- **Policy-driven:** Automatic optimization within constraints
- **Observable:** Full execution trace
- **Predictable:** Cost and latency estimates
- **Auditable:** Complete history
- **Scalable:** Handles concurrent executions
- **Reliable:** Error handling, retries, fallbacks

---

### Stage 9 — Self-Improvement Loop

**Description:** System refines templates, arguments, and playbooks based on usage.

**Characteristics:**
- Learns from execution logs
- Identifies patterns in failures
- Refines templates based on feedback
- Optimizes model selection
- Improves cost efficiency
- **Bounded by deterministic rules** (not unconstrained learning)

**Learning Sources:**

```python
class LearningSystem:
    """Continuously improves system based on execution data."""

    async def analyze_executions(self):
        """
        Periodic analysis of execution logs to find improvements.
        """
        # Get recent executions
        executions = await execution_store.get_recent(limit=1000)

        # Analyze by intent
        for intent in Intent.all():
            intent_executions = [e for e in executions if e.intent == intent]

            # Find patterns
            await self.analyze_cost_patterns(intent, intent_executions)
            await self.analyze_failure_patterns(intent, intent_executions)
            await self.analyze_cache_effectiveness(intent, intent_executions)
            await self.analyze_model_performance(intent, intent_executions)

    async def analyze_cost_patterns(self, intent: Intent, executions: List[Execution]):
        """
        Find opportunities to reduce costs.
        """
        # Are we using expensive models for simple tasks?
        for execution in executions:
            if execution.total_cost > intent.avg_cost * 2:
                # Analyze if cheaper model could work
                similar_cheap = await self.find_similar_cheap_executions(execution)
                if similar_cheap and similar_cheap.success_rate > 0.9:
                    # Recommend policy change
                    await self.suggest_policy_update(
                        intent=intent,
                        suggestion=f"Use {similar_cheap.model} instead of {execution.model}",
                        estimated_savings=execution.total_cost - similar_cheap.avg_cost
                    )

    async def analyze_failure_patterns(self, intent: Intent, executions: List[Execution]):
        """
        Identify common failure modes and suggest fixes.
        """
        failures = [e for e in executions if not e.success]

        if len(failures) > 0.1 * len(executions):  # >10% failure rate
            # Analyze failure causes
            error_types = defaultdict(list)
            for failure in failures:
                error_types[failure.error_type].append(failure)

            # Find most common error
            most_common = max(error_types.items(), key=lambda x: len(x[1]))

            if most_common[0] == "token_limit_exceeded":
                # Suggest template improvement
                await self.suggest_template_update(
                    intent=intent,
                    suggestion="Increase max_tokens or add truncation logic",
                    affected_executions=len(most_common[1])
                )

    async def optimize_cache_thresholds(self):
        """
        Learn optimal semantic similarity thresholds per intent.
        """
        for intent in Intent.all():
            # Get executions with cache attempts
            cache_attempts = await execution_store.get_cache_attempts(intent)

            # Analyze false positives (cached but wrong)
            false_positives = [
                a for a in cache_attempts
                if a.cache_hit and a.user_rating < 3
            ]

            # Analyze false negatives (not cached but could be)
            false_negatives = [
                a for a in cache_attempts
                if not a.cache_hit and a.similarity > current_threshold - 0.1
            ]

            # Find optimal threshold
            optimal = find_optimal_threshold(
                false_positives,
                false_negatives,
                cost_savings_weight=0.3,
                quality_weight=0.7
            )

            if abs(optimal - current_threshold) > 0.05:
                await self.suggest_policy_update(
                    intent=intent,
                    parameter="semantic_threshold",
                    current=current_threshold,
                    suggested=optimal,
                    confidence=0.85
                )
```

**Improvement Dashboard (Prompt Studio):**

```
┌─────────────────────────────────────────────┐
│ 🧠 System Improvements                      │
├─────────────────────────────────────────────┤
│ Pending Suggestions:                        │
│                                             │
│ 💰 Cost Optimization                        │
│   "Use gpt-3.5-turbo for code_review when  │
│    file < 500 lines"                        │
│   Estimated savings: $12.50/month           │
│   Confidence: 92%                           │
│   [Apply] [Dismiss]                         │
│                                             │
│ 🎯 Cache Tuning                             │
│   "Lower semantic threshold for             │
│    content_summarization to 0.72"           │
│   Cache hit rate improvement: +15%          │
│   Quality impact: -2% (acceptable)          │
│   [Apply] [Test] [Dismiss]                  │
│                                             │
│ 🔧 Workflow Improvement                     │
│   "Add static analysis step before LLM     │
│    review to reduce failures by 23%"        │
│   Cost increase: +$0.001/execution          │
│   Failure reduction: -23%                   │
│   [Apply] [Review] [Dismiss]                │
│                                             │
│ Applied Improvements (Last 30 days):        │
│ • 5 cost optimizations → saved $47.23       │
│ • 3 cache tunings → +12% hit rate           │
│ • 2 workflow fixes → -15% failures          │
└─────────────────────────────────────────────┘
```

**Safeguards:**

```python
class ImprovementSafeguards:
    """Ensure learning doesn't break the system."""

    async def validate_suggestion(self, suggestion: Improvement) -> bool:
        """
        Check if suggestion is safe to apply.
        """
        # 1. Simulate on historical data
        simulation = await self.simulate_on_historical(suggestion)

        if simulation.failure_rate > current_failure_rate * 1.1:
            return False  # Would increase failures by >10%

        if simulation.cost > current_cost * 1.2:
            return False  # Would increase cost by >20%

        # 2. Canary test on small % of traffic
        if suggestion.impact == "high":
            canary_result = await self.canary_test(suggestion, traffic_percent=5)

            if not canary_result.success:
                return False

        # 3. Require human approval for major changes
        if suggestion.estimated_savings > 100 or suggestion.affects_users > 1000:
            await self.request_human_approval(suggestion)
            return False  # Wait for approval

        return True

    async def rollback_if_needed(self, suggestion: Improvement):
        """
        Monitor applied suggestion and rollback if problems detected.
        """
        # Monitor for 24 hours
        metrics = await self.monitor_improvement(suggestion, hours=24)

        if metrics.failure_rate > baseline * 1.15:
            await self.rollback(suggestion)
            await self.notify_admins("Rolled back improvement due to failures")
```

**Benefits:**
- **Automatic optimization:** System gets better over time
- **Cost reduction:** Finds cheaper ways to achieve same quality
- **Quality improvement:** Fixes failure patterns
- **Transparent:** Shows what it learned and why
- **Safe:** Simulations, canary tests, rollbacks
- **Human oversight:** Requires approval for major changes

---

## Implementation Roadmap

### Phase 1: Foundation (Weeks 1-2) ✅ **Mostly Done**

- [x] Semantic caching (Stage 3 primitive)
- [x] Usage logging and metrics
- [x] Prompt Studio UI
- [x] Cost tracking
- [ ] Template storage schema

### Phase 2: Smart Prompts (Weeks 3-4)

**Goal:** Reach Stage 2

- [ ] Add "Generate Smart Prompt" feature to Prompt Studio
- [ ] Create `/v1/prompts/enhance` endpoint
- [ ] Use GPT-4/Claude to improve prompts
- [ ] Store enhanced prompts for template building
- [ ] UI to compare original vs enhanced

### Phase 3: Template Library (Weeks 5-8)

**Goal:** Reach Stage 3-4

- [ ] Template storage and retrieval
- [ ] Semantic template matching
- [ ] Template statistics (usage, cost, success rate)
- [ ] Argument extraction
- [ ] Interactive argument filling UI
- [ ] Template sharing and library

### Phase 4: Frozen Requests (Weeks 9-10)

**Goal:** Reach Stage 5

- [ ] Freeze request API
- [ ] Frozen artifact storage
- [ ] Deterministic execution from frozen artifacts
- [ ] Versioning and history
- [ ] Sharing and replay

### Phase 5: Playbooks (Weeks 11-14)

**Goal:** Reach Stage 6

- [ ] Playbook schema and storage
- [ ] DAG execution engine
- [ ] Tool integration (MCP)
- [ ] Step-by-step UI
- [ ] Simulation and dry-run
- [ ] Error handling and rollback

### Phase 6: Intent Engine (Weeks 15-18)

**Goal:** Reach Stage 7-8

- [ ] Intent classification
- [ ] Workflow routing
- [ ] Policy engine
- [ ] Cost prediction
- [ ] Execution logging
- [ ] Analytics dashboard

### Phase 7: Self-Improvement (Weeks 19-20)

**Goal:** Reach Stage 9

- [ ] Learning system
- [ ] Improvement suggestions
- [ ] Safeguards and validation
- [ ] Canary testing
- [ ] Improvement dashboard

---

## Success Metrics

### Technical Metrics

- **Cost Reduction:** 40-60% reduction through caching and optimization
- **Cache Hit Rate:** >50% for common intents
- **Template Reuse:** >70% of requests match existing templates
- **Execution Success Rate:** >95%
- **Latency P95:** <3s for simple requests, <10s for complex playbooks

### User Metrics

- **Time to First Value:** <30s from idea to execution
- **Learning Curve:** New users productive in <5 minutes
- **Template Library Growth:** 50+ templates in first 3 months
- **User Satisfaction:** >4.5/5 rating
- **Repeat Usage:** >80% of users return weekly

### Business Metrics

- **Cost per Request:** Decreasing over time (learning effect)
- **Request Volume:** Increasing (easier = more usage)
- **Template Contributions:** Users creating and sharing templates
- **Enterprise Adoption:** Policy controls enable enterprise use

---

## Why This Approach Works

1. **Gradual Evolution:** Each stage adds value independently
2. **User-Driven:** Prompt Studio makes advanced features accessible
3. **Data Flywheel:** More usage → better templates → better recommendations
4. **Cost-Aware:** Optimization built in from Stage 1
5. **Observable:** Full visibility at every stage
6. **Deterministic:** Reproducible, auditable, trustworthy
7. **Safe:** Bounded learning, human oversight, rollback capability

---

## Related Documentation

- [Project Overview (CLAUDE.md)](../CLAUDE.md)
- [Troubleshooting Guide](TROUBLESHOOTING.md)
- [API Documentation](../gateway/README.md)

