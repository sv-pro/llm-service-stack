# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**LLM Service Stack** is a modular backend stack for building ChatGPT-style LLM services. The system consists of four main components:

1. **Gateway** (FastAPI + LiteLLM) - LLM routing, caching, and cost tracking
2. **App Server** (Next.js) - User management, sessions, and API keys
3. **Playground** (Next.js) - Developer control panel for testing and analytics
4. **Web Chat** (React) - End-user chat interface

## Architecture

The system follows a layered architecture where the web chat and playground communicate with the app-server, which proxies requests to the gateway. The gateway handles all LLM provider interactions via LiteLLM.

```
web-chat + playground → app-server → gateway → LLM providers (OpenAI, Anthropic, etc.)
                            ↓            ↓
                        PostgreSQL    Redis + DuckDB
```

## Technology Stack

### Gateway (`gateway/`)
- **Language**: Python 3.9+
- **Framework**: FastAPI
- **Key Dependencies**: LiteLLM, SQLAlchemy, DuckDB, Redis
- **Purpose**: OpenAI-compatible API with multi-provider routing, response caching, and cost tracking

### App Server (`app-server/`)
- **Language**: TypeScript
- **Framework**: Next.js 14 (App Router)
- **Purpose**: User management, chat sessions, API key management, gateway proxy

### Playground (`playground/`)
- **Language**: TypeScript
- **Framework**: Next.js 14 (App Router)
- **Features**: Dashboard, Prompt Studio, Usage Inspector
- **Purpose**: Developer tools for testing and monitoring

### Web Chat (`web-chat/`)
- **Language**: TypeScript
- **Framework**: React (Create React App)
- **Purpose**: End-user chat interface

## Development Commands

### Docker Compose (Recommended)

```bash
# Start all services
docker-compose up -d

# Stop all services
docker-compose down

# View logs
docker-compose logs -f [service-name]

# Rebuild after changes
docker-compose build --no-cache
docker-compose up -d
```

Services run on:
- Gateway: http://localhost:8000
- App Server: http://localhost:3000
- Playground: http://localhost:3001
- Web Chat: http://localhost:3002

### Gateway (Python/FastAPI)

```bash
cd gateway

# Install dependencies
pip install -r requirements.txt

# Run development server with auto-reload
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Run tests
pytest

# Run with verbose LiteLLM logging
LITELLM_VERBOSE=true uvicorn app.main:app --reload
```

**Key files**:
- `app/main.py` - FastAPI application and endpoints
- `app/config.py` - Configuration and environment variables
- `app/cache.py` - Redis caching implementation
- `app/cost_tracker.py` - Cost tracking logic
- `app/database.py` - Database initialization
- `app/models.py` - SQLAlchemy models

### App Server (Next.js)

```bash
cd app-server

# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Run production build
npm start

# Run tests
npm test

# Lint
npm run lint
```

**Key directories**:
- `app/api/users/` - User management endpoints
- `app/api/sessions/` - Chat session endpoints
- `app/api/keys/` - API key management endpoints
- `app/api/gateway/` - Gateway proxy endpoint
- `lib/db.ts` - Database utilities (scaffolded)

### Playground (Next.js)

```bash
cd playground

# Install dependencies
npm install

# Run development server (uses PORT env var or 3000)
npm run dev
PORT=3001 npm run dev  # Run on different port

# Build and run
npm run build
npm start

# Run tests
npm test
```

**Key directories**:
- `app/dashboard/` - System overview and metrics
- `app/prompt-studio/` - Interactive prompt testing
- `app/usage-inspector/` - Usage logs and analytics
- `components/` - Shared React components

### Web Chat (React)

```bash
cd web-chat

# Install dependencies
npm install

# Run development server
npm start

# Build for production
npm run build

# Run tests
npm test
```

**Key directories**:
- `src/components/` - React components
- `src/services/` - API client services
- `src/types/` - TypeScript type definitions

## Testing the Gateway API

```bash
# Health check
curl http://localhost:8000/

# List available models
curl http://localhost:8000/v1/models

# Send chat completion request
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Hello!"}],
    "temperature": 0.7
  }'

# Get usage statistics
curl http://localhost:8000/v1/usage/stats
```

## Configuration

All services use environment variables for configuration:

### Gateway `.env`
```env
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
REDIS_URL=redis://localhost:6379
DATABASE_URL=duckdb:///./gateway.db
LITELLM_VERBOSE=false
```

### App Server `.env.local`
```env
GATEWAY_URL=http://localhost:8000
DATABASE_URL=postgresql://user:password@localhost:5432/llm_service
```

### Playground `.env.local`
```env
NEXT_PUBLIC_API_URL=http://localhost:3000/api
```

### Web Chat `.env`
```env
REACT_APP_API_URL=http://localhost:3000/api
REACT_APP_API_KEY=your_api_key
```

## Key Architecture Patterns

### Gateway Caching
The gateway implements Redis-based caching for LLM responses. Cache keys are generated from request parameters (model, messages, temperature). Cached responses are returned immediately without hitting the LLM provider.

### Cost Tracking
The `CostTracker` class in `gateway/app/cost_tracker.py` calculates costs based on token usage and model pricing. Usage logs are stored for analytics.

### OpenAI Compatibility
The gateway implements OpenAI-compatible endpoints (`/v1/chat/completions`, `/v1/models`) so it can be used as a drop-in replacement for OpenAI's API.

### Multi-Provider Routing
LiteLLM handles routing to different providers (OpenAI, Anthropic, etc.) based on the model name in the request. No provider-specific code is needed in the application layer.

## Common Development Tasks

### Adding a New LLM Provider
1. Add provider API key to `gateway/.env`
2. LiteLLM automatically supports most major providers
3. Add model to the `/v1/models` endpoint in `gateway/app/main.py`

### Adding a New API Endpoint
- **Gateway**: Add route to `gateway/app/main.py`
- **App Server**: Create new route in `app-server/app/api/[endpoint]/route.ts`

### Implementing Database Schema
The app-server has placeholder database functions in `lib/db.ts`. To implement:
1. Choose database solution (PostgreSQL recommended)
2. Add migration tool (Prisma, Drizzle, or raw SQL)
3. Implement schema for users, sessions, and API keys
4. Update API routes to use real database queries

### Adding Authentication
Current implementation is scaffolded without authentication. To add:
1. Install NextAuth.js or similar for app-server
2. Add authentication middleware to API routes
3. Implement JWT validation in gateway
4. Add user context to all services

## Port Configuration

Default ports:
- Gateway: 8000
- App Server: 3000
- Playground: 3001 (or set via `PORT` env var)
- Web Chat: 3002 (or 3000 for standalone)
- Redis: 6379
- PostgreSQL: 5432

To change Next.js ports: `PORT=4000 npm run dev`

## Troubleshooting

### Gateway won't start
- Verify Python 3.9+ is installed
- Check API keys are set in `.env`
- Ensure Redis is running if using cache
- Run `pip install -r requirements.txt`

### Next.js services won't start
- Delete `node_modules` and reinstall: `rm -rf node_modules && npm install`
- Check port conflicts: `lsof -ti:3000 | xargs kill -9`
- Clear Next.js cache: `rm -rf .next`

### Docker services fail
- Check logs: `docker-compose logs [service-name]`
- Rebuild: `docker-compose build --no-cache`
- Verify environment variables in `.env`
