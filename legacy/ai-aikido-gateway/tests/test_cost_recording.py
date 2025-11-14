"""Tests for completion cost recording fallbacks in the API layer."""

from src.api.routes import _record_completion_cost
from src.core.context import RequestContext


def test_record_completion_cost_populates_ledger():
    """Ensure completion spend is captured when no proxy plugin recorded it."""
    ctx = RequestContext()
    response = {"usage": {"prompt_tokens": 18, "completion_tokens": 80}}

    _record_completion_cost(ctx, provider="openai", model_id="gpt-4", response_data=response)

    completion_entries = [entry for entry in ctx.cost_entries if entry.get("type") == "completion"]
    assert len(completion_entries) == 1
    summary = ctx.metadata.get("cost_summary") or {}
    assert summary.get("completion_cost")
    assert summary.get("total_cost") == summary.get("completion_cost")


def test_record_completion_cost_skips_when_entry_exists():
    """Avoid double-counting when proxy plugins already tracked spend."""
    ctx = RequestContext()
    ctx.add_cost_entry(
        {
            "type": "completion",
            "provider": "openai",
            "model": "gpt-4",
            "prompt_tokens": 10,
            "completion_tokens": 20,
            "cost": 0.001,
        }
    )

    response = {"usage": {"prompt_tokens": 25, "completion_tokens": 50}}
    _record_completion_cost(ctx, provider="openai", model_id="gpt-4", response_data=response)

    completion_entries = [entry for entry in ctx.cost_entries if entry.get("type") == "completion"]
    assert len(completion_entries) == 1
