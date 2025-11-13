# AGENTS.md - AI Aikido Gateway Development Setup

---

## 🎯 Project Overview

**AI Aikido Gateway**: OpenAI-compatible API proxy that routes requests intelligently to save 90% on LLM costs.

**Core Value**: One-line integration, measurable savings, extensible architecture.

---

## 🚀 Modern Development Setup

### Prerequisites

```bash
# Required
- Python 3.11+ (via pyenv)
- Git
- Docker & Docker Compose (for deployment)

# Optional but recommended
- VS Code with Python extension
- Cursor or Claude for AI-assisted coding
```

---

## 📦 Initial Project Setup

### 1. Install pyenv (Python Version Manager)

```bash
# macOS (via Homebrew)
brew update
brew install pyenv
brew install pyenv-virtualenv

# Linux
curl https://pyenv.run | bash

# Add to ~/.zshrc or ~/.bashrc:
export PYENV_ROOT="$HOME/.pyenv"
export PATH="$PYENV_ROOT/bin:$PATH"
eval "$(pyenv init -)"
eval "$(pyenv virtualenv-init -)"

# Reload shell
source ~/.zshrc  # or source ~/.bashrc
```

### 2. Install Python 3.11

```bash
# Install Python 3.11 (latest stable)
pyenv install 3.11.7

# Set as global default (optional)
pyenv global 3.11.7

# Verify
python --version  # Should show Python 3.11.7
```

### 3. Create Project Directory

```bash
# Create and enter project directory
mkdir ai-aikido-gateway
cd ai-aikido-gateway

# Initialize git repository
git init

# Set local Python version for this project
pyenv local 3.11.7
```

### 4. Create Virtual Environment

```bash
# Create virtual environment with pyenv
pyenv virtualenv 3.11.7 aikido-env

# Activate it
pyenv activate aikido-env

# Or set it as local environment (auto-activates on cd)
pyenv local aikido-env

# Verify
which python  # Should point to aikido-env
python --version  # Python 3.11.7
```

---

## 📁 Project Structure

```bash
# Create project structure
mkdir -p {src/{core,plugins,api},tests,config,docs,scripts}
touch src/__init__.py
touch src/core/__init__.py
touch src/plugins/__init__.py
touch src/api/__init__.py
touch tests/__init__.py
```

### Final Structure:

```
ai-aikido-gateway/
├── .git/
├── .gitignore
├── .python-version          # pyenv auto-activation
├── README.md
├── AGENTS.md               # This file
├── requirements.txt        # Python dependencies
├── requirements-dev.txt    # Development dependencies
├── pyproject.toml         # Modern Python project config
├── docker-compose.yml     # Local development
├── Dockerfile
├── config/
│   ├── aikido.yaml        # Main config
│   └── plugins.yaml       # Plugin configurations
├── src/
│   ├── __init__.py
│   ├── main.py           # FastAPI application
│   ├── core/
│   │   ├── __init__.py
│   │   ├── classifier.py    # Cheap LLM classifier
│   │   ├── router.py        # Routing logic
│   │   ├── plugin.py        # Plugin base classes
│   │   └── config.py        # Config management
│   ├── plugins/
│   │   ├── __init__.py
│   │   ├── cache.py         # Cache plugin
│   │   ├── openai.py        # OpenAI proxy plugin
│   │   └── mcp.py           # MCP plugin (optional)
│   └── api/
│       ├── __init__.py
│       ├── routes.py        # API endpoints
│       └── models.py        # Pydantic models
├── tests/
│   ├── __init__.py
│   ├── test_classifier.py
│   ├── test_router.py
│   └── test_api.py
├── scripts/
│   ├── setup.sh            # Project setup
│   └── test_gateway.py     # Manual testing
└── docs/
    ├── architecture.md
    └── plugin_guide.md
```

---

## 📝 Configuration Files

### `.gitignore`

```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
share/python-wheels/
*.egg-info/
.installed.cfg
*.egg
MANIFEST

# Virtual Environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/
aikido-env/

# pyenv
.python-version

# IDE
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store

# Testing
.pytest_cache/
.coverage
htmlcov/
.tox/

# Logs
*.log
logs/

# Config (with secrets)
config/secrets.yaml
config/local.yaml
.env.local

# Docker
.dockerignore

# Temporary files
tmp/
temp/
*.tmp

# Database
*.db
*.sqlite
*.sqlite3

# API Keys (important!)
**/api_keys.txt
**/*_key.txt
**/*_secret.txt
.anthropic_key
.openai_key
```

### `.python-version` (auto-created by pyenv)

```
aikido-env
```

### `pyproject.toml` (Modern Python Config)

