#!/usr/bin/env python3
"""
Demo script for Tool Registry and Adapters.

Demonstrates Week 10 implementation:
- Tool registration and execution
- LLM, HTTP, and Python function tools
- Integration with playbook workflows
"""

import asyncio
import os
from typing import Dict

from src.tools import ToolRegistry
from src.tools.adapters import LLMTool, HTTPTool, PythonFunctionTool
from src.workflows import execute_playbook, PlaybookConfig


# ============================================================================
# DEMO 1: Basic Tool Registry
# ============================================================================


async def demo_basic_registry():
    """Demo: Register and execute tools"""
    print("\n" + "=" * 70)
    print("DEMO 1: Basic Tool Registry")
    print("=" * 70)

    registry = ToolRegistry()

    # Define a simple Python function tool
    def add_numbers(a: int, b: int) -> int:
        """Add two numbers together"""
        return a + b

    def multiply_numbers(x: int, y: int) -> int:
        """Multiply two numbers"""
        return x * y

    # Register tools
    registry.register(PythonFunctionTool("add", add_numbers, cost_per_call=0.001))
    registry.register(
        PythonFunctionTool("multiply", multiply_numbers, cost_per_call=0.001)
    )

    print(f"\n✓ Registered tools: {', '.join(registry.list_tools())}")

    # Execute tools
    result1 = await registry.execute("add", {"a": 5, "b": 3})
    print(f"\n✓ add(5, 3) = {result1.data['result']}")
    print(f"  Cost: ${result1.cost:.4f}")

    result2 = await registry.execute("multiply", {"x": 4, "y": 7})
    print(f"\n✓ multiply(4, 7) = {result2.data['result']}")
    print(f"  Cost: ${result2.cost:.4f}")


# ============================================================================
# DEMO 2: Async Python Functions
# ============================================================================


async def demo_async_functions():
    """Demo: Async Python function tools"""
    print("\n" + "=" * 70)
    print("DEMO 2: Async Python Function Tools")
    print("=" * 70)

    registry = ToolRegistry()

    # Define async function
    async def fetch_data(query: str) -> Dict:
        """Simulate async data fetching"""
        await asyncio.sleep(0.1)  # Simulate I/O
        return {
            "query": query,
            "results": [f"Result {i}" for i in range(1, 4)],
            "count": 3,
        }

    # Register async tool
    registry.register(PythonFunctionTool("fetch", fetch_data, cost_per_call=0.005))

    print(f"\n✓ Registered async tool: fetch")

    # Execute async tool
    result = await registry.execute("fetch", {"query": "test query"})
    print(f"\n✓ fetch('test query'):")
    print(f"  Results: {result.data['result']['results']}")
    print(f"  Count: {result.data['result']['count']}")
    print(f"  Cost: ${result.cost:.4f}")


# ============================================================================
# DEMO 3: HTTP Tool Adapter
# ============================================================================


async def demo_http_tool():
    """Demo: HTTP API tool"""
    print("\n" + "=" * 70)
    print("DEMO 3: HTTP Tool Adapter")
    print("=" * 70)

    registry = ToolRegistry()

    # Register HTTP tool for JSONPlaceholder API
    registry.register(
        HTTPTool(
            name="get_post",
            base_url="https://jsonplaceholder.typicode.com",
            method="GET",
            description="Fetch a post from JSONPlaceholder",
        )
    )

    print(f"\n✓ Registered HTTP tool: get_post")

    # Execute HTTP tool
    result = await registry.execute("get_post", {"path": "posts/1"})

    if result.success:
        post = result.data["response"]
        print(f"\n✓ Fetched post #{post['id']}:")
        print(f"  Title: {post['title'][:50]}...")
        print(f"  Status: {result.data['status_code']}")
        print(f"  Time: {result.metadata['elapsed_ms']:.1f}ms")
    else:
        print(f"\n✗ HTTP request failed: {result.error}")


# ============================================================================
# DEMO 4: LLM Tool (if API key available)
# ============================================================================


async def demo_llm_tool():
    """Demo: LLM tool adapter"""
    print("\n" + "=" * 70)
    print("DEMO 4: LLM Tool Adapter")
    print("=" * 70)

    # Check if API key is available
    if not os.getenv("OPENAI_API_KEY"):
        print(
            "\n⊘ Skipping LLM demo - OPENAI_API_KEY not set"
        )
        print("  Set OPENAI_API_KEY to enable this demo")
        return

    registry = ToolRegistry()

    # Register LLM tool
    registry.register(
        LLMTool(
            model="gpt-3.5-turbo",
            name="chat_gpt",
            description="Chat with GPT-3.5",
            temperature=0.7,
            max_tokens=100,
        )
    )

    print(f"\n✓ Registered LLM tool: chat_gpt")

    # Execute LLM tool
    result = await registry.execute(
        "chat_gpt",
        {
            "messages": [
                {"role": "user", "content": "What is 2+2? Reply in one sentence."}
            ]
        },
    )

    if result.success:
        print(f"\n✓ LLM Response:")
        print(f"  {result.data['content']}")
        print(f"  Model: {result.data['model']}")
        print(f"  Tokens: {result.data['usage']['total_tokens']}")
        print(f"  Cost: ${result.cost:.6f}")
    else:
        print(f"\n✗ LLM request failed: {result.error}")


