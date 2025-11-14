"""
Plugin pipeline for orchestrating plugin execution.

The pipeline manages the lifecycle of plugins and coordinates their execution
during request processing.
"""

import logging
from typing import List, Optional

from src.core.context import RequestContext
from src.core.logging import logging_context
from src.core.plugin import BasePlugin

logger = logging.getLogger(__name__)


class PluginPipeline:
    """
    Orchestrates plugin execution during request processing.

    The pipeline executes plugins in priority order (lowest priority first)
    for before_request hooks, and in reverse priority order for after_response
    hooks. This ensures symmetric processing (e.g., timing starts before and
    stops after, in correct order).

    Example:
        >>> pipeline = PluginPipeline([cache_plugin, cost_plugin, proxy_plugin])
        >>> context = RequestContext(request=request_data)
        >>> await pipeline.execute_before_request(context)
        >>> # ... execute LLM request ...
        >>> await pipeline.execute_after_response(context)
    """

    def __init__(self, plugins: Optional[List[BasePlugin]] = None):
        """
        Initialize the pipeline with a list of plugins.

        Args:
            plugins: List of plugin instances (will be sorted by priority)
        """
        self.plugins = sorted(plugins or [], key=lambda p: p.priority)
        self.logger = logging.getLogger("pipeline")
        self.logger.info(
            f"Pipeline initialized with {len(self.plugins)} plugins: "
            f"{[p.name for p in self.plugins]}"
        )

    async def startup(self) -> None:
        """
        Call on_startup for all enabled plugins.

        This should be called when the application starts, before processing
        any requests.

        Raises:
            Exception: If any plugin's on_startup fails
        """
        self.logger.info("Starting up plugins...")

        for plugin in self.plugins:
            if not plugin.enabled:
                self.logger.debug(f"Skipping disabled plugin: {plugin.name}")
                continue

            try:
                self.logger.info(f"Starting plugin: {plugin.name}")
                await plugin.on_startup()
            except Exception as e:
                self.logger.error(
                    f"Plugin '{plugin.name}' failed to start: {e}",
                    exc_info=True,
                )
                raise

        self.logger.info("All plugins started successfully")

    async def shutdown(self) -> None:
        """
        Call on_shutdown for all enabled plugins.

        This should be called when the application shuts down.
        Errors are logged but don't stop the shutdown process.
        """
        self.logger.info("Shutting down plugins...")

        # Shutdown in reverse order
        for plugin in reversed(self.plugins):
            if not plugin.enabled:
                continue

            try:
                self.logger.info(f"Shutting down plugin: {plugin.name}")
                await plugin.on_shutdown()
            except Exception as e:
                self.logger.error(
                    f"Error shutting down plugin '{plugin.name}': {e}",
                    exc_info=True,
                )

        self.logger.info("All plugins shut down")

    async def execute_before_request(self, context: RequestContext) -> None:
        """
        Execute before_request hooks for all enabled plugins.

        Plugins execute in priority order (lowest priority first).
        If any plugin raises an exception, the pipeline stops and the
        exception is propagated.

        If a plugin calls context.stop_pipeline(), remaining plugins
        are skipped (useful for cache hits).

        Args:
            context: Request context

        Raises:
            Exception: If any plugin's before_request fails
        """
        with logging_context(context.request_id):
            self.logger.debug(
                f"Executing before_request for {len(self.plugins)} plugins "
                f"(request_id={context.request_id[:8]}...)"
            )

            for plugin in self.plugins:
                if not plugin.enabled:
                    continue

                if not context.should_continue():
                    self.logger.info(
                        "Pipeline stopped by previous plugin, skipping remaining plugins"
                    )
                    break

                try:
                    self.logger.debug(
                        f"Plugin '{plugin.name}' before_request "
                        f"(priority={plugin.priority})"
                    )
                    await plugin.before_request(context)
                except Exception as e:
                    self.logger.error(
                        f"Plugin '{plugin.name}' before_request failed: {e}",
                        exc_info=True,
                    )
                    context.add_error(e)
                    raise

            self.logger.debug(
                f"Completed before_request hooks (request_id={context.request_id[:8]}...)"
            )

    async def execute_after_response(self, context: RequestContext) -> None:
        """
        Execute after_response hooks for all enabled plugins.

        Plugins execute in reverse priority order (highest priority first).
        This ensures symmetric processing with before_request.

        Errors in after_response hooks are logged but don't fail the request,
        since the response has already been generated.

        Args:
            context: Request context (must have response set)
        """
        with logging_context(context.request_id):
            self.logger.debug(
                f"Executing after_response for {len(self.plugins)} plugins "
                f"(request_id={context.request_id[:8]}...)"
            )

            # Execute in reverse priority order
            for plugin in reversed(self.plugins):
                if not plugin.enabled:
                    continue

                try:
                    self.logger.debug(
                        f"Plugin '{plugin.name}' after_response "
                        f"(priority={plugin.priority})"
                    )
                    await plugin.after_response(context)
                except Exception as e:
                    # Log error but don't fail the request
                    self.logger.error(
                        f"Plugin '{plugin.name}' after_response failed: {e}",
                        exc_info=True,
                    )
                    context.add_error(e)

            self.logger.debug(
                f"Completed after_response hooks (request_id={context.request_id[:8]}...)"
            )

    async def handle_error(
        self, context: RequestContext, error: Exception
    ) -> Optional[dict]:
        """
        Execute on_error hooks for all enabled plugins.

        Plugins are called in reverse priority order. The first plugin to
        return a custom error response stops the chain and that response
        is used.

        Args:
            context: Request context
            error: The exception that occurred

        Returns:
            Custom error response dict (or None to use default)
        """
        with logging_context(context.request_id):
            self.logger.error(
                f"Handling error in pipeline: {error} "
                f"(request_id={context.request_id[:8]}...)",
                exc_info=True,
            )

            context.add_error(error)

            # Execute in reverse priority order
            for plugin in reversed(self.plugins):
                if not plugin.enabled:
                    continue

                try:
                    self.logger.debug(
                        f"Plugin '{plugin.name}' on_error (priority={plugin.priority})"
                    )
                    custom_response = await plugin.on_error(context, error)

                    if custom_response is not None:
                        self.logger.info(
                            f"Plugin '{plugin.name}' provided custom error response"
                        )
                        return custom_response

                except Exception as e:
                    # Log error in error handler, but continue
                    self.logger.error(
                        f"Plugin '{plugin.name}' on_error failed: {e}",
                        exc_info=True,
                    )

            return None

    def get_enabled_plugins(self) -> List[BasePlugin]:
        """
        Get list of enabled plugins.

        Returns:
            List of enabled plugins in priority order
        """
        return [p for p in self.plugins if p.enabled]

    def __repr__(self) -> str:
        """String representation of the pipeline."""
        enabled = len(self.get_enabled_plugins())
        return (
            f"<PluginPipeline "
            f"total={len(self.plugins)} "
            f"enabled={enabled}>"
        )
