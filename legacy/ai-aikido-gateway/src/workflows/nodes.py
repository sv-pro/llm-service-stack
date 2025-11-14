"""
Workflow nodes implementing the Re^Re loop.

Each node represents a step in the Reason → Act → Reflect → Re-reason cycle.
"""

from typing import Dict, Any, Optional

from .state import PlaybookState, append_decision, record_budget_event
from .telemetry import emit_phase_event

# Optional import of ToolRegistry (not required for backward compatibility)
try:
    from src.tools import ToolRegistry
except ImportError:
    ToolRegistry = None

TOOL_COSTS = {
    "calculator": 0.001,
    "search": 0.01,
    "echo": 0.0001,
}

MIN_STEP_COST = min(TOOL_COSTS.values())


def _next_step_index(state: PlaybookState) -> int:
    """Return the upcoming step index (1-based)."""

    return len(state.get("steps_completed", [])) + 1


def analyze_intent_node(state: PlaybookState) -> PlaybookState:
    """
    REASON phase: Analyze the intent and determine execution plan.

    This node examines the user's intent and plans the next action.
    In a full implementation, this would use an LLM to understand the request.

    For the prototype, we implement simple intent parsing.
    """
    intent = state["intent"]
    lower_intent = intent.lower()
    step_index = _next_step_index(state)

    # Simple parsing for prototype
    # TODO: Replace with LLM-based intent analysis
    if "calculate" in lower_intent or "math" in lower_intent:
        tool = "calculator"
        tool_input = {"expression": intent}
    elif "search" in lower_intent or "find" in lower_intent:
        tool = "search"
        tool_input = {"query": intent}
    else:
        # Default: echo tool for demonstration
        tool = "echo"
        tool_input = {"message": intent}

    plan_step = {
        "step": step_index,
        "tool": tool,
        "goal": intent,
        "metadata": {
            "improvement_hints": list(state.get("improvement_suggestions", [])),
            "remaining_budget": state.get("remaining_budget"),
        },
    }
    state.setdefault("plan", []).append(plan_step)

    append_decision(
        state,
        phase="reason",
        message=f"Planned step {step_index} using {tool}",
        data={"tool_input": tool_input, "plan_step": plan_step},
    )

    # Update state
    state["selected_tool"] = tool
    state["tool_input"] = tool_input
    state["current_step"] = "execute_tool"

    emit_phase_event(
        state,
        phase="reason",
        node="analyze_intent",
        metadata={"plan_step": plan_step, "tool_input": tool_input},
    )

    return state


async def execute_tool_node(state: PlaybookState) -> PlaybookState:
    """
    ACT phase: Execute the selected tool.

    This node performs the actual action based on the reasoned plan.
    Uses ToolRegistry if available in context, otherwise falls back to stubs.
    """
    tool_name = state["selected_tool"]
    tool_input = state["tool_input"]
    step_index = len(state.get("steps_completed", [])) + 1

    # Check if ToolRegistry is available in context
    registry = state.get("context", {}).get("tool_registry")

    if registry is not None:
        # Use ToolRegistry for execution
        result = await _execute_with_registry(
            registry, tool_name, tool_input, state, step_index
        )
    else:
        # Fall back to stub tools for backward compatibility
        result = _execute_with_stubs(tool_name, tool_input, state, step_index)

    output = result["output"]
    cost = result["cost"]

    # Update state
    state["tool_result"] = output

    # Create artifact
    artifact = {
        "step": step_index,
        "tool": tool_name,
        "input": tool_input,
        "output": output,
        "cost": cost,
    }
    state["artifacts"].append(artifact)
    state["steps_completed"].append(f"{tool_name}_{step_index}")

    state["current_step"] = "evaluate_result"

    emit_phase_event(
        state,
        phase="act",
        node="execute_tool",
        metadata={"artifact": artifact, "error": state.get("error")},
    )

    return state


async def _execute_with_registry(
    registry, tool_name: str, tool_input: Dict, state: PlaybookState, step_index: int
) -> Dict[str, Any]:
    """Execute tool using ToolRegistry"""
    budget_max = state["context"].get("budget_max", 1.0)

    try:
        # Execute tool via registry
        tool_result = await registry.execute(tool_name, tool_input, validate=False)

        # Check budget after execution
        projected_budget = state["budget_used"] + tool_result.cost

        if projected_budget > budget_max and tool_result.success:
            # Tool succeeded but would exceed budget
            output = {
                "success": False,
                "error": "Budget exceeded after tool execution",
            }
            cost = 0.0
            record_budget_event(state, tool_name, cost, "budget_exceeded", step_index)
            state["error"] = output["error"]
        else:
            # Use tool result
            output = {
                "success": tool_result.success,
                "data": tool_result.data,
                "error": tool_result.error,
            }
            cost = tool_result.cost
            record_budget_event(
                state,
                tool_name,
                cost,
                "tool_execution" if tool_result.success else "tool_error",
                step_index,
            )

            if not tool_result.success:
                state.setdefault("improvement_suggestions", []).append(
                    f"Tool execution failed: {tool_result.error}"
                )

        append_decision(
            state,
            phase="act",
            message=f"Executed {tool_name} via registry",
            data={"output": output, "cost": cost},
        )

        return {"output": output, "cost": cost}

    except Exception as e:
        output = {"success": False, "error": str(e)}
        cost = 0.0
        record_budget_event(state, tool_name, cost, "execution_error", step_index)
        state["error"] = str(e)

        append_decision(
            state,
            phase="act",
            message=f"Tool execution error: {str(e)}",
            data={"tool": tool_name, "error": str(e)},
        )

        return {"output": output, "cost": cost}


