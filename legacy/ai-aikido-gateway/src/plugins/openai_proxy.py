"""
OpenAI proxy plugin powered by LiteLLM.

This plugin provides a thin abstraction around LiteLLM so the gateway can
forward chat completion requests through the plugin layer rather than
talking to the OpenAI REST API directly. It prepares the LiteLLM call,
captures useful metadata, and returns a dict compatible with the OpenAI
Chat Completions response format.
"""

from __future__ import annotations

import asyncio
import copy
import logging
import os
from typing import Any, Dict, Optional, Tuple

import litellm
from litellm import exceptions as litellm_exceptions

from src.core.context import RequestContext
from src.core.costs import calculate_completion_cost
from src.core.plugin import BasePlugin


def _collect_litellm_error_types() -> tuple[type, ...]:
    """Collect available LiteLLM exception classes for graceful error handling."""
    candidate_names = [
        "APIError",
        "APIConnectionError",
        "APIResponseValidationError",
        "APIStatusError",
        "APITimeoutError",
        "AuthenticationError",
        "BadRequestError",
        "BudgetExceededError",
        "ContentPolicyViolationError",
        "ContextWindowExceededError",
        "InvalidRequestError",
        "NotFoundError",
        "OpenAIError",
        "PermissionDeniedError",
        "RateLimitError",
        "ServiceUnavailableError",
        "Timeout",
        "UnprocessableEntityError",
    ]
    types: list[type] = []
    for name in candidate_names:
        error_type = getattr(litellm_exceptions, name, None)
        if isinstance(error_type, type):
            types.append(error_type)
    return tuple(types)


LITELLM_ERROR_TYPES = _collect_litellm_error_types() or (Exception,)


