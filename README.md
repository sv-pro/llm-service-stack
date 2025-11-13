# LLM Service Stack

A modular backend stack for building your own ChatGPT-style LLM service: gateway, API server, developer studio, dashboard, and reference web client.

## Architecture

```
┌────────────┐
│  web-chat  │ (React chat client)
└─────┬──────┘
      │
      ▼
┌─────────────┐
│ playground  │ (Next.js control panel)
└─────┬───────┘
      │
      ▼
┌─────────────┐      ┌──────────┐
│ app-server  │─────▶│ gateway  │ (FastAPI + LiteLLM)
│ (Next.js)   │      │          │
└─────┬───────┘      └────┬─────┘
      │                   │
      ▼                   ▼
┌──────────┐         ┌─────────┐
│ Database │         │  Redis  │
└──────────┘         └─────────┘
```

## Components

### 1. Gateway (FastAPI + LiteLLM)
**Location**: `gateway/`

FastAPI-based LLM gateway with intelligent routing, caching, and cost tracking.

**Features**:
- 🔀 Multi-provider LLM routing via LiteLLM (OpenAI, Anthropic, etc.)
- 🌐 OpenAI-compatible API endpoints
- 💾 Redis-based response caching
- 💰 Cost tracking and usage analytics
- 📊 SQLite/DuckDB usage logs

**Tech Stack**: Python, FastAPI, LiteLLM, SQLAlchemy, DuckDB, Redis

### 2. App Server (Next.js)
**Location**: `app-server/`

Backend API server for user management, chat sessions, and API keys.

**Features**:
- 👤 User management
- 💬 Chat session storage
- 🔑 API key generation and management
- 🔀 Gateway request forwarding
- 🔐 Authentication and authorization

**Tech Stack**: Next.js 14, TypeScript, React

### 3. Playground (Next.js)
**Location**: `playground/`

Developer control panel for testing, monitoring, and analytics.

**Features**:
- 🎨 **Prompt Studio**: Interactive prompt testing environment
- 🔍 **Usage Inspector**: Detailed usage logs and analytics
- 📊 **Dashboard**: System overview and key metrics
- 📈 Real-time charts and statistics

**Tech Stack**: Next.js 14, TypeScript, React, TailwindCSS

### 4. Web Chat (React)
**Location**: `web-chat/`

Minimal chat client for end-users.

**Features**:
- 💬 Clean chat interface
- 🔑 API key authentication
- ⚡ Real-time responses
- 📝 Message history

**Tech Stack**: React, TypeScript

## Quick Start

### Prerequisites

- **Python 3.9+** (for gateway)
- **Node.js 18+** (for app-server, playground, web-chat)
- **Redis** (optional, for caching)
- **Docker & Docker Compose** (optional, for containerized setup)

### Option 1: Docker Compose (Recommended)

```bash
# Start all services
docker-compose up -d

# Gateway: http://localhost:8000
# App Server: http://localhost:3000
# Playground: http://localhost:3001
# Web Chat: http://localhost:3002
```

### Option 2: Manual Setup

#### 1. Gateway Service

```bash
cd gateway
pip install -r requirements.txt
cp .env.example .env
# Edit .env with your API keys
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

#### 2. App Server

```bash
cd app-server
npm install
cp .env.example .env.local
# Edit .env.local
npm run dev
```

#### 3. Playground

```bash
cd playground
npm install
npm run dev
```

#### 4. Web Chat

```bash
cd web-chat
npm install
cp .env.example .env
# Edit .env with API URL and key
npm start
```

## Configuration

### Gateway Configuration

Edit `gateway/.env`:

```env
OPENAI_API_KEY=your_openai_key
ANTHROPIC_API_KEY=your_anthropic_key
REDIS_URL=redis://localhost:6379
DATABASE_URL=duckdb:///./gateway.db
```

### App Server Configuration

Edit `app-server/.env.local`:

```env
GATEWAY_URL=http://localhost:8000
DATABASE_URL=postgresql://user:password@localhost:5432/llm_service
```

### Playground Configuration

Edit `playground/.env.local`:

```env
NEXT_PUBLIC_API_URL=http://localhost:3000/api
```

### Web Chat Configuration

Edit `web-chat/.env`:

```env
REACT_APP_API_URL=http://localhost:3000/api
REACT_APP_API_KEY=your_api_key
```

## API Documentation

### Gateway API

- `GET /` - Health check
- `GET /v1/models` - List available models
- `POST /v1/chat/completions` - Chat completions (OpenAI-compatible)
- `GET /v1/usage/stats` - Usage statistics

### App Server API

- `GET/POST/PUT/DELETE /api/users` - User management
- `GET/POST/PUT/DELETE /api/sessions` - Chat sessions
- `GET/POST/DELETE /api/keys` - API key management
- `POST /api/gateway` - Gateway proxy

## Development

### Running Tests

```bash
# Gateway
cd gateway
pytest

# App Server
cd app-server
npm test

# Playground
cd playground
npm test

# Web Chat
cd web-chat
npm test
```

### Building for Production

```bash
# Gateway
cd gateway
# Deploy with gunicorn or uvicorn

# App Server
cd app-server
npm run build
npm start

# Playground
cd playground
npm run build
npm start

# Web Chat
cd web-chat
npm run build
```

## Project Structure

```
llm-service-stack/
├── gateway/              # FastAPI LLM gateway
│   ├── app/
│   │   ├── main.py      # FastAPI application
│   │   ├── config.py    # Configuration
│   │   ├── models.py    # Database models
│   │   ├── cache.py     # Redis caching
│   │   └── cost_tracker.py
│   ├── requirements.txt
│   └── README.md
├── app-server/          # Next.js backend
│   ├── app/
│   │   └── api/         # API routes
│   ├── lib/
│   │   └── db.ts        # Database utilities
│   └── README.md
├── playground/          # Next.js control panel
│   ├── app/
│   │   ├── dashboard/
│   │   ├── prompt-studio/
│   │   └── usage-inspector/
│   ├── components/
│   └── README.md
├── web-chat/            # React chat client
│   ├── src/
│   │   ├── components/
│   │   ├── services/
│   │   └── types/
│   └── README.md
├── docker-compose.yml
└── README.md
```

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Built with [FastAPI](https://fastapi.tiangolo.com/)
- [LiteLLM](https://github.com/BerriAI/litellm) for LLM routing
- [Next.js](https://nextjs.org/) for the frontend
- [React](https://reactjs.org/) for the UI
