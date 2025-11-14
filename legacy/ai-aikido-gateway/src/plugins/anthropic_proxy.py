"""
Anthropic proxy plugin powered by LiteLLM.

Provides a consistent entry point for routing Claude requests through LiteLLM,
mirroring the behaviour of the OpenAI proxy plugin. Stores useful metadata in
the request context and returns OpenAI-compatible response payloads.
"""

from __future__ import annotations

import asyncio
import copy
import logging
import os
from typing import Any, Dict, Optional, Tuple

import litellm

from src.core.context import RequestContext
from src.core.costs import calculate_completion_cost
from src.core.plugin import BasePlugin
from src.plugins.openai_proxy import LITELLM_ERROR_TYPES, OpenAIProxyPlugin


class AnthropicProxyPlugin(BasePlugin):
    """Proxy plugin that delegates chat completions to LiteLLM for Anthropic models."""

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
        self.default_api_key: Optional[str] = None
        self.api_keys: list[Dict[str, Any]] = []
        self._key_lock: Optional[asyncio.Lock] = None
        self._key_index: int = 0
        self.disabled_reason: Optional[str] = None

    async def on_startup(self) -> None:
        await super().on_startup()

        self.timeout = self._parse_float(self.config.get("timeout"))
        self.max_retries = self._parse_int(self.config.get("max_retries"))
        self.api_base = self.config.get("api_base") or os.getenv("ANTHROPIC_API_BASE")
        self.default_api_key = self.config.get("api_key") or os.getenv("ANTHROPIC_API_KEY")
        self.api_keys = self._load_api_keys()

        if not self.default_api_key and not self.api_keys:
            self.enabled = False
            self.disabled_reason = "ANTHROPIC_API_KEY missing; Anthropic proxy disabled"
            self.logger.warning(
                "Disabling Anthropic proxy plugin: no API keys configured (set ANTHROPIC_API_KEY or provide api_keys config)."
            )
            return

        self._key_lock = asyncio.Lock()

        if self.max_retries is not None:
            try:
                litellm.set_max_retries = self.max_retries  # type: ignore[attr-defined]
            except Exception:  # pragma: no cover
                self.logger.debug("liteLLM retry configuration not supported on this version")

        try:
            litellm.set_verbose = False  # type: ignore[attr-defined]
        except Exception:  # pragma: no cover
            pass

        self.logger.info(
            "Anthropic proxy ready (timeout=%s, max_retries=%s, api_base=%s)",
            self.timeout,
            self.max_retries,
            self.api_base or "default",
        )

        if self.api_keys:
            self.logger.info(
                "Anthropic proxy key pool initialized with %s keys",
                len(self.api_keys),
            )

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
            payload: Normalized payload ready for LiteLLM/Anthropic.
            api_key: API key to use for the call (falls back to config/env).

        Returns:
            Dictionary response compatible with OpenAI Chat Completions.
        """
        effective_api_key = api_key or self.default_api_key
        if not effective_api_key:
            raise RuntimeError("ANTHROPIC_API_KEY is not configured for Anthropic proxy")

        litellm_payload = copy.deepcopy(payload)
        litellm_payload["api_key"] = effective_api_key
        litellm_payload.setdefault("custom_llm_provider", "anthropic")

        if self.timeout is not None:
            litellm_payload.setdefault("timeout", self.timeout)
            litellm_payload.setdefault("request_timeout", self.timeout)

        if self.max_retries is not None:
            litellm_payload.setdefault("max_retries", self.max_retries)

        if self.api_base:
            litellm_payload.setdefault("api_base", self.api_base)

        self.logger.debug(
            "Forwarding request via LiteLLM (model=%s, timeout=%s)",
            litellm_payload.get("model"),
            litellm_payload.get("timeout"),
        )

        try:
            response = await litellm.acompletion(**litellm_payload)
        except LITELLM_ERROR_TYPES:
            raise
        except Exception as exc:  # pragma: no cover
            self.logger.exception("Unexpected error calling LiteLLM")
            raise RuntimeError(str(exc)) from exc

        response_data = OpenAIProxyPlugin._serialize_response(response)
        usage = response_data.get("usage") or {}
        prompt_tokens = usage.get("prompt_tokens", 0) or 0
        completion_tokens = usage.get("completion_tokens", 0) or 0
        model_id = response_data.get("model") or payload.get("model")
        completion_cost = calculate_completion_cost(model_id, prompt_tokens, completion_tokens)

        if completion_cost:
            ctx.add_cost_entry(
                {
                    "type": "completion",
                    "provider": "anthropic",
                    "model": model_id,
                    "prompt_tokens": prompt_tokens,
                    "completion_tokens": completion_tokens,
                    "cost": completion_cost,
                }
            )

        ctx.metadata.setdefault("anthropic_proxy", {})
        ctx.metadata["anthropic_proxy"].update(
            {
                "library": "litellm",
                "timeout": litellm_payload.get("timeout"),
                "api_base": litellm_payload.get("api_base"),
            }
        )

        return response_data

    async def on_error(self, ctx: RequestContext, error: Exception) -> Optional[Dict[str, Any]]:
        self.logger.error("Anthropic proxy encountered an error: %s", error, exc_info=True)
        return await super().on_error(ctx, error)

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

    async def acquire_api_key(self, attempt: int = 1) -> Tuple[str, Dict[str, Any]]:
        if not self.api_keys:
            if self.default_api_key:
                return self.default_api_key, {"label": "default", "pool_size": 1, "index": 1, "usage": 1}
            raise RuntimeError("ANTHROPIC_API_KEY is not configured for Anthropic proxy")

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
