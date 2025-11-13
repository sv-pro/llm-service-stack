"""
Tool registry for managing and executing tools.

The ToolRegistry is the central hub for tool management in the playbook system.
"""

from typing import Dict, List, Optional
from .base import Tool, ToolResult, ToolNotFoundError


class ToolRegistry:
    """
    Registry for managing and executing tools.

    The registry maintains a collection of tools and provides methods to:
    - Register new tools
    - Execute tools by name
    - List available tools
    - Get tool metadata
    """

    def __init__(self):
        """Initialize empty tool registry"""
        self._tools: Dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        """
        Register a tool in the registry.

        Args:
            tool: Tool instance to register

        Raises:
            ValueError: If a tool with the same name already exists
        """
        if tool.name in self._tools:
            raise ValueError(f"Tool '{tool.name}' is already registered")

        self._tools[tool.name] = tool

    def unregister(self, tool_name: str) -> None:
        """
        Remove a tool from the registry.

        Args:
            tool_name: Name of tool to remove

        Raises:
            ToolNotFoundError: If tool doesn't exist
        """
        if tool_name not in self._tools:
            raise ToolNotFoundError(f"Tool '{tool_name}' not found")

        del self._tools[tool_name]

    async def execute(
        self, tool_name: str, input_data: Dict, validate: bool = True
    ) -> ToolResult:
        """
        Execute a tool by name.

        Args:
            tool_name: Name of the tool to execute
            input_data: Input parameters for the tool
            validate: Whether to validate input/output schemas (default: True)

        Returns:
            ToolResult from tool execution

        Raises:
            ToolNotFoundError: If tool doesn't exist
            Exception: If tool execution fails
        """
        tool = self._tools.get(tool_name)
        if not tool:
            raise ToolNotFoundError(f"Tool '{tool_name}' not found")

        # Validate input schema
        if validate:
            tool.validate_input(input_data)

        # Execute tool
        try:
            result = await tool.execute(input_data)

            # Validate output schema
            if validate and result.success:
                tool.validate_output(result.data)

            return result

        except Exception as e:
            # Return error result instead of raising
            return ToolResult(
                success=False,
                data={},
                error=str(e),
                metadata={"tool": tool_name, "exception_type": type(e).__name__},
            )

    def get_tool(self, tool_name: str) -> Optional[Tool]:
        """
        Get a tool by name.

        Args:
            tool_name: Name of the tool

        Returns:
            Tool instance or None if not found
        """
        return self._tools.get(tool_name)

    def list_tools(self) -> List[str]:
        """
        List all registered tool names.

        Returns:
            List of tool names
        """
        return list(self._tools.keys())

    def get_tool_descriptions(self) -> List[Dict]:
        """
        Get metadata for all registered tools.

        Returns:
            List of tool metadata dictionaries
        """
        return [tool.to_dict() for tool in self._tools.values()]

    def has_tool(self, tool_name: str) -> bool:
        """
        Check if a tool is registered.

        Args:
            tool_name: Name of the tool

        Returns:
            True if tool exists, False otherwise
        """
        return tool_name in self._tools

    def clear(self) -> None:
        """Remove all tools from the registry"""
        self._tools.clear()

    def __len__(self) -> int:
        """Return number of registered tools"""
        return len(self._tools)

    def __contains__(self, tool_name: str) -> bool:
        """Check if tool exists using 'in' operator"""
        return tool_name in self._tools
