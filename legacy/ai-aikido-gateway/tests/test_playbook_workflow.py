import pytest

from src.workflows import PlaybookConfig, execute_playbook


pytestmark = pytest.mark.asyncio


async def test_playbook_workflow_records_budget_events():
    config = PlaybookConfig(max_steps=2, budget_max=0.05)
    state = await execute_playbook("calculate 1 + 1", config=config)

    assert state["budget_events"], "Budget events should be recorded for each step"
    total_events = sum(event["amount"] for event in state["budget_events"])
    assert state["budget_used"] == pytest.approx(total_events)
    assert state["decision_log"], "Decision log should capture Re^Re phases"


async def test_playbook_workflow_loops_when_quality_below_threshold():
    config = PlaybookConfig(max_steps=3, budget_max=0.015, quality_threshold=0.95)
    state = await execute_playbook("calculate 2 + 2", config=config)

    assert len(state["artifacts"]) >= 2, "Should attempt multiple steps before stopping"
    assert state["should_continue"] is False
    assert state["quality_score"] < config.quality_threshold


async def test_playbook_workflow_stops_when_budget_guardrail_hits():
    config = PlaybookConfig(max_steps=2, budget_max=0.0005)
    state = await execute_playbook("calculate 5 + 5", config=config)

    assert state["budget_used"] == pytest.approx(0.0)
    assert "Budget" in (state.get("error") or state["tool_result"].get("error", ""))
    assert state["should_continue"] is False