class OpenAIProxyPlugin(BasePlugin):
    """Proxy plugin that delegates chat completions to LiteLLM."""

    def __init__(
        self,
        name: str,
        config: Optional[Dict[str, Any]] = None,
        enabled: bool = True,
        priority: int = 50,
    ):
        super().__init__(name, config, enabled, priority)
        self.timeout: Optional[float] = None
        self.max_retries: Optional[int] = None
        self.api_base: Optional[str] = None
        self.organization: Optional[str] = None
        self.default_api_key: Optional[str] = None
        self.api_keys: list[Dict[str, Any]] = []
        self._key_lock: Optional[asyncio.Lock] = None
        self._key_index: int = 0
        self.disabled_reason: Optional[str] = None

    async def on_startup(self) -> None:
        await super().on_startup()

        self.timeout = self._parse_float(self.config.get("timeout"))
        self.max_retries = self._parse_int(self.config.get("max_retries"))
        self.api_base = self.config.get("api_base") or os.getenv("OPENAI_API_BASE")
        self.organization = self.config.get("organization") or os.getenv("OPENAI_ORG_ID")
        self.default_api_key = self.config.get("api_key") or os.getenv("OPENAI_API_KEY")
        self.api_keys = self._load_api_keys()

        if not self.default_api_key and not self.api_keys:
            self.enabled = False
            self.disabled_reason = "OPENAI_API_KEY missing; OpenAI proxy disabled"
            self.logger.warning(
                "Disabling OpenAI proxy plugin: no API keys configured (set OPENAI_API_KEY or provide api_keys config)."
            )
            return

        self._key_lock = asyncio.Lock()

        # Configure LiteLLM retries if provided.
        if self.max_retries is not None:
            try:
                litellm.set_max_retries = self.max_retries  # type: ignore[attr-defined]
            except Exception:  # pragma: no cover - defensive (API may change)
                self.logger.debug("liteLLM retry configuration not supported on this version")

        # Reduce noise unless user explicitly enables it.
        try:
            litellm.set_verbose = False  # type: ignore[attr-defined]
        except Exception:  # pragma: no cover - defensive
            pass

        self.logger.info(
            "OpenAI proxy ready (timeout=%s, max_retries=%s, api_base=%s)",
            self.timeout,
            self.max_retries,
            self.api_base or "default",
        )

        if self.api_keys:
            self.logger.info(
                "OpenAI proxy key pool initialized with %s keys",
                len(self.api_keys),
            )

    async def acquire_api_key(self, attempt: int = 1) -> Tuple[str, Dict[str, Any]]:
        """
        Acquire the next API key according to the configured rotation strategy.

        Returns the key value and safe metadata describing the selection.
        """
        if not self.api_keys:
            if self.default_api_key:
                return self.default_api_key, {"label": "default", "pool_size": 1, "index": 1, "usage": 1}
            raise RuntimeError("OPENAI_API_KEY is not configured for OpenAI proxy")

        assert self._key_lock is not None
        async with self._key_lock:
            entry = self.api_keys[self._key_index]
            self._key_index = (self._key_index + 1) % len(self.api_keys)
            entry["usage"] += 1
            meta = {
                "label": entry["label"],
                "pool_size": len(self.api_keys),
                "index": entry["index"],
                "usage": entry["usage"],
            }
            return entry["value"], meta

    async def create_chat_completion(
        self,
        ctx: RequestContext,
        payload: Dict[str, Any],
        api_key: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Execute a chat completion request through LiteLLM.

        Args:
            ctx: Request context for the current invocation.
            payload: Normalized payload ready for LiteLLM/OpenAI.
            api_key: API key to use for the call (falls back to config/env).

        Returns:
            Dictionary response compatible with OpenAI Chat Completions.

        Raises:
            RuntimeError / provider-specific exceptions if the request fails.
        """
        effective_api_key = api_key or self.default_api_key
        if not effective_api_key:
            raise RuntimeError("OPENAI_API_KEY is not configured for OpenAI proxy")

        litellm_payload = copy.deepcopy(payload)
        litellm_payload["api_key"] = effective_api_key

        # Apply optional configuration overrides.
        request_timeout = self._parse_float(litellm_payload.pop("timeout", None)) or self.timeout
        if request_timeout:
            litellm_payload.setdefault("timeout", request_timeout)
            litellm_payload.setdefault("request_timeout", request_timeout)

        if self.max_retries is not None:
            litellm_payload.setdefault("max_retries", self.max_retries)

        if self.api_base:
            litellm_payload.setdefault("api_base", self.api_base)

        if self.organization:
            litellm_payload.setdefault("organization", self.organization)

        self.logger.debug(
            "Forwarding request via LiteLLM (model=%s, timeout=%s)",
            litellm_payload.get("model"),
            litellm_payload.get("timeout"),
        )

        try:
            response = await litellm.acompletion(**litellm_payload)
        except LITELLM_ERROR_TYPES:
            raise
        except Exception as exc:  # pragma: no cover - guard for unexpected errors
            self.logger.exception("Unexpected error calling LiteLLM")
            raise RuntimeError(str(exc)) from exc

        response_data = self._serialize_response(response)
        usage = response_data.get("usage") or {}
        prompt_tokens = usage.get("prompt_tokens", 0) or 0
        completion_tokens = usage.get("completion_tokens", 0) or 0
        model_id = response_data.get("model") or payload.get("model")
        completion_cost = calculate_completion_cost(model_id, prompt_tokens, completion_tokens)
        if completion_cost:
            ctx.add_cost_entry(
                {
                    "type": "completion",
                    "provider": "openai",
                    "model": model_id,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "cost": completion_cost,
                }
            )

        ctx.metadata.setdefault("openai_proxy", {})
        ctx.metadata["openai_proxy"].update(
            {
                "library": "litellm",
                "timeout": litellm_payload.get("timeout"),
                "api_base": litellm_payload.get("api_base"),
            }
        )

        return response_data

    async def on_error(self, ctx: RequestContext, error: Exception) -> Optional[Dict[str, Any]]:
        self.logger.error("OpenAI proxy encountered an error: %s", error, exc_info=True)
        return await super().on_error(ctx, error)

    @staticmethod
    def _serialize_response(response: Any) -> Dict[str, Any]:
        """Convert LiteLLM response into a plain dictionary."""
        if hasattr(response, "model_dump"):
            return response.model_dump()
        if hasattr(response, "dict"):
            return response.dict()  # type: ignore[return-value]
        if hasattr(response, "json"):
            try:
                import json

                return json.loads(response.json())
            except Exception:
                logging.getLogger("plugin.openai_proxy").error("Failed to JSON-decode LiteLLM response")
        if isinstance(response, dict):
            return response
        raise RuntimeError("Unexpected LiteLLM response type; expected dict-compatible payload")

    @staticmethod
    def _parse_float(value: Any) -> Optional[float]:
        if value is None or value == "":
            return None
        try:
            return float(value)
        except (TypeError, ValueError):
            return None

    @staticmethod
    def _parse_int(value: Any) -> Optional[int]:
        if value is None or value == "":
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    def _load_api_keys(self) -> list[Dict[str, Any]]:
        keys_config = self.config.get("api_keys")
        entries: list[Dict[str, Any]] = []

        if keys_config:
            raw_entries = keys_config if isinstance(keys_config, (list, tuple)) else [keys_config]
            for idx, entry in enumerate(raw_entries, start=1):
                if isinstance(entry, dict):
                    value = entry.get("key") or entry.get("value")
                    label = entry.get("label") or f"key_{idx}"
                else:
                    value = entry
                    label = f"key_{idx}"

                if not value:
                    continue
                entries.append(
                    {
                        "value": value,
                        "label": label,
                        "index": idx,
                        "usage": 0,
                    }
                )

        if not entries and self.default_api_key:
            entries.append(
                {"value": self.default_api_key, "label": "default", "index": 1, "usage": 0}
            )

        return entries