```toml
[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "ai-aikido-gateway"
version = "0.1.0"
description = "OpenAI-compatible API proxy with intelligent routing"
authors = [{name = "Your Name", email = "your.email@example.com"}]
readme = "README.md"
requires-python = ">=3.11"
license = {text = "MIT"}
keywords = ["llm", "gateway", "proxy", "openai", "cost-optimization"]
classifiers = [
    "Development Status :: 3 - Alpha",
    "Intended Audience :: Developers",
    "Programming Language :: Python :: 3.11",
]

dependencies = [
    "fastapi>=0.109.0",
    "uvicorn[standard]>=0.27.0",
    "pydantic>=2.5.0",
    "pydantic-settings>=2.1.0",
    "openai>=1.10.0",
    "anthropic>=0.18.0",
    "pyyaml>=6.0",
    "httpx>=0.26.0",
    "python-multipart>=0.0.6",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "pytest-cov>=4.1.0",
    "black>=24.0.0",
    "ruff>=0.1.0",
    "mypy>=1.8.0",
    "ipython>=8.20.0",
]

[tool.setuptools]
package-dir = {"" = "src"}

[tool.setuptools.packages.find]
where = ["src"]

[tool.black]
line-length = 100
target-version = ['py311']
include = '\.pyi?$'

[tool.ruff]
line-length = 100
target-version = "py311"
select = ["E", "F", "I", "N", "W"]
ignore = []

[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
```

### `requirements.txt` (Production Dependencies)

```txt
# Core Framework
fastapi==0.109.0
uvicorn[standard]==0.27.0
pydantic==2.5.3
pydantic-settings==2.1.0

# LLM SDKs
openai==1.10.0
anthropic==0.18.0

# HTTP & Async
httpx==0.26.0
aiofiles==23.2.1

# Config & Utils
pyyaml==6.0.1
python-multipart==0.0.6
python-dotenv==1.0.0

# Optional: MCP (if using)
# mcp==0.1.0

# Optional: Database (if using)
# sqlalchemy==2.0.25
# asyncpg==0.29.0
```

### `requirements-dev.txt` (Development Dependencies)

```txt
-r requirements.txt

# Testing
pytest==7.4.4
pytest-asyncio==0.21.1
pytest-cov==4.1.0
pytest-mock==3.12.0

# Code Quality
black==24.1.1
ruff==0.1.14
mypy==1.8.0
pre-commit==3.6.0

# Development Tools
ipython==8.20.0
ipdb==0.13.13

# Documentation
mkdocs==1.5.3
mkdocs-material==9.5.6
```

### `Dockerfile`

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY src/ ./src/
COPY config/ ./config/

# Expose port
EXPOSE 8000

# Run application
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### `docker-compose.yml`

```yaml
version: '3.8'

services:
  gateway:
    build: .
    ports:
      - "8000:8000"
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
      - OPENAI_API_KEY=${OPENAI_API_KEY}
    volumes:
      - ./src:/app/src
      - ./config:/app/config
    command: uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload

  # Optional: Add dashboard service later
  # dashboard:
  #   build: ./dashboard
  #   ports:
  #     - "3000:3000"
```

### `.env.example` (Copy to .env)

```bash
# LLM API Keys
ANTHROPIC_API_KEY=sk-ant-your-key-here
OPENAI_API_KEY=sk-your-key-here

# Gateway Config
GATEWAY_HOST=0.0.0.0
GATEWAY_PORT=8000
LOG_LEVEL=INFO

# Optional: Database
# DATABASE_URL=postgresql://user:pass@localhost:5432/aikido
```

---

## 🔧 Installation & Setup

### One-Command Setup

```bash
# Clone or create project
git clone <your-repo> ai-aikido-gateway  # or create new
cd ai-aikido-gateway

# Run setup script
chmod +x scripts/setup.sh
./scripts/setup.sh
```

### Manual Setup (Step by Step)

```bash
# 1. Ensure pyenv is active
pyenv local aikido-env

# 2. Upgrade pip
pip install --upgrade pip setuptools wheel

# 3. Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 4. Create .env file
cp .env.example .env
# Edit .env with your API keys

# 5. Install pre-commit hooks (optional)
pre-commit install

# 6. Verify installation
python -c "import fastapi; import anthropic; import openai; print('✅ All imports successful')"
```

---

## 🏃 Running the Gateway

### Development Mode

```bash
# Activate environment (if not auto-activated)
pyenv activate aikido-env

# Run with hot reload
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Or with custom log level
uvicorn src.main:app --reload --log-level debug
```

### Using Docker

```bash
# Build and run
docker-compose up --build

# Run in background
docker-compose up -d

# View logs
docker-compose logs -f gateway

# Stop
docker-compose down
```

### Production Mode

```bash
# Run with multiple workers
uvicorn src.main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## 🧪 Testing

### Run Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=src --cov-report=html

# Specific test file
pytest tests/test_classifier.py

# Verbose mode
pytest -v

# Watch mode (requires pytest-watch)
ptw
```

### Manual Testing

```bash
# Run test script
python scripts/test_gateway.py

# Or use curl
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-4",
    "messages": [{"role": "user", "content": "Hello!"}]
  }'
```

---

## 🎨 Code Quality

### Format Code

```bash
# Format with black
black src/ tests/

# Lint with ruff
ruff check src/ tests/

# Type check with mypy
mypy src/
```

### Pre-commit Hooks

Create `.pre-commit-config.yaml`:

