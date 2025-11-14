"""
LangGraph workflow definitions for playbook execution.

This module creates the state graph that orchestrates the Re^Re loop.
"""

from langgraph.graph import StateGraph, END
from .state import PlaybookState
from .nodes import (
    analyze_intent_node,
    execute_tool_node,
    evaluate_result_node,
    decide_next_node,
    should_continue,
)


def create_playbook_graph() -> StateGraph:
    """
    Create the playbook execution graph.

    Graph flow implements the Re^Re (Reflective Reasoning) loop:

    ```
    START
      ↓
    analyze_intent (REASON)
      ↓
    execute_tool (ACT)
      ↓
    evaluate_result (REFLECT)
      ↓
    decide_next (RE-REASON)
      ↓
    [should_continue?]
      ├─ Yes → analyze_intent (loop back)
      └─ No → END
    ```

    Returns:
        Configured StateGraph ready for compilation
    """
    # Create graph with PlaybookState
    workflow = StateGraph(PlaybookState)

    # Add nodes (Re^Re cycle)
    workflow.add_node("analyze_intent", analyze_intent_node)  # REASON
    workflow.add_node("execute_tool", execute_tool_node)  # ACT
    workflow.add_node("evaluate_result", evaluate_result_node)  # REFLECT
    workflow.add_node("decide_next", decide_next_node)  # RE-REASON

    # Add edges
    workflow.add_edge("analyze_intent", "execute_tool")
    workflow.add_edge("execute_tool", "evaluate_result")
    workflow.add_edge("evaluate_result", "decide_next")

    # Conditional edge: continue or end?
    workflow.add_conditional_edges(
        "decide_next",
        should_continue,
        {
            "continue": "analyze_intent",  # Loop back to REASON
            "end": END,  # Terminate
        },
    )

    # Set entry point
    workflow.set_entry_point("analyze_intent")

    return workflow
