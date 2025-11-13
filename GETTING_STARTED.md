# Getting Started with LLM Service Stack

This guide will help you get the LLM Service Stack up and running quickly.

## Prerequisites

Before you begin, ensure you have the following installed:

- **Docker & Docker Compose** (recommended for quick setup)
  - OR -
- **Python 3.9+** (for gateway)
- **Node.js 18+** (for app-server, playground, web-chat)
- **Redis** (optional, for caching)
- **PostgreSQL** (optional, for app-server database)

## API Keys

You'll need API keys from LLM providers:

1. **OpenAI API Key**: Get from [platform.openai.com](https://platform.openai.com/)
2. **Anthropic API Key** (optional): Get from [console.anthropic.com](https://console.anthropic.com/)

## Quick Start with Docker Compose

The fastest way to get everything running:

### 1. Configure Environment

```bash
# Copy the example environment file
cp .env.example .env

# Edit .env and add your API keys
nano .env  # or use your preferred editor
```

Add your keys:
```env
OPENAI_API_KEY=sk-...your-key-here...
ANTHROPIC_API_KEY=sk-ant-...your-key-here...
```

### 2. Start All Services

```bash
docker-compose up -d
```

This will start:
- **Gateway** at http://localhost:8000
- **App Server** at http://localhost:3000
- **Playground** at http://localhost:3001
- **Web Chat** at http://localhost:3002
- **Redis** at localhost:6379
- **PostgreSQL** at localhost:5432

### 3. Verify Services

Check that all services are running:

```bash
docker-compose ps
```

Test the gateway:
```bash
curl http://localhost:8000/
```

### 4. Access the Applications

- **Playground Control Panel**: http://localhost:3001
  - Dashboard: http://localhost:3001/dashboard
  - Prompt Studio: http://localhost:3001/prompt-studio
  - Usage Inspector: http://localhost:3001/usage-inspector

- **Web Chat Client**: http://localhost:3002

## Manual Setup (Without Docker)

If you prefer to run services manually:

### 1. Setup Gateway (FastAPI)

```bash
cd gateway

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your API keys

# Run the service
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### 2. Setup App Server (Next.js)

```bash
cd app-server

# Install dependencies
npm install

# Configure environment
cp .env.example .env.local
# Edit .env.local

# Run development server
npm run dev
```

### 3. Setup Playground (Next.js)

```bash
cd playground

# Install dependencies
npm install

# Run development server
npm run dev
```

The playground will run on port 3000 by default. If app-server is already on 3000, you can change it:

```bash
# Run on different port
PORT=3001 npm run dev
```

### 4. Setup Web Chat (React)

```bash
cd web-chat

# Install dependencies
npm install

# Configure environment
cp .env.example .env
# Edit .env

# Run development server
npm start
```

## Next Steps

### 1. Test the Gateway

```bash
# Health check
curl http://localhost:8000/

# List models
curl http://localhost:8000/v1/models

# Send a chat request
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [
      {"role": "user", "content": "Hello!"}
    ]
  }'
```

### 2. Create an API Key

Currently, the API key management is scaffolded. To use the web chat:

1. Access the app-server API key endpoint
2. Generate an API key
3. Use it in the web chat client

### 3. Explore the Playground

- **Dashboard**: See system overview and metrics
- **Prompt Studio**: Test prompts interactively
- **Usage Inspector**: View usage logs and analytics

### 4. Implement Database Schema

The current implementation has placeholder database functions. To fully implement:

1. Choose a database solution (PostgreSQL, MySQL, etc.)
2. Implement the schema in `app-server/lib/db.ts`
3. Add migrations if needed
4. Update the API routes to use actual database queries

### 5. Add Authentication

For production use, add authentication:

1. Implement user authentication (e.g., NextAuth.js)
2. Secure API endpoints
3. Add JWT token validation
4. Implement role-based access control

## Development Workflow

### Making Changes

1. **Gateway**: Edit Python files in `gateway/app/`
2. **App Server**: Edit TypeScript files in `app-server/app/`
3. **Playground**: Edit TypeScript files in `playground/app/`
4. **Web Chat**: Edit TypeScript files in `web-chat/src/`

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

## Troubleshooting

### Gateway Issues

**Problem**: "Module not found" errors
```bash
cd gateway
pip install -r requirements.txt
```

**Problem**: Database connection errors
- Ensure Redis is running (if using cache)
- Check DATABASE_URL in .env

### Node.js Issues

**Problem**: "Cannot find module" errors
```bash
rm -rf node_modules package-lock.json
npm install
```

**Problem**: Port already in use
```bash
# Kill process on port 3000
lsof -ti:3000 | xargs kill -9

# Or use a different port
PORT=3001 npm run dev
```

### Docker Issues

**Problem**: Services won't start
```bash
# Check logs
docker-compose logs gateway
docker-compose logs app-server

# Rebuild containers
docker-compose build --no-cache
docker-compose up -d
```

## Production Deployment

For production deployment, refer to:

- **Gateway**: Deploy with Gunicorn or uvicorn behind nginx
- **Next.js apps**: Deploy to Vercel, or build and serve with Node
- **React app**: Build and serve static files with nginx
- **Databases**: Use managed PostgreSQL (RDS, Cloud SQL, etc.)
- **Redis**: Use managed Redis (ElastiCache, Cloud Memorystore, etc.)

## Support

For issues or questions:

1. Check the README files in each component directory
2. Review the API documentation
3. Check the examples in the code
4. Open an issue on GitHub

## License

This project is licensed under the MIT License - see the LICENSE file for details.
