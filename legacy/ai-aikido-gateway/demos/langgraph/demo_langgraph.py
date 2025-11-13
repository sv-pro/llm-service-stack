#!/usr/bin/env python3
"""
Demo script for LangGraph playbook execution prototype.

This demonstrates the Re^Re (Reflective Reasoning) loop in action.
"""

import asyncio
import json
from src.workflows import execute_playbook, PlaybookConfig


async def demo_calculator():
    """Demo: Calculator tool"""
    print("\n" + "=" * 60)
    print("DEMO 1: Calculator Tool")
    print("=" * 60)

    result = await execute_playbook(
        intent="calculate 2 + 2",
        config=PlaybookConfig(max_steps=3, budget_max=0.1),
    )

    print(f"\n✓ Intent: {result['intent']}")
    print(f"✓ Steps completed: {len(result['steps_completed'])}")
    print(f"✓ Budget used: ${result['budget_used']:.4f}")
    print(f"✓ Quality score: {result['quality_score']:.2f}")

    if result["artifacts"]:
        print(f"\n✓ Result: {result['artifacts'][-1]['output']}")

    if result.get("error"):
        print(f"\n✗ Error: {result['error']}")


async def demo_search():
    """Demo: Search tool"""
    print("\n" + "=" * 60)
    print("DEMO 2: Search Tool")
    print("=" * 60)

    result = await execute_playbook(
        intent="search for Python tutorials",
        config=PlaybookConfig(max_steps=5, budget_max=0.5),
    )

    print(f"\n✓ Intent: {result['intent']}")
    print(f"✓ Steps completed: {len(result['steps_completed'])}")
    print(f"✓ Budget used: ${result['budget_used']:.4f}")
    print(f"✓ Quality score: {result['quality_score']:.2f}")

    if result["artifacts"]:
        print(f"\n✓ Result: {json.dumps(result['artifacts'][-1]['output'], indent=2)}")


async def demo_echo():
    """Demo: Echo tool (default)"""
    print("\n" + "=" * 60)
    print("DEMO 3: Echo Tool (Default)")
    print("=" * 60)

    result = await execute_playbook(
        intent="Hello, AI Aikido Gateway!",
        config=PlaybookConfig(max_steps=2, budget_max=0.01),
    )

    print(f"\n✓ Intent: {result['intent']}")
    print(f"✓ Steps completed: {len(result['steps_completed'])}")
    print(f"✓ Budget used: ${result['budget_used']:.4f}")
    print(f"✓ Quality score: {result['quality_score']:.2f}")

    if result["artifacts"]:
        print(f"\n✓ Result: {result['artifacts'][-1]['output']}")


async def demo_budget_limit():
    """Demo: Budget limit enforcement"""
    print("\n" + "=" * 60)
    print("DEMO 4: Budget Limit Enforcement")
    print("=" * 60)

    result = await execute_playbook(
        intent="search for expensive results",
        config=PlaybookConfig(max_steps=10, budget_max=0.005),  # Very low budget
    )

    print(f"\n✓ Intent: {result['intent']}")
    print(f"✓ Steps completed: {len(result['steps_completed'])}")
    print(f"✓ Budget used: ${result['budget_used']:.4f}")
    print(f"✓ Budget max: ${result['context']['budget_max']:.4f}")

    if result.get("error"):
        print(f"\n⚠ Execution stopped: {result['error']}")
    else:
        print(f"\n✓ Quality score: {result['quality_score']:.2f}")


async def demo_full_state():
    """Demo: Full state inspection"""
    print("\n" + "=" * 60)
    print("DEMO 5: Full State Inspection")
    print("=" * 60)

    result = await execute_playbook(
        intent="calculate 10 * 5",
        config=PlaybookConfig(max_steps=3, budget_max=1.0),
    )

    print("\n📊 Complete Final State:")
    print(json.dumps(result, indent=2, default=str))


async def main():
    """Run all demos"""
    print("\n" + "=" * 60)
    print("🧭 AI Aikido Gateway — LangGraph Prototype Demo")
    print("=" * 60)
    print("\nDemonstrating the Re^Re (Reflective Reasoning) Loop:")
    print("  Reason → Act → Reflect → Re-reason → ∞")
    print("\n" + "=" * 60)

    # Run demos sequentially
    await demo_calculator()
    await demo_search()
    await demo_echo()
    await demo_budget_limit()
    await demo_full_state()

    print("\n" + "=" * 60)
    print("✓ All demos completed!")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Install LangGraph: pip install -r requirements.txt")
    print("  2. Implement real tool registry (Phase 3, Week 10)")
    print("  3. Add LLM-based reasoning (replace stubs in nodes.py)")
    print("  4. Implement three-path API (Week 11-12)")
    print("\n" + "=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
