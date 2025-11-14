"""
Tests for tool registry and tool adapters.
"""

import pytest
from src.tools import Tool, ToolResult, ToolNotFoundError, ToolRegistry
from src.tools.adapters import PythonFunctionTool, HTTPTool, MCPTool


pytestmark = pytest.mark.asyncio


# Test helper: Simple test tool
class MockTool(Tool):
    """Mock tool for testing"""

    def __init__(self, name: str = "mock", cost: float = 0.01):
        super().__init__(name, f"Mock tool: {name}")
        self.cost = cost
        self.call_count = 0

    async def execute(self, input_data):
        self.call_count += 1
        return ToolResult(
            success=True,
            data={"result": f"mock_{input_data.get('value', '')}"},
            cost=self.cost,
        )


# ToolRegistry Tests


async def test_tool_registry_register():
    """Test registering tools"""
    registry = ToolRegistry()
    tool = MockTool("test_tool")

    registry.register(tool)

    assert len(registry) == 1
    assert "test_tool" in registry
    assert registry.has_tool("test_tool")


async def test_tool_registry_duplicate_registration():
    """Test that duplicate registration raises error"""
    registry = ToolRegistry()
    tool = MockTool("duplicate")

    registry.register(tool)

    with pytest.raises(ValueError, match="already registered"):
        registry.register(tool)


async def test_tool_registry_execute():
    """Test executing a registered tool"""
    registry = ToolRegistry()
    tool = MockTool("exec_tool")
    registry.register(tool)

    result = await registry.execute("exec_tool", {"value": "test"})

    assert result.success
    assert result.data["result"] == "mock_test"
    assert tool.call_count == 1


async def test_tool_registry_execute_not_found():
    """Test executing non-existent tool"""
    registry = ToolRegistry()

    with pytest.raises(ToolNotFoundError, match="not found"):
        await registry.execute("nonexistent", {})


async def test_tool_registry_unregister():
    """Test unregistering tools"""
    registry = ToolRegistry()
    tool = MockTool("remove_me")
    registry.register(tool)

    assert "remove_me" in registry

    registry.unregister("remove_me")

    assert "remove_me" not in registry
    assert len(registry) == 0


async def test_tool_registry_unregister_not_found():
    """Test unregistering non-existent tool"""
    registry = ToolRegistry()

    with pytest.raises(ToolNotFoundError):
        registry.unregister("nonexistent")


async def test_tool_registry_list_tools():
    """Test listing registered tools"""
    registry = ToolRegistry()
    registry.register(MockTool("tool1"))
    registry.register(MockTool("tool2"))
    registry.register(MockTool("tool3"))

    tools = registry.list_tools()

    assert len(tools) == 3
    assert "tool1" in tools
    assert "tool2" in tools
    assert "tool3" in tools


async def test_tool_registry_get_tool_descriptions():
    """Test getting tool metadata"""
    registry = ToolRegistry()
    registry.register(MockTool("described_tool"))

    descriptions = registry.get_tool_descriptions()

    assert len(descriptions) == 1
    assert descriptions[0]["name"] == "described_tool"
    assert "description" in descriptions[0]


async def test_tool_registry_clear():
    """Test clearing all tools"""
    registry = ToolRegistry()
    registry.register(MockTool("tool1"))
    registry.register(MockTool("tool2"))

    assert len(registry) == 2

    registry.clear()

    assert len(registry) == 0
    assert registry.list_tools() == []


async def test_tool_registry_error_handling():
    """Test registry handles tool execution errors gracefully"""

    class FailingTool(Tool):
        def __init__(self):
            super().__init__("failing", "Tool that always fails")

        async def execute(self, input_data):
            raise RuntimeError("Tool execution failed")

    registry = ToolRegistry()
    registry.register(FailingTool())

    result = await registry.execute("failing", {})

    assert not result.success
    assert result.error == "Tool execution failed"
    assert result.metadata["exception_type"] == "RuntimeError"


# PythonFunctionTool Tests


async def test_python_function_tool_sync():
    """Test wrapping synchronous Python function"""

    def add_numbers(a: int, b: int) -> int:
        """Add two numbers"""
        return a + b

    tool = PythonFunctionTool("add", add_numbers)

    assert tool.name == "add"
    assert "Add two numbers" in tool.description

    result = await tool.execute({"a": 2, "b": 3})

    assert result.success
    assert result.data["result"] == 5


async def test_python_function_tool_async():
    """Test wrapping asynchronous Python function"""

    async def fetch_data(query: str) -> dict:
        """Fetch data asynchronously"""
        return {"query": query, "data": [1, 2, 3]}

    tool = PythonFunctionTool("fetch", fetch_data)

    result = await tool.execute({"query": "test"})

    assert result.success
    assert result.data["result"]["query"] == "test"
    assert result.data["result"]["data"] == [1, 2, 3]


async def test_python_function_tool_with_cost():
    """Test function tool with custom cost"""

    def expensive_function(x: int) -> int:
        return x * 2

    tool = PythonFunctionTool("expensive", expensive_function, cost_per_call=0.05)

    result = await tool.execute({"x": 10})

    assert result.success
    assert result.cost == 0.05


async def test_python_function_tool_error_handling():
    """Test function tool handles errors"""

    def failing_function(x: int) -> int:
        raise ValueError("Invalid input")

    tool = PythonFunctionTool("failer", failing_function)

    result = await tool.execute({"x": 5})

    assert not result.success
    assert "Invalid input" in result.error


# HTTPTool Tests


async def test_http_tool_initialization():
    """Test HTTP tool initialization"""
    tool = HTTPTool(
        name="api_call",
        base_url="https://api.example.com",
        method="POST",
        default_headers={"Authorization": "Bearer token"},
    )

    assert tool.name == "api_call"
    assert tool.base_url == "https://api.example.com"
    assert tool.method == "POST"
    assert tool.default_headers["Authorization"] == "Bearer token"


# MCPTool Tests


async def test_mcp_tool_stub():
    """Test MCP tool stub implementation"""
    tool = MCPTool("mcp_test", "https://mcp.example.com")

    result = await tool.execute({"action": "test_action", "parameters": {"key": "value"}})

    assert result.success
    assert "stub" in result.data["result"]
    assert result.metadata["implementation_status"] == "stub"
    assert result.metadata["planned_phase"] == "Phase 4"
