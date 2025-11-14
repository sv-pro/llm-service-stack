"""
WebSocket connection manager for Re^Re telemetry streams.

Routes register WebSocket connections per execution, and the telemetry
emitter broadcasts workflow events to all connected clients.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import WebSocket

logger = logging.getLogger(__name__)

_connections: Dict[str, List[WebSocket]] = {}
_lock = asyncio.Lock()
_connection_events: List[Dict[str, str]] = []


async def register_connection(execution_id: str, websocket: WebSocket) -> None:
    """Attach a WebSocket to an execution's subscriber list."""
    async with _lock:
        _connections.setdefault(execution_id, []).append(websocket)
        _connection_events.append(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "execution_id": execution_id,
                "event": "connected",
            }
        )
        del _connection_events[:-20]
    logger.info("WebSocket registered for execution %s", execution_id)


async def unregister_connection(execution_id: str, websocket: WebSocket) -> None:
    """Detach a WebSocket from the subscriber list."""
    async with _lock:
        if execution_id in _connections:
            try:
                _connections[execution_id].remove(websocket)
            except ValueError:
                pass
            if not _connections[execution_id]:
                del _connections[execution_id]
        _connection_events.append(
            {
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "execution_id": execution_id,
                "event": "disconnected",
            }
        )
        del _connection_events[:-20]
    logger.info("WebSocket unregistered for execution %s", execution_id)


async def broadcast_event(execution_id: str, payload: Dict[str, Any]) -> None:
    """Broadcast a telemetry payload to all listeners for an execution."""
    async with _lock:
        subscribers: Optional[List[WebSocket]] = list(_connections.get(execution_id, []))

    if not subscribers:
        return

    stale: List[WebSocket] = []
    for ws in subscribers:
        try:
            await ws.send_json(payload)
        except Exception as exc:  # pragma: no cover - network errors
            logger.warning("Failed to send telemetry payload: %s", exc)
            stale.append(ws)

    # Clean up failed sockets outside the send loop
    for ws in stale:
        await unregister_connection(execution_id, ws)


async def get_connection_snapshot() -> Dict[str, Any]:
    async with _lock:
        snapshot = {exec_id: len(sockets) for exec_id, sockets in _connections.items()}
        events = list(_connection_events)
    return {"connections": snapshot, "events": events}
