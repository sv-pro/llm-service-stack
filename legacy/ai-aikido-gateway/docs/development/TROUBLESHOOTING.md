# Troubleshooting Guide

This document captures common issues encountered during development and deployment, with their root causes and solutions.

## Table of Contents

- [Docker Import Errors](#docker-import-errors)
- [Docker Environment Variables](#docker-environment-variables)
- [Volume Mount Path Issues](#volume-mount-path-issues)
- [Quick Diagnosis Commands](#quick-diagnosis-commands)

---

## Docker Import Errors

### Symptom

```
ERROR: Error loading ASGI app. Could not import module 'src.main'
ModuleNotFoundError: No module named 'core.config'
```

### Root Cause

Python cannot find the modules because `PYTHONPATH` is not set correctly inside the Docker container.

### Solution

The Dockerfile needs **both** paths in `PYTHONPATH`:

```dockerfile
ENV PYTHONPATH=/app:/app/src
```

**Why both paths?**

- `/app` - needed for `import src.main` (uvicorn import string)
- `/app/src` - needed for `from core.config import ...` (internal imports)

### Common Mistakes

❌ **Wrong:** `ENV PYTHONPATH=/app/src` only
❌ **Wrong:** `ENV PYTHONPATH=/app` only
✅ **Correct:** `ENV PYTHONPATH=/app:/app/src`

### How to Verify

Test inside a running container:

```bash
docker run -it --rm <image-name> python -c "
import sys
sys.path.insert(0, '/app')
sys.path.insert(0, '/app/src')
print('Python path:', sys.path)
try:
    from core.config import ConfigLoader
    print('✓ core.config import works')
except Exception as e:
    print('✗ core.config failed:', e)
try:
    import src.main
    print('✓ src.main import works')
except Exception as e:
    print('✗ src.main failed:', e)
"
```

---

## Docker Environment Variables

### Symptom

```
HTTP 400: Bad Request
WARNING - Model 'gpt-3.5-turbo' is not available: Provider not configured (missing OPENAI_API_KEY)
```

### Root Cause

Docker containers don't automatically load `.env` files from the project root. The API keys are not passed to the container.

### Solution Options

#### Option 1: Add `env_file` to docker-compose.yml

```yaml
services:
  gateway:
    env_file:
      - ../.env # Relative to docker-compose.yml location
    environment:
      - OPENAI_API_KEY=${OPENAI_API_KEY:-}
```

#### Option 2: Use `--env-file` flag

```bash
docker-compose --env-file .env -f deployment/docker-compose.yml up
```

#### Option 3: Update docker.sh script

```bash
ENV_FILE=".env"
docker-compose --env-file ${ENV_FILE} -f ${DEPLOYMENT_DIR}/docker-compose.yml up
```

### How to Verify

Check if environment variables are loaded:

```bash
# Check key length (without exposing the actual key)
docker exec <container-name> bash -c 'echo "OPENAI_API_KEY length: ${#OPENAI_API_KEY}"'

# Should show a length > 0, typically 100-200 characters
# If it shows "0", the key is not loaded
```

### Prevention

Add a check to your docker.sh script:

```bash
if [ ! -f "$ENV_FILE" ]; then
    echo "⚠️  Warning: .env file not found. API keys may not be configured."
    echo "   Copy .env.example to .env and add your API keys."
fi
```

---

## Volume Mount Path Issues

### Symptom

After reorganizing project structure (moving files to subdirectories), Docker containers fail with:

- Import errors
- "File not found" errors
- Empty directories inside container

### Root Cause

When docker-compose files are moved to a subdirectory (e.g., `deployment/`), volume mount paths need to be updated to use relative paths from the new location.

### Example Problem

**Before** (when docker-compose.yml was in root):

```yaml
volumes:
  - ./src:/app/src:ro
  - ./config:/app/config:ro
```

**After moving to deployment/** (WRONG):

```yaml
build:
  context: .. # Build context is parent directory
volumes:
  - ./src:/app/src:ro # ❌ This looks in deployment/src (doesn't exist!)
  - ./config:/app/config:ro # ❌ This looks in deployment/config (doesn't exist!)
```

**After moving to deployment/** (CORRECT):

```yaml
build:
  context: .. # Build context is parent directory
volumes:
  - ../src:/app/src:ro # ✅ Correctly references parent/src
  - ../config:/app/config:ro # ✅ Correctly references parent/config
```

### Rule of Thumb

**Volume mount paths are relative to the directory containing the docker-compose.yml file, NOT the build context.**

If your docker-compose.yml uses `context: ..` (parent directory), your volume mounts should also use `../` prefix.

### How to Verify

1. Check what docker-compose resolves:

```bash
docker-compose -f deployment/docker-compose.yml config | grep -A 3 "volumes:"
```

2. Inspect the container to see mounted volumes:

```bash
docker inspect <container-name> | grep -A 10 "Mounts"
```

3. Check if files exist inside container:

```bash
docker exec <container-name> ls -la /app/src
docker exec <container-name> ls -la /app/config
```

---

## Quick Diagnosis Commands

### Check Container Health

```bash
# View all containers
docker ps -a

# Check logs
docker logs <container-name>
docker logs <container-name> --tail 50

# Follow logs in real-time
docker logs <container-name> -f
```

### Test API Endpoints

```bash
# Health check
curl http://localhost:8000/health

# Test chat completion (requires API key)
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{"model": "gpt-3.5-turbo", "messages": [{"role": "user", "content": "Hello"}]}'
```

### Inspect Container Environment

```bash
# Check all environment variables
docker exec <container-name> env

# Check specific variable
docker exec <container-name> bash -c 'echo $PYTHONPATH'
docker exec <container-name> bash -c 'echo ${#OPENAI_API_KEY}'

# Check Python can import modules
docker exec <container-name> python -c "import src.main; print('OK')"
docker exec <container-name> python -c "from core.config import ConfigLoader; print('OK')"
```

### Inspect Files Inside Container

```bash
# List directory contents
docker exec <container-name> ls -la /app
docker exec <container-name> ls -la /app/src

# Check if file exists
docker exec <container-name> cat /app/src/main.py | head -20
```

### Debug docker-compose Configuration

```bash
# View merged configuration
docker-compose -f deployment/docker-compose.yml config

# View configuration with env file
docker-compose --env-file .env -f deployment/docker-compose.yml config

# Check what variables are set
docker-compose -f deployment/docker-compose.yml config | grep -A 2 "OPENAI_API_KEY"
```

---

## Pattern Recognition: Common Failure Modes

### Pattern 1: Works locally, fails in Docker

**Likely causes:**

1. Missing environment variables
2. Wrong PYTHONPATH
3. Files not copied to container (check Dockerfile COPY commands)

### Pattern 2: Works after project setup, breaks after reorganization

**Likely causes:**

1. Volume mount paths need updating (add `../` prefix)
2. Build context changed but paths not updated
3. Environment file location changed

### Pattern 3: Builds successfully, fails at runtime

**Likely causes:**

1. Import errors (PYTHONPATH issue)
2. Missing API keys (environment variables)
3. Permission issues (check USER in Dockerfile)

---

## Best Practices to Avoid These Issues

### 1. Always Test Docker After Structure Changes

```bash
# After any reorganization, run full test:
docker-compose -f deployment/docker-compose.yml build
docker-compose -f deployment/docker-compose.yml up -d
docker logs <container-name>
curl http://localhost:8000/health
```

### 2. Document File Paths in Comments

```yaml
# When using relative paths, add comments:
volumes:
  - ../src:/app/src:ro # Project root is parent directory
```

### 3. Use Convenience Scripts

Instead of long docker-compose commands, use wrapper scripts:

```bash
./scripts/docker.sh dev   # Handles paths and env files correctly
```

### 4. Keep .env.example Updated

Whenever you add new environment variables, update `.env.example` so others know what to configure.

### 5. Add Validation to Scripts

```bash
# Check prerequisites before starting
if [ ! -f ".env" ]; then
    echo "ERROR: .env file missing"
    exit 1
fi
```

---

## Project-Specific Context

### File Structure

```
ai-aikido-gateway/
├── .env                    # API keys (not in git)
├── .env.example           # Template for API keys
├── deployment/            # Docker files moved here during housekeeping
│   ├── Dockerfile.gateway
│   ├── docker-compose.yml
│   └── docker-compose.dev.yml
├── scripts/
│   └── docker.sh          # Convenience wrapper
├── src/                   # Python source
│   ├── main.py           # Entry point
│   └── core/             # Core modules
└── config/               # Configuration files
```

### Working Commands (Project Root)

```bash
# Development
bash scripts/docker.sh dev

# Production
bash scripts/docker.sh prod

# Stop all
bash scripts/docker.sh stop

# Build images
bash scripts/docker.sh build

# View logs
bash scripts/docker.sh logs
```

### Working Commands (Manual)

```bash
# From project root with explicit paths:
docker-compose --env-file .env -f deployment/docker-compose.yml up -d

# From deployment/ directory:
cd deployment
docker-compose --env-file ../.env up -d
```

---

## When to Update This Document

Add to this document whenever you encounter:

1. A new type of failure mode
2. A solution that took > 15 minutes to find
3. An issue that repeats across sessions
4. A subtle gotcha that's easy to miss

**The goal:** Next time you hit the same issue, the solution should be here in < 2 minutes.
