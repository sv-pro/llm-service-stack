# Intent Engine Design (Stages 7-8)

## Overview

The Intent Engine automatically detects user intent and routes to appropriate workflows, with policy-driven execution.

**Repository:** intent-engine/ (future, separate repo)
**Timeline:** Part of Phase 4 (8-12 weeks)
**Status:** Future design

---

## Stage 7: Intent Detection

### Concept

User sends natural language → system detects intent → selects best playbook → executes.

No manual template/playbook selection needed.

### Intent Classification

```python
class IntentClassifier:
    """Fast intent detection with LLM fallback."""

    async def classify(self, user_message: str) -> Intent:
        # Fast path: embedding-based classification
        embedding = await generate_embedding(user_message)
        intent = await fast_classifier.predict(embedding)

        if intent.confidence > 0.9:
            return intent

        # Slow path: LLM classification
        intent = await llm_classify(user_message)

        # Learn for next time
        await training_store.record(embedding, intent)

        return intent
```

### Workflow Router

```python
async def route_request(user_message: str, user_context: Dict) -> WorkflowPlan:
    """Detect intent → select workflow → extract args → return plan."""

    # 1. Detect intent
    intent = await intent_classifier.classify(user_message)

    # 2. Get applicable playbooks
    candidates = await playbook_store.get_by_intent(intent)

    # 3. Rank by historical performance
    ranked = rank_playbooks(candidates, user_history={
        'past_success_rate': 0.95,
        'preferred_models': ['gpt-4'],
        'avg_budget': 0.05
    })

    # 4. Select best
    playbook = ranked[0]

    # 5. Extract arguments
    args = await extract_arguments(user_message, playbook)

    # 6. Apply policies
    plan = await policy_engine.plan(playbook, args, user_context)

    return WorkflowPlan(
        intent=intent,
        playbook=playbook,
        arguments=args,
        execution_plan=plan,
        estimated_cost=plan.cost,
        estimated_latency=plan.latency
    )
```

---

## Stage 8: Intent Engine Runtime

### Full Runtime Components

```
┌─────────────────────────────────────────┐
│        Intent Engine Runtime            │
├─────────────────────────────────────────┤
│                                         │
│  ┌──────────────┐  ┌──────────────┐    │
│  │  Intent      │→│  Workflow    │    │
│  │  Classifier  │  │  Router      │    │
│  └──────────────┘  └──────────────┘    │
│         ↓                 ↓             │
│  ┌──────────────┐  ┌──────────────┐    │
│  │  Policy      │→│  Playbook    │    │
│  │  Engine      │  │  Executor    │    │
│  └──────────────┘  └──────────────┘    │
│         ↓                 ↓             │
│  ┌──────────────┐  ┌──────────────┐    │
│  │  Cost        │  │  Execution   │    │
│  │  Predictor   │  │  Logger      │    │
│  └──────────────┘  └──────────────┘    │
│                                         │
└─────────────────────────────────────────┘
```

### Policy Engine

Defines constraints and strategies:

```yaml
# policies.yaml
policies:
  cost_limits:
    - scope: user
      max_per_request: 0.10
      max_per_day: 5.00

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

  caching:
    - intent: code_review
      semantic_threshold: 0.90  # High - code changes matter

    - intent: content_summarization
      semantic_threshold: 0.75  # Lower - summaries flexible

  execution:
    - max_concurrent: 10
    - timeout_ms: 30000
    - retry_on_failure: 3
```

### High-Level API

```python
@app.post("/v1/intents/execute")
async def execute_intent(request: IntentRequest):
    """
    Magic endpoint: send natural language → system handles everything.
    """

    # Plan workflow
    plan = await intent_engine.route_request(
        message=request.message,
        user_context=request.user_context
    )

    # Check cost approval
    if plan.estimated_cost > request.max_auto_cost:
        return {
            "status": "confirmation_required",
            "plan": plan,
            "message": f"Cost: ${plan.estimated_cost:.4f}. Confirm?"
        }

    # Execute
    result = await playbook_engine.execute(
        plan.playbook.id,
        plan.arguments
    )

    # Log for learning
    await log_execution(
        intent=plan.intent,
        playbook=plan.playbook.id,
        cost=result.cost,
        success=result.success
    )

    return result
```

---

## UI: Intent Mode

Prompt Studio adds "Intent Mode":

```
┌────────────────────────────────────────┐
│ 💬 Intent Mode                         │
├────────────────────────────────────────┤
│ What do you want to do?                │
│                                        │
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
│ Est: $0.012, ~6s                       │
│                                        │
│ [Confirm & Execute] [Adjust] [Cancel] │
└────────────────────────────────────────┘
```

Users can:
- Accept plan as-is (one click)
- Adjust parameters (model, focus areas)
- View/edit full playbook
- Save customized version

---

## Relationship to LLM Service Stack

Intent Engine is **a separate service** that:
- Calls LLM Service Stack for frozen request execution
- Calls Tools Gateway for tool execution
- Manages its own playbook storage and policies

**Architecture:**
```
User → Prompt Studio → Intent Engine → ┬→ LLM Service Stack (frozen requests)
                                       └→ Tools Gateway (MCP tools)
```

Prompt Studio provides the UI, Intent Engine provides the intelligence.

---

## Benefits

### For Users
- Zero configuration
- Natural language input
- Automatic optimization
- Cost-predictable

### For Operators
- Policy-driven control
- Full observability
- Cost management
- Quality control

### For System
- Learning from usage
- Continuous improvement
- Reusable workflows
- Auditable execution

---

## Next Steps

- Build intent classifier training dataset
- Define initial policy schemas
- Prototype workflow router
- Design learning system (Stage 9 - long term)
