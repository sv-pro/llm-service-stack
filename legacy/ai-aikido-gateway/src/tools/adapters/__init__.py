"""
Tool adapters for different execution contexts.

Provides adapters for:
- LLM calls (OpenAI, Anthropic, etc.)
- HTTP APIs
- MCP (Model Context Protocol)
- Python functions
"""

from .llm import LLMTool
from .http import HTTPTool
from .mcp import MCPTool
from .python_function import PythonFunctionTool

__all__ = [
    "LLMTool",
    "HTTPTool",
    "MCPTool",
    "PythonFunctionTool",
]
