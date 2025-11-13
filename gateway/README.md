# LLM Gateway Service

FastAPI-based LLM gateway with LiteLLM routing, OpenAI-compatible API, caching, and cost tracking.

## Features

- 🚀 **OpenAI-Compatible API**: Drop-in replacement for OpenAI API endpoints
- 🔀 **LiteLLM Routing**: Support for multiple LLM providers (OpenAI, Anthropic, etc.)
- 💾 **Response Caching**: Redis-based caching for improved performance
- 💰 **Cost Tracking**: Track usage and costs across models and users
- 📊 **Usage Logs**: SQLite/DuckDB for storing detailed usage analytics
- ⚡ **Fast & Async**: Built on FastAPI with async support

## Setup

### Prerequisites

- Python 3.9+
- Redis (optional, for caching)

### Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your API keys and settings
```

3. Run the service:
```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## API Endpoints

### Health Check
```
GET /
```

### List Models
```
GET /v1/models
```

### Chat Completions (OpenAI-compatible)
```
POST /v1/chat/completions
Content-Type: application/json

{
  "model": "gpt-3.5-turbo",
  "messages": [
    {"role": "user", "content": "Hello!"}
  ],
  "temperature": 0.7
}
```

### Usage Statistics
```
GET /v1/usage/stats
```

## Configuration

See `.env.example` for all available configuration options.

Key settings:
- `OPENAI_API_KEY`: Your OpenAI API key
- `ANTHROPIC_API_KEY`: Your Anthropic API key
- `REDIS_URL`: Redis connection URL for caching
- `DATABASE_URL`: DuckDB database path
- `CACHE_ENABLED`: Enable/disable response caching

## Database Schema

### UsageLog
Stores detailed request/response logs:
- timestamp, model, provider
- token counts (prompt, completion, total)
- cost, latency
- user_id, api_key_id
- request/response data
- cache_hit flag

### CostTracking
Aggregated cost statistics:
- date, model
- total requests/tokens/cost
- per-user tracking

## Development

Run with auto-reload:
```bash
uvicorn app.main:app --reload
```

Run tests:
```bash
pytest
```

## Architecture

```
┌─────────────┐
│   Client    │
└──────┬──────┘
       │
       ▼
┌─────────────┐
│  FastAPI    │
│  Gateway    │
└──────┬──────┘
       │
       ├──► Redis (Cache)
       │
       ├──► LiteLLM ──► OpenAI/Anthropic/etc
       │
       └──► SQLite/DuckDB (Logs)
```
