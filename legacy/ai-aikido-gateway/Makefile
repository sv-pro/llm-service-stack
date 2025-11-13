.PHONY: help setup install dev-install start start-reload start-debug start-all stop stop-all restart restart-all test test-cov test-watch format lint type-check quality clean ui-test ui-tests-pw ui-tests-pw-show docker-build docker-up docker-down docker-logs docker-redeploy docker-redeploy-infra docker-rebuild-all docker-reset git-status client-install client-start client-stop

# Docker compose configuration
DOCKER_COMPOSE ?= $(shell if docker compose version >/dev/null 2>&1; then echo "docker compose"; elif command -v docker-compose >/dev/null 2>&1; then echo "docker-compose"; else echo ""; fi)
COMPOSE_FILE_BASE := -f deployment/docker-compose.yml
COMPOSE_ENV_FILE := $(if $(wildcard .env),--env-file .env,)
APP_SERVICES := gateway dashboard
INFRA_SERVICES := embeddings qdrant redis

ifeq ($(DOCKER_COMPOSE),)
$(error Neither 'docker compose' nor 'docker-compose' is available on this system)
endif

# Default target - show help
help:
	@echo "AI Aikido Gateway - Available Commands"
	@echo ""
	@echo "Setup & Installation:"
	@echo "  make setup          - Full project setup (creates venv, installs deps, creates .env)"
	@echo "  make install        - Install production dependencies only"
	@echo "  make dev-install    - Install all dependencies (prod + dev)"
	@echo ""
	@echo "Development:"
	@echo "  make start          - Start the gateway server (production mode)"
	@echo "  make start-reload   - Start with hot reload (development mode)"
	@echo "  make start-debug    - Start with debug logging"
	@echo "  make start-all      - Start gateway + unified dashboard"
	@echo "  make stop           - Stop the gateway server"
	@echo "  make stop-all       - Stop all services (gateway + dashboard)"
	@echo "  make restart        - Stop and restart the gateway server"
	@echo "  make restart-all    - Stop and restart all services (gateway + dashboard)"
	@echo ""
	@echo "Testing:"
	@echo "  make test           - Run all tests"
	@echo "  make test-cov       - Run tests with coverage report"
	@echo "  make test-watch     - Run tests in watch mode"
	@echo "  make ui-test        - Run Playwright dashboard UI tests"
	@echo "  make ui-tests-pw    - Start dashboard automatically and run Playwright"
	@echo "  make ui-tests-pw-show - Start dashboard and run Playwright in headed mode"
	@echo ""
	@echo "Code Quality:"
	@echo "  make format         - Format code with black"
	@echo "  make lint           - Lint code with ruff"
	@echo "  make type-check     - Type check with mypy"
	@echo "  make quality        - Run all quality checks (format + lint + type-check)"
	@echo ""
	@echo "Reference Client (optional - deprecated):"
	@echo "  make client-install - Install reference client dependencies"
	@echo "  make client-start   - Start reference client (port 3000 - conflicts with dashboard!)"
	@echo "  make client-stop    - Stop reference client"
	@echo "  Note: The unified dashboard replaces this. Only use for testing."
	@echo ""
	@echo "Docker:"
	@echo "  make docker-build        - Build gateway/dashboard images (deployment/docker-compose.yml)"
	@echo "  make docker-up           - Start stack via deployment/docker-compose.yml (detached)"
	@echo "  make docker-down         - Stop stack via deployment/docker-compose.yml"
	@echo "  make docker-redeploy     - Rebuild gateway + dashboard only (preserves infra services)"
	@echo "  make docker-redeploy-infra - Rebuild infra services only (embeddings/qdrant/redis)"
	@echo "  make docker-rebuild-all  - Rebuild ALL services from scratch"
	@echo "  make docker-reset        - DANGER: Stop and delete all containers + volumes"
	@echo "  make docker-logs         - Follow logs from deployment/docker-compose.yml"
	@echo ""
	@echo "Utilities:"
	@echo "  make clean          - Remove cache files and build artifacts"
	@echo "  make git-status     - Show git status"
	@echo ""

# Setup - Full project initialization
setup:
	@echo "Setting up AI Aikido Gateway..."
	@bash scripts/setup.sh
	@echo ""
	@echo "Setup complete! Next steps:"
	@echo "1. Edit .env file and add your API keys"
	@echo "2. Run 'make start-reload' to start the server"

# Install - Production dependencies only
install:
	pip install -r requirements.txt

# Dev Install - All dependencies
dev-install:
	pip install -r requirements.txt
	pip install -r requirements-dev.txt

# Start - Production mode
start:
	@echo "Starting AI Aikido Gateway (production mode)..."
	uvicorn src.main:app --host 0.0.0.0 --port 8000

# Start with reload - Development mode
start-reload:
	@echo "Starting AI Aikido Gateway (development mode with hot reload)..."
	uvicorn src.main:app --reload --host 0.0.0.0 --port 8000