# ============================================================================
# DEMO 5: ToolRegistry with Playbook Workflow
# ============================================================================


async def demo_registry_with_workflow():
    """Demo: Integrate ToolRegistry with playbook workflow"""
    print("\n" + "=" * 70)
    print("DEMO 5: ToolRegistry with Playbook Workflow")
    print("=" * 70)

    # Create and populate registry
    registry = ToolRegistry()

    def calculator(expression: str) -> float:
        """Evaluate a mathematical expression"""
        try:
            # Safe eval - only for demo purposes
            return eval(expression)
        except Exception as e:
            raise ValueError(f"Invalid expression: {e}")

    def search(query: str) -> Dict:
        """Search for information"""
        return {
            "query": query,
            "results": [
                f"Result 1 for '{query}'",
                f"Result 2 for '{query}'",
                f"Result 3 for '{query}'",
            ],
        }

    def echo(message: str) -> str:
        """Echo back a message"""
        return message

    # Register tools
    registry.register(PythonFunctionTool("calculator", calculator, cost_per_call=0.001))
    registry.register(PythonFunctionTool("search", search, cost_per_call=0.01))
    registry.register(PythonFunctionTool("echo", echo, cost_per_call=0.0001))

    print(f"\n✓ Registered {len(registry)} tools for workflow")

    # Create playbook config with registry
    config = PlaybookConfig(max_steps=3, budget_max=0.05)

    # Execute workflow with registry in context
    print(f"\n✓ Executing playbook: 'calculate 10 + 20'")
    result = await execute_playbook(
        intent="calculate 10 + 20",
        config=config,
        context={"tool_registry": registry},
    )

    print(f"\n✓ Workflow completed:")
    print(f"  Steps: {len(result['steps_completed'])}")
    print(f"  Budget used: ${result['budget_used']:.6f}")
    print(f"  Quality score: {result['quality_score']:.2f}")
    print(f"  Decision log entries: {len(result.get('decision_log', []))}")

    if result["artifacts"]:
        last_artifact = result["artifacts"][-1]
        print(f"\n✓ Final result:")
        print(f"  Tool: {last_artifact['tool']}")
        print(f"  Output: {last_artifact['output']}")


# ============================================================================
# DEMO 6: Error Handling
# ============================================================================


async def demo_error_handling():
    """Demo: Tool error handling"""
    print("\n" + "=" * 70)
    print("DEMO 6: Error Handling")
    print("=" * 70)

    registry = ToolRegistry()

    def failing_function(x: int) -> int:
        """A function that always fails"""
        raise ValueError("This function intentionally fails")

    registry.register(PythonFunctionTool("failer", failing_function))

    print(f"\n✓ Registered failing tool")

    # Execute failing tool
    result = await registry.execute("failer", {"x": 5})

    print(f"\n✓ Error handled gracefully:")
    print(f"  Success: {result.success}")
    print(f"  Error: {result.error}")
    print(f"  Exception type: {result.metadata['exception_type']}")

    # Try to execute non-existent tool
    print(f"\n✓ Attempting to execute non-existent tool...")
    try:
        await registry.execute("nonexistent", {})
    except Exception as e:
        print(f"  Caught exception: {type(e).__name__}: {e}")


# ============================================================================
# Main
# ============================================================================


async def main():
    """Run all demos"""
    print("\n" + "=" * 70)
    print("🧭 AI Aikido Gateway — Tool Registry Demo (Week 10)")
    print("=" * 70)
    print("\nDemonstrating:")
    print("  • Tool registration and execution")
    print("  • Python function adapters (sync & async)")
    print("  • HTTP API adapter")
    print("  • LLM adapter (if API key available)")
    print("  • Workflow integration")
    print("  • Error handling")

    await demo_basic_registry()
    await demo_async_functions()
    await demo_http_tool()
    await demo_llm_tool()
    await demo_registry_with_workflow()
    await demo_error_handling()

    print("\n" + "=" * 70)
    print("✓ All demos completed successfully!")
    print("=" * 70)
    print("\nNext steps:")
    print("  • Week 11-12: Implement three-path API (Semantic, Syntactic, Intent)")
    print("  • Add more tool adapters (database, file system, etc.)")
    print("  • Implement LLM-based intent analysis")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
