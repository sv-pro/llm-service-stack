"""
Configuration management and plugin loader.

This module handles loading plugin configurations from YAML files and
instantiating plugin instances.
"""

import logging
import os
import sys
from datetime import datetime, timezone
from importlib import import_module
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml
from pydantic import BaseModel, Field, ValidationError

from src.core.plugin import BasePlugin, PluginRegistry

logger = logging.getLogger(__name__)


class PluginConfig:
    """
    Configuration for a single plugin.

    Attributes:
        name: Plugin name
        enabled: Whether plugin is enabled
        priority: Execution priority
        class_path: Python class path (e.g., "plugins.cost_monitor.CostMonitorPlugin")
        config: Plugin-specific configuration dict
    """

    def __init__(
        self,
        name: str,
        enabled: bool = True,
        priority: int = 50,
        class_path: Optional[str] = None,
        config: Optional[Dict[str, Any]] = None,
    ):
        self.name = name
        self.enabled = enabled
        self.priority = priority
        self.class_path = class_path
        self.config = config or {}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PluginConfig":
        """
        Create PluginConfig from dictionary.

        Args:
            data: Configuration dictionary

        Returns:
            PluginConfig instance
        """
        return cls(
            name=data["name"],
            enabled=data.get("enabled", True),
            priority=data.get("priority", 50),
            class_path=data.get("class"),
            config=data.get("config", {}),
        )

    def __repr__(self) -> str:
        return (
            f"<PluginConfig "
            f"name='{self.name}' "
            f"enabled={self.enabled} "
            f"priority={self.priority} "
            f"class='{self.class_path}'>"
        )


