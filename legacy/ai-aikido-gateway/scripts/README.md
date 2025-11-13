# Utility Scripts

This directory contains utility scripts for testing, debugging, and maintenance.

## Available Scripts

### test_embedding_service.py
Tests the on-premise embedding service.

**Usage:**
```bash
python scripts/test_embedding_service.py
```

**Requirements:**
- Embedding service running (port 8001)
- Start with: `make docker-redeploy`

### test_semantic_fix.sh
Tests semantic cache functionality after bug fixes.

**Usage:**
```bash
bash scripts/test_semantic_fix.sh
```

**Requirements:**
- Docker services running
- Gateway on port 8000

### restart_and_test.sh
Restarts Docker services and runs tests.

**Usage:**
```bash
bash scripts/restart_and_test.sh
```

**What it does:**
- Stops all Docker services
- Rebuilds and restarts services
- Runs full test suite
- Reports status

## Running from Project Root

All scripts should be run from the project root directory:

```bash
# From project root
python scripts/test_embedding_service.py
bash scripts/test_semantic_fix.sh
```
