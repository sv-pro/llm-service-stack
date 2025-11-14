"""
Python function tool adapter.

Allows wrapping arbitrary Python functions as tools.
"""

from typing import Dict, Any, Callable, Optional
import inspect
from ..base import Tool, ToolResult


class PythonFunctionTool(Tool):
    """
    Tool adapter for Python functions.

    Wraps a Python function (sync or async) as a tool that can be executed
    in the playbook workflow.
    """

    def __init__(
        self,
        name: str,
        func: Callable,
        description: str = None,
        cost_per_call: float = 0.0,
    ):
        """
        Initialize Python function tool.

        Args:
            name: Tool name
            func: Python function to wrap (can be sync or async)
            description: Tool description (uses function docstring if not provided)
            cost_per_call: Fixed cost per function call (default: 0.0)
        """
        self.func = func
        self.cost_per_call = cost_per_call
        self.is_async = inspect.iscoroutinefunction(func)

        # Use function docstring if no description provided
        tool_description = description or func.__doc__ or f"Python function: {name}"

        # Extract function signature for schema
        sig = inspect.signature(func)
        input_properties = {}
        required_params = []

        for param_name, param in sig.parameters.items():
            # Skip self and cls parameters
            if param_name in ("self", "cls"):
                continue

            input_properties[param_name] = {"type": "string"}

            # Mark as required if no default value
            if param.default == inspect.Parameter.empty:
                required_params.append(param_name)

        super().__init__(
            name=name,
            description=tool_description,
            input_schema={
                "type": "object",
                "properties": input_properties,
                "required": required_params,
            },
            output_schema={
                "type": "object",
                "properties": {
                    "result": {"description": "Function return value"},
                },
            },
        )

    async def execute(self, input_data: Dict[str, Any]) -> ToolResult:
        """
        Execute Python function.

        Args:
            input_data: Dictionary of function arguments

        Returns:
            ToolResult with function output
        """
        try:
            # Call function with input data as kwargs
            if self.is_async:
                result = await self.func(**input_data)
            else:
                result = self.func(**input_data)

            return ToolResult(
                success=True,
                data={"result": result},
                cost=self.cost_per_call,
                metadata={
                    "function": self.func.__name__,
                    "module": self.func.__module__,
                    "is_async": self.is_async,
                },
            )

        except Exception as e:
            return ToolResult(
                success=False,
                data={},
                error=str(e),
                metadata={
                    "function": self.func.__name__,
                    "exception_type": type(e).__name__,
                },
            )
