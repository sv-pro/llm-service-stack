"""
Structured logging utilities for the AI Aikido Gateway.

Provides JSON-formatted logs and helpers for binding request-level correlation
IDs so that log streams can be traced per execution.
"""

from __future__ import annotations

import contextlib
import contextvars
import json
import logging
from datetime import UTC, datetime
from typing import Any, Dict, Iterable, Optional

_CORRELATION_ID = contextvars.ContextVar("gateway_correlation_id", default=None)

_RESERVED_KEYS: Iterable[str] = (
    "name",
    "msg",
    "args",
    "levelname",
    "levelno",
    "pathname",
    "filename",
    "module",
    "exc_info",
    "exc_text",
    "stack_info",
    "lineno",
    "funcName",
    "created",
    "msecs",
    "relativeCreated",
    "thread",
    "threadName",
    "processName",
    "process",
)


class JSONLogFormatter(logging.Formatter):
    """Format log records as JSON strings."""

    def format(self, record: logging.LogRecord) -> str:
        base: Dict[str, Any] = {
            "timestamp": datetime.fromtimestamp(record.created, tz=UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        correlation_id = _CORRELATION_ID.get()
        if correlation_id:
            base["correlation_id"] = correlation_id

        if record.exc_info:
            base["exc_info"] = self.formatException(record.exc_info)
        if record.stack_info:
            base["stack_info"] = record.stack_info

        for key, value in record.__dict__.items():
            if key not in _RESERVED_KEYS and key not in base:
                base[key] = value

        return json.dumps(base, default=str)


def configure_logging(level: int = logging.INFO) -> None:
    """
    Configure root logging to use JSON formatting.

    Args:
        level: Logging level for the root logger.
    """
    root_logger = logging.getLogger()
    root_logger.setLevel(level)

    for handler in list(root_logger.handlers):
        root_logger.removeHandler(handler)

    handler = logging.StreamHandler()
    handler.setFormatter(JSONLogFormatter())
    root_logger.addHandler(handler)


def bind_correlation_id(correlation_id: Optional[str]) -> Optional[contextvars.Token]:
    """
    Bind a correlation ID for downstream log records.

    Args:
        correlation_id: The ID to bind.

    Returns:
        Context variable token that can be used to reset the value.
    """
    if correlation_id is None:
        return None
    return _CORRELATION_ID.set(correlation_id)


def reset_correlation_id(token: Optional[contextvars.Token]) -> None:
    """
    Reset the correlation ID context variable using the provided token.
    """
    if token is None:
        return
    _CORRELATION_ID.reset(token)


@contextlib.contextmanager
def logging_context(correlation_id: Optional[str]):
    """
    Context manager that binds a correlation ID for the duration of the block.
    """
    token = bind_correlation_id(correlation_id)
    try:
        yield
    finally:
        reset_correlation_id(token)
