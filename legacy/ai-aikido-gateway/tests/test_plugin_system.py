"""
Tests for the plugin system.

Tests cover:
- BasePlugin interface
- PluginRegistry
- RequestContext
- PluginPipeline
- ConfigLoader
"""

import pytest
from pathlib import Path
import tempfile
import yaml

from core.context import RequestContext
from core.plugin import BasePlugin, PluginRegistry
from core.pipeline import PluginPipeline
from core.config import ConfigLoader, PluginConfig
from plugins.example import ExampleLoggerPlugin


# Test Plugin for testing purposes
class TestPlugin(BasePlugin):
    """Simple test plugin for unit tests."""

    def __init__(self, name: str, **kwargs):
        super().__init__(name=name, **kwargs)
        self.startup_called = False
        self.shutdown_called = False
        self.before_request_called = False
        self.after_response_called = False
        self.error_called = False

    async def on_startup(self):
        self.startup_called = True

    async def on_shutdown(self):
        self.shutdown_called = True

    async def before_request(self, context: RequestContext):
        self.before_request_called = True
        context.set_metadata(f"{self.name}_before", True)

    async def after_response(self, context: RequestContext):
        self.after_response_called = True
        context.set_metadata(f"{self.name}_after", True)

    async def on_error(self, context: RequestContext, error: Exception):
        self.error_called = True
        return await super().on_error(context, error)


class TestRequestContext:
    """Tests for RequestContext."""

    def test_context_creation(self):
        """Test creating a context."""
        ctx = RequestContext()
        assert ctx.request_id is not None
        assert ctx.timestamp is not None
        assert ctx.request is None
        assert ctx.response is None
        assert len(ctx.metadata) == 0
        assert len(ctx.errors) == 0
        assert ctx.stopped is False

    def test_metadata_operations(self):
        """Test metadata get/set operations."""
        ctx = RequestContext()

        # Set metadata
        ctx.set_metadata("key1", "value1")
        ctx.set_metadata("key2", 42)

        # Get metadata
        assert ctx.get_metadata("key1") == "value1"
        assert ctx.get_metadata("key2") == 42
        assert ctx.get_metadata("nonexistent") is None
        assert ctx.get_metadata("nonexistent", "default") == "default"

        # Has metadata
        assert ctx.has_metadata("key1") is True
        assert ctx.has_metadata("nonexistent") is False

    def test_error_operations(self):
        """Test error operations."""
        ctx = RequestContext()

        assert ctx.has_errors() is False

        # Add errors
        error1 = ValueError("test error 1")
        error2 = RuntimeError("test error 2")

        ctx.add_error(error1)
        assert ctx.has_errors() is True
        assert len(ctx.errors) == 1

        ctx.add_error(error2)
        assert len(ctx.errors) == 2
        assert ctx.errors[0] == error1
        assert ctx.errors[1] == error2

    def test_pipeline_control(self):
        """Test pipeline control methods."""
        ctx = RequestContext()

        assert ctx.should_continue() is True
        assert ctx.stopped is False

        ctx.stop_pipeline()
        assert ctx.should_continue() is False
        assert ctx.stopped is True


class TestPluginRegistry:
    """Tests for PluginRegistry."""

    def test_register_plugin(self):
        """Test registering plugins."""
        registry = PluginRegistry()

        plugin1 = TestPlugin("plugin1", priority=10)
        plugin2 = TestPlugin("plugin2", priority=20)

        registry.register(plugin1)
        registry.register(plugin2)

        assert registry.count() == 2
        assert registry.get("plugin1") == plugin1
        assert registry.get("plugin2") == plugin2

    def test_register_duplicate_fails(self):
        """Test that registering duplicate name fails."""
        registry = PluginRegistry()

        plugin1 = TestPlugin("duplicate")
        plugin2 = TestPlugin("duplicate")

        registry.register(plugin1)

        with pytest.raises(ValueError, match="already registered"):
            registry.register(plugin2)

    def test_unregister_plugin(self):
        """Test unregistering plugins."""
        registry = PluginRegistry()

        plugin = TestPlugin("plugin")
        registry.register(plugin)
        assert registry.count() == 1

        registry.unregister("plugin")
        assert registry.count() == 0
        assert registry.get("plugin") is None

    def test_unregister_nonexistent_fails(self):
        """Test that unregistering nonexistent plugin fails."""
        registry = PluginRegistry()

        with pytest.raises(KeyError, match="not registered"):
            registry.unregister("nonexistent")

    def test_get_enabled_plugins(self):
        """Test getting enabled plugins."""
        registry = PluginRegistry()

        plugin1 = TestPlugin("plugin1", enabled=True, priority=30)
        plugin2 = TestPlugin("plugin2", enabled=False, priority=10)
        plugin3 = TestPlugin("plugin3", enabled=True, priority=20)

        registry.register(plugin1)
        registry.register(plugin2)
        registry.register(plugin3)

        enabled = registry.get_enabled_plugins()
        assert len(enabled) == 2
        # Should be sorted by priority
        assert enabled[0].name == "plugin3"  # priority 20
        assert enabled[1].name == "plugin1"  # priority 30

    def test_count_enabled(self):
        """Test counting enabled plugins."""
        registry = PluginRegistry()

        registry.register(TestPlugin("plugin1", enabled=True))
        registry.register(TestPlugin("plugin2", enabled=False))
        registry.register(TestPlugin("plugin3", enabled=True))

        assert registry.count() == 3
        assert registry.count_enabled() == 2


