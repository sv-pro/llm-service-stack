"""
Playbook state models for workflow orchestration.

Implements the state structure for the Re^Re (Reflective Reasoning) loop.
"""

from typing import TypedDict, List, Dict, Any, Optional
from pydantic import BaseModel
from datetime import datetime, timezone


class BudgetEvent(TypedDict):
    """Tracks how much budget each step consumed."""

    step: int
    tool: str
    amount: float
    reason: str


class DecisionLogEntry(TypedDict, total=False):
    """Captures reasoning/decision making telemetry for each phase."""

    phase: str
    message: str
    data: Dict[str, Any]


class PlanStep(TypedDict, total=False):
    """Represents a planned action in the playbook."""

    step: int
    tool: str
    goal: str
    metadata: Dict[str, Any]


class PlaybookState(TypedDict, total=False):
    """
    State for playbook workflow execution.

    The Re^Re Loop:
    - Reason: analyze_intent extracts parameters and plans execution
    - Act: execute_tool performs the action
    - Reflect: evaluate_result scores quality and checks goals
    - Re-reason: decide_next determines if more steps needed or adjustments required
    """

    # Core state
    intent: str  # Original user intent/request
    context: Dict[str, Any]  # Execution context (model, params, etc.)
    steps_completed: List[str]  # History of executed steps
    artifacts: List[Dict[str, Any]]  # Generated artifacts from each step
    budget_used: float  # Total cost incurred (USD)
    budget_events: List[BudgetEvent]  # Per-step budget consumption
    remaining_budget: float  # Budget still available
    plan: List[PlanStep]  # Planned steps for execution
    decision_log: List[DecisionLogEntry]  # Trace of reasoning decisions

    # Control flow
    current_step: str  # Current step identifier
    should_continue: bool  # Whether to continue execution
    error: Optional[str]  # Error message if execution failed

    # Reflection (Re^Re loop)
    quality_score: float  # Quality evaluation (0.0-1.0)
    improvement_suggestions: List[str]  # Insights for future improvements
    reasoning_tokens: int  # Tokens used in reasoning steps

    # Tool execution
    selected_tool: str  # Currently selected tool
    tool_input: Dict[str, Any]  # Input for tool execution
    tool_result: Dict[str, Any]  # Result from tool execution


class PlaybookConfig(BaseModel):
    """Configuration for playbook execution"""

    max_steps: int = 10  # Maximum execution steps
    budget_max: float = 1.0  # Maximum budget in USD
    quality_threshold: float = 0.7  # Minimum quality score to accept
    timeout_seconds: int = 300  # Maximum execution time

    # Model selection
    reasoning_model: str = "gpt-4"  # Model for reasoning steps
    action_model: str = "gpt-3.5-turbo"  # Model for actions
    evaluation_model: str = "gpt-3.5-turbo"  # Model for evaluation

    # Checkpoint settings
    checkpoint_enabled: bool = False  # Enable checkpoint storage (disabled by default for compatibility)
    checkpoint_interval: int = 1  # Checkpoint every N steps


def create_initial_state(
    intent: str, config: PlaybookConfig, context: Optional[Dict[str, Any]] = None
) -> PlaybookState:
    """
    Create initial playbook state.

    Args:
        intent: User intent/request
        config: Playbook configuration
        context: Additional context (optional)

    Returns:
        Initialized PlaybookState
    """
    return PlaybookState(
        intent=intent,
        context={
            **({} if context is None else context),
            "max_steps": config.max_steps,
            "budget_max": config.budget_max,
            "quality_threshold": config.quality_threshold,
            "timeout_seconds": config.timeout_seconds,
            "reasoning_model": config.reasoning_model,
            "action_model": config.action_model,
            "evaluation_model": config.evaluation_model,
        },
        steps_completed=[],
        artifacts=[],
        budget_used=0.0,
        budget_events=[],
        remaining_budget=config.budget_max,
        plan=[],
        decision_log=[],
        current_step="analyze_intent",
        should_continue=True,
        error=None,
        quality_score=0.0,
        improvement_suggestions=[],
        reasoning_tokens=0,
        selected_tool="",
        tool_input={},
        tool_result={},
    )


def record_budget_event(
    state: PlaybookState, tool: str, amount: float, reason: str, step: Optional[int] = None
) -> None:
    """
    Record a budget event and keep aggregate fields in sync.
    """

    events = state.setdefault("budget_events", [])
    event_step = step if step is not None else len(state.get("steps_completed", [])) + 1
    events.append(
        {
            "step": event_step,
            "tool": tool,
            "amount": round(amount, 6),
            "reason": reason,
        }
    )

    state["budget_used"] = round(sum(event["amount"] for event in events), 6)
    budget_max = state.get("context", {}).get("budget_max", state["budget_used"])
    state["remaining_budget"] = max(budget_max - state["budget_used"], 0.0)


def append_decision(
    state: PlaybookState, phase: str, message: str, data: Optional[Dict[str, Any]] = None
) -> None:
    """
    Store a structured decision log entry for observability.
    """

    decision = {"phase": phase, "message": message}
    if data:
        decision["data"] = data
    decision.setdefault(
        "timestamp", datetime.now(timezone.utc).isoformat(timespec="seconds")
    )
    decision.setdefault("step", len(state.get("steps_completed", [])) + 1)

    state.setdefault("decision_log", []).append(decision)
