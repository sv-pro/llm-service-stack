# Frozen Requests Design (Stage 5)

## Overview

Freeze template + arguments into immutable, deterministic execution artifacts. This is the **first strong boundary of determinism** - no further prompt interpretation, fully reproducible.

**Repository:** llm-service-stack/
**Timeline:** 2-3 weeks
**Status:** Future (after Stages 2-4)

---

## Concept

A frozen request is an **immutable artifact** containing:
- Template reference + version
- Extracted arguments (validated)
- Materialized prompt (fully rendered)
- Execution parameters (model, temperature, etc.)
- Metadata (cost estimate, expected latency)

**Key Property:** Can be executed identically multiple times, shared, versioned, audited.

---

## Frozen Request Schema

```yaml
# frozen_request_abc123.yaml
version: 1.0
frozen_id: req_abc123
created_at: 2025-01-13T10:30:00Z
created_by: user_456

# Template reference
template:
  id: code_review_001
  version: 2.3
  name: "Code Review Request"

# Validated arguments
arguments:
  code: |
    def calculate_total(items):
      return sum(item.price for item in items)
  language: python
  focus_areas: [bugs, performance, security]
  style_guide: "PEP 8"

# Execution config
execution:
  model: gpt-4
  temperature: 0.3
  max_tokens: 2000
  cache_mode: auto
  cache_ttl: 3600

# Materialized prompt (frozen - no reinterpretation)
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

# Cost/performance estimates
metadata:
  estimated_cost: 0.0023
  estimated_latency_ms: 1200
  template_usage_count: 43
  template_success_rate: 0.95
```

---

## API

### POST /v1/requests/freeze

Create immutable artifact:

```python
@app.post("/v1/requests/freeze")
async def freeze_request(request: FreezeRequest):
    """Create frozen, reproducible execution artifact."""

    template = await template_store.get(request.template_id)

    # Validate arguments
    validate_args(request.args, template)

    # Materialize prompt (render template with args)
    materialized = template.render(request.args)

    # Create frozen artifact
    frozen = FrozenRequest(
        frozen_id=generate_id(),
        template_id=request.template_id,
        template_version=template.version,
        arguments=request.args,
        execution_params=request.execution_params,
        materialized_prompt=materialized,
        metadata=await get_execution_estimates(template.id),
        created_at=datetime.utcnow(),
        created_by=request.user_id
    )

    # Store
    frozen_id = await frozen_store.save(frozen)

    return {
        "frozen_id": frozen_id,
        "artifact_url": f"/v1/frozen/{frozen_id}",
        "can_execute": True,
        "estimated_cost": frozen.metadata.estimated_cost
    }
```

### POST /v1/frozen/{frozen_id}/execute

Execute deterministically:

```python
@app.post("/v1/frozen/{frozen_id}/execute")
async def execute_frozen(frozen_id: str):
    """Execute frozen request - deterministic, no interpretation."""

    frozen = await frozen_store.get(frozen_id)

    # Execute EXACTLY as frozen (no changes allowed)
    response = await litellm.acompletion(
        model=frozen.execution.model,
        messages=[
            {"role": "system", "content": frozen.materialized_prompt.system},
            {"role": "user", "content": frozen.materialized_prompt.user}
        ],
        temperature=frozen.execution.temperature,
        max_tokens=frozen.execution.max_tokens
    )

    # Log execution with frozen reference
    await execution_log.record(
        frozen_id=frozen_id,
        response=response,
        actual_cost=calculate_cost(response),
        actual_latency_ms=measure_latency()
    )

    return {
        "frozen_id": frozen_id,
        "response": response,
        "executed_at": datetime.utcnow()
    }
```

---

## UI: Freeze & Execute

```typescript
// After filling arguments, offer to freeze
<button
  onClick={async () => {
    const frozenId = await freezeRequest({
      template_id: selectedTemplate.id,
      args: args,
      execution_params: {
        model: selectedModel,
        temperature,
        max_tokens: maxTokens
      }
    });

    setFrozenRequest({id: frozenId, ...});
  }}
  className="bg-blue-600 text-white px-4 py-2 rounded"
>
  Freeze Request
</button>

// Show frozen artifact
{frozenRequest && (
  <div className="bg-blue-50 border-2 border-blue-300 rounded p-4">
    <h3 className="font-bold">Request Frozen ✅</h3>
    <div className="text-sm text-gray-700 mt-2">
      <div>Frozen ID: <code>{frozenRequest.id}</code></div>
      <div>Template: {frozenRequest.template_name} v{frozenRequest.template_version}</div>
      <div>Est. Cost: ${frozenRequest.estimated_cost.toFixed(4)}</div>
      <div>Success Rate: {(frozenRequest.success_rate * 100).toFixed(0)}%</div>
    </div>

    <div className="flex gap-2 mt-3">
      <button
        onClick={() => executeFrozen(frozenRequest.id)}
        className="bg-green-600 text-white px-4 py-2 rounded"
      >
        Execute
      </button>
      <button
        onClick={() => viewArtifact(frozenRequest.id)}
        className="bg-gray-200 px-4 py-2 rounded"
      >
        View Artifact
      </button>
      <button
        onClick={() => shareFrozen(frozenRequest.id)}
        className="bg-gray-200 px-4 py-2 rounded"
      >
        Share
      </button>
    </div>
  </div>
)}
```

---

## Benefits

### Reproducibility
- Exact same prompt every execution
- No drift from template changes
- Can replay historical requests

### Auditability
- Full trace of how prompt was constructed
- Arguments explicitly recorded
- Template version locked

### Sharing
- Send frozen ID to colleagues
- They get identical execution
- Collaboration without ambiguity

### Cost Control
- Know exact cost before execution
- Budget approval for expensive requests
- Track actual vs estimated costs

### Testing
- Replay with different models
- A/B test parameter changes
- Regression testing for templates

---

## Storage

```sql
CREATE TABLE frozen_requests (
  frozen_id TEXT PRIMARY KEY,
  template_id TEXT NOT NULL,
  template_version TEXT NOT NULL,
  arguments JSONB NOT NULL,
  execution_params JSONB NOT NULL,
  materialized_prompt JSONB NOT NULL,
  metadata JSONB,
  created_at TIMESTAMP NOT NULL,
  created_by TEXT,

  -- Indexing
  template_id_idx,
  created_by_idx,
  created_at_idx
);

CREATE TABLE frozen_executions (
  execution_id TEXT PRIMARY KEY,
  frozen_id TEXT REFERENCES frozen_requests(frozen_id),
  executed_at TIMESTAMP NOT NULL,
  response JSONB,
  actual_cost FLOAT,
  actual_latency_ms INT,
  success BOOLEAN,
  error TEXT
);
```

---

## Next Steps

After Stage 5:
- **Stage 6:** Convert frozen requests into multi-step playbooks
- **Stage 7:** Automatic freezing based on detected intent
- Enable frozen request marketplace/library