def _execute_with_stubs(
    tool_name: str, tool_input: Dict, state: PlaybookState, step_index: int
) -> Dict[str, Any]:
    """Execute tool using stub implementation (backward compatibility)"""
    estimated_cost = TOOL_COSTS.get(tool_name, 0.001)
    budget_max = state["context"].get("budget_max", 1.0)
    projected_budget = state["budget_used"] + estimated_cost

    # Budget guardrail check
    if projected_budget > budget_max:
        output = {
            "success": False,
            "error": "Budget would be exceeded by executing this step",
        }
        cost = 0.0
        record_budget_event(state, tool_name, cost, "budget_guardrail", step_index)
        state["error"] = output["error"]
        append_decision(
            state,
            phase="act",
            message="Budget guardrail prevented tool execution",
            data={
                "tool": tool_name,
                "estimated_cost": estimated_cost,
                "budget_used": state["budget_used"],
                "budget_max": budget_max,
            },
        )
    else:
        if tool_name == "calculator":
            # Stub: Simple calculator
            try:
                result = eval(tool_input.get("expression", "0"))
                output = {"result": result, "success": True}
            except Exception as exc:
                output = {"error": str(exc), "success": False}
            cost = estimated_cost
        elif tool_name == "search":
            # Stub: Search tool
            output = {
                "results": ["Result 1", "Result 2", "Result 3"],
                "query": tool_input.get("query", ""),
                "success": True,
            }
            cost = estimated_cost
        else:  # echo
            # Stub: Echo tool
            output = {"message": tool_input.get("message", ""), "success": True}
            cost = estimated_cost

        record_budget_event(state, tool_name, cost, "tool_execution", step_index)
        append_decision(
            state,
            phase="act",
            message=f"Executed {tool_name}",
            data={"output": output, "cost": cost},
        )
        if not output.get("success", False):
            state.setdefault("improvement_suggestions", []).append(
                "Tool execution failed; consider alternate strategy"
            )

    return {"output": output, "cost": cost}


def evaluate_result_node(state: PlaybookState) -> PlaybookState:
    """
    REFLECT phase: Evaluate execution outcomes.

    This node assesses the quality of the result and determines if the goal is met.
    In a full implementation, this would use an LLM to evaluate quality.

    For the prototype, we implement simple success checking.
    """
    tool_result = state["tool_result"]

    # Simple quality evaluation for prototype
    # TODO: Replace with LLM-based quality scoring
    if tool_result.get("success", False):
        quality_score = 0.85  # Good quality if successful
    else:
        quality_score = 0.25  # Low quality if failed

    if state["budget_used"] > 0:
        utilization_ratio = state["budget_used"] / max(
            state["context"].get("budget_max", state["budget_used"]), 1e-9
        )
        # Penalize if too close to budget ceiling
        quality_score -= min(utilization_ratio * 0.2, 0.2)

    quality_score = max(min(quality_score, 1.0), 0.0)

    state["quality_score"] = quality_score

    # Check if quality meets threshold
    quality_threshold = state["context"].get("quality_threshold", 0.7)
    goal_met = quality_score >= quality_threshold

    if goal_met:
        state["current_step"] = "decide_next"
    else:
        # Quality too low, might need retry
        state["improvement_suggestions"].append(
            f"Quality score {quality_score} below threshold {quality_threshold}"
        )
        state["current_step"] = "decide_next"

    append_decision(
        state,
        phase="reflect",
        message="Evaluated tool output",
        data={
            "quality_score": quality_score,
            "threshold": quality_threshold,
            "goal_met": goal_met,
        },
    )

    emit_phase_event(
        state,
        phase="reflect",
        node="evaluate_result",
        metadata={
            "quality_score": quality_score,
            "goal_met": goal_met,
            "quality_threshold": quality_threshold,
        },
    )

    return state


def decide_next_node(state: PlaybookState) -> PlaybookState:
    """
    RE-REASON phase: Decide next action based on results.

    This node determines whether to continue, loop back, or terminate.
    It embodies the "Re-reason" part of the Re^Re loop.

    For the prototype, we implement simple continuation logic.
    """
    budget_max = state["context"].get("budget_max", 1.0)
    remaining_budget = max(budget_max - state["budget_used"], 0.0)
    state["remaining_budget"] = remaining_budget

    max_steps = state["context"].get("max_steps", 10)
    steps_taken = len(state.get("steps_completed", []))

    quality_threshold = state["context"].get("quality_threshold", 0.7)
    quality_score = state.get("quality_score", 0.0)

    if state.get("error"):
        state["should_continue"] = False
        append_decision(
            state,
            phase="re-reason",
            message="Terminating due to fatal error",
            data={"error": state["error"]},
        )
        return state

    can_afford_more_steps = remaining_budget >= MIN_STEP_COST
    has_capacity = steps_taken < max_steps
    needs_retry = quality_score < quality_threshold

    should_loop = bool(can_afford_more_steps and has_capacity and needs_retry)
    state["should_continue"] = should_loop

    append_decision(
        state,
        phase="re-reason",
        message="Looping for another step"
        if should_loop
        else "Stopping execution",
        data={
            "quality_score": quality_score,
            "quality_threshold": quality_threshold,
            "remaining_budget": remaining_budget,
            "steps_taken": steps_taken,
            "max_steps": max_steps,
        },
    )

    emit_phase_event(
        state,
        phase="re-reason",
        node="decide_next",
        metadata={
            "remaining_budget": remaining_budget,
            "should_continue": should_loop,
            "steps_taken": steps_taken,
        },
    )

    return state


def should_continue(state: PlaybookState) -> str:
    """
    Conditional edge function: Determine if execution should continue.

    Returns:
        "continue" if should continue, "end" otherwise
    """
    return "continue" if state.get("should_continue", False) else "end"
