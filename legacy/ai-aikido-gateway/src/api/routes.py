"""
API routes for the AI Aikido Gateway

Implements OpenAI-compatible endpoints for chat completions.
"""

import asyncio
import logging
import os
import time
from typing import Optional, List, Dict, Any, Tuple, Callable, Awaitable

import litellm

from fastapi import APIRouter, HTTPException, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import JSONResponse

from src.api.auth import authenticate_request
from src.api.models import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionChoice,
    ChatMessage,
    UsageInfo,
    ErrorResponse,
    ErrorDetail,
    SemanticThresholdUpdate,
    SemanticSearchRequest,
    SemanticCacheEntry,
    ResponsesRequest,
    PlaybookExecuteRequest,
)
from src.api.exceptions import (
    ModelNotSupportedException,
    ProviderNotConfiguredException,
)
from src.core.context import RequestContext
from src.core.config import CostAlertSettings
from src.core.costs import calculate_completion_cost
from src.core.logging import logging_context
from src.core.pipeline import PluginPipeline
from plugins.openai_proxy import OpenAIProxyPlugin, LITELLM_ERROR_TYPES
from plugins.anthropic_proxy import AnthropicProxyPlugin

try:
    from src.workflows.executor import execute_playbook
    from src.workflows.state import PlaybookConfig
    from src.telemetry.re_re_events import (
        ReReTelemetryEmitter,
        _ensure_re_re_table,
        get_emitter_diagnostics,
    )
    from src.telemetry.re_re_ws import (
        register_connection,
        unregister_connection,
        get_connection_snapshot,
    )
    WORKFLOWS_AVAILABLE = True
except ImportError:
    WORKFLOWS_AVAILABLE = False
    execute_playbook = None
    PlaybookConfig = None
    ReReTelemetryEmitter = None
    _ensure_re_re_table = None
    register_connection = None
    unregister_connection = None

logger = logging.getLogger(__name__)

router = APIRouter()

# ============================================================================
# MODEL REGISTRY & CONFIGURATION
# ============================================================================
#
# IMPORTANT: GPT-5 API ARCHITECTURE NOTES
# ----------------------------------------
# GPT-5, GPT-5-mini, and GPT-5-nano are REASONING MODELS that use a completely
# different API endpoint and parameter structure:
#
# Responses API (GPT-5): /v1/responses
#   - Different parameters: reasoning.effort, text.verbosity, max_output_tokens
#   - Does NOT support: temperature, top_p, logprobs, presence_penalty, frequency_penalty
#   - Uses "input" instead of "messages"
#   - Returns response with reasoning chain-of-thought
#
# Chat Completions API (All other models): /v1/chat/completions
#   - Standard parameters: temperature, top_p, max_tokens/max_completion_tokens
#   - Uses "messages" array
#   - Traditional completion response
#
# CURRENT IMPLEMENTATION:
# - We currently use Chat Completions API for ALL models (including GPT-5)
# - OpenAI provides a fallback that makes GPT-5 work with Chat Completions
# - BUT: This fallback has limitations and doesn't expose reasoning features
# - We filter out unsupported parameters (temperature, top_p, etc.) for GPT-5
#
# FUTURE IMPROVEMENT:
# - Implement proper Responses API integration for GPT-5 models
# - Detect api_type="responses" in MODEL_REGISTRY
# - Route to /v1/responses with proper parameter transformation
# - Return reasoning chain to client (optional feature)
#
# See: https://platform.openai.com/docs/guides/gpt-5
# ============================================================================

