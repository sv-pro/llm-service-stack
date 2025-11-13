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
                         MongoDB     Redis + DuckDB
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
- **Database**: MongoDB with Mongoose ODM
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

### Makefile (Quickest Way)

A comprehensive Makefile is provided for convenient lifecycle management:

```bash
# Quick start - build and run everything
make quickstart

# Show all available commands
make help

# Service management
make start              # Start all services
make stop               # Stop all services
make restart            # Restart all services
make status             # Show service status

# Individual services
make start-gateway      # Start only gateway
make restart-app-server # Restart only app-server
make logs-playground    # View playground logs

# Database operations
make mongo-shell        # Connect to MongoDB shell
make mongo-backup       # Backup database
make redis-flush        # Clear Redis cache

# Development
make dev-gateway        # Run gateway locally (no Docker)
make install            # Install all dependencies
make test               # Run all tests

# Cleanup
make clean              # Remove all containers and volumes
make clean-cache        # Clear all caches
```

**Most useful commands**:
- `make quickstart` - One command to build and start everything
- `make status` - Check health of all services
- `make logs` - Follow logs for all services
- `make help` - See all 50+ available commands

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
- `app/api/users/` - User management endpoints (fully implemented)
- `app/api/sessions/` - Chat session endpoints (fully implemented)
- `app/api/keys/` - API key management endpoints (fully implemented)
- `app/api/gateway/` - Gateway proxy endpoint
- `lib/db.ts` - MongoDB connection utility
- `lib/models/` - Mongoose models (User, Session, Message, ApiKey)

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
MONGODB_URI=mongodb://localhost:27017/llm_service

# Development Mode - Allow localhost requests without API keys
# Set to 'true' for local development (default in docker-compose)
# WARNING: Never enable this in production!
ALLOW_LOCALHOST_BYPASS=true
```

### Playground `.env.local`
```env
NEXT_PUBLIC_API_URL=http://localhost:3000/api
NEXT_PUBLIC_GATEWAY_URL=http://localhost:8000
```

### Web Chat `.env` (Optional)
```env
REACT_APP_API_URL=http://localhost:3000/api

# API Key is OPTIONAL for localhost development when ALLOW_LOCALHOST_BYPASS=true
# Leave empty for local development without authentication
# For production or explicit API key requirement, generate one with:
#   bash scripts/create-demo-api-key.sh
REACT_APP_API_KEY=
```

**Note on API Keys**: When `ALLOW_LOCALHOST_BYPASS=true` is set in the app-server, requests from localhost automatically bypass API key validation. This makes local development much easier - just start all services with `make quickstart` and the web-chat works immediately without any API key configuration. For production, always disable this and require proper API keys.

## Key Architecture Patterns

### Gateway Caching
The gateway implements Redis-based caching for LLM responses. Cache keys are generated from request parameters (model, messages, temperature). Cached responses are returned immediately without hitting the LLM provider.

### Cost Tracking
The `CostTracker` class in `gateway/app/cost_tracker.py` calculates costs based on token usage and model pricing. Usage logs are stored for analytics.

### OpenAI Compatibility
The gateway implements OpenAI-compatible endpoints (`/v1/chat/completions`, `/v1/models`) so it can be used as a drop-in replacement for OpenAI's API.

### Multi-Provider Routing
LiteLLM handles routing to different providers (OpenAI, Anthropic, etc.) based on the model name in the request. No provider-specific code is needed in the application layer.

### API Key Management & Localhost Bypass
The app-server gateway proxy handles API key authentication for web-chat and other clients. Two modes are supported:

**Development Mode (Localhost Bypass)**:
- Set `ALLOW_LOCALHOST_BYPASS=true` in app-server (enabled by default in docker-compose)
- Requests from localhost automatically bypass API key validation
- A "dev@localhost" user is auto-created for usage tracking
- Perfect for local development - no API key configuration needed
- The web-chat works immediately after `make quickstart`

**Production Mode (API Key Required)**:
- Set `ALLOW_LOCALHOST_BYPASS=false` or leave unset
- All requests must include a valid API key in the `Authorization: Bearer <key>` header
- API keys are hashed with bcrypt and stored in MongoDB
- Generate API keys with: `bash scripts/create-demo-api-key.sh`

**Security Notes**:
- Localhost bypass checks `X-Forwarded-For` header and `Host` header
- Only truly local requests (127.0.0.1, ::1, localhost) are allowed
- **Never enable localhost bypass in production environments**
- For production, always use proper API key authentication

**Creating API Keys**:
```bash
# Generate a new API key for the web-chat
bash scripts/create-demo-api-key.sh

