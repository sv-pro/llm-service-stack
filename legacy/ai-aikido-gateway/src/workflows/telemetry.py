"""
Helpers for emitting Re^Re telemetry events from workflow nodes.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from .state import PlaybookState

TELEMETRY_CONTEXT_KEY = "_re_re_telemetry_session"


def emit_phase_event(
    state: PlaybookState,
    *,
    phase: str,
    node: str,
    status: str = "completed",
    metadata: Optional[Dict[str, Any]] = None,
) -> None:
    """
    Emit a telemetry event for the current phase if a telemetry session exists.
    """

    context = state.get("context") or {}
    session = context.get(TELEMETRY_CONTEXT_KEY)
    if session is None:
        return

    try:
        session.emit(phase=phase, status=status, node=node, state=state, metadata=metadata)
    except Exception:  # pragma: no cover - telemetry failures must never break workflows
        import logging

        logging.getLogger(__name__).warning("Failed to emit Re^Re telemetry event", exc_info=True)
