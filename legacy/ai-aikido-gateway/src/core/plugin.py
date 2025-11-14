"""
Base plugin class and plugin registry for the AI Aikido Gateway.

This module provides the foundation for the plugin-first architecture,
defining the lifecycle hooks and interface that all plugins must implement.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class BasePlugin(ABC):
    """
    Abstract base class for all plugins.

    Plugins extend gateway functionality through lifecycle hooks that are called
    at different stages of request processing. Each plugin should handle a single
    concern (e.g., cost monitoring, caching, routing).

    Lifecycle:
        1. on_startup() - Initialize resources (connections, caches, etc.)
        2. before_request(context) - Pre-process request (modify, route, check cache)
        3. [Request execution happens here]
        4. after_response(context) - Post-process response (track costs, cache, log)
        5. on_error(context, error) - Handle errors if they occur
        6. on_shutdown() - Cleanup resources

    Attributes:
        name: Plugin name (from config)
        config: Plugin-specific configuration dictionary
        enabled: Whether plugin is currently enabled
        priority: Execution priority (lower = earlier execution)
    """

    def __init__(
        self,
        name: str,
        config: Optional[Dict[str, Any]] = None,
        enabled: bool = True,
        priority: int = 50,
    ):
        """
        Initialize the plugin.

        Args:
            name: Plugin name
            config: Plugin-specific configuration
            enabled: Whether plugin is enabled
            priority: Execution priority (lower runs first)
        """
        self.name = name
        self.config = config or {}
        self.enabled = enabled
        self.priority = priority
        self.logger = logging.getLogger(f"plugin.{name}")

    async def on_startup(self) -> None:
        """
        Called when the application starts.

        Use this hook to:
        - Initialize database connections
        - Load resources into memory
        - Connect to external services
        - Validate configuration

        Raises:
            Exception: If startup fails (will prevent app from starting)
        """
        self.logger.info(f"Plugin '{self.name}' starting up")

    async def on_shutdown(self) -> None:
        """
        Called when the application shuts down.

        Use this hook to:
        - Close database connections
        - Flush caches
        - Save state
        - Release resources

        Note:
            Should not raise exceptions. Log errors instead.
        """
        self.logger.info(f"Plugin '{self.name}' shutting down")

    async def before_request(self, context: "RequestContext") -> None:
        """
        Called before the request is sent to the LLM provider.

        Use this hook to:
        - Check cache for existing response
        - Modify request (add headers, change model, etc.)
        - Make routing decisions
        - Validate request
        - Start timing/tracking

        Args:
            context: Request context containing request data and metadata

        Raises:
            Exception: If pre-processing fails (will abort request)
        """
        pass

    async def after_response(self, context: "RequestContext") -> None:
        """
        Called after receiving response from the LLM provider.

        Use this hook to:
        - Calculate and store costs
        - Cache the response
        - Update metrics
        - Log request/response
        - Transform response

        Args:
            context: Request context with both request and response data

        Note:
            Exceptions are logged but don't fail the request.
            Response is already generated at this point.
        """
        pass

    async def on_error(
        self, context: "RequestContext", error: Exception
    ) -> Optional[Dict[str, Any]]:
        """
        Called when an error occurs during request processing.

        Use this hook to:
        - Log error details
        - Update error metrics
        - Attempt recovery
        - Generate custom error response

        Args:
            context: Request context (response may be None)
            error: The exception that occurred

        Returns:
            Optional custom error response dict (or None to use default)

        Note:
            Should not raise exceptions. Log errors instead.
        """
        self.logger.error(
            f"Plugin '{self.name}' handling error: {error}",
            exc_info=True,
        )
        return None

    def __repr__(self) -> str:
        """String representation of the plugin."""
        return (
            f"<{self.__class__.__name__} "
            f"name='{self.name}' "
            f"enabled={self.enabled} "
            f"priority={self.priority}>"
        )


class PluginRegistry:
    """
    Registry for managing plugin instances.

    The registry maintains a collection of plugins and provides methods to
    access them by name or in priority order.
    """

    def __init__(self):
        """Initialize an empty plugin registry."""
        self._plugins: Dict[str, BasePlugin] = {}
        self.logger = logging.getLogger("plugin.registry")

    def register(self, plugin: BasePlugin) -> None:
        """
        Register a plugin.

        Args:
            plugin: Plugin instance to register

        Raises:
            ValueError: If a plugin with the same name is already registered
        """
        if plugin.name in self._plugins:
            raise ValueError(
                f"Plugin '{plugin.name}' is already registered. "
                "Plugin names must be unique."
            )

        self._plugins[plugin.name] = plugin
        self.logger.info(
            f"Registered plugin '{plugin.name}' "
            f"(enabled={plugin.enabled}, priority={plugin.priority})"
        )

    def unregister(self, name: str) -> None:
        """
        Unregister a plugin by name.

        Args:
            name: Name of plugin to unregister

        Raises:
            KeyError: If plugin is not registered
        """
        if name not in self._plugins:
            raise KeyError(f"Plugin '{name}' is not registered")

        del self._plugins[name]
        self.logger.info(f"Unregistered plugin '{name}'")

    def get(self, name: str) -> Optional[BasePlugin]:
        """
        Get a plugin by name.

        Args:
            name: Plugin name

        Returns:
            Plugin instance or None if not found
        """
        return self._plugins.get(name)

    def get_enabled_plugins(self) -> list[BasePlugin]:
        """
        Get all enabled plugins sorted by priority.

        Returns:
            List of enabled plugins in priority order (lower priority first)
        """
        enabled = [p for p in self._plugins.values() if p.enabled]
        return sorted(enabled, key=lambda p: p.priority)

    def get_all_plugins(self) -> list[BasePlugin]:
        """
        Get all registered plugins (enabled and disabled).

        Returns:
            List of all plugins sorted by priority
        """
        return sorted(self._plugins.values(), key=lambda p: p.priority)

    def count(self) -> int:
        """
        Get the total number of registered plugins.

        Returns:
            Number of plugins in registry
        """
        return len(self._plugins)

    def count_enabled(self) -> int:
        """
        Get the number of enabled plugins.

        Returns:
            Number of enabled plugins
        """
        return sum(1 for p in self._plugins.values() if p.enabled)

    def __repr__(self) -> str:
        """String representation of the registry."""
        return (
            f"<PluginRegistry "
            f"total={self.count()} "
            f"enabled={self.count_enabled()}>"
        )
