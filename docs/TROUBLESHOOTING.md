# Troubleshooting Guide

This document captures common issues encountered during development and their solutions.

## Table of Contents

- [Gateway Issues](#gateway-issues)
- [Playground/Frontend Issues](#playgroundfrontend-issues)
- [Caching Issues](#caching-issues)
- [Docker & Environment](#docker--environment)
- [CORS Issues](#cors-issues)

---

## Gateway Issues

### Gateway crashes on startup with "ModuleNotFoundError: No module named 'numpy'"

**Symptoms:**
- Gateway container fails to start
- Frontend shows CORS errors
- Logs show: `ModuleNotFoundError: No module named 'numpy'`

**Cause:**
The semantic caching feature requires numpy for vector operations (cosine similarity), but it wasn't included in `requirements.txt`.

**Solution:**
```bash
# Add to gateway/requirements.txt
numpy==1.24.3

# Rebuild the gateway container
docker compose build gateway
docker compose restart gateway
```

**Commit reference:** Added numpy dependency for semantic caching

---

### LiteLLM error: "The api_key client option must be set"

**Symptoms:**
- Gateway starts successfully but chat completions fail
- Error message: `The api_key client option must be set either by passing api_key to the client or by setting the OPENAI_API_KEY environment variable`
- API keys are present in `.env` file

**Cause:**
LiteLLM requires API keys to be set in `os.environ`, not just loaded into Pydantic settings. The settings object holds the values, but LiteLLM doesn't have access to them.

**Solution:**
Update `gateway/app/main.py` startup event to explicitly set environment variables:

```python
@app.on_event("startup")
async def startup_event():
    import os

    init_db()
    litellm.set_verbose = settings.LITELLM_VERBOSE

    # Set API keys in environment for LiteLLM
    if settings.OPENAI_API_KEY:
        os.environ["OPENAI_API_KEY"] = settings.OPENAI_API_KEY
    if settings.ANTHROPIC_API_KEY:
        os.environ["ANTHROPIC_API_KEY"] = settings.ANTHROPIC_API_KEY
```

**Commit reference:** Fixed semantic caching error handling and LiteLLM API key configuration

---

### JSON serialization error: "Object of type ModelResponse is not JSON serializable"

**Symptoms:**
- Chat completions endpoint returns 500 error
- Error message: `Object of type ModelResponse is not JSON serializable`
- Or: `Object of type Choices is not JSON serializable`
- Or: `Object of type Message is not JSON serializable`

**Cause:**
LiteLLM returns `ModelResponse` objects which are Pydantic models. These contain nested Pydantic models (`Choices`, `Message`, etc.) that cannot be serialized with Python's built-in `dict()` function.

**Solution:**
Use Pydantic's serialization methods which recursively convert nested models:

```python
# ❌ Wrong - doesn't handle nested Pydantic models
response_dict = dict(response) if hasattr(response, '__dict__') else response

# ✅ Correct - properly serializes all nested models
if hasattr(response, 'model_dump'):
    # Pydantic v2 - recursively converts nested models
    response_dict = response.model_dump()
elif hasattr(response, 'dict'):
    # Pydantic v1 - recursively converts nested models
    response_dict = response.dict()
else:
    # Fallback: JSON round-trip for any remaining serialization issues
    import json as json_lib
    response_dict = json_lib.loads(json_lib.dumps(response, default=str))
```

Apply this fix in both:
- `/v1/chat/completions` endpoint (around line 319)
- `/v1/responses` endpoint (around line 411)

**Commit reference:** Fix LiteLLM ModelResponse JSON serialization

---

## Playground/Frontend Issues

### Playground shows empty fields or old values after code changes

**Symptoms:**
- Default values (system prompt, user message) don't appear
- UI changes aren't visible
- Old JavaScript behavior persists

**Cause:**
Browser is serving cached JavaScript bundle from previous build.

**Solution:**

1. **Rebuild the container:**
   ```bash
   docker compose build playground
   docker compose restart playground
   ```

2. **Hard refresh browser:**
   - Chrome/Firefox: `Ctrl+Shift+R` (Windows/Linux) or `Cmd+Shift+R` (Mac)
   - This clears cached JavaScript and CSS

3. **Verify container is running the latest build:**
   ```bash
   docker compose ps playground
   docker compose logs playground
   ```

**Prevention:**
During active development, use a local dev server instead of Docker:
```bash
cd playground
npm run dev
```

---

### Source badge not appearing in Prompt Studio

**Symptoms:**
- Cache status badge (🌐 API Call, ⚡ Simple Cache, 🧠 Semantic Cache) doesn't appear
- Metadata shows tokens and cost but not cache source
- Console logs show `cacheType: undefined, cacheStatus: undefined`

**Cause:**
Custom HTTP headers (`X-Gateway-Cache-Status`, `X-Gateway-Cache-Type`, `X-Gateway-Cache-Similarity`) are not exposed in the CORS configuration. Browsers block access to custom response headers by default for security reasons.

**Solution:**
Add `expose_headers` to the CORS middleware in `gateway/app/main.py`:

```python
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=[
        "X-Gateway-Cache-Status",
        "X-Gateway-Cache-Type",
        "X-Gateway-Cache-Similarity"
    ],
)
```

After updating, restart the gateway:
```bash
docker compose restart gateway
```

**Verification:**
1. Open browser DevTools (F12) → Network tab
2. Make a request in Prompt Studio
3. Click on the request → Headers → Response Headers
4. You should now see the `X-Gateway-*` headers

**Commit reference:** Expose cache headers in CORS for client access

---

## Caching Issues

### Semantic cache not working / always showing "API Call"

**Symptoms:**
- Similar prompts always result in API calls
- Never see "🧠 Semantic Cache" badge
- Cache mode is set to "Auto"

**Possible causes and solutions:**

#### 1. Numpy not installed
See [Gateway crashes on startup with numpy error](#gateway-crashes-on-startup-with-modulenotfounderror-no-module-named-numpy)

#### 2. OpenAI API key not configured
Semantic caching uses OpenAI's embedding API (`text-embedding-ada-002`). Check:

```bash
# Verify API key is set
docker compose exec gateway printenv | grep OPENAI_API_KEY
```

If empty, add to your `.env` file in the project root:
```env
OPENAI_API_KEY=sk-...
```

#### 3. Redis connection failed
Check Redis is running and accessible:

```bash
docker compose ps redis
docker compose logs redis

# Test connection from gateway
docker compose exec gateway redis-cli -h redis ping
# Should return: PONG
```

#### 4. Similarity threshold too high
Lower the semantic similarity threshold in Prompt Studio:
- Current default: 85%
- Try: 75% or lower for more aggressive matching

#### 5. Check gateway logs
```bash
docker compose logs -f gateway | grep -i "semantic\|cache\|embedding"
```

Look for errors like:
- `Embedding generation error: ...`
- `Semantic cache error: ...`

---

### Cache showing stale responses

**Symptoms:**
- Updating code/prompts but getting old responses
- Cache TTL seems to be ignored

**Solution:**

1. **Flush Redis cache:**
   ```bash
   docker compose exec redis redis-cli FLUSHALL
   ```

2. **Or use the Makefile:**
   ```bash
   make redis-flush
   ```

3. **Adjust cache TTL in Prompt Studio:**
   - Go to Cache Configuration
   - Set Cache TTL to a lower value (e.g., 60 seconds for testing)

4. **Disable cache temporarily:**
   - Set Cache Mode to "🌐 No Cache (Always API)"

---

## Docker & Environment

### Environment variables not loading in Docker containers

**Symptoms:**
- Gateway container has no API keys
- Only `.env.example` present in container
- `docker compose exec gateway printenv` shows missing variables

**Cause:**
The `env_file` directive in `docker-compose.yml` points to the wrong location, or the `.env` file doesn't exist.

**Solution:**

1. **Check your `.env` file exists:**
   ```bash
   ls -la .env
   ```

2. **Ensure docker-compose.yml references the correct path:**
   ```yaml
   services:
     gateway:
       env_file:
         - .env  # Load from project root
       environment:
         # Docker-specific overrides
         - REDIS_URL=redis://redis:6379
         - DATABASE_URL=duckdb:///./gateway.db
   ```

3. **Recreate containers to pick up changes:**
   ```bash
   docker compose down
   docker compose up -d
   ```

4. **Verify variables are set:**
   ```bash
   docker compose exec gateway printenv | grep -E "OPENAI|ANTHROPIC|REDIS"
   ```

**Note:** The `.env` file should NOT be committed to git for security reasons. Keep it in `.gitignore`.

**Commit reference:** Load gateway environment variables from root .env file

---

### Docker build fails or containers won't start

**Common solutions:**

1. **Clean rebuild:**
   ```bash
   docker compose down -v
   docker compose build --no-cache
   docker compose up -d
   ```

2. **Check logs:**
   ```bash
   docker compose logs gateway
   docker compose logs app-server
   docker compose logs playground
   ```

3. **Check port conflicts:**
   ```bash
   # See what's using port 8000 (gateway)
   lsof -ti:8000

   # Kill the process if needed
   lsof -ti:8000 | xargs kill -9
   ```

4. **Check disk space:**
   ```bash
   docker system df
   docker system prune  # Clean up unused resources
   ```

---

## CORS Issues

### Frontend can't reach Gateway: "Cross-Origin Request Blocked"

**Symptoms:**
- Browser console shows: `Cross-Origin Request Blocked: The Same Origin Policy disallows reading...`
- Network tab shows failed requests
- Gateway is running but unreachable from browser

**Possible causes:**

#### 1. Gateway is offline
```bash
docker compose ps gateway
docker compose logs gateway
```

#### 2. CORS origins not configured
Check `gateway/app/config.py`:

```python
CORS_ORIGINS: List[str] = Field(
    default=[
        "http://localhost:3000",  # app-server
        "http://localhost:3001",  # playground
        "http://localhost:3002",  # web-chat
    ]
)
```

Add your frontend URL if different.

#### 3. Custom headers not exposed
See [Source badge not appearing](#source-badge-not-appearing-in-prompt-studio)

#### 4. Requests going to wrong URL
Check `playground/.env.local`:
```env
NEXT_PUBLIC_GATEWAY_URL=http://localhost:8000
```

Verify in browser console:
```javascript
console.log(process.env.NEXT_PUBLIC_GATEWAY_URL)
```

---

### Playground or App Server shows "Gateway Offline"

**Diagnosis steps:**

1. **Verify gateway is running:**
   ```bash
   docker compose ps
   # gateway should show "Up"
   ```

2. **Test gateway health directly:**
   ```bash
   curl http://localhost:8000/
   # Should return: {"service":"LLM Gateway","version":"0.1.0","status":"running"}
   ```

3. **Check gateway logs:**
   ```bash
   docker compose logs -f gateway
   ```

4. **Verify port mapping:**
   ```bash
   docker compose port gateway 8000
   # Should return: 0.0.0.0:8000
   ```

5. **Test from inside Docker network:**
   ```bash
   docker compose exec playground curl http://gateway:8000/
   ```

---

## General Debugging Tips

### Enable verbose logging

**Gateway (LiteLLM):**
```env
# In .env
LITELLM_VERBOSE=true
```

**App Server (Next.js):**
```bash
cd app-server
NODE_ENV=development npm run dev
```

**Playground (Next.js):**
```bash
cd playground
NODE_ENV=development npm run dev
```

---

### Inspect database state

**DuckDB (Gateway usage logs):**
```bash
docker compose exec gateway python3 -c "
from app.database import SessionLocal, init_db
from app.models import UsageLog
init_db()
db = SessionLocal()
logs = db.query(UsageLog).order_by(UsageLog.timestamp.desc()).limit(5).all()
for log in logs:
    print(f'{log.timestamp} | {log.model} | cache_hit={log.cache_hit} | cost={log.cost}')
"
```

**MongoDB (App Server data):**
```bash
docker compose exec mongo mongosh llm_service --eval "
  db.sessions.find().limit(5).pretty()
"
```

**Redis (Cache):**
```bash
docker compose exec redis redis-cli

# List all keys
KEYS *

# Get a specific cached response
GET "chat_completion:sha256_hash_here"

# Check key TTL
TTL "chat_completion:sha256_hash_here"

# Count keys
DBSIZE
```

---

### Clean slate restart

When all else fails, nuclear option:

```bash
# Stop everything and remove volumes
docker compose down -v

# Remove all images
docker compose down --rmi all

# Clean Docker system
docker system prune -a --volumes

# Rebuild from scratch
docker compose build --no-cache
docker compose up -d

# Watch logs
docker compose logs -f
```

---

## Getting Help

If you encounter an issue not covered here:

1. **Check the logs:**
   ```bash
   make logs              # All services
   make logs-gateway      # Just gateway
   make logs-playground   # Just playground
   ```

2. **Check service status:**
   ```bash
   make status
   ```

3. **Review recent commits:**
   ```bash
   git log --oneline -10
   ```

4. **Search the codebase:**
   ```bash
   # Find where errors are raised
   grep -r "Object of type" gateway/

   # Find configuration files
   find . -name "*.env*" -o -name "config.*"
   ```

5. **File an issue:**
   Include:
   - Error message
   - Steps to reproduce
   - Relevant logs
   - Output of `docker compose ps`
   - Output of `docker compose version`

---

## Related Documentation

- [CLAUDE.md](../CLAUDE.md) - Project overview and development guide
- [Gateway API Documentation](../gateway/README.md)
- [App Server Documentation](../app-server/README.md)
- [Playground Documentation](../playground/README.md)
