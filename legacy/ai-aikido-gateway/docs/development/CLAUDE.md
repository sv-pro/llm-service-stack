# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**AI Aikido Gateway** is an OpenAI-compatible API proxy with a plugin-first architecture that provides modular, composable functionality for LLM request handling. The gateway enables cost monitoring, caching, intelligent routing, and other concerns through an extensible plugin system.

**Current Priority**: Cost monitoring and tracking as the foundational plugin.

## Architecture

### Plugin-First Design Philosophy

The gateway is built around a **modular plugin system** where each concern (cost monitoring, caching, routing, etc.) is implemented as an independent, composable plugin. Plugins can be enabled/disabled via configuration without code changes.

**Core Principles:**
- Each plugin handles one concern (single responsibility)
- Plugins are composable and can work together
- Plugins can be enabled/disabled independently
- Minimal core - maximum extensibility

### Core Components

**Three-Layer Architecture:**

1. **src/core/** - Minimal core infrastructure
   - `plugin.py`: Base plugin class and plugin manager/registry
   - `pipeline.py`: Plugin execution pipeline (request/response flow)
   - `config.py`: Configuration management and plugin loading
   - `context.py`: Request context shared across plugins

2. **src/plugins/** - Extensible plugin system
   - `cost_monitor.py`: **[PRIORITY]** Cost tracking and analytics plugin
   - `cache.py`: Response caching plugin (future)
   - `router.py`: Intelligent model routing plugin (future)
   - `openai_proxy.py`: OpenAI API proxy plugin
   - `anthropic_proxy.py`: Anthropic API proxy plugin

3. **src/api/** - FastAPI application layer
   - `routes.py`: API endpoint definitions
   - `models.py`: Pydantic models for request/response validation
   - `middleware.py`: Request middleware for plugin pipeline
   - `main.py`: FastAPI application entry point

### Request Flow (Plugin Pipeline)

1. **Client** sends OpenAI-compatible request to gateway
2. **Pipeline** executes plugins in configured order:
   - **Pre-request hooks**: Cost estimation, cache check, routing decisions
   - **Request execution**: Proxy to LLM provider
   - **Post-response hooks**: Cost tracking, cache storage, metrics update
3. **Response** returned to client in OpenAI format

### Plugin Lifecycle Hooks

Each plugin can implement these hooks:
- `on_startup()`: Initialize plugin (load config, connect to databases)
- `on_shutdown()`: Cleanup resources
- `before_request(context)`: Pre-process request (modify, route, check cache)
- `after_response(context)`: Post-process response (track costs, cache, log)
- `on_error(context, error)`: Handle errors

## Development Commands

### Environment Setup

```bash
# Activate virtual environment (pyenv auto-activates with .python-version file)
pyenv activate aikido-env

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Running the Gateway

```bash
# Development with hot reload
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# With debug logging
uvicorn src.main:app --reload --log-level debug

# Using Docker
docker-compose up --build
```

### Testing

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_classifier.py

# Run single test
pytest tests/test_classifier.py::test_function_name -v
```

### Code Quality

```bash
# Format code (required before commits)
black src/ tests/

# Lint code
ruff check src/ tests/

# Fix linting issues automatically
ruff check src/ tests/ --fix

# Type checking
mypy src/
```

## Configuration

### Environment Variables

Required in `.env` file (copy from `.env.example`):
- `ANTHROPIC_API_KEY`: Anthropic API key for Claude models
- `OPENAI_API_KEY`: OpenAI API key
- `GATEWAY_HOST`: Host to bind to (default: 0.0.0.0)
- `GATEWAY_PORT`: Port to listen on (default: 8000)
- `LOG_LEVEL`: Logging level (INFO, DEBUG, WARNING, ERROR)

### YAML Configuration

- `config/aikido.yaml`: Main gateway configuration (routing rules, model mappings)
- `config/plugins.yaml`: Plugin-specific configurations

## Python Environment

- **Python Version**: 3.11+ (managed via pyenv)
- **Virtual Environment**: `aikido-env` (pyenv virtualenv)
- **Package Management**: pip with requirements.txt files

The `.python-version` file ensures automatic environment activation when entering the directory.

## Plugin Development

### Creating a New Plugin

Plugins extend gateway functionality. Base plugin class in `src/core/plugin.py` provides:
- Lifecycle hooks (startup, shutdown, before_request, after_response, on_error)
- Async processing support
- Configuration injection
- Access to shared request context

**Steps to create a new plugin:**

1. **Inherit from BasePlugin** in `src/plugins/your_plugin.py`:
```python
from core.plugin import BasePlugin
from core.context import RequestContext

class YourPlugin(BasePlugin):
    async def on_startup(self):
        # Initialize resources
        pass

    async def before_request(self, context: RequestContext):
        # Pre-process request
        pass

    async def after_response(self, context: RequestContext):
        # Post-process response
        pass
```

2. **Register in `config/plugins.yaml`**:
```yaml
plugins:
  - name: your_plugin
    enabled: true
    class: plugins.your_plugin.YourPlugin
    config:
      setting1: value1
```

3. **Add to `src/plugins/__init__.py`**:
```python
from .your_plugin import YourPlugin
```

### Plugin Configuration

Each plugin receives its config section from `plugins.yaml` via the constructor:
```python
def __init__(self, config: dict):
    self.config = config
```

## Testing the Gateway

### Manual Testing Script

```bash
python scripts/test_gateway.py
```

### cURL Testing

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

### Health Check

```bash
curl http://localhost:8000/health
```

## API Documentation

Interactive API docs available at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Code Style

- **Line Length**: 100 characters
- **Formatter**: Black
- **Linter**: Ruff
- **Type Checker**: mypy (enforce type hints)
- **Target Version**: Python 3.11

Pre-commit hooks enforce formatting and linting automatically.

## Import Structure

Source code is in `src/` directory. When importing:

```python
# Correct imports
from core.classifier import Classifier
from plugins.cache import CachePlugin
from api.models import ChatRequest

# NOT
from src.core.classifier import Classifier  # Wrong
```

If import errors occur, install package in editable mode:
```bash
pip install -e .
```
