"""
AI Aikido Gateway - Main FastAPI Application

OpenAI-compatible API proxy that intelligently routes requests to save costs.
"""

import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, UTC
from pathlib import Path

from dotenv import load_dotenv
from fastapi import FastAPI, WebSocket
from fastapi.responses import JSONResponse

# Import our custom middleware
from fastapi.middleware.cors import CORSMiddleware

from src.api.middleware import TraceMiddleware
from src.api.routes import router as api_router
from src.core.config import (
    ConfigLoader,
    load_cost_alert_config,
    load_tenant_registry,
)
from src.core.logging import configure_logging
from src.core.pipeline import PluginPipeline

# Load environment variables from .env file
env_path = Path(__file__).parent.parent / ".env"
load_dotenv(dotenv_path=env_path)

# Configure structured logging
log_level_name = os.getenv("GATEWAY_LOG_LEVEL", "INFO").upper()
log_level = logging._nameToLevel.get(log_level_name, logging.INFO)  # type: ignore[attr-defined]
configure_logging(level=log_level)
logger = logging.getLogger(__name__)

# Global plugin pipeline (will be initialized during startup)
plugin_pipeline: PluginPipeline | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager for startup and shutdown events."""
    global plugin_pipeline

    # Startup
    logger.info("Starting AI Aikido Gateway...")
    logger.info("Initializing plugin system...")

    try:
        # Load plugins from configuration
        config_loader = ConfigLoader()
        plugins = config_loader.load_plugins()

        # Create plugin pipeline
        plugin_pipeline = PluginPipeline(plugins)

        # Start all plugins
        await plugin_pipeline.startup()

        logger.info(f"Plugin system initialized with {len(plugin_pipeline.get_enabled_plugins())} enabled plugins")
        
        # Store plugin pipeline and history plugin in app state for route access
        app.state.plugin_pipeline = plugin_pipeline
        logger.info("Plugin pipeline registered with app state")
        
        for plugin in plugin_pipeline.get_enabled_plugins():
            if plugin.name == "history":
                app.state.history_plugin = plugin
                logger.info("Request history plugin registered with app state")
            if plugin.name == "cache":
                app.state.cache_plugin = plugin
                logger.info("Cache plugin registered with app state")
            if plugin.name == "semantic_cache":
                app.state.semantic_cache_plugin = plugin
                logger.info("Semantic cache plugin registered with app state")
            if plugin.name == "openai_proxy":
                app.state.openai_proxy_plugin = plugin
                logger.info("OpenAI proxy plugin registered with app state")
            if plugin.name == "anthropic_proxy":
                app.state.anthropic_proxy_plugin = plugin
                logger.info("Anthropic proxy plugin registered with app state")

        # Load tenant and billing configuration
        tenant_registry = load_tenant_registry()
        app.state.tenant_registry = tenant_registry
        auth_required_env = os.getenv("GATEWAY_REQUIRE_API_KEY", "false").lower()
        app.state.auth_required = auth_required_env in {"1", "true", "yes"} and not tenant_registry.is_empty()

        cost_alerts = load_cost_alert_config()
        app.state.cost_alerts = cost_alerts
        logger.info(
            "Configuration loaded",
            extra={
                "tenants": len(tenant_registry.tenants),
                "auth_required": app.state.auth_required,
                "cost_alert_defaults": cost_alerts.default.model_dump(exclude_none=True),
            },
        )

    except Exception as e:
        logger.error(f"Failed to initialize plugin system: {e}", exc_info=True)
        raise

    yield

    # Shutdown
    logger.info("Shutting down AI Aikido Gateway...")
    if plugin_pipeline:
        await plugin_pipeline.shutdown()
    logger.info("All plugins shut down successfully")


# Create FastAPI application
app = FastAPI(
    title="AI Aikido Gateway",
    description="OpenAI-compatible API proxy with intelligent routing for cost optimization",
    version="0.1.0",
    lifespan=lifespan,
)

# Add middleware
app.add_middleware(TraceMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/v1")



@app.websocket("/ws_test")
async def websocket_test_endpoint(websocket: WebSocket):
    await websocket.accept()
    logger.info("!!! TEST WEBSOCKET CONNECTED !!!")
    await websocket.send_text("Test connection successful!")
    await websocket.close()


@app.get("/health")
async def health_check():
    """
    Health check endpoint.

    Returns the current status of the gateway and basic system information.
    """
    return JSONResponse(
        content={
            "status": "healthy",
            "service": "ai-aikido-gateway",
            "version": "0.1.0",
            "timestamp": datetime.now(UTC).isoformat(),
        }
    )


@app.get("/")
async def root():
    """Root endpoint with basic information."""
    return {
        "service": "AI Aikido Gateway",
        "version": "0.1.0",
        "description": "OpenAI-compatible API proxy with intelligent routing",
        "docs": "/docs",
        "health": "/health",
        "plugins": "/plugins",
    }


@app.get("/plugins")
async def plugins_status():
    """
    Get information about loaded plugins.

    Returns the list of all plugins with their status, priority, and configuration.
    """
    if plugin_pipeline is None:
        return JSONResponse(
            status_code=503,
            content={
                "error": "Plugin system not initialized",
                "plugins": [],
            }
        )

    all_plugins = plugin_pipeline.plugins
    enabled_plugins = plugin_pipeline.get_enabled_plugins()

    return {
        "total_plugins": len(all_plugins),
        "enabled_plugins": len(enabled_plugins),
        "plugins": [
            {
                "name": p.name,
                "enabled": p.enabled,
                "priority": p.priority,
                "class": p.__class__.__name__,
                "module": p.__class__.__module__,
            }
            for p in all_plugins
        ],
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