@pytest.mark.asyncio
class TestPluginPipeline:
    """Tests for PluginPipeline."""

    async def test_startup_shutdown(self):
        """Test startup and shutdown lifecycle."""
        plugin1 = TestPlugin("plugin1")
        plugin2 = TestPlugin("plugin2")

        pipeline = PluginPipeline([plugin1, plugin2])

        # Startup
        await pipeline.startup()
        assert plugin1.startup_called is True
        assert plugin2.startup_called is True

        # Shutdown
        await pipeline.shutdown()
        assert plugin1.shutdown_called is True
        assert plugin2.shutdown_called is True

    async def test_disabled_plugins_skipped(self):
        """Test that disabled plugins are skipped."""
        plugin1 = TestPlugin("plugin1", enabled=True)
        plugin2 = TestPlugin("plugin2", enabled=False)

        pipeline = PluginPipeline([plugin1, plugin2])

        await pipeline.startup()
        assert plugin1.startup_called is True
        assert plugin2.startup_called is False

    async def test_before_request_execution(self):
        """Test before_request hook execution."""
        plugin1 = TestPlugin("plugin1", priority=10)
        plugin2 = TestPlugin("plugin2", priority=20)

        pipeline = PluginPipeline([plugin1, plugin2])

        context = RequestContext(request={"test": "data"})
        await pipeline.execute_before_request(context)

        assert plugin1.before_request_called is True
        assert plugin2.before_request_called is True

        # Check metadata was set by plugins
        assert context.get_metadata("plugin1_before") is True
        assert context.get_metadata("plugin2_before") is True

    async def test_after_response_execution(self):
        """Test after_response hook execution."""
        plugin1 = TestPlugin("plugin1", priority=10)
        plugin2 = TestPlugin("plugin2", priority=20)

        pipeline = PluginPipeline([plugin1, plugin2])

        context = RequestContext(
            request={"test": "data"},
            response={"result": "success"}
        )
        await pipeline.execute_after_response(context)

        assert plugin1.after_response_called is True
        assert plugin2.after_response_called is True

        # Check metadata was set
        assert context.get_metadata("plugin1_after") is True
        assert context.get_metadata("plugin2_after") is True

    async def test_pipeline_stops_on_stop_signal(self):
        """Test that pipeline stops when context.stop_pipeline() is called."""

        class StopperPlugin(TestPlugin):
            async def before_request(self, context: RequestContext):
                await super().before_request(context)
                context.stop_pipeline()

        plugin1 = StopperPlugin("stopper", priority=10)
        plugin2 = TestPlugin("plugin2", priority=20)

        pipeline = PluginPipeline([plugin1, plugin2])

        context = RequestContext(request={"test": "data"})
        await pipeline.execute_before_request(context)

        # First plugin runs
        assert plugin1.before_request_called is True
        # Second plugin should be skipped
        assert plugin2.before_request_called is False

    async def test_error_handling(self):
        """Test error handling in pipeline."""

        class ErrorPlugin(TestPlugin):
            async def before_request(self, context: RequestContext):
                raise ValueError("Test error")

        plugin = ErrorPlugin("error_plugin")
        pipeline = PluginPipeline([plugin])

        context = RequestContext(request={"test": "data"})

        # Error should propagate
        with pytest.raises(ValueError, match="Test error"):
            await pipeline.execute_before_request(context)

        # Error should be added to context
        assert len(context.errors) == 1

    async def test_handle_error_hook(self):
        """Test on_error hook execution."""
        plugin = TestPlugin("plugin")
        pipeline = PluginPipeline([plugin])

        context = RequestContext()
        error = RuntimeError("test error")

        result = await pipeline.handle_error(context, error)

        assert plugin.error_called is True
        assert len(context.errors) == 1
        assert context.errors[0] == error
        assert result is None  # No custom response


