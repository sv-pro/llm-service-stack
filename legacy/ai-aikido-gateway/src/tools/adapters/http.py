"""
HTTP API tool adapter.

Allows calling external HTTP APIs as tools.
"""

from typing import Dict, Any, Optional
import httpx
from ..base import Tool, ToolResult


class HTTPTool(Tool):
    """
    Tool adapter for HTTP API calls.

    Supports GET, POST, PUT, DELETE, PATCH methods with configurable
    headers, authentication, and timeouts.
    """

    def __init__(
        self,
        name: str,
        base_url: str,
        method: str = "GET",
        default_headers: Optional[Dict[str, str]] = None,
        timeout: float = 30.0,
        description: str = None,
    ):
        """
        Initialize HTTP tool.

        Args:
            name: Tool name
            base_url: Base URL for API calls
            method: HTTP method (GET, POST, PUT, DELETE, PATCH)
            default_headers: Headers to include in all requests
            timeout: Request timeout in seconds
            description: Tool description
        """
        self.base_url = base_url.rstrip("/")
        self.method = method.upper()
        self.default_headers = default_headers or {}
        self.timeout = timeout

        tool_description = (
            description or f"HTTP {self.method} to {self.base_url}"
        )

        super().__init__(
            name=name,
            description=tool_description,
            input_schema={
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "API path"},
                    "params": {
                        "type": "object",
                        "description": "Query parameters",
                    },
                    "body": {"type": "object", "description": "Request body"},
                    "headers": {"type": "object", "description": "Request headers"},
                },
            },
            output_schema={
                "type": "object",
                "properties": {
                    "response": {"description": "Response data"},
                    "status_code": {"type": "integer"},
                },
            },
        )

    async def execute(self, input_data: Dict[str, Any]) -> ToolResult:
        """
        Execute HTTP request.

        Args:
            input_data: Dictionary with:
                - path: API path (optional, default: "")
                - params: Query parameters (optional)
                - body: Request body for POST/PUT/PATCH (optional)
                - headers: Additional headers (optional)

        Returns:
            ToolResult with API response
        """
        path = input_data.get("path", "")
        params = input_data.get("params", {})
        body = input_data.get("body")
        headers = {**self.default_headers, **input_data.get("headers", {})}

        # Build full URL
        url = f"{self.base_url}/{path.lstrip('/')}" if path else self.base_url

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.request(
                    method=self.method,
                    url=url,
                    params=params,
                    json=body if body else None,
                    headers=headers,
                )

                # Try to parse JSON response
                try:
                    response_data = response.json()
                except Exception:
                    # If not JSON, use text
                    response_data = response.text

                return ToolResult(
                    success=response.is_success,
                    data={
                        "response": response_data,
                        "status_code": response.status_code,
                        "headers": dict(response.headers),
                    },
                    cost=0.0,  # External API calls don't have LLM cost
                    metadata={
                        "url": str(response.url),
                        "method": self.method,
                        "elapsed_ms": response.elapsed.total_seconds() * 1000,
                    },
                )

        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                error=str(e),
                metadata={
                    "url": url,
                    "method": self.method,
                    "exception_type": type(e).__name__,
                },
            )
