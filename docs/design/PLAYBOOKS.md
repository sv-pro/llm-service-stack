# Playbooks Design (Stage 6)

## Overview

Convert frozen requests into multi-step executable workflows (DAGs) with tool integration, conditional logic, and error handling.

**Repository:** intent-engine/ (future, separate repo)
**Timeline:** 8-12 weeks (Phase 4)
**Status:** Future design

---

## Concept

A **playbook** is a deterministic workflow composed of:
- Multiple steps (LLM calls, tool calls, conditionals)
- DAG structure (dependencies between steps)
- Tool integration (MCP servers, APIs)
- Error handling and rollback
- Full observability

**Example:** Full code review workflow
```
1. Run static analysis (tool)
2. LLM review based on static analysis
3. Generate fix suggestions (conditional: if score < 7)
4. Apply fixes (conditional: if user approves)
```

---

## Playbook Schema

```yaml
playbook_id: code_review_full_001
version: 1.0
name: "Full Code Review with Fixes"

inputs:
  - name: code
    type: string
    required: true
  - name: language
    type: enum
    values: [python, javascript, typescript]
    required: true
  - name: apply_fixes
    type: boolean
    default: false

steps:
  - id: static_analysis
    type: tool_call
    tool: code_analyzer_mcp
    inputs:
      code: ${inputs.code}
      language: ${inputs.language}
    outputs:
      - issues
      - metrics

  - id: llm_review
    type: frozen_request
    frozen_id: code_review_001
    inputs:
      code: ${inputs.code}
      language: ${inputs.language}
      static_analysis: ${steps.static_analysis.outputs.issues}
    outputs:
      - review_text
      - severity_score

  - id: suggest_fixes
    type: frozen_request
    condition: ${steps.llm_review.outputs.severity_score} > 5
    frozen_id: code_fix_001
    inputs:
      code: ${inputs.code}
      review: ${steps.llm_review.outputs.review_text}
    outputs:
      - fixed_code
      - explanation

  - id: apply_fixes
    type: tool_call
    condition: ${inputs.apply_fixes} == true
    tool: file_writer_mcp
    inputs:
      content: ${steps.suggest_fixes.outputs.fixed_code}

outputs:
  review: ${steps.llm_review.outputs.review_text}
  severity: ${steps.llm_review.outputs.severity_score}
  fixes: ${steps.suggest_fixes.outputs.fixed_code}
  applied: ${steps.apply_fixes.success}

error_handling:
  - on_step_failure: static_analysis
    action: continue  # LLM review works without it
  - on_step_failure: apply_fixes
    action: rollback_and_notify
```

---

## Execution Engine

```python
class PlaybookEngine:
    """Executes playbooks as deterministic DAGs."""

    async def execute(self, playbook_id: str, inputs: Dict) -> PlaybookResult:
        playbook = await playbook_store.get(playbook_id)
        context = ExecutionContext(inputs=inputs)

        for step in playbook.steps:
            # Check condition
            if step.condition and not evaluate(step.condition, context):
                log_step_skipped(step.id)
                continue

            # Execute based on type
            try:
                if step.type == "frozen_request":
                    result = await execute_frozen_request(step.frozen_id, step.inputs)
                elif step.type == "tool_call":
                    result = await execute_tool(step.tool, step.inputs)

                context.set_step_outputs(step.id, result)
                log_step_success(step.id, result)

            except Exception as e:
                await handle_error(playbook.error_handling, step, e, context)

        return PlaybookResult(
            playbook_id=playbook_id,
            outputs=context.get_outputs(playbook.outputs),
            steps_executed=context.steps,
            total_cost=context.total_cost,
            success=context.all_succeeded
        )
```

---

## Key Features

### Tool Integration
- Execute MCP server tools
- Sandboxed execution
- Policy constraints (allowed tools, rate limits)

### Conditionals
- Skip steps based on previous outputs
- Branch based on scores/thresholds
- Dynamic workflow paths

### Error Handling
- Retry with exponential backoff
- Rollback on failure
- Continue with warnings
- Notify on critical errors

### Observability
- Step-by-step execution trace
- Inputs/outputs logged
- Cost per step
- Latency per step

---

## UI: Playbook Execution

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
│ Time: 2.1s / ~6.5s                     │
│                                        │
│ [Pause] [Cancel] [View Logs]          │
└────────────────────────────────────────┘
```

---

## Relationship to LLM Service Stack

Playbooks **consume** frozen requests from LLM Service Stack:
- Frozen requests = single-step deterministic execution
- Playbooks = multi-step workflows composed of frozen requests + tools

**Interface:**
```
Intent Engine calls → /v1/frozen/{id}/execute
                  ← deterministic response
```

No changes needed to LLM Service Stack. Clean separation.

---

## Next Steps

- Stage 7: Automatic playbook selection based on intent
- Stage 8: Full policy engine and runtime
- Playbook marketplace/sharing
- Visual playbook editor
