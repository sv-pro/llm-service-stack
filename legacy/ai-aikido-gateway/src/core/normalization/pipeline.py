"""Normalization pipeline for request preprocessing."""

import logging
from typing import Any, List

from .rules import (
    CanonicalizeToolPayloadRule,
    NormalizationRule,
    NormalizeTemperatureRule,
    StandardizeWhitespaceRule,
    TrimSystemPromptRule,
)

logger = logging.getLogger(__name__)


class NormalizationPipeline:
    """Pipeline for applying normalization rules to requests.

    This pipeline applies a sequence of normalization rules to
    ensure consistent request formatting for caching and routing.

    Args:
        rules: List of normalization rules (default: all built-in rules)
        enabled: Whether pipeline is enabled
    """

    DEFAULT_RULES = [
        TrimSystemPromptRule(),
        StandardizeWhitespaceRule(),
        CanonicalizeToolPayloadRule(),
        NormalizeTemperatureRule(),
    ]

    def __init__(
        self,
        rules: List[NormalizationRule] = None,
        enabled: bool = True
    ):
        self.rules = rules if rules is not None else self.DEFAULT_RULES
        self.enabled = enabled

        logger.info(
            f"Normalization pipeline initialized: "
            f"enabled={enabled}, rules={len(self.rules)}"
        )

    def normalize(self, request: Any) -> Any:
        """Apply all normalization rules to request.

        Args:
            request: ChatCompletionRequest to normalize

        Returns:
            Normalized request
        """
        if not self.enabled:
            return request

        # Make a copy to avoid modifying original
        # Note: Pydantic v2 models have .model_copy() method
        if hasattr(request, "model_copy"):
            normalized = request.model_copy(deep=True)
        elif hasattr(request, "copy"):
            # Fallback for Pydantic v1
            normalized = request.copy(deep=True)
        else:
            # Fallback for non-Pydantic objects
            import copy
            normalized = copy.deepcopy(request)

        # Apply each rule in sequence
        for rule in self.rules:
            try:
                normalized = rule.apply(normalized)
                logger.debug(f"Applied normalization rule: {rule.__class__.__name__}")
            except Exception as e:
                logger.error(
                    f"Error applying normalization rule {rule.__class__.__name__}: {e}",
                    exc_info=True
                )
                # Continue with next rule, don't fail the entire pipeline

        return normalized

    def add_rule(self, rule: NormalizationRule):
        """Add a custom normalization rule.

        Args:
            rule: Normalization rule to add
        """
        self.rules.append(rule)
        logger.info(f"Added normalization rule: {rule.__class__.__name__}")

    def remove_rule(self, rule_class: type):
        """Remove a normalization rule by class.

        Args:
            rule_class: Class of rule to remove
        """
        self.rules = [r for r in self.rules if not isinstance(r, rule_class)]
        logger.info(f"Removed normalization rule: {rule_class.__name__}")