# Start with debug logging
start-debug:
	@echo "Starting AI Aikido Gateway (debug mode)..."
	uvicorn src.main:app --reload --log-level debug --host 0.0.0.0 --port 8000

# Start all - Start gateway and unified React dashboard
start-all:
	@echo "Starting all services (gateway + dashboard)..."
	@echo ""
	@echo "Starting gateway on http://localhost:8000 ..."
	@nohup uvicorn src.main:app --reload --host 0.0.0.0 --port 8000 > /tmp/aikido-gateway.log 2>&1 & echo $$! > /tmp/aikido-gateway.pid
	@sleep 2
	@echo "✅ Gateway started (PID: $$(cat /tmp/aikido-gateway.pid))"
	@echo ""
	@echo "Starting unified dashboard on http://localhost:3000 ..."
	@cd dashboard && nohup npm run dev > /tmp/aikido-dashboard.log 2>&1 & echo $$! > /tmp/aikido-dashboard.pid
	@sleep 2
	@echo "✅ Unified dashboard started (PID: $$(cat /tmp/aikido-dashboard.pid))"
	@echo ""
	@echo "🎉 All services running!"
	@echo "   Gateway:   http://localhost:8000"
	@echo "   Dashboard: http://localhost:3000"
	@echo ""
	@echo "View logs:"
	@echo "   tail -f /tmp/aikido-gateway.log"
	@echo "   tail -f /tmp/aikido-dashboard.log"
	@echo ""
	@echo "Stop with: make stop-all"

# Stop - Kill any running uvicorn server on port 8000
stop:
	@echo "Stopping AI Aikido Gateway..."
	@-bash -c 'PID=$$(lsof -ti:8000); if [ -n "$$PID" ]; then kill -9 $$PID && echo "Gateway stopped (PID: $$PID)"; else echo "No gateway server running on port 8000"; fi'

# Stop all - Kill gateway and unified dashboard
stop-all:
	@echo "Stopping all services (gateway + dashboard)..."
	@-bash -c 'PID=$$(lsof -ti:8000); if [ -n "$$PID" ]; then kill -9 $$PID && echo "✅ Gateway stopped (PID: $$PID)"; else echo "⚠️  No gateway server running on port 8000"; fi'
	@-bash -c 'PID=$$(lsof -ti:3000); if [ -n "$$PID" ]; then kill -9 $$PID && echo "✅ Dashboard stopped (PID: $$PID)"; else echo "⚠️  No dashboard running on port 3000"; fi'
	@echo "All services stopped"

# Restart - Stop and start with reload
restart: stop
	@sleep 1
	@echo "Restarting AI Aikido Gateway..."
	@$(MAKE) start-reload

# Restart all - Stop and restart all services
restart-all: stop-all
	@sleep 1
	@echo "Restarting all services..."
	@$(MAKE) start-all

# Test - Run all tests
test:
	@echo "Running tests..."
	pytest

# Test with coverage
test-cov:
	@echo "Running tests with coverage..."
	pytest --cov=src --cov-report=html --cov-report=term
	@echo ""
	@echo "Coverage report generated in htmlcov/index.html"

# Test watch mode
test-watch:
	@echo "Running tests in watch mode..."
	pytest-watch

# UI tests - Run Playwright dashboard tests
ui-test:
	@echo "Running dashboard Playwright tests..."
	cd dashboard && npm run ui-test $(if $(ARGS),-- $(ARGS),)

ui-tests-pw:
	@echo "Running Playwright tests with dashboard auto-start..."
	cd dashboard && PLAYWRIGHT_WEB_SERVER=true npm run ui-test $(if $(ARGS),-- $(ARGS),)

ui-tests-pw-show:
	@echo "Running Playwright tests in headed mode with dashboard auto-start..."
	cd dashboard && PLAYWRIGHT_WEB_SERVER=true PLAYWRIGHT_SLOWMO=$(PLAYWRIGHT_SLOWMO) npm run ui-test -- --headed $(ARGS)

# Format - Format code with black
format:
	@echo "Formatting code with black..."
	black src/ tests/

# Lint - Check code with ruff
lint:
	@echo "Linting code with ruff..."
	ruff check src/ tests/

# Lint fix - Auto-fix linting issues
lint-fix:
	@echo "Auto-fixing linting issues..."
	ruff check src/ tests/ --fix

# Type check - Run mypy
type-check:
	@echo "Type checking with mypy..."
	mypy src/

# Quality - Run all quality checks
quality: format lint type-check
	@echo ""
	@echo "All quality checks passed!"

# Clean - Remove cache and build artifacts
clean:
	@echo "Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".pytest_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".mypy_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name ".ruff_cache" -exec rm -rf {} + 2>/dev/null || true
	find . -type d -name "htmlcov" -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name ".coverage" -delete 2>/dev/null || true
	@echo "Cleanup complete!"

