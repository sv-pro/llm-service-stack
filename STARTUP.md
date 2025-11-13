# Quick Startup Guide

This guide will help you get the entire LLM Service Stack running locally.

## Prerequisites

1. **Docker and Docker Compose** installed
2. **Make** installed (usually pre-installed on Linux/Mac)
3. **curl** and **jq** for testing (optional)

## Step-by-Step Startup

### 1. Quick Start (Recommended)

The fastest way to get everything running:

```bash
# From the project root
make quickstart
```

This single command will:
- Build all Docker images
- Start all services (Gateway, App Server, Playground, Web Chat, MongoDB, Redis)
- Show service status

### 2. Verify Services Are Running

```bash
# Check status
make status

# Or run the verification script
chmod +x scripts/verify-startup.sh
bash scripts/verify-startup.sh
```

You should see:
- ✓ MongoDB container is running
- ✓ Redis container is running
- ✓ Gateway is running
- ✓ App Server is running
- ✓ Playground is running
- ✓ Web Chat is running

### 3. Access the Services

Open your browser to:

- **Playground**: http://localhost:3001 (Developer control panel)
- **Web Chat**: http://localhost:3002 (End-user chat interface)
- **Gateway API**: http://localhost:8000 (Direct LLM gateway)
- **App Server API**: http://localhost:3000 (Backend APIs)

### 4. Test End-to-End Flow

Run the complete test to verify everything works:

```bash
chmod +x scripts/test-e2e.sh
bash scripts/test-e2e.sh
```

This will:
1. Create a test user
2. Generate an API key
3. Create a chat session
4. Send a message to the LLM
5. Verify data was stored correctly

## Common Issues and Solutions

### Issue: "docker: unknown command: docker compose"

**Solution**: Your Docker uses the older `docker-compose` command. The Makefile should auto-detect this.

```bash
# Try with the hyphenated version
docker-compose up -d
```

### Issue: Services fail to start

**Check logs for the specific service**:
```bash
make logs-gateway
make logs-app-server
make logs-playground
make logs-web-chat
```

**Common causes**:
1. Port already in use (kill the conflicting process)
2. Missing environment variables (check `.env` files)
3. Docker daemon not running

### Issue: Gateway returns errors

**Check if API keys are configured**:
```bash
cat gateway/.env
```

You should see:
```
ANTHROPIC_API_KEY=sk-ant-...
OPENAI_API_KEY=sk-proj-...
```

If missing, add your API keys to `gateway/.env`.

### Issue: MongoDB connection errors

**Check if MongoDB is accessible**:
```bash
make mongo-shell

# Inside mongosh:
db.users.find()
```

### Issue: App Server can't connect to Gateway

**Verify Gateway is accessible**:
```bash
curl http://localhost:8000/

# Should return:
# {"service":"LLM Gateway","version":"0.1.0","status":"running"}
```

## Useful Commands

### Service Management

```bash
make start              # Start all services
make stop               # Stop all services
make restart            # Restart all services
make status             # Show status
```

### Individual Services

```bash
make start-gateway      # Start only gateway
make restart-app-server # Restart only app-server
make logs-playground    # View playground logs
```

### Database

```bash
make mongo-shell        # Connect to MongoDB
make redis-cli          # Connect to Redis
make mongo-backup       # Backup MongoDB
```

### Logs

```bash
make logs               # View all logs
make logs-gateway       # View gateway logs
make logs-app-server    # View app-server logs
```

### Cleanup

```bash
make stop               # Stop services
make clean              # Remove all containers and volumes
make clean-cache        # Clear Redis and build caches
```

## Testing the System

### 1. Test Gateway Directly

```bash
# List available models
curl http://localhost:8000/v1/models

# Send a chat request (requires API key in gateway/.env)
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

### 2. Test App Server APIs

```bash
# Create a user
curl -X POST http://localhost:3000/api/users \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com", "name": "Test User"}'

# List users
curl http://localhost:3000/api/users
```

### 3. Complete Integration Test

See `app-server/TESTING.md` for detailed API testing examples, or run:

```bash
bash scripts/test-e2e.sh
```

## Service Architecture

```
┌─────────────┐     ┌─────────────┐
│  Web Chat   │────▶│ App Server  │
│ :3002       │     │ :3000       │
└─────────────┘     └──────┬──────┘
                           │
┌─────────────┐            │
│ Playground  │───────────┘
│ :3001       │            │
└─────────────┘            ▼
                    ┌─────────────┐
                    │   Gateway   │
                    │   :8000     │
                    └──────┬──────┘
                           │
        ┌──────────────────┼──────────────────┐
        ▼                  ▼                  ▼
   ┌─────────┐      ┌──────────┐      ┌──────────┐
   │  Redis  │      │ DuckDB   │      │  OpenAI  │
   │  :6379  │      │ (SQLite) │      │ Anthropic│
   └─────────┘      └──────────┘      │  Ollama  │
                                       └──────────┘
        ┌───────────────────────────────┘
        ▼
   ┌─────────┐
   │ MongoDB │
   │ :27017  │
   └─────────┘
```

## Next Steps

Once all services are running:

1. **Test the Playground**: Go to http://localhost:3001
2. **Test the Web Chat**: Go to http://localhost:3002
3. **Review the logs**: Run `make logs` to see all service logs
4. **Run E2E tests**: Execute `bash scripts/test-e2e.sh`
5. **Check the documentation**: See `CLAUDE.md` for detailed information

## Getting Help

If you encounter issues:

1. Check service logs: `make logs-<service-name>`
2. Verify service status: `make status`
3. Review environment variables in `.env` files
4. Check port availability: `lsof -i :3000` (or other ports)
5. Restart services: `make restart`

For more detailed information, see:
- `CLAUDE.md` - Complete project documentation
- `app-server/TESTING.md` - API testing guide
- `Makefile` - All available commands (`make help`)
