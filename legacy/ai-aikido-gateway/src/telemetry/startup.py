from __future__ import annotations

from typing import Optional

from .re_re_events import ReReTelemetryEmitter

_emitter: Optional[ReReTelemetryEmitter] = None


def get_emitter() -> Optional[ReReTelemetryEmitter]:
    return _emitter


def initialize_emitter() -> Optional[ReReTelemetryEmitter]:
    global _emitter
    if _emitter is None:
        _emitter = ReReTelemetryEmitter()
    return _emitter
