"""
Playbook integration module for three-path API.

Provides common utilities for integrating playbook execution with API endpoints.
"""

import time
import uuid
from typing import Dict, Any, Optional

from src.workflows import execute_playbook, PlaybookConfig
from src.tools import ToolRegistry
from src.api.models import (
    PlaybookExecutionMetadata,
    ResponseUsageInfo,
    ResponseObject,
    Intent,
    IntentResponse,
)


async def execute_playbook_for_api(
    input_text: str,
    model: Optional[str] = None,
    budget_max: float = 1.0,
    max_steps: int = 10,
    tool_registry: Optional[ToolRegistry] = None,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Execute a playbook and return structured result for API.

    Args:
        input_text: User input/intent
        model: Model to use (optional)
        budget_max: Maximum budget in USD
        max_steps: Maximum execution steps
        tool_registry: Tool registry for execution
        context: Additional context

    Returns:
        Dictionary with execution results
    """
    # Create config
    config = PlaybookConfig(
        max_steps=max_steps,
        budget_max=budget_max,
        quality_threshold=0.7,
        timeout_seconds=300,
    )

    # Build execution context
    exec_context = {
        "model": model,
        **(context or {}),
    }

    # Add tool registry if provided
    if tool_registry:
        exec_context["tool_registry"] = tool_registry

    # Execute playbook
    result = await execute_playbook(
        intent=input_text, config=config, context=exec_context
    )

    return result


def create_response_metadata(playbook_result: Dict[str, Any]) -> PlaybookExecutionMetadata:
    """
    Create playbook execution metadata from result.

    Args:
        playbook_result: Playbook execution result

    Returns:
        PlaybookExecutionMetadata object
    """
    return PlaybookExecutionMetadata(
        playbook_executed=True,
        steps_completed=playbook_result.get("steps_completed", []),
        budget_used=playbook_result.get("budget_used", 0.0),
        quality_score=playbook_result.get("quality_score", 0.0),
        reasoning_tokens=playbook_result.get("reasoning_tokens", 0),
        artifacts=playbook_result.get("artifacts", []),
        decision_log=playbook_result.get("decision_log", []),
    )


def create_response_usage(
    playbook_result: Dict[str, Any],
    prompt_tokens: int = 0,
    completion_tokens: int = 0,
) -> ResponseUsageInfo:
    """
    Create usage information from playbook result.

    Args:
        playbook_result: Playbook execution result
        prompt_tokens: Prompt tokens (if known)
        completion_tokens: Completion tokens (if known)

    Returns:
        ResponseUsageInfo object
    """
    reasoning_tokens = playbook_result.get("reasoning_tokens", 0)
    total_tokens = prompt_tokens + completion_tokens + reasoning_tokens

    return ResponseUsageInfo(
        prompt_tokens=prompt_tokens,
        completion_tokens=completion_tokens,
        reasoning_tokens=reasoning_tokens,
        total_tokens=total_tokens,
    )


def create_response_object(
    playbook_result: Dict[str, Any],
    model: str,
    include_metadata: bool = True,
) -> ResponseObject:
    """
    Create ResponseObject from playbook result.

    Args:
        playbook_result: Playbook execution result
        model: Model name
        include_metadata: Whether to include playbook metadata

    Returns:
        ResponseObject
    """
    # Extract output from artifacts
    artifacts = playbook_result.get("artifacts", [])
    if artifacts:
        output = artifacts[-1].get("output", {})
    else:
        output = {"result": "No output generated"}

    # Build metadata
    metadata = {}
    if include_metadata:
        meta = create_response_metadata(playbook_result)
        metadata = {
            "playbook_executed": meta.playbook_executed,
            "steps_completed": len(meta.steps_completed),
            "budget_used": meta.budget_used,
            "quality_score": meta.quality_score,
        }

    return ResponseObject(
        id=f"resp_{uuid.uuid4().hex[:24]}",
        object="response",
        created=int(time.time()),
        model=model,
        output=output,
        usage=create_response_usage(playbook_result),
        metadata=metadata,
    )


async def resolve_intent(input_text: str) -> Intent:
    """
    Resolve input to intent (stub for Phase 4).

    In Phase 4, this will:
    - Generate embedding for input
    - Search intent database
    - Return best matching intent with confidence

    For now, returns a default intent.

    Args:
        input_text: User input

    Returns:
        Intent object
    """
    # Stub implementation
    return Intent(
        id="default",
        name="DefaultIntent",
        confidence=1.0,
        embedding=[],
    )


async def get_playbook_for_intent(intent_id: str) -> Dict[str, Any]:
    """
    Get playbook configuration for intent (stub for Phase 4).

    In Phase 4, this will:
    - Load playbook template from database
    - Configure tools for playbook
    - Set execution parameters

    For now, returns a default playbook config.

    Args:
        intent_id: Intent identifier

    Returns:
        Playbook configuration dictionary
    """
    # Stub implementation
    return {
        "id": f"playbook_{intent_id}",
        "name": "DefaultPlaybook",
        "tools": ["calculator", "search", "echo"],
        "max_steps": 10,
        "budget_max": 1.0,
    }


def create_intent_response(
    intent: Intent,
    playbook_config: Dict[str, Any],
    playbook_result: Dict[str, Any],
) -> IntentResponse:
    """
    Create IntentResponse from execution result.

    Args:
        intent: Resolved intent
        playbook_config: Playbook configuration
        playbook_result: Playbook execution result

    Returns:
        IntentResponse object
    """
    return IntentResponse(
        intent=intent.name,
        confidence=intent.confidence,
        playbook_id=playbook_config["id"],
        artifacts=playbook_result.get("artifacts", []),
        cost=playbook_result.get("budget_used", 0.0),
        execution_log=playbook_result.get("steps_completed", []),
    )
