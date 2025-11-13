"""Normalization plugin for request preprocessing."""

import logging
from typing import Any, Dict, Optional

from src.core.context import RequestContext
from src.core.normalization import NormalizationPipeline
from src.core.plugin import BasePlugin

logger = logging.getLogger(__name__)


class NormalizationPlugin(BasePlugin):
    """Plugin for normalizing requests before caching/routing.

    This plugin ensures consistent request formatting by applying
    normalization rules like whitespace trimming, parameter rounding,
    and payload canonicalization.

    Configuration:
        enabled: Enable/disable normalization
        priority: Execution priority (should run early, before caches)
        rules: List of rule names to apply (default: all)
    """

    def __init__(
        self,
        name: str,
        config: Optional[Dict[str, Any]] = None,
        enabled: bool = True,
        priority: int = 4,
    ):
        super().__init__(name, config, enabled, priority)

        # Initialize normalization pipeline
        self.pipeline = NormalizationPipeline(enabled=self.enabled)

        logger.info(
            f"Normalization plugin '{self.name}' initialized: "
            f"enabled={self.enabled}, rules={len(self.pipeline.rules)}"
        )

    async def before_request(self, ctx: RequestContext):
        """Normalize request before processing.

        Args:
            ctx: Request context
        """
        if not self.enabled:
            return

        try:
            # Normalize the request
            original_request = ctx.request
            normalized_request = self.pipeline.normalize(original_request)

            # Update context with normalized request
            ctx.request = normalized_request

            logger.debug("Request normalized successfully")

        except Exception as e:
            logger.error(f"Error normalizing request: {e}", exc_info=True)
            # Don't fail the request, continue with original

    async def on_startup(self):
        """Initialize plugin on startup."""
        if self.enabled:
            logger.info(
                f"Normalization plugin started with {len(self.pipeline.rules)} rules"
            )

    async def on_shutdown(self):
        """Cleanup on shutdown."""
        logger.info("Normalization plugin shutdown")
