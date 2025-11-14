"""
Example plugin for testing and demonstration purposes.

This simple plugin logs requests and responses, demonstrating
the plugin lifecycle hooks.
"""

from src.core.context import RequestContext
from src.core.plugin import BasePlugin


class ExampleLoggerPlugin(BasePlugin):
    """
    Simple example plugin that logs requests and responses.

    This plugin demonstrates:
    - Using lifecycle hooks (startup, shutdown, before_request, after_response)
    - Accessing request context
    - Setting metadata
    - Configuration usage
    """

    async def on_startup(self) -> None:
        """Initialize the plugin."""
        await super().on_startup()
        log_level = self.config.get("log_level", "INFO")
        self.logger.info(f"Example logger plugin started (log_level={log_level})")

    async def on_shutdown(self) -> None:
        """Cleanup the plugin."""
        await super().on_shutdown()
        self.logger.info("Example logger plugin shut down")

    async def before_request(self, context: RequestContext) -> None:
        """Log before request is processed."""
        self.logger.info(
            f"[{context.request_id[:8]}] Before request - "
            f"Processing new request"
        )

        # Add some metadata
        context.set_metadata("example_plugin_started", True)
        context.set_metadata("example_plugin_priority", self.priority)

    async def after_response(self, context: RequestContext) -> None:
        """Log after response is received."""
        self.logger.info(
            f"[{context.request_id[:8]}] After response - "
            f"Request completed"
        )

        # Check if we set metadata earlier
        if context.has_metadata("example_plugin_started"):
            self.logger.debug("Confirmed: metadata was set in before_request")

    async def on_error(self, context: RequestContext, error: Exception) -> None:
        """Log errors."""
        self.logger.error(
            f"[{context.request_id[:8]}] Error occurred: {error}"
        )
        return await super().on_error(context, error)
