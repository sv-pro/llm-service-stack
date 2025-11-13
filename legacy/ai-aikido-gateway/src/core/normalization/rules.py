"""Normalization rules for request preprocessing."""

import re
from abc import ABC, abstractmethod
from typing import Any


class NormalizationRule(ABC):
    """Base class for normalization rules."""

    @abstractmethod
    def apply(self, request: Any) -> Any:
        """Apply normalization rule to request.

        Args:
            request: ChatCompletionRequest to normalize

        Returns:
            Normalized request
        """
        pass


class TrimSystemPromptRule(NormalizationRule):
    """Trim whitespace from system messages.

    System prompts often have trailing/leading whitespace that
    doesn't affect semantics but breaks cache keys.
    """

    def apply(self, request: Any) -> Any:
        """Trim system message content.

        Args:
            request: Request to normalize

        Returns:
            Request with trimmed system messages
        """
        if not hasattr(request, "messages") or not request.messages:
            return request

        for message in request.messages:
            if hasattr(message, "role") and message.role == "system":
                if hasattr(message, "content") and isinstance(message.content, str):
                    message.content = message.content.strip()

        return request


class StandardizeWhitespaceRule(NormalizationRule):
    """Standardize whitespace in all messages.

    Collapses multiple spaces, removes trailing spaces, and
    normalizes line endings for consistent cache keys.
    """

    def apply(self, request: Any) -> Any:
        """Standardize whitespace in messages.

        Args:
            request: Request to normalize

        Returns:
            Request with normalized whitespace
        """
        if not hasattr(request, "messages") or not request.messages:
            return request

        for message in request.messages:
            if hasattr(message, "content") and isinstance(message.content, str):
                # Normalize line endings
                content = message.content.replace("\r\n", "\n")

                # Collapse multiple spaces (but preserve single newlines)
                content = re.sub(r"[ \t]+", " ", content)

                # Remove trailing spaces from each line
                content = re.sub(r" +$", "", content, flags=re.MULTILINE)

                # Remove leading/trailing whitespace
                content = content.strip()

                message.content = content

        return request


class CanonicalizeToolPayloadRule(NormalizationRule):
    """Canonicalize tool/function call payloads.

    Ensures tool definitions and function calls are in a
    consistent format for caching.
    """

    def apply(self, request: Any) -> Any:
        """Canonicalize tool payloads.

        Args:
            request: Request to normalize

        Returns:
            Request with canonical tool payloads
        """
        # Normalize tools field (if present)
        if hasattr(request, "tools") and request.tools:
            # Sort tools by name for consistent ordering
            try:
                request.tools = sorted(
                    request.tools,
                    key=lambda t: t.get("function", {}).get("name", "")
                    if isinstance(t, dict)
                    else getattr(t, "function", None).name
                    if hasattr(t, "function")
                    else ""
                )
            except Exception:
                # If sorting fails, leave as-is
                pass

        # Normalize tool_choice field
        if hasattr(request, "tool_choice"):
            # Normalize "auto" / None to consistent value
            if request.tool_choice in (None, "auto", "none"):
                request.tool_choice = "auto"

        return request


class NormalizeTemperatureRule(NormalizationRule):
    """Normalize temperature and sampling parameters.

    Rounds temperature to reasonable precision and normalizes
    default values for consistent caching.
    """

    def apply(self, request: Any) -> Any:
        """Normalize sampling parameters.

        Args:
            request: Request to normalize

        Returns:
            Request with normalized parameters
        """
        # Normalize temperature (round to 2 decimal places)
        if hasattr(request, "temperature") and request.temperature is not None:
            request.temperature = round(float(request.temperature), 2)

            # Treat very small values as 0
            if request.temperature <= 0.01:
                request.temperature = 0.0

        # Normalize top_p
        if hasattr(request, "top_p") and request.top_p is not None:
            request.top_p = round(float(request.top_p), 2)

        # Normalize max_tokens / max_completion_tokens
        if hasattr(request, "max_tokens") and request.max_tokens is not None:
            request.max_tokens = int(request.max_tokens)

        if hasattr(request, "max_completion_tokens") and request.max_completion_tokens is not None:
            request.max_completion_tokens = int(request.max_completion_tokens)

        return request


class RemoveMetadataRule(NormalizationRule):
    """Remove metadata that doesn't affect response semantics.

    Removes fields like user IDs, request IDs, etc. that don't
    affect the actual LLM response but break cache keys.
    """

    def apply(self, request: Any) -> Any:
        """Remove non-semantic metadata.

        Args:
            request: Request to normalize

        Returns:
            Request without metadata fields
        """
        # List of fields to remove
        metadata_fields = ["user", "metadata", "extra_headers"]

        for field in metadata_fields:
            if hasattr(request, field):
                setattr(request, field, None)

        return request
