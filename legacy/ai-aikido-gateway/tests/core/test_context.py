"""Tests for RequestContext helpers."""

import pytest

from src.core.context import RequestContext


def test_add_cost_entry_accumulates_totals():
    """Ensure add_cost_entry maintains per-type + total summaries."""
    ctx = RequestContext()

    ctx.add_cost_entry(
        {
            "type": "embedding",
            "cost": 0.0001,
            "prompt_tokens": 12,
        }
    )
    ctx.add_cost_entry(
        {
            "type": "completion",
            "cost": 0.003,
            "prompt_tokens": 20,
            "completion_tokens": 5,
        }
    )
    ctx.add_cost_entry(
        {
            "type": "completion",
            "cost": 0.0015,
            "prompt_tokens": 10,
        }
    )

    assert len(ctx.cost_entries) == 3
    summary = ctx.metadata["cost_summary"]

    assert summary["total_cost"] == pytest.approx(0.0046)
    assert summary["embedding_cost"] == pytest.approx(0.0001)
    assert summary["completion_cost"] == pytest.approx(0.0045)
    assert summary["embedding_tokens"] == 12
    assert summary["completion_tokens"] == 30
    assert summary.get("completion_completion_tokens", 0) == 5


def test_add_cost_entry_ignores_empty_payloads():
    """Empty payloads should not mutate context."""
    ctx = RequestContext()
    ctx.add_cost_entry({})
    ctx.add_cost_entry(None)  # type: ignore[arg-type]

    assert ctx.cost_entries == []
    assert "cost_summary" not in ctx.metadata