# Model capability definitions
MODEL_REGISTRY = {
    "gpt-5": {
        "id": "gpt-5",
        "name": "GPT-5",
        "provider": "openai",
        "supported": True,
        "requires_env": "OPENAI_API_KEY",
        "description": "Latest reasoning model (requires Responses API)",
        "max_tokens_param": "max_output_tokens",  # GPT-5 uses max_output_tokens
        "supports_legacy_params": False,
        "unsupported_params": ["temperature", "top_p", "logprobs", "presence_penalty", "frequency_penalty", "max_tokens", "max_completion_tokens"],
        "api_type": "responses",  # Uses /v1/responses instead of /v1/chat/completions
        "reasoning_model": True,  # Supports reasoning effort levels
        "pricing": {
            "input": 2.50,   # USD per 1M tokens (cheaper than GPT-4o)
            "output": 10.00  # USD per 1M tokens
        },
        "notes": "GPT-5 uses Responses API (/v1/responses) with different parameters: reasoning.effort (minimal/low/medium/high), text.verbosity, max_output_tokens. Does not support temperature, top_p, logprobs. Currently using Chat Completions fallback."
    },
    "gpt-5-mini": {
        "id": "gpt-5-mini",
        "name": "GPT-5 Mini",
        "provider": "openai",
        "supported": True,
        "requires_env": "OPENAI_API_KEY",
        "description": "Efficient reasoning model (replaces gpt-4.1-mini, o4-mini)",
        "max_tokens_param": "max_output_tokens",
        "supports_legacy_params": False,
        "unsupported_params": ["temperature", "top_p", "logprobs", "presence_penalty", "frequency_penalty", "max_tokens", "max_completion_tokens"],
        "api_type": "responses",
        "reasoning_model": True,
        "pricing": {
            "input": 1.00,   # USD per 1M tokens (more cost-effective than GPT-5)
            "output": 4.00   # USD per 1M tokens
        },
        "notes": "GPT-5-mini uses Responses API. Currently using Chat Completions fallback."
    },
    "gpt-5-nano": {
        "id": "gpt-5-nano",
        "name": "GPT-5 Nano",
        "provider": "openai",
        "supported": True,
        "requires_env": "OPENAI_API_KEY",
        "description": "Lightweight reasoning model (replaces gpt-4.1-nano)",
        "max_tokens_param": "max_output_tokens",
        "supports_legacy_params": False,
        "unsupported_params": ["temperature", "top_p", "logprobs", "presence_penalty", "frequency_penalty", "max_tokens", "max_completion_tokens"],
        "api_type": "responses",
        "reasoning_model": True,
        "pricing": {
            "input": 0.40,   # USD per 1M tokens (cheapest GPT-5 variant)
            "output": 1.60   # USD per 1M tokens
        },
        "notes": "GPT-5-nano uses Responses API. Currently using Chat Completions fallback."
    },
    "gpt-4o": {
        "id": "gpt-4o",
        "name": "GPT-4o",
        "provider": "openai",
        "supported": True,
        "requires_env": "OPENAI_API_KEY",
        "description": "Optimized GPT-4 with multimodal capabilities",
        "max_tokens_param": "max_completion_tokens",
        "supports_legacy_params": False,
        "unsupported_params": [],  # Supports all standard parameters
        "pricing": {
            "input": 5.00,    # USD per 1M tokens
            "output": 20.00   # USD per 1M tokens
        }
    },
    "gpt-4-turbo": {
        "id": "gpt-4-turbo",
        "name": "GPT-4 Turbo",
        "provider": "openai",
        "supported": True,
        "requires_env": "OPENAI_API_KEY",
        "description": "Fast GPT-4 with improved performance",
        "max_tokens_param": "max_completion_tokens",
        "supports_legacy_params": False,
        "unsupported_params": [],  # Supports all standard parameters
        "pricing": {
            "input": 10.00,   # USD per 1M tokens
            "output": 30.00   # USD per 1M tokens
        }
    },
    "gpt-4": {
        "id": "gpt-4",
        "name": "GPT-4",
        "provider": "openai",
        "supported": True,
        "requires_env": "OPENAI_API_KEY",
        "description": "Highly capable model",
        "max_tokens_param": "max_tokens",  # Older models use this
        "supports_legacy_params": True,
        "unsupported_params": [],  # Supports all standard parameters
        "pricing": {
            "input": 30.00,   # USD per 1M tokens
            "output": 60.00   # USD per 1M tokens
        }
    },
    "gpt-3.5-turbo": {
        "id": "gpt-3.5-turbo",
        "name": "GPT-3.5 Turbo",
        "provider": "openai",
        "supported": True,
        "requires_env": "OPENAI_API_KEY",
        "description": "Fast and efficient for most tasks",
        "max_tokens_param": "max_tokens",
        "supports_legacy_params": True,
        "unsupported_params": [],  # Supports all standard parameters
        "pricing": {
            "input": 0.50,    # USD per 1M tokens
            "output": 1.50    # USD per 1M tokens
        }
    },
    "claude-3-haiku-20240307": {
        "id": "claude-3-haiku-20240307",
        "name": "Claude 3 Haiku",
        "provider": "anthropic",
        "supported": True,
        "requires_env": "ANTHROPIC_API_KEY",
        "description": "Fast and lightweight Claude model",
        "max_tokens_param": "max_tokens",
        "supports_legacy_params": False,
        "unsupported_params": ["presence_penalty", "frequency_penalty", "logit_bias"],
        "pricing": {
            "input": 0.25,
            "output": 1.25
        }
    },
    "claude-3-sonnet-20240229": {
        "id": "claude-3-sonnet-20240229",
        "name": "Claude 3 Sonnet",
        "provider": "anthropic",
        "supported": True,
        "requires_env": "ANTHROPIC_API_KEY",
        "description": "Balanced Claude model for general tasks",
        "max_tokens_param": "max_tokens",
        "supports_legacy_params": False,
        "unsupported_params": ["presence_penalty", "frequency_penalty", "logit_bias"],
        "pricing": {
            "input": 3.00,
            "output": 15.00
        }
    },
    "claude-3-opus-20240229": {
        "id": "claude-3-opus-20240229",
        "name": "Claude 3 Opus",
        "provider": "anthropic",
        "supported": True,
        "requires_env": "ANTHROPIC_API_KEY",
        "description": "Most capable Claude model",
        "max_tokens_param": "max_tokens",
        "supports_legacy_params": False,
        "unsupported_params": ["presence_penalty", "frequency_penalty", "logit_bias"],
        "pricing": {
            "input": 15.00,
            "output": 75.00
        }
    },
}

MODEL_FALLBACKS = {
    "gpt-4": ["gpt-3.5-turbo"],
    "gpt-4-turbo": ["gpt-3.5-turbo"],
    "gpt-4o": ["gpt-3.5-turbo"],
}


def _build_provider_not_configured_detail(provider: str, env_var: Optional[str]) -> Dict[str, Any]:
    """
    Build a consistent error payload for provider configuration issues.
    """
    provider_label = provider or "Provider"
    message = f"{provider_label} proxy is not configured"
    if env_var:
        message += f" (missing {env_var})"
    return {
        "error": {
            "type": "provider_not_configured",
            "provider": provider_label,
            "missing": env_var,
            "message": message,
        }
    }


def get_model_info(model_id: str) -> Dict[str, Any]:
    """Get information about a specific model"""
    return MODEL_REGISTRY.get(model_id)


class ProviderRequestError(Exception):
    """Wraps provider request failures for fallback handling."""

    def __init__(
        self,
        original: Exception,
        model_id: str,
        provider: str,
        payload: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ):
        super().__init__(str(original))
        self.original = original
        self.model_id = model_id
        self.provider = provider
        self.payload = payload
        self.metadata = metadata or {}


def normalize_payload_for_model(payload: Dict[str, Any], model_id: str) -> tuple[Dict[str, Any], List[str]]:
    """
    Normalize the request payload based on model-specific requirements.
    
    Handles:
    - Parameter name differences (e.g., max_tokens vs max_completion_tokens)
    - Unsupported parameters that must be removed for certain models
    
    Returns:
        tuple: (normalized_payload, list_of_changes)
    """
    model_info = get_model_info(model_id)
    if not model_info:
        return payload, []
    
    normalized = payload.copy()
    changes = []
    
    # Handle max_tokens parameter name differences
    max_tokens_param = model_info.get("max_tokens_param", "max_tokens")
    
    # If payload has max_tokens or max_completion_tokens, use the correct one for this model
    if "max_tokens" in normalized or "max_completion_tokens" in normalized:
        # Get the value from whichever parameter is present
        max_tokens_value = normalized.pop("max_tokens", None) or normalized.pop("max_completion_tokens", None)
        
        # Set it using the model's preferred parameter name
        if max_tokens_value:
            if "max_tokens" in payload and max_tokens_param != "max_tokens":
                changes.append(f"Renamed 'max_tokens' to '{max_tokens_param}'")
            elif "max_completion_tokens" in payload and max_tokens_param != "max_completion_tokens":
                changes.append(f"Renamed 'max_completion_tokens' to '{max_tokens_param}'")
            normalized[max_tokens_param] = max_tokens_value
    
    # Remove unsupported parameters for this model
    unsupported_params = model_info.get("unsupported_params", [])
    for param in unsupported_params:
        if param in normalized:
            logger.info(f"Removing unsupported parameter '{param}' for model {model_id}")
            changes.append(f"Removed unsupported parameter '{param}'")
            normalized.pop(param)
    
    return normalized, changes