```yaml
repos:
  - repo: https://github.com/psf/black
    rev: 24.1.1
    hooks:
      - id: black
        language_version: python3.11

  - repo: https://github.com/charliermarsh/ruff-pre-commit
    rev: v0.1.14
    hooks:
      - id: ruff
        args: [--fix, --exit-non-zero-on-fix]

  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.5.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
```

Install:
```bash
pre-commit install
```

---

## 📚 Useful Commands

```bash
# Update all dependencies
pip install --upgrade -r requirements.txt

# List installed packages
pip list

# Show package info
pip show fastapi

# Generate requirements from current env
pip freeze > requirements-frozen.txt

# Clean cache
pip cache purge

# Check for outdated packages
pip list --outdated

# Create new migration (if using alembic)
# alembic revision --autogenerate -m "description"

# Access interactive shell with app context
ipython
```

---

## 🐳 Docker Commands

```bash
# Build image
docker build -t ai-aikido-gateway .

# Run container
docker run -p 8000:8000 --env-file .env ai-aikido-gateway

# Execute command in running container
docker-compose exec gateway bash

# View logs
docker-compose logs -f

# Rebuild after changes
docker-compose up --build

# Clean up
docker-compose down -v
```

---

## 🔍 Debugging

### VS Code Launch Configuration

Create `.vscode/launch.json`:

```json
{
  "version": "0.2.0",
  "configurations": [
    {
      "name": "FastAPI: Debug",
      "type": "python",
      "request": "launch",
      "module": "uvicorn",
      "args": [
        "src.main:app",
        "--reload",
        "--host", "0.0.0.0",
        "--port", "8000"
      ],
      "jinja": true,
      "justMyCode": false,
      "env": {
        "ANTHROPIC_API_KEY": "${env:ANTHROPIC_API_KEY}",
        "OPENAI_API_KEY": "${env:OPENAI_API_KEY}"
      }
    },
    {
      "name": "Python: Current File",
      "type": "python",
      "request": "launch",
      "program": "${file}",
      "console": "integratedTerminal",
      "justMyCode": false
    }
  ]
}
```

### Debug Mode

```bash
# Run with debugger
python -m debugpy --listen 5678 --wait-for-client -m uvicorn src.main:app --reload

# Or use ipdb
import ipdb; ipdb.set_trace()  # Add breakpoint in code
```

---

## 📊 Monitoring & Logging

### Check Gateway Health

```bash
# Health check endpoint
curl http://localhost:8000/health

# Metrics endpoint (if implemented)
curl http://localhost:8000/metrics

# API docs
open http://localhost:8000/docs
```

### View Logs

```bash
# Application logs
tail -f logs/aikido.log

# Docker logs
docker-compose logs -f gateway

# Follow specific service
docker-compose logs -f --tail=100 gateway
```

---

## 🚀 Deployment Checklist

- [ ] All tests passing (`pytest`)
- [ ] Code formatted (`black src/`)
- [ ] Linting clean (`ruff check src/`)
- [ ] Type checking passes (`mypy src/`)
- [ ] `.env` configured with production keys
- [ ] `config/aikido.yaml` reviewed
- [ ] Docker image builds successfully
- [ ] Health endpoint responds
- [ ] API docs accessible
- [ ] Monitoring configured
- [ ] Backups configured (if using database)

---

## 🆘 Troubleshooting

### pyenv not working
```bash
# Reinstall pyenv
brew reinstall pyenv pyenv-virtualenv

# Add to shell config
echo 'eval "$(pyenv init -)"' >> ~/.zshrc
source ~/.zshrc
```

### Virtual environment issues
```bash
# Remove and recreate
pyenv virtualenv-delete aikido-env
pyenv virtualenv 3.11.7 aikido-env
pyenv local aikido-env
pip install -r requirements.txt
```

### Import errors
```bash
# Ensure you're in project root
cd /path/to/ai-aikido-gateway

# Verify PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)/src"

# Or install in editable mode
pip install -e .
```

### Port already in use
```bash
# Find process using port 8000
lsof -i :8000

# Kill process
kill -9 <PID>
```

---

## 📖 Additional Resources

- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [pyenv Documentation](https://github.com/pyenv/pyenv)
- [Anthropic API Docs](https://docs.anthropic.com/)
- [OpenAI API Docs](https://platform.openai.com/docs)
- [MCP Protocol](https://modelcontextprotocol.io/)

---

## 🤝 Git Workflow

```bash
# Initial commit
git add .
git commit -m "Initial project setup"

# Create feature branch
git checkout -b feature/classifier

# Regular commits
git add src/core/classifier.py
git commit -m "Add cheap LLM classifier"

# Push to remote
git push origin feature/classifier

# Keep main branch clean
git checkout main
git pull origin main
git merge feature/classifier
```

---

## ✅ Quick Start Checklist

- [ ] pyenv installed
- [ ] Python 3.11 installed via pyenv
- [ ] Virtual environment created
- [ ] Dependencies installed
- [ ] `.env` file configured
- [ ] Git repository initialized
- [ ] `.gitignore` in place
- [ ] Can run `uvicorn src.main:app --reload`
- [ ] Health endpoint responds at `/health`
- [ ] API docs visible at `/docs`

---

**Ready to build! 🚀**