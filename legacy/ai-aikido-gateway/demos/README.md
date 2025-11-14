# AI Aikido Gateway - Demos

This directory contains demonstration scripts showcasing various gateway features.

## Running Demos

All demos should be run from the **project root directory**:

```bash
# From project root
python demos/tool_registry/demo_tool_registry.py
python demos/langgraph/demo_langgraph.py
python demos/semantic_cache/demo_semantic_cache.py
```

## Available Demos

### 1. Tool Registry (`tool_registry/`)
Demonstrates the tool registry and adapter system (Week 10):
- Tool registration and execution
- Python function adapters (sync & async)
- HTTP API adapter
- LLM adapter (requires OPENAI_API_KEY)
- Workflow integration
- Error handling

**Run:**
```bash
python demos/tool_registry/demo_tool_registry.py
```

### 2. LangGraph Workflow (`langgraph/`)
Demonstrates the Re^Re (Reflective Reasoning) loop:
- Multi-step playbook execution
- Budget tracking and enforcement
- Quality scoring
- State management
- Decision logging

**Run:**
```bash
python demos/langgraph/demo_langgraph.py
```

### 3. Semantic Cache (`semantic_cache/`)
Demonstrates semantic caching capabilities:
- On-premise embeddings
- Qdrant vector database
- Semantic similarity matching
- Cache performance metrics

**Run:**
```bash
# Python demo
python demos/semantic_cache/demo_semantic_cache.py

# Shell script with Docker setup
bash demos/semantic_cache/demo_semantic_cache.sh
```

## Requirements

- All Python demos require dependencies from `requirements.txt`
- LLM demo requires `OPENAI_API_KEY` environment variable
- Semantic cache demos require Docker services running:
  ```bash
  make docker-redeploy
  ```

## Troubleshooting

**ModuleNotFoundError: No module named 'src'**
- Make sure you're running from the project root directory
- Ensure all dependencies are installed: `pip install -r requirements.txt`

**OPENAI_API_KEY not set**
- The LLM demo will skip if the API key is not set
- Other demos will continue to work
- Set the key: `export OPENAI_API_KEY="your-key"`

**Docker services not running**
- For semantic cache demos, start services: `make docker-redeploy`
- Check status: `docker ps`