# Docker build
docker-build:
	@echo "Building Docker images defined in deployment/docker-compose.yml..."
	$(DOCKER_COMPOSE) $(COMPOSE_ENV_FILE) $(COMPOSE_FILE_BASE) build

# Docker up
docker-up:
	@echo "Starting services with docker compose (detached)..."
	$(DOCKER_COMPOSE) $(COMPOSE_ENV_FILE) $(COMPOSE_FILE_BASE) up -d
	@echo ""
	@echo "Gateway available at: http://localhost:8000"
	@echo "Dashboard available at: http://localhost:3000"

# Docker redeploy - rebuild gateway + dashboard only (preserves data, embeddings, qdrant)
docker-redeploy:
	@echo "Redeploying application services (gateway + dashboard)..."
	@echo "Note: This preserves embeddings/Qdrant/Redis infrastructure services"
	$(DOCKER_COMPOSE) $(COMPOSE_ENV_FILE) $(COMPOSE_FILE_BASE) stop $(APP_SERVICES)
	$(DOCKER_COMPOSE) $(COMPOSE_ENV_FILE) $(COMPOSE_FILE_BASE) build $(APP_SERVICES)
	$(DOCKER_COMPOSE) $(COMPOSE_ENV_FILE) $(COMPOSE_FILE_BASE) up -d $(APP_SERVICES)
	@echo ""
	@echo "Application redeployed! Services preserved:"
	@echo "  ✓ Embeddings service (unchanged)"
	@echo "  ✓ Qdrant vector DB (unchanged)"
	@echo "  ✓ Redis service (unchanged)"
	@echo "  ✓ All data volumes (persisted)"

# Docker redeploy infra-only
docker-redeploy-infra:
	@echo "Redeploying infrastructure services (embeddings + qdrant + redis)..."
	$(DOCKER_COMPOSE) $(COMPOSE_ENV_FILE) $(COMPOSE_FILE_BASE) stop $(INFRA_SERVICES)
	$(DOCKER_COMPOSE) $(COMPOSE_ENV_FILE) $(COMPOSE_FILE_BASE) build $(INFRA_SERVICES)
	$(DOCKER_COMPOSE) $(COMPOSE_ENV_FILE) $(COMPOSE_FILE_BASE) up -d $(INFRA_SERVICES)
	@echo "Infrastructure services redeployed (application containers untouched)."

# Docker reset - full teardown including volumes
docker-reset:
	@echo "⚠️  WARNING: This will delete ALL data including:"
	@echo "   - Request history database"
	@echo "   - Cache database"
	@echo "   - Qdrant vector storage"
	@echo "   - Semantic metrics"
	@echo ""
	@read -p "Are you sure? Type 'yes' to continue: " confirm; \
	if [ "$$confirm" = "yes" ]; then \
		echo "Stopping and removing all containers and volumes..."; \
		$(DOCKER_COMPOSE) $(COMPOSE_ENV_FILE) $(COMPOSE_FILE_BASE) down -v; \
		echo "✓ Full reset complete"; \
	else \
		echo "Reset cancelled"; \
	fi

# Docker full rebuild - rebuild everything from scratch
docker-rebuild-all:
	@echo "Full rebuild of all services (down -> build all -> up)..."
	@$(MAKE) docker-down
	$(DOCKER_COMPOSE) $(COMPOSE_ENV_FILE) $(COMPOSE_FILE_BASE) build
	@$(MAKE) docker-up

# Docker down
docker-down:
	@echo "Stopping services..."
	$(DOCKER_COMPOSE) $(COMPOSE_ENV_FILE) $(COMPOSE_FILE_BASE) down

# Docker logs (follow)
docker-logs:
	@echo "Tailing logs (Ctrl+C to stop)..."
	$(DOCKER_COMPOSE) $(COMPOSE_ENV_FILE) $(COMPOSE_FILE_BASE) logs -f

# Git status
git-status:
	@git status

# Client install - Install Node.js dependencies
client-install:
	@echo "Installing client dependencies..."
	cd client && npm install

# Client start - Start the reference client
client-start:
	@echo "Starting reference client..."
	@echo "Client will run on http://localhost:3000"
	cd client && npm start

# Client stop - Stop the reference client
client-stop:
	@echo "Stopping reference client..."
	@-bash -c 'PID=$$(lsof -ti:3000); if [ -n "$$PID" ]; then kill -9 $$PID && echo "Reference client stopped (PID: $$PID)"; else echo "No reference client running on port 3000"; fi'
.DEFAULT_GOAL := help

PLAYWRIGHT_SLOWMO ?= 200
ifdef PLAYWRIGHT_SLOW_MO
PLAYWRIGHT_SLOWMO := $(PLAYWRIGHT_SLOW_MO)
endif