# Output will show the API key (only displayed once!)
# Add to web-chat/.env.local:
echo 'REACT_APP_API_KEY=sk_...' > web-chat/.env.local

# Restart web-chat to pick up the new key
make restart-web-chat
```

### Ollama Support (Local Models)
The gateway includes built-in support for Ollama, enabling you to run LLMs locally without API costs.

**Features**:
- Automatic detection of Ollama installation on startup
- Health checks for required models
- Seamless integration with LiteLLM routing
- Cost-free local inference

**Setup**:
1. Install Ollama: https://ollama.ai
2. Start Ollama: `ollama serve`
3. Pull models: `ollama pull llama2`, `ollama pull codellama`, etc.
4. Configure in `gateway/.env`:
   ```env
   OLLAMA_API_BASE=http://localhost:11434
   OLLAMA_CHECK_MODELS=llama2,codellama
   OLLAMA_ENABLED=true
   ```

**Usage**:
```bash
# List available models (includes Ollama models if running)
curl http://localhost:8000/v1/models

# Use Ollama model via gateway
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "ollama/llama2",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

**Startup Checks**:
When the gateway starts, it automatically:
- Checks if Ollama is accessible
- Lists installed models
- Validates required models (if specified)
- Provides installation commands if models are missing

## Common Development Tasks

### Adding a New LLM Provider
1. Add provider API key to `gateway/.env`
2. LiteLLM automatically supports most major providers
3. Add model to the `/v1/models` endpoint in `gateway/app/main.py`

### Adding a New API Endpoint
- **Gateway**: Add route to `gateway/app/main.py`
- **App Server**: Create new route in `app-server/app/api/[endpoint]/route.ts`

### Database Schema (MongoDB)
The app-server uses MongoDB with Mongoose ODM. Schema is fully implemented in `lib/models/`:

**Models**:
- `User` - User accounts with email and name
- `Session` - Chat sessions linked to users
- `Message` - Individual messages within sessions
- `ApiKey` - Hashed API keys for authentication

**Key Features**:
- Automatic timestamps (createdAt, updatedAt)
- Indexes for performance optimization
- Cascading deletes for related data
- bcrypt hashing for API keys

All CRUD operations are implemented in the API routes with proper validation and error handling.

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
- MongoDB: 27017

To change Next.js ports: `PORT=4000 npm run dev`

## Troubleshooting

For comprehensive troubleshooting guidance, see **[docs/TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md)**.

This guide covers:
- **Gateway issues**: numpy dependencies, API key configuration, JSON serialization errors
- **Playground/Frontend issues**: cached builds, CORS headers, source badges
- **Caching issues**: semantic cache, Redis connections, TTL configuration
- **Docker & Environment**: environment variables, container startup, port conflicts
- **CORS issues**: cross-origin requests, header exposure
- **General debugging**: verbose logging, database inspection, clean slate procedures

### Quick fixes for common issues:

**Gateway won't start:**
```bash
docker compose logs gateway
docker compose build --no-cache gateway
```

**Playground shows old UI:**
```bash
docker compose restart playground
# Hard refresh browser: Ctrl+Shift+R
```

**Cache not working:**
```bash
docker compose exec redis redis-cli FLUSHALL
docker compose restart gateway
```

**Environment variables missing:**
```bash
# Verify .env exists in project root
ls -la .env

# Restart services
docker compose down && docker compose up -d
```