class TestPluginConfig:
    """Tests for PluginConfig."""

    def test_plugin_config_creation(self):
        """Test creating PluginConfig."""
        config = PluginConfig(
            name="test_plugin",
            enabled=True,
            priority=10,
            class_path="plugins.test.TestPlugin",
            config={"key": "value"}
        )

        assert config.name == "test_plugin"
        assert config.enabled is True
        assert config.priority == 10
        assert config.class_path == "plugins.test.TestPlugin"
        assert config.config == {"key": "value"}

    def test_plugin_config_from_dict(self):
        """Test creating PluginConfig from dictionary."""
        data = {
            "name": "test_plugin",
            "enabled": False,
            "priority": 20,
            "class": "plugins.test.TestPlugin",
            "config": {"setting": 123}
        }

        config = PluginConfig.from_dict(data)

        assert config.name == "test_plugin"
        assert config.enabled is False
        assert config.priority == 20
        assert config.class_path == "plugins.test.TestPlugin"
        assert config.config == {"setting": 123}

    def test_plugin_config_defaults(self):
        """Test PluginConfig defaults."""
        config = PluginConfig(name="test")

        assert config.enabled is True
        assert config.priority == 50
        assert config.class_path is None
        assert config.config == {}


class TestConfigLoader:
    """Tests for ConfigLoader."""

    def test_load_yaml_file(self):
        """Test loading YAML configuration file."""
        # Create temporary YAML file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml_content = {
                "plugins": [
                    {
                        "name": "test_plugin",
                        "enabled": True,
                        "priority": 10,
                        "class": "plugins.example.ExampleLoggerPlugin",
                        "config": {"log_level": "DEBUG"}
                    }
                ]
            }
            yaml.dump(yaml_content, f)
            temp_path = f.name

        try:
            loader = ConfigLoader(config_path=Path(temp_path))
            config = loader.load_yaml()

            assert "plugins" in config
            assert len(config["plugins"]) == 1
        finally:
            Path(temp_path).unlink()

    def test_load_plugin_configs(self):
        """Test loading plugin configurations."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml_content = {
                "plugins": [
                    {
                        "name": "plugin1",
                        "enabled": True,
                        "priority": 10,
                        "class": "plugins.example.ExampleLoggerPlugin"
                    },
                    {
                        "name": "plugin2",
                        "enabled": False,
                        "priority": 20,
                        "class": "plugins.example.ExampleLoggerPlugin",
                        "config": {"setting": "value"}
                    }
                ]
            }
            yaml.dump(yaml_content, f)
            temp_path = f.name

        try:
            loader = ConfigLoader(config_path=Path(temp_path))
            configs = loader.load_plugin_configs()

            assert len(configs) == 2
            assert configs[0].name == "plugin1"
            assert configs[0].enabled is True
            assert configs[1].name == "plugin2"
            assert configs[1].enabled is False
        finally:
            Path(temp_path).unlink()

    def test_instantiate_plugin(self):
        """Test instantiating a plugin from configuration."""
        loader = ConfigLoader()

        config = PluginConfig(
            name="example",
            enabled=True,
            priority=10,
            class_path="plugins.example.ExampleLoggerPlugin",
            config={"log_level": "INFO"}
        )

        plugin = loader.instantiate_plugin(config)

        assert isinstance(plugin, ExampleLoggerPlugin)
        assert plugin.name == "example"
        assert plugin.enabled is True
        assert plugin.priority == 10
        assert plugin.config == {"log_level": "INFO"}


# Integration test
@pytest.mark.asyncio
async def test_full_plugin_lifecycle():
    """Integration test: full plugin lifecycle."""
    # Create plugins
    plugin1 = TestPlugin("plugin1", priority=10)
    plugin2 = TestPlugin("plugin2", priority=20)

    # Create pipeline
    pipeline = PluginPipeline([plugin1, plugin2])

    # Startup
    await pipeline.startup()

    # Process request
    context = RequestContext(request={"test": "request"})
    await pipeline.execute_before_request(context)

    # Simulate LLM response
    context.response = {"result": "response"}

    # Process response
    await pipeline.execute_after_response(context)

    # Shutdown
    await pipeline.shutdown()

    # Verify all lifecycle hooks were called
    assert plugin1.startup_called
    assert plugin1.before_request_called
    assert plugin1.after_response_called
    assert plugin1.shutdown_called

    assert plugin2.startup_called
    assert plugin2.before_request_called
    assert plugin2.after_response_called
    assert plugin2.shutdown_called