class ConfigLoader:
    """
    Loads plugin configurations from YAML files and instantiates plugins.
    """

    def __init__(self, config_path: Optional[Path] = None):
        """
        Initialize the config loader.

        Args:
            config_path: Path to plugins.yaml file (default: config/plugins.yaml)
        """
        if config_path is None:
            # Default to config/plugins.yaml in project root
            project_root = Path(__file__).parent.parent.parent
            config_path = project_root / "config" / "plugins.yaml"

        self.config_path = Path(config_path)
        self.logger = logging.getLogger("config")

    def load_yaml(self) -> Dict[str, Any]:
        """
        Load YAML configuration file.

        Returns:
            Configuration dictionary

        Raises:
            FileNotFoundError: If config file doesn't exist
            yaml.YAMLError: If YAML is invalid
        """
        if not self.config_path.exists():
            raise FileNotFoundError(
                f"Plugin configuration file not found: {self.config_path}"
            )

        self.logger.info(f"Loading plugin configuration from {self.config_path}")

        with open(self.config_path, "r") as f:
            config = yaml.safe_load(f)

        return config or {}

    def _expand_env_vars(self, value: Any) -> Any:
        """
        Recursively expand environment variables in configuration.

        Supports ${VAR_NAME} syntax.

        Args:
            value: Configuration value (str, dict, list, or other)

        Returns:
            Value with environment variables expanded
        """
        if isinstance(value, str):
            # Replace ${VAR_NAME} with environment variable value
            if value.startswith("${") and value.endswith("}"):
                var_name = value[2:-1]
                return os.getenv(var_name, value)
            return value
        elif isinstance(value, dict):
            return {k: self._expand_env_vars(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._expand_env_vars(item) for item in value]
        else:
            return value

    def load_plugin_configs(self) -> List[PluginConfig]:
        """
        Load all plugin configurations from YAML file.

        Returns:
            List of PluginConfig instances

        Raises:
            ValueError: If configuration is invalid
        """
        yaml_config = self.load_yaml()

        if "plugins" not in yaml_config:
            self.logger.warning("No 'plugins' section in configuration file")
            return []

        plugins_data = yaml_config["plugins"]
        if not isinstance(plugins_data, list):
            raise ValueError("'plugins' must be a list")

        plugin_configs = []
        for plugin_data in plugins_data:
            # Expand environment variables
            plugin_data = self._expand_env_vars(plugin_data)

            try:
                config = PluginConfig.from_dict(plugin_data)
                plugin_configs.append(config)
                self.logger.debug(f"Loaded config for plugin: {config.name}")
            except KeyError as e:
                raise ValueError(
                    f"Invalid plugin configuration: missing required field {e}"
                )

        self.logger.info(f"Loaded {len(plugin_configs)} plugin configurations")
        return plugin_configs

    def _import_plugin_class(self, class_path: str) -> type:
        """
        Dynamically import a plugin class from a string path.

        Args:
            class_path: Python class path (e.g., "plugins.cache.CachePlugin")

        Returns:
            Plugin class

        Raises:
            ImportError: If module or class cannot be imported
            ValueError: If class is not a BasePlugin subclass
        """
        try:
            # Split into module and class name
            module_path, class_name = class_path.rsplit(".", 1)

            # Import the module
            module = import_module(module_path)

            # Get the class
            plugin_class = getattr(module, class_name)

            # Verify it's a BasePlugin subclass
            if not issubclass(plugin_class, BasePlugin):
                raise ValueError(
                    f"Plugin class {class_path} must inherit from BasePlugin"
                )

            return plugin_class

        except (ImportError, AttributeError) as e:
            raise ImportError(
                f"Failed to import plugin class '{class_path}': {e}"
            ) from e

    def instantiate_plugin(self, config: PluginConfig) -> BasePlugin:
        """
        Instantiate a plugin from its configuration.

        Args:
            config: Plugin configuration

        Returns:
            Plugin instance

        Raises:
            ImportError: If plugin class cannot be imported
            Exception: If plugin instantiation fails
        """
        if config.class_path is None:
            raise ValueError(
                f"Plugin '{config.name}' has no 'class' specified in configuration"
            )

        self.logger.info(
            f"Instantiating plugin '{config.name}' from {config.class_path}"
        )

        # Import the plugin class
        plugin_class = self._import_plugin_class(config.class_path)

        # Instantiate the plugin
        try:
            plugin = plugin_class(
                name=config.name,
                config=config.config,
                enabled=config.enabled,
                priority=config.priority,
            )
        except Exception as e:
            raise RuntimeError(
                f"Failed to instantiate plugin '{config.name}': {e}"
            ) from e
        return plugin

    def load_plugins(self) -> List[BasePlugin]:
        """
        Load and instantiate all plugins from configuration file.

        Returns:
            List of plugin instances
        """
        plugin_configs = self.load_plugin_configs()
        plugins: List[BasePlugin] = []
        for config in plugin_configs:
            try:
                plugin = self.instantiate_plugin(config)
                plugins.append(plugin)
            except Exception as e:
                self.logger.error(
                    f"Failed to load plugin '{config.name}': {e}",
                    exc_info=True,
                )
                raise

        self.logger.info("Successfully loaded %s plugins", len(plugins))
        return plugins


class GatewayApiKeyConfig(BaseModel):
    key_id: str
    secret: str
    label: Optional[str] = None
    status: str = Field("active", pattern="^(active|disabled)$")
    scopes: List[str] = Field(default_factory=list)
    expires_at: Optional[datetime] = None

    def is_active(self) -> bool:
        if self.status != "active":
            return False
        if self.expires_at is None:
            return True
        expires_at = self.expires_at
        if expires_at.tzinfo is None:
            expires_at = expires_at.replace(tzinfo=timezone.utc)
        return expires_at > datetime.now(timezone.utc)


class TenantConfigEntry(BaseModel):
    tenant_id: str
    display_name: Optional[str] = None
    allow_provider_keys: bool = False
    rate_limit_per_minute: Optional[int] = Field(None, ge=0)
    api_keys: List[GatewayApiKeyConfig] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class TenantRegistry(BaseModel):
    tenants: Dict[str, TenantConfigEntry] = Field(default_factory=dict)

    def is_empty(self) -> bool:
        return not self.tenants

    def get(self, tenant_id: str) -> Optional[TenantConfigEntry]:
        return self.tenants.get(tenant_id)

    def find_api_key(self, secret: str) -> Optional[Tuple[TenantConfigEntry, GatewayApiKeyConfig]]:
        for tenant in self.tenants.values():
            for api_key in tenant.api_keys:
                if api_key.secret == secret and api_key.is_active():
                    return tenant, api_key
        return None


class CostThresholds(BaseModel):
    daily: Optional[float] = Field(None, ge=0)
    weekly: Optional[float] = Field(None, ge=0)
    monthly: Optional[float] = Field(None, ge=0)


class CostAlertSettings(BaseModel):
    default: CostThresholds = Field(default_factory=CostThresholds)
    tenants: Dict[str, CostThresholds] = Field(default_factory=dict)

    def get_thresholds_for(self, tenant_id: Optional[str]) -> CostThresholds:
        if tenant_id and tenant_id in self.tenants:
            return self.tenants[tenant_id]
        return self.default

    def to_dict(self) -> Dict[str, Any]:
        return {
            "default": self.default.model_dump(exclude_none=True),
            "tenants": {tenant: cfg.model_dump(exclude_none=True) for tenant, cfg in self.tenants.items()},
        }


def _resolve_config_path(filename: str) -> Path:
    project_root = Path(__file__).parent.parent.parent
    return project_root / "config" / filename


def load_tenant_registry(path: Optional[Path] = None) -> TenantRegistry:
    """
    Load tenant configuration from YAML.
    """
    registry_path = path or _resolve_config_path("tenants.yml")
    if not registry_path.exists():
        logger.info("Tenant configuration not found at %s, skipping auth scaffolding", registry_path)
        return TenantRegistry()

    with open(registry_path, "r") as handle:
        data = yaml.safe_load(handle) or {}

    tenants_raw = data.get("tenants", [])
    tenants: Dict[str, TenantConfigEntry] = {}
    for entry in tenants_raw:
        try:
            tenant = TenantConfigEntry(**entry)
            tenants[tenant.tenant_id] = tenant
        except ValidationError as exc:
            logger.error("Invalid tenant configuration entry: %s", exc)
            continue

    logger.info("Loaded %s tenant definitions", len(tenants))
    return TenantRegistry(tenants=tenants)


def load_cost_alert_config(path: Optional[Path] = None) -> CostAlertSettings:
    """
    Load cost alert thresholds from YAML.
    """
    billing_path = path or _resolve_config_path("billing.yml")
    if not billing_path.exists():
        logger.info("Billing configuration not found at %s, using defaults", billing_path)
        return CostAlertSettings()

    with open(billing_path, "r") as handle:
        data = yaml.safe_load(handle) or {}

    default_cfg = CostThresholds(**(data.get("default") or {}))
    tenant_cfgs = {
        tenant_id: CostThresholds(**thresholds)
        for tenant_id, thresholds in (data.get("tenants") or {}).items()
    }

    logger.info(
        "Loaded cost alert configuration",
        extra={"tenants_with_overrides": len(tenant_cfgs)},
    )
    return CostAlertSettings(default=default_cfg, tenants=tenant_cfgs)

# Ensure module is importable via both 'core.config' and 'src.core.config'
_current_module = sys.modules[__name__]
sys.modules.setdefault("core.config", _current_module)
sys.modules.setdefault("src.core.config", _current_module)