async def _execute_chat_completion_via_litellm(
    payload: Dict[str, Any],
    api_key: str,
    provider: str,
) -> tuple[Dict[str, Any], Dict[str, Any]]:
    """
    Execute a chat completion using LiteLLM directly.

    Returns the response data and the payload that was sent to LiteLLM (for metadata).
    """
    litellm_payload = payload.copy()
    litellm_payload["api_key"] = api_key
    if provider == "anthropic":
        litellm_payload.setdefault("custom_llm_provider", "anthropic")

    # Ensure a sensible timeout for the fallback path.
    litellm_payload.setdefault("timeout", 60.0)
    litellm_payload.setdefault("request_timeout", litellm_payload["timeout"])

    response = await litellm.acompletion(**litellm_payload)
    response_data = OpenAIProxyPlugin._serialize_response(response)
    return response_data, litellm_payload


def _build_litellm_error_payload(exc: Exception) -> tuple[int, Dict[str, Any]]:
    """
    Convert a LiteLLM exception into an HTTP status code and error payload.
    """
    status_code = getattr(exc, "status_code", None)
    response_payload: Dict[str, Any] = {}

    candidate = getattr(exc, "response", None)
    if isinstance(candidate, dict):
        response_payload = candidate
    elif candidate is not None:
        json_handler = getattr(candidate, "json", None)
        if callable(json_handler):
            try:
                response_payload = json_handler()
            except Exception:
                logger.debug("Failed to read JSON from LiteLLM response object")

    if not response_payload:
        response_payload = {"error": {"message": str(exc)}}

    if status_code is None:
        status_code = response_payload.get("status") or response_payload.get("status_code") or 502

    try:
        status_code_int = int(status_code)
    except (TypeError, ValueError):
        status_code_int = 502

    return status_code_int, response_payload


def _resolve_provider_resources(request: Request, provider: str) -> tuple[str, Optional[str], Any, str]:
    """Return API key, metadata key, and proxy plugin for the provider."""
    if provider == "openai":
        api_key = os.getenv("OPENAI_API_KEY")
        metadata_key = "openai_proxy"
        proxy_plugin = getattr(request.app.state, "openai_proxy_plugin", None)
    elif provider == "anthropic":
        api_key = os.getenv("ANTHROPIC_API_KEY")
        metadata_key = "anthropic_proxy"
        proxy_plugin = getattr(request.app.state, "anthropic_proxy_plugin", None)
    else:
        api_key = None
        metadata_key = "provider"
        proxy_plugin = None

    return api_key, metadata_key, proxy_plugin


def _record_completion_cost(
    ctx: RequestContext,
    provider: str,
    model_id: str,
    response_data: Dict[str, Any],
) -> None:
    """
    Ensure completion spend is tracked even when proxy plugins are disabled.

    If a completion ledger entry already exists (e.g., proxy plugin recorded it),
    exit early to avoid double counting.
    """
    if any(entry.get("type") == "completion" for entry in ctx.cost_entries):
        return

    usage = (response_data or {}).get("usage") or {}
    prompt_tokens = usage.get("prompt_tokens") or 0
    completion_tokens = usage.get("completion_tokens") or 0

    if not prompt_tokens or not completion_tokens:
        return

    completion_cost = calculate_completion_cost(model_id, prompt_tokens, completion_tokens)
    if not completion_cost:
        return

    ctx.add_cost_entry(
        {
            "type": "completion",
            "provider": provider,
            "model": model_id,
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "cost": completion_cost,
        }
    )


async def _execute_model_request(
    request: Request,
    ctx: RequestContext,
    request_data: ChatCompletionRequest,
    model_id: str,
    pipeline: Optional[PluginPipeline],
    is_fallback: bool = False,
) -> Dict[str, Any]:
    with logging_context(ctx.request_id):
        model_info = get_model_info(model_id)
        if not model_info:
            raise HTTPException(status_code=400, detail=f"Model '{model_id}' is not supported")

        provider = model_info["provider"]
        api_key, metadata_key, proxy_plugin = _resolve_provider_resources(request, provider)

        plugin_has_pool = False
        if isinstance(proxy_plugin, (OpenAIProxyPlugin, AnthropicProxyPlugin)):
            pool = getattr(proxy_plugin, "api_keys", []) or []
            plugin_has_pool = bool(pool)

        if not api_key and not plugin_has_pool:
            raise ProviderNotConfiguredException(provider.capitalize(), f"{provider.upper()}_API_KEY")

        ctx.metadata["model"] = model_id
        ctx.metadata["provider"] = provider

        payload = request_data.model_dump(exclude_none=True)
        payload["model"] = model_id
        payload, normalization_changes = normalize_payload_for_model(payload, model_id)

        if normalization_changes:
            ctx.metadata["normalizations"] = normalization_changes

        logger.info(
            "Dispatching payload to provider",
            extra={
                "provider": provider,
                "model": payload.get("model"),
                "message_count": len(payload.get("messages", [])),
            },
        )
        logger.debug("Normalized payload", extra={"payload": payload})

        debug_attempts: List[Dict[str, Any]] = []

        def record_attempt(state: str, extra: Optional[Dict[str, Any]] = None) -> None:
            entry: Dict[str, Any] = {
                "state": state,
                "timestamp": time.time(),
            }
            if extra:
                entry.update(extra)
            debug_attempts.append(entry)

        def append_summary(success: bool, key_meta: Optional[Dict[str, Any]] = None, error: Optional[str] = None) -> None:
            attempt_records = [entry for entry in debug_attempts if "attempt" in entry]
            failures = [entry for entry in attempt_records if entry.get("status") in {"error", "provider_error"}]
            summary: Dict[str, Any] = {
                "provider": provider,
                "model": model_id,
                "attempts": len(attempt_records) if attempt_records else 1,
                "failures": len(failures),
                "successful": success,
                "is_fallback": is_fallback,
            }
            if key_meta:
                summary.update(
                    {
                        "key_label": key_meta.get("label"),
                        "key_index": key_meta.get("index"),
                        "key_pool_size": key_meta.get("pool_size"),
                    }
                )
            if error:
                summary["error"] = error

            ctx.metadata.setdefault("retry_summary", []).append(summary)

        try:
            async def acquire_key(attempt: int) -> Tuple[str, Dict[str, Any]]:
                if isinstance(proxy_plugin, (OpenAIProxyPlugin, AnthropicProxyPlugin)) and proxy_plugin.enabled:
                    key_value, key_meta = await proxy_plugin.acquire_api_key(attempt)
                    key_meta = {
                        **key_meta,
                        "source": "pool",
                        "plugin": proxy_plugin.name,
                    }
                    return key_value, key_meta

                if api_key:
                    return api_key, {"label": "env", "pool_size": 1, "index": 1, "usage": attempt, "source": "env"}
                raise ProviderNotConfiguredException(provider.capitalize(), f"{provider.upper()}_API_KEY")

            response_data: Dict[str, Any]
            key_meta: Dict[str, Any]
            if isinstance(proxy_plugin, (OpenAIProxyPlugin, AnthropicProxyPlugin)) and proxy_plugin.enabled:
                record_attempt("proxy_call", {"plugin": proxy_plugin.name})

                async def call_with_key(key_value: str, key_meta: Dict[str, Any]) -> Dict[str, Any]:
                    return await proxy_plugin.create_chat_completion(ctx, payload, key_value)

                response_data, key_meta = await _call_with_retries(
                    call_with_key,
                    provider,
                    model_id,
                    payload,
                    debug_attempts,
                    acquire_key,
                )

                proxy_meta = ctx.metadata.setdefault(metadata_key, {})
                proxy_meta.setdefault("source", "plugin")
                proxy_meta.update(
                    {
                        "key_label": key_meta.get("label"),
                        "key_pool_size": key_meta.get("pool_size"),
                        "key_index": key_meta.get("index"),
                    }
                )
            else:
                record_attempt("litellm_direct")

                async def call_litellm(key_value: str, key_meta: Dict[str, Any]) -> Dict[str, Any]:
                    response_data, litellm_payload = await _execute_chat_completion_via_litellm(payload, key_value, provider)
                    ctx.metadata[metadata_key] = {
                        "library": "litellm",
                        "timeout": litellm_payload.get("timeout"),
                        "api_base": litellm_payload.get("api_base"),
                        "source": "fallback",
                    }
                    ctx.metadata[metadata_key].update(
                        {
                            "key_label": key_meta.get("label"),
                            "key_pool_size": key_meta.get("pool_size"),
                            "key_index": key_meta.get("index"),
                        }
                    )
                    return response_data

                response_data, key_meta = await _call_with_retries(
                    call_litellm,
                    provider,
                    model_id,
                    payload,
                    debug_attempts,
                    acquire_key,
                )

            ctx.metadata.setdefault("retry_attempts", []).extend(debug_attempts)
            append_summary(True, key_meta=key_meta)
            _record_completion_cost(ctx, provider, model_id, response_data)
            return response_data
        except ProviderRequestError as exc:
            exc.metadata.setdefault("attempts", []).extend(debug_attempts)
            ctx.metadata.setdefault("retry_attempts", []).extend(debug_attempts)
            append_summary(False, error=str(exc))
            raise
        except LITELLM_ERROR_TYPES as exc:  # type: ignore[misc]
            ctx.metadata.setdefault("retry_attempts", []).extend(debug_attempts)
            append_summary(False, error=str(exc))
            raise ProviderRequestError(exc, model_id, provider, payload, {"attempts": debug_attempts}) from exc


