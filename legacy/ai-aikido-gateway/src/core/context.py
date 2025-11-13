"""
Request context for sharing data between plugins.

The RequestContext is the primary means of communication between plugins.
It flows through the plugin pipeline, accumulating data at each stage.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from uuid import uuid4


@dataclass
class RequestContext:
    """
    Context object that flows through the plugin pipeline.

    The context contains the original request, the response (when available),
    metadata accumulated by plugins, and any errors that occurred.

    Attributes:
        request_id: Unique identifier for this request
        timestamp: When the request was received
        request: Original request data (dict or Pydantic model)
        response: Response data (None until LLM responds)
        metadata: Dictionary for plugins to store arbitrary data
        errors: List of exceptions that occurred during processing
        stopped: Flag to stop pipeline execution early (e.g., cache hit)
    """

    request_id: str = field(default_factory=lambda: str(uuid4()))
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    request: Optional[Any] = None
    response: Optional[Any] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    errors: List[Exception] = field(default_factory=list)
    stopped: bool = False
    cost_entries: List[Dict[str, Any]] = field(default_factory=list)

    def set_metadata(self, key: str, value: Any) -> None:
        """
        Set a metadata value.

        Args:
            key: Metadata key
            value: Metadata value
        """
        self.metadata[key] = value

    def get_metadata(self, key: str, default: Any = None) -> Any:
        """
        Get a metadata value.

        Args:
            key: Metadata key
            default: Default value if key not found

        Returns:
            Metadata value or default
        """
        return self.metadata.get(key, default)

    def has_metadata(self, key: str) -> bool:
        """
        Check if metadata key exists.

        Args:
            key: Metadata key

        Returns:
            True if key exists, False otherwise
        """
        return key in self.metadata

    def add_error(self, error: Exception) -> None:
        """
        Add an error to the context.

        Args:
            error: Exception that occurred
        """
        self.errors.append(error)

    def add_cost_entry(self, entry: Dict[str, Any]) -> None:
        """Record a provider cost entry for the current request."""
        if not entry:
            return

        self.cost_entries.append(entry)
        summary = self.metadata.setdefault("cost_summary", {})

        cost = entry.get("cost", 0.0) or 0.0
        prompt_tokens = entry.get("prompt_tokens", 0) or 0
        completion_tokens = entry.get("completion_tokens", 0) or 0
        entry_type = entry.get("type")

        summary["total_cost"] = round(summary.get("total_cost", 0.0) + cost, 6)

        if entry_type:
            summary[f"{entry_type}_cost"] = round(
                summary.get(f"{entry_type}_cost", 0.0) + cost,
                6,
            )
            if prompt_tokens:
                summary[f"{entry_type}_tokens"] = summary.get(
                    f"{entry_type}_tokens", 0
                ) + prompt_tokens
            if completion_tokens:
                summary[f"{entry_type}_completion_tokens"] = summary.get(
                    f"{entry_type}_completion_tokens", 0
                ) + completion_tokens

    def has_errors(self) -> bool:
        """
        Check if any errors have occurred.

        Returns:
            True if there are errors, False otherwise
        """
        return len(self.errors) > 0

    def stop_pipeline(self) -> None:
        """
        Signal that the pipeline should stop early.

        Use this when a plugin has fully handled the request (e.g., cache hit)
        and further processing is not needed.
        """
        self.stopped = True

    def should_continue(self) -> bool:
        """
        Check if pipeline should continue processing.

        Returns:
            True if pipeline should continue, False if stopped
        """
        return not self.stopped

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert context to a dictionary.

        Returns:
            Dictionary representation of context
        """
        return {
            "request_id": self.request_id,
            "timestamp": self.timestamp.isoformat(),
            "has_request": self.request is not None,
            "has_response": self.response is not None,
            "metadata": self.metadata,
            "error_count": len(self.errors),
            "stopped": self.stopped,
        }

    def __repr__(self) -> str:
        """String representation of the context."""
        return (
            f"<RequestContext "
            f"id={self.request_id[:8]}... "
            f"request={'✓' if self.request else '✗'} "
            f"response={'✓' if self.response else '✗'} "
            f"metadata={len(self.metadata)} "
            f"errors={len(self.errors)} "
            f"stopped={self.stopped}>"
        )
