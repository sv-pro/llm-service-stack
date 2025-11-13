"""
Custom FastAPI middleware for the AI Aikido Gateway.
"""

from __future__ import annotations

import logging
from typing import Callable, Awaitable
from uuid import uuid4

from fastapi import Request, Response
from starlette.types import ASGIApp, Receive, Scope, Send
from starlette.middleware.cors import CORSMiddleware as StarletteCORSMiddleware

from src.core.logging import logging_context


logger = logging.getLogger(__name__)


class WebSocketBypassCORSMiddleware:
    """
    Custom CORS middleware that applies CORS logic to HTTP requests only
    and completely bypasses WebSocket connections to prevent 403 Forbidden errors.
    """
    
    def __init__(
        self,
        app: ASGIApp,
        allow_origins=None,
        allow_credentials=False,
        allow_methods=None,
        allow_headers=None,
    ):
        self.app = app
        # self.allow_origins = allow_origins or ["*"]
        self.allow_origins = ["*"]
        self.allow_credentials = allow_credentials
        self.allow_methods = allow_methods or ["*"]
        self.allow_headers = allow_headers or ["*"]
    
    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        """Process request with trace ID in logging context."""
        if scope["type"] == "websocket":
            logger.info(f"TraceMiddleware: WebSocket connection to {scope.get('path')}")
            # For WebSocket, just pass through with a trace ID
            trace_id = str(uuid4())
            scope["state"] = {"trace_id": trace_id}
            await self.app(scope, receive, send)
            return
        
        # For HTTP requests, handle CORS manually
        logger.debug("CORS: Processing HTTP request")
        
        async def send_wrapper(message):
            if message["type"] == "http.response.start":
                headers = list(message.get("headers", []))
                
                # Add CORS headers
                headers.append((b"access-control-allow-origin", b"*"))
                headers.append((b"access-control-allow-credentials", b"true"))
                headers.append((b"access-control-allow-methods", b"*"))
                headers.append((b"access-control-allow-headers", b"*"))
                
                message["headers"] = headers
            
            await send(message)
        
        # Handle preflight requests
        if scope["method"] == "OPTIONS":
            await send_wrapper({
                "type": "http.response.start",
                "status": 200,
                "headers": [(b"content-length", b"0")],
            })
            await send({"type": "http.response.body", "body": b""})
            return
        
        await self.app(scope, receive, send_wrapper)


class TraceMiddleware:
    """
    Pure ASGI middleware for trace IDs that works with HTTP and WebSocket.
    """

    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ("http", "websocket"):
            await self.app(scope, receive, send)
            return

        # Generate trace ID
        headers = dict(scope.get("headers", []))
        trace_id = headers.get(b"x-trace-id", b"").decode() or uuid4().hex
        
        # Store in scope
        if "state" not in scope:
            scope["state"] = {}
        scope["state"]["correlation_id"] = trace_id

        if scope["type"] == "websocket":
            # WebSocket: just pass through
            await self.app(scope, receive, send)
        else:
            # HTTP: add trace header to response
            async def send_with_trace(message):
                if message["type"] == "http.response.start":
                    headers = list(message.get("headers", []))
                    headers.append((b"x-trace-id", trace_id.encode()))
                    message["headers"] = headers
                await send(message)

            with logging_context(trace_id):
                await self.app(scope, receive, send_with_trace)