def enrich_error_with_fix_hint(error_data: Dict[str, Any], model_id: str, request_payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Enrich error responses with helpful fix hints when API calls fail.
    
    Analyzes the error and provides actionable guidance for developers.
    """
    model_info = get_model_info(model_id)
    if not model_info:
        return error_data
    
    error_message = error_data.get("error", {}).get("message", "")
    enriched = error_data.copy()
    
    # Check if error is about unsupported parameters
    unsupported_params = model_info.get("unsupported_params", [])
    
    # Common error patterns and fixes
    fix_hint = None
    example = None
    
    if "temperature" in error_message.lower() and "temperature" in unsupported_params:
        fix_hint = f"Model '{model_id}' does not support the 'temperature' parameter. Remove it from your request or use a different model."
        example = {
            "model": model_id,
            "messages": request_payload.get("messages", [{"role": "user", "content": "Your message here"}]),
            "max_output_tokens": 1000  # GPT-5 uses max_output_tokens
        }
    
    elif "top_p" in error_message.lower() and "top_p" in unsupported_params:
        fix_hint = f"Model '{model_id}' does not support the 'top_p' parameter. Remove it from your request."
    
    elif "max_tokens" in error_message.lower() and model_info.get("api_type") == "responses":
        fix_hint = f"Model '{model_id}' uses the Responses API which requires 'max_output_tokens' instead of 'max_tokens' or 'max_completion_tokens'."
        example = {
            "model": model_id,
            "input": request_payload.get("messages", "Your message here"),
            "reasoning": {"effort": "low"},
            "max_output_tokens": 1000
        }
    
    # Add fix hint to error response
    if fix_hint:
        if "error" not in enriched:
            enriched["error"] = {}
        enriched["error"]["fix_hint"] = fix_hint
        if example:
            enriched["error"]["corrected_example"] = example
        enriched["error"]["documentation"] = f"https://platform.openai.com/docs/models/{model_id}"
    
    return enriched


def is_model_available(model_id: str) -> tuple[bool, Optional[str]]:
    """
    Check if a model is available for use.

    Returns:
        tuple: (is_available, reason_if_not)
    """
    model_info = get_model_info(model_id)

    if not model_info:
        return False, f"Model '{model_id}' is not recognized"

    if not model_info.get("supported", False):
        return False, model_info.get("reason", "Model is not supported")

    # Check if required API key is configured
    required_env = model_info.get("requires_env")
    if required_env and not os.getenv(required_env):
        return False, f"Provider not configured (missing {required_env})"

    return True, None


def get_available_models() -> List[Dict[str, Any]]:
    """
    Get list of all models with their availability status.

    Returns enriched model info including whether each model is currently available.
    """
    models = []
    for model_id, model_info in MODEL_REGISTRY.items():
        info = model_info.copy()
        is_available, reason = is_model_available(model_id)
        info["available"] = is_available
        if not is_available:
            info["unavailable_reason"] = reason
        models.append(info)

    return models


@router.get("/models")
async def list_models(available_only: bool = False):
    """
    List all models with their availability status.

    Query parameters:
    - available_only: If true, only return models that are currently available
    """
    models = get_available_models()

    if available_only:
        models = [m for m in models if m["available"]]

    return {
        "object": "list",
        "data": models
    }


@router.get("/settings")
async def read_settings(request: Request):
    """
    Return configuration settings required by the dashboard.
    """
    cost_alerts = getattr(request.app.state, "cost_alerts", None)
    if isinstance(cost_alerts, CostAlertSettings):
        alerts_payload = cost_alerts.to_dict()
    else:
        alerts_payload = CostAlertSettings().to_dict()

    return {
        "object": "settings",
        "cost_alerts": alerts_payload,
    }


@router.post("/chat/completions", response_model=ChatCompletionResponse)
async def create_chat_completion(
    request_data: ChatCompletionRequest,
    request: Request,
):
    """
    Create a chat completion (OpenAI-compatible endpoint)
    
    This endpoint forwards requests to the configured LLM provider (OpenAI by default).
    Executes through the plugin pipeline for intelligent routing, caching, cost tracking, etc.
    """
    start_time = time.time()
    correlation_id = getattr(request.state, "correlation_id", None)
    if correlation_id:
        ctx = RequestContext(request=request_data, request_id=correlation_id)
    else:
        ctx = RequestContext(request=request_data)
        request.state.correlation_id = ctx.request_id
    ctx.metadata["cache_type"] = ctx.metadata.get("cache_type", "api")

    pipeline = getattr(request.app.state, 'plugin_pipeline', None)

    try:
        with logging_context(ctx.request_id):
            tenant_id = authenticate_request(request)
            if tenant_id:
                ctx.metadata["tenant_id"] = tenant_id
                request.state.tenant_id = tenant_id

            logger.info(
                "Chat completion request received",
                extra={"model": request_data.model, "message_count": len(request_data.messages)},
            )

            model_info = get_model_info(request_data.model)
            # Check if model is available
            is_available, reason = is_model_available(request_data.model)
            if not is_available:
                logger.warning(
                    "Model unavailable for request",
                    extra={"model": request_data.model, "reason": reason},
                )
                provider_name = (model_info or {}).get("provider")
                required_env = (model_info or {}).get("requires_env")
                if reason and reason.startswith("Provider not configured"):
                    detail = _build_provider_not_configured_detail(
                        provider_name.capitalize() if provider_name else request_data.model,
                        required_env,
                    )
                    raise HTTPException(status_code=503, detail=detail)
                raise HTTPException(status_code=400, detail=reason)

            if not model_info:
                raise HTTPException(status_code=400, detail=f"Model '{request_data.model}' is not supported")
            provider = model_info["provider"]

            if provider not in {"openai", "anthropic"}:
                raise ModelNotSupportedException(
                    request_data.model,
                    f"Provider '{provider}' is not supported"
                )

            # Populate context metadata
            ctx.metadata["model"] = request_data.model
            ctx.metadata["provider"] = provider
            ctx.metadata["start_time"] = start_time

            try:
                # Execute before_request hooks
                if pipeline:
                    await pipeline.execute_before_request(ctx)

                    # Check if pipeline stopped (e.g., cache hit)
                    if not ctx.should_continue():
                        logger.info("Pipeline stopped early (likely cache hit)")
                        ctx.metadata["latency_ms"] = (time.time() - start_time) * 1000

                        # Allow after_response hooks (history, transparency, etc.) to run
                        await pipeline.execute_after_response(ctx)

                        transparency_headers = ctx.metadata.get("transparency_headers")
                        if transparency_headers:
                            return JSONResponse(
                                content=ctx.response,
                                headers=transparency_headers
                            )

                        return ctx.response

                attempt_models = [request_data.model] + MODEL_FALLBACKS.get(request_data.model, [])
                response_data: Optional[Dict[str, Any]] = None

                for idx, model_id in enumerate(attempt_models):
                    is_fallback = idx > 0
                    if is_fallback:
                        ctx.metadata.setdefault("fallback_chain", []).append(model_id)
                        logger.warning(
                            "Fallback attempt triggered",
                            extra={
                                "attempt": idx + 1,
                                "total_attempts": len(attempt_models),
                                "model": model_id,
                            },
                        )

                    try:
                        response_data = await _execute_model_request(
                            request,
                            ctx,
                            request_data,
                            model_id,
                            pipeline,
                            is_fallback=is_fallback,
                        )
                        break
                    except ProviderRequestError as err:
                        logger.error(
                            "Provider error during chat completion",
                            extra={"model": err.model_id, "provider": err.provider},
                            exc_info=True,
                        )
                        ctx.add_error(err.original)
                        if pipeline:
                            await pipeline.handle_error(ctx, err.original)

                        if idx == len(attempt_models) - 1:
                            status_code, error_payload = _build_litellm_error_payload(err.original)
                            enriched_error = enrich_error_with_fix_hint(error_payload, err.model_id, err.payload)
                            headers = ctx.metadata.get("transparency_headers") or None
                            raise HTTPException(
                                status_code=status_code,
                                detail=enriched_error,
                                headers=headers,
                            ) from err.original
                        continue

                if response_data is None:
                    headers = ctx.metadata.get("transparency_headers") or None
                    raise HTTPException(
                        status_code=502,
                        detail="Failed to obtain response from provider",
                        headers=headers,
                    )

                # Store response in context
                ctx.response = response_data
                ctx.metadata["latency_ms"] = (time.time() - start_time) * 1000

                if not ctx.metadata.get("cache_hit"):
                    ctx.metadata.setdefault("cache_type", "api")
                    ctx.metadata["cache_miss"] = True

                logger.info(
                    "Chat completion successful",
                    extra={"response_id": response_data.get("id")},
                )

                # Execute after_response hooks (plugins may add transparency headers)
                if pipeline:
                    await pipeline.execute_after_response(ctx)

                transparency_headers = ctx.metadata.get("transparency_headers")
                if transparency_headers:
                    return JSONResponse(content=response_data, headers=transparency_headers)

                return response_data

            except ProviderNotConfiguredException as exc:
                ctx.add_error(exc)
                if pipeline:
                    await pipeline.handle_error(ctx, exc)
                headers = ctx.metadata.get("transparency_headers") or None
                detail = _build_provider_not_configured_detail(exc.provider, exc.env_var)
                raise HTTPException(
                    status_code=503,
                    detail=detail,
                    headers=headers,
                ) from exc
            except asyncio.TimeoutError as e:
                logger.error(
                    "Request to provider timed out",
                    extra={"provider": provider},
                )
                ctx.add_error(e)
                if pipeline:
                    await pipeline.handle_error(ctx, e)
                headers = ctx.metadata.get("transparency_headers") or None
                raise HTTPException(
                    status_code=504,
                    detail="Request to LLM provider timed out",
                    headers=headers,
                ) from e
    except HTTPException:
        # Re-raise HTTP exceptions without wrapping
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}", exc_info=True)
        ctx.add_error(e)
        if pipeline:
            await pipeline.handle_error(ctx, e)
        headers = ctx.metadata.get("transparency_headers") or None
        raise HTTPException(
            status_code=500,
            detail=f"Internal server error: {str(e)}",
            headers=headers,
        ) from e


@router.post("/responses")
async def create_responses_completion(
    request_data: ResponsesRequest,
    request: Request,
):
    """Shim endpoint that maps Responses API payloads to chat completions."""
    try:
        chat_request = request_data.to_chat_completion()
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))

    return await create_chat_completion(chat_request, request)


# =============================================================================
# Request History Endpoints
# =============================================================================

@router.get("/history/requests")
async def get_request_history(
    request: Request,
    limit: int = 50,
    offset: int = 0,
    model: Optional[str] = None,
    cached: Optional[bool] = None,
    cache_type: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
    search: Optional[str] = None,
):
    """
    Get request history with optional filters.
    
    Query Parameters:
    - limit: Number of requests to return (default: 50, max: 100)
    - offset: Pagination offset (default: 0)
    - model: Filter by model name
    - cached: Filter by cached status (true/false)
    - start_date: Filter by start date (ISO format)
    - end_date: Filter by end date (ISO format)
    - search: Search in messages and responses
    """
    # Get history plugin from app state
    history_plugin = getattr(request.app.state, "history_plugin", None)
    
    if not history_plugin:
        raise HTTPException(
            status_code=503,
            detail="Request history plugin is not available"
        )
    
    # Validate limit
    if limit > 100:
        limit = 100
    if limit < 1:
        limit = 1
    
    try:
        requests_data = history_plugin.get_requests(
            limit=limit,
            offset=offset,
            model=model,
            cached=cached,
            cache_type=cache_type,
            start_date=start_date,
            end_date=end_date,
            search=search,
        )
        
        return {
            "requests": requests_data,
            "limit": limit,
            "offset": offset,
            "count": len(requests_data),
        }
    
    except Exception as e:
        logger.error(f"Error fetching request history: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch request history: {str(e)}"
        )


@router.get("/history/requests/{request_id}")
async def get_request_by_id(request_id: str, request: Request):
    """Get a single request by ID."""
    history_plugin = getattr(request.app.state, "history_plugin", None)
    
    if not history_plugin:
        raise HTTPException(
            status_code=503,
            detail="Request history plugin is not available"
        )
    
    try:
        request_data = history_plugin.get_request_by_id(request_id)
        
        if not request_data:
            raise HTTPException(
                status_code=404,
                detail=f"Request {request_id} not found"
            )
        
        return request_data
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching request {request_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch request: {str(e)}"
        )


@router.get("/history/stats")
async def get_history_stats(request: Request):
    """Get summary statistics for request history."""
    history_plugin = getattr(request.app.state, "history_plugin", None)
    
    if not history_plugin:
        raise HTTPException(
            status_code=503,
            detail="Request history plugin is not available"
        )
    
    try:
        stats = history_plugin.get_stats()
        
        cache_plugin = getattr(request.app.state, "cache_plugin", None)
        if cache_plugin:
            stats["cache_metrics"] = cache_plugin.get_cache_stats()

        semantic_cache_plugin = getattr(request.app.state, "semantic_cache_plugin", None)
        if semantic_cache_plugin:
            stats["semantic_cache_metrics"] = semantic_cache_plugin.get_stats()

        return stats
    
    except Exception as e:
        logger.error(f"Error fetching history stats: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch history stats: {str(e)}"
        )


@router.get("/cache/semantic/stats")
async def get_semantic_cache_stats(request: Request):
    """Return enriched semantic cache metrics + cost summary."""
    semantic_cache_plugin = getattr(request.app.state, "semantic_cache_plugin", None)
    if not semantic_cache_plugin or not getattr(semantic_cache_plugin, "enabled", False):
        raise HTTPException(
            status_code=503,
            detail="Semantic cache plugin is not available",
        )

    history_plugin = getattr(request.app.state, "history_plugin", None)

    try:
        metrics = semantic_cache_plugin.get_stats()
        metrics_recorder = getattr(semantic_cache_plugin, "metrics_recorder", None)

        histogram = None
        recent_samples: List[Dict[str, Any]] = []
        if metrics_recorder:
            histogram = metrics_recorder.get_similarity_histogram()
            try:
                recent_samples = await metrics_recorder.query_timeseries(limit=20)
            except Exception as exc:  # pragma: no cover - defensive logging
                logger.warning("Failed to load recent semantic metrics samples: %s", exc)

        cost_summary: Optional[Dict[str, Any]] = None
        if history_plugin:
            try:
                history_stats = history_plugin.get_stats()
                cost_summary = {
                    "embedding_cost_total": history_stats.get("embedding_cost_total"),
                    "net_cost_total": history_stats.get("net_cost_total"),
                    "avoided_cost_total": history_stats.get("avoided_cost_total"),
                }
            except Exception as exc:  # pragma: no cover - defensive logging
                logger.warning("Failed to read history stats for cost summary: %s", exc)

        transparency = {
            "provider": metrics.get("provider"),
            "embedding_model": metrics.get("embedding_model"),
            "backend": metrics.get("backend"),
            "similarity_threshold": metrics.get("similarity_threshold"),
            "ttl_seconds": metrics.get("ttl_seconds"),
            "timeseries_enabled": metrics.get("timeseries_enabled"),
        }
        if metrics.get("timeseries"):
            transparency["last_sample_time"] = metrics["timeseries"].get(
                "last_sample_time"
            )

        return {
            "object": "semantic_cache_stats",
            "semantic_cache_metrics": metrics,
            "timeseries": {
                "available": metrics.get("timeseries_available", False),
                "recent_samples": recent_samples,
            },
            "histogram": histogram,
            "cost_summary": cost_summary,
            "transparency": transparency,
        }
    except HTTPException:
        raise
    except Exception as exc:
        logger.error("Failed to fetch semantic cache stats: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Failed to fetch semantic cache stats",
        ) from exc


@router.post("/cache/semantic/threshold")
async def update_semantic_threshold(
    payload: SemanticThresholdUpdate,
    request: Request,
):
    """Adjust semantic cache similarity threshold at runtime."""
    semantic_cache_plugin = getattr(request.app.state, "semantic_cache_plugin", None)

    if not semantic_cache_plugin or not getattr(semantic_cache_plugin, "enabled", False):
        raise HTTPException(
            status_code=503,
            detail="Semantic cache plugin is not available"
        )

    try:
        stats = semantic_cache_plugin.update_similarity_threshold(
            payload.similarity_threshold
        )
        return {
            "message": "Similarity threshold updated",
            "semantic_cache_metrics": stats,
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except Exception as exc:
        logger.error(
            "Error updating semantic cache threshold: %s",
            exc,
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to update semantic cache threshold"
        )


@router.post("/cache/semantic/search")
async def semantic_cache_search(
    payload: SemanticSearchRequest,
    request: Request,
):
    """Return semantic cache candidates for a prompt."""
    semantic_cache_plugin = getattr(request.app.state, "semantic_cache_plugin", None)

    if not semantic_cache_plugin or not getattr(semantic_cache_plugin, "enabled", False):
        raise HTTPException(
            status_code=503,
            detail="Semantic cache plugin is not available"
        )

    try:
        candidates = await semantic_cache_plugin.preview_candidates(
            prompt_text=payload.prompt,
            model=payload.model,
            limit=payload.limit,
        )
        return {"candidates": candidates}
    except Exception as exc:
        logger.error(
            "Error previewing semantic cache candidates: %s",
            exc,
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to preview semantic cache candidates"
        )


@router.get("/cache/semantic/entries")
async def semantic_cache_entries(
    request: Request,
    limit: int = 20,
):
    """List recent semantic cache entries for inspection."""
    semantic_cache_plugin = getattr(request.app.state, "semantic_cache_plugin", None)

    if not semantic_cache_plugin or not getattr(semantic_cache_plugin, "enabled", False):
        raise HTTPException(
            status_code=503,
            detail="Semantic cache plugin is not available"
        )

    try:
        limit = max(1, min(limit, 100))
        entries = semantic_cache_plugin.list_entries(limit=limit)
        return {
            "entries": entries,
            "count": len(entries),
        }
    except Exception as exc:
        logger.error(
            "Error listing semantic cache entries: %s",
            exc,
            exc_info=True,
        )
        raise HTTPException(
            status_code=500,
            detail="Failed to list semantic cache entries"
        )


@router.get("/cache/semantic/timeseries")
async def get_semantic_timeseries(
    request: Request,
    start: Optional[int] = None,
    end: Optional[int] = None,
    limit: int = 100,
):
    """Get time-series metrics for semantic cache.

    Query Parameters:
    - start: Start timestamp (Unix epoch, default: 1 hour ago)
    - end: End timestamp (Unix epoch, default: now)
    - limit: Maximum number of data points (default: 100, max: 1000)
    """
    semantic_cache_plugin = getattr(request.app.state, "semantic_cache_plugin", None)

    if not semantic_cache_plugin or not getattr(semantic_cache_plugin, "enabled", False):
        raise HTTPException(
            status_code=503,
            detail="Semantic cache plugin is not available"
        )

    # Get metrics recorder
    metrics_recorder = getattr(semantic_cache_plugin, "metrics_recorder", None)
    if not metrics_recorder:
        raise HTTPException(
            status_code=503,
            detail="Time-series tracking is not enabled"
        )

    # Validate limit
    if limit > 1000:
        limit = 1000
    if limit < 1:
        limit = 1

    try:
        # Query time-series data
        data = await metrics_recorder.query_timeseries(
            start=start,
            end=end,
            limit=limit
        )

        return {
            "object": "timeseries",
            "start": start or (int(time.time()) - 3600),
            "end": end or int(time.time()),
            "data": data,
            "count": len(data)
        }

    except Exception as e:
        logger.error(f"Error fetching semantic timeseries: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch semantic timeseries: {str(e)}"
        )


def _is_transient_error(error: Exception) -> bool:
    message = str(error).lower()
    transient_markers = [
        "timeout",
        "temporarily unavailable",
        "try again",
        "rate limit",
        "connection reset",
        "connection aborted",
        "service unavailable",
    ]
    return any(marker in message for marker in transient_markers)


async def _call_with_retries(
    call_func: Callable[[str, Dict[str, Any]], Awaitable[Dict[str, Any]]],
    provider: str,
    model_id: str,
    payload: Dict[str, Any],
    attempt_log: List[Dict[str, Any]],
    acquire_key: Callable[[int], Awaitable[Tuple[str, Dict[str, Any]]]],
    max_attempts: int = 3,
    backoff_base: float = 0.5,
) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    for attempt in range(1, max_attempts + 1):
        key_value, key_meta = await acquire_key(attempt)
        entry: Dict[str, Any] = {
            "provider": provider,
            "attempt": attempt,
            "timestamp": time.time(),
            "key": {k: v for k, v in key_meta.items() if k != "value"},
        }
        attempt_log.append(entry)

        try:
            result = await call_func(key_value, key_meta)
            entry["status"] = "success"
            return result, key_meta
        except ProviderRequestError as err:
            entry["status"] = "provider_error"
            entry["error"] = str(err)
            err.metadata.setdefault("attempts", []).extend(attempt_log)
            raise
        except Exception as exc:  # noqa: BLE001
            entry["status"] = "error"
            entry["error"] = str(exc)

            if attempt >= max_attempts or not _is_transient_error(exc):
                raise ProviderRequestError(
                    exc,
                    model_id,
                    provider,
                    payload,
                    {"attempts": attempt_log},
                ) from exc

            sleep_time = backoff_base * (2 ** (attempt - 1))
            entry["backoff_seconds"] = sleep_time
            await asyncio.sleep(sleep_time)

    raise ProviderRequestError(
        Exception("Max retries exceeded"),
        model_id,
        provider,
        payload,
        {"attempts": attempt_log},
    )


# =============================================================================
# Re^Re Loop Demo Endpoints
# =============================================================================

# Global telemetry emitter and active WebSocket connections
_telemetry_emitter: Optional[ReReTelemetryEmitter] = None


def _get_telemetry_emitter() -> ReReTelemetryEmitter:
    """Get or create the global telemetry emitter."""
    global _telemetry_emitter
    if _telemetry_emitter is None and ReReTelemetryEmitter is not None:
        _telemetry_emitter = ReReTelemetryEmitter()
    return _telemetry_emitter


@router.post("/playbooks/execute")
async def execute_playbook_endpoint(
    request_data: PlaybookExecuteRequest,
    request: Request,
):
    """
    Execute a playbook with the Re^Re Loop.

    Request Body:
    - intent: User intent/request to execute
    - max_steps: Maximum number of steps (default: 10)
    - budget_max: Maximum budget in USD (default: 1.0)
    - model: Model to use for execution (default: gpt-4o)

    Returns:
    - execution_id: ID for tracking the execution
    - status: Execution status
    """
    if not WORKFLOWS_AVAILABLE:
        raise HTTPException(
            status_code=503,
            detail="Playbook workflows are not available (missing dependencies)"
        )

    try:
        # Create playbook configuration
        config = PlaybookConfig(
            max_steps=request_data.max_steps,
            budget_max=request_data.budget_max,
            model=request_data.model,
        )

        # Generate execution ID
        import uuid
        execution_id = f"exec_{uuid.uuid4().hex[:12]}"

        # Execute playbook asynchronously
        # Note: This should ideally be run in the background with proper task management
        final_state = await execute_playbook(
            intent=request_data.intent,
            config=config,
            thread_id=execution_id,
        )

        # Store execution result in history plugin for later retrieval
        history_plugin = getattr(request.app.state, "history_plugin", None)
        if history_plugin:
            try:
                # Store the execution bundle
                execution_data = {
                    "execution_id": execution_id,
                    "intent": request_data.intent,
                    "config": config.model_dump(),
                    "final_state": final_state,
                    "completed_at": time.time(),
                }
                # Use the history plugin to persist this
                # For now, we'll store it in metadata
                logger.info(f"Execution {execution_id} completed successfully")
            except Exception as e:
                logger.warning(f"Failed to persist execution {execution_id}: {e}")

        return {
            "execution_id": execution_id,
            "status": "completed",
            "intent": request_data.intent,
            "steps_taken": final_state.get("step_index", 0),
            "budget_used": final_state.get("budget_used", 0.0),
            "quality_score": final_state.get("quality_score"),
            "artifacts": final_state.get("artifacts", []),
        }

    except Exception as e:
        logger.error(f"Error executing playbook: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to execute playbook: {str(e)}"
        )


@router.get("/re-re/executions/{execution_id}")
async def get_execution(execution_id: str, request: Request):
    """
    Get execution details and event history by ID.

    Returns:
    - execution_id: ID of the execution
    - events: List of workflow events
    - final_state: Final state of the execution
    """
    emitter = _get_telemetry_emitter()
    if not emitter or not emitter.enabled:
        raise HTTPException(
            status_code=503,
            detail="Re^Re telemetry is not enabled (set RE_RE_DEMO_ENABLED=true)"
        )

    try:
        # Query events from SQLite history
        import sqlite3
        conn = sqlite3.connect(str(emitter.history_db_path))
        conn.row_factory = sqlite3.Row

        # Ensure table exists
        if _ensure_re_re_table:
            _ensure_re_re_table(conn)

        cursor = conn.execute(
            """
            SELECT * FROM re_re_events
            WHERE thread_id = ?
            ORDER BY step_index ASC, created_at ASC
            """,
            (execution_id,)
        )

        events = []
        import json
        for row in cursor.fetchall():
            event_data = dict(row)
            # Parse metadata JSON
            if event_data.get("metadata"):
                event_data["metadata"] = json.loads(event_data["metadata"])
            if event_data.get("state_snapshot"):
                try:
                    event_data["state_snapshot"] = json.loads(event_data["state_snapshot"])
                except json.JSONDecodeError:
                    event_data["state_snapshot"] = None
            events.append(event_data)

        conn.close()

        if not events:
            raise HTTPException(
                status_code=404,
                detail=f"Execution {execution_id} not found"
            )

        # Get final state from last event snapshot
        final_state = {}
        if events:
            final_event = events[-1]
            final_state = final_event.get("state_snapshot") or {}
            if not final_state:
                final_state = {
                    "status": final_event.get("status"),
                    "budget_used": final_event.get("budget_used"),
                    "quality_score": final_event.get("quality_score"),
                }

        return {
            "execution_id": execution_id,
            "intent": events[0].get("intent") if events else "",
            "events": events,
            "event_count": len(events),
            "final_state": final_state,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching execution {execution_id}: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to fetch execution: {str(e)}"
        )


@router.get("/re-re/status")
async def get_re_re_status():
    emitter = _get_telemetry_emitter()
    emitter_info = get_emitter_diagnostics() if emitter else {"status": {}, "event_log": []}
    websocket_info: Dict[str, Any] = {
        "connections": {},
        "events": [],
    }
    try:
        websocket_info = await get_connection_snapshot()
    except Exception as exc:  # pragma: no cover
        logger.warning("Failed to capture websocket snapshot: %s", exc)

    return {
        "emitter": emitter_info,
        "websockets": websocket_info,
    }


@router.get("/re-re/executions/compare")
async def compare_executions(
    a: str,
    b: str,
    request: Request,
):
    """
    Compare two executions side-by-side.

    Query Parameters:
    - a: First execution ID
    - b: Second execution ID

    Returns:
    - execution_a: First execution data
    - execution_b: Second execution data
    - comparison: Comparison metrics
    """
    try:
        # Fetch both executions
        exec_a = await get_execution(a, request)
        exec_b = await get_execution(b, request)

        # Calculate comparison metrics
        comparison = {
            "budget_delta": exec_a["final_state"]["budget_used"] - exec_b["final_state"]["budget_used"],
            "quality_delta": (exec_a["final_state"].get("quality_score") or 0) - (exec_b["final_state"].get("quality_score") or 0),
            "event_count_delta": exec_a["event_count"] - exec_b["event_count"],
        }

        return {
            "execution_a": exec_a,
            "execution_b": exec_b,
            "comparison": comparison,
        }

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error comparing executions: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail=f"Failed to compare executions: {str(e)}"
        )


@router.get("/re-re/executions/{execution_id}/export")
async def export_execution(execution_id: str, request: Request):
    """
    Export execution data as JSON.

    Returns the complete execution bundle including all events and metadata.
    """
    execution_data = await get_execution(execution_id, request)

    # Add export metadata
    execution_data["exported_at"] = time.time()
    execution_data["export_version"] = "1.0"

    return execution_data


@router.websocket("/ws/re-re/{execution_id}")
async def websocket_re_re_telemetry(websocket: WebSocket, execution_id: str):
    """
    WebSocket endpoint for real-time Re^Re telemetry streaming.

    Clients connect to receive live workflow events as they occur.
    """
    logger.info(f"WebSocket endpoint called for execution {execution_id}")
    logger.info(f"register_connection is None: {register_connection is None}")
    logger.info(f"unregister_connection is None: {unregister_connection is None}")
    
    # Must accept before we can send/close properly
    await websocket.accept()
    logger.info(f"WebSocket accepted for execution {execution_id}")
    
    if register_connection is None or unregister_connection is None:
        logger.error("Re^Re telemetry modules not available")
        await websocket.send_json({
            "type": "error",
            "message": "Re^Re telemetry is not available. Workflow modules failed to load."
        })
        await websocket.close(code=1011)
        return

    await register_connection(execution_id, websocket)

    logger.info(f"WebSocket connected for execution {execution_id}")

    try:
        # Keep connection alive and listen for client messages
        while True:
            # Wait for client messages (like ping/pong)
            try:
                data = await websocket.receive_text()
                # Echo back for now (can add commands later)
                await websocket.send_json({"type": "pong", "data": data})
            except WebSocketDisconnect:
                break

    except Exception as e:
        logger.error(f"WebSocket error for {execution_id}: {e}", exc_info=True)

    finally:
        # Unregister WebSocket
        await unregister_connection(execution_id, websocket)
        logger.info(f"WebSocket disconnected for execution {execution_id}")
