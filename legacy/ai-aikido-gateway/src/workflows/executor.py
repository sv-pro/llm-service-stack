"""
Playbook execution engine.

This module provides the main interface for executing playbooks with LangGraph.
"""

import uuid
from typing import Dict, Any, Optional

from langgraph.checkpoint.sqlite import SqliteSaver

from src.telemetry.re_re_events import ReReTelemetryEmitter

from .graphs import create_playbook_graph
from .state import PlaybookState, PlaybookConfig, create_initial_state
from .telemetry import TELEMETRY_CONTEXT_KEY


# Global checkpoint storage (will be initialized on first use)
_checkpoint_saver: Optional[SqliteSaver] = None
_telemetry_emitter = ReReTelemetryEmitter()


def get_checkpoint_saver(db_path: str = "./data/checkpoints.db") -> SqliteSaver:
    """
    Get or create the checkpoint saver.

    Args:
        db_path: Path to SQLite database for checkpoints

    Returns:
        SqliteSaver instance

    Note: Using async context manager for langgraph-checkpoint-sqlite 3.x compatibility
    """
    global _checkpoint_saver
    if _checkpoint_saver is None:
        # For langgraph-checkpoint-sqlite 3.x, use SqliteSaver with connection string
        import aiosqlite
        _checkpoint_saver = SqliteSaver.from_conn_string(f"sqlite:///{db_path}")
    return _checkpoint_saver


async def execute_playbook(
    intent: str,
    config: Optional[PlaybookConfig] = None,
    context: Optional[Dict[str, Any]] = None,
    thread_id: Optional[str] = None,
) -> PlaybookState:
    """
    Execute a playbook workflow.

    This is the main entry point for playbook execution. It:
    1. Creates initial state
    2. Compiles the workflow graph
    3. Executes the Re^Re loop
    4. Returns final state with results

    Args:
        intent: User intent/request to execute
        config: Playbook configuration (optional, uses defaults if not provided)
        context: Additional execution context (optional)
        thread_id: Thread ID for checkpoint storage (optional, generated if not provided)

    Returns:
        Final PlaybookState after execution

    Example:
        >>> config = PlaybookConfig(max_steps=5, budget_max=0.5)
        >>> result = await execute_playbook(
        ...     intent="calculate 2 + 2",
        ...     config=config
        ... )
        >>> print(result["artifacts"][-1]["output"])
        {'result': 4, 'success': True}
    """
    # Use default config if not provided
    if config is None:
        config = PlaybookConfig()

    # Generate thread ID if not provided
    if thread_id is None:
        thread_id = f"playbook_{uuid.uuid4()}"

    # Create initial state
    initial_state = create_initial_state(intent, config, context)
    initial_state["context"]["thread_id"] = thread_id

    telemetry_session = _telemetry_emitter.create_session(
        thread_id=thread_id,
        intent=intent,
        base_metadata={
            "config": config.model_dump(),
            "input_context": context or {},
        },
    )
    if telemetry_session:
        initial_state["context"][TELEMETRY_CONTEXT_KEY] = telemetry_session

    # Create workflow graph
    workflow = create_playbook_graph()

    # Compile graph with checkpoint support
    if config.checkpoint_enabled:
        checkpointer = get_checkpoint_saver()
        app = workflow.compile(checkpointer=checkpointer)
    else:
        app = workflow.compile()

    # Execute workflow
    run_config = {"configurable": {"thread_id": thread_id}}

    try:
        final_state = await app.ainvoke(initial_state, run_config)
        return final_state
    except Exception as e:
        # Handle execution errors
        initial_state["error"] = str(e)
        initial_state["should_continue"] = False
        return initial_state


async def get_execution_history(thread_id: str) -> list:
    """
    Get execution history for a playbook thread.

    Args:
        thread_id: Thread ID to get history for

    Returns:
        List of checkpoint states
    """
    checkpointer = get_checkpoint_saver()
    history = []

    async for state in checkpointer.alist({"configurable": {"thread_id": thread_id}}):
        history.append(state)

    return history


async def rollback_to_checkpoint(
    thread_id: str, checkpoint_id: str
) -> Optional[PlaybookState]:
    """
    Rollback execution to a specific checkpoint.

    Args:
        thread_id: Thread ID
        checkpoint_id: Checkpoint ID to rollback to

    Returns:
        State at checkpoint, or None if not found
    """
    checkpointer = get_checkpoint_saver()

    try:
        checkpoint = await checkpointer.aget(
            {"configurable": {"thread_id": thread_id, "checkpoint_id": checkpoint_id}}
        )
        if checkpoint:
            return checkpoint.values
        return None
    except Exception:
        return None
