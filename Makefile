.PHONY: help status start stop restart logs build clean install test dev

# Colors for output
RED := \033[0;31m
GREEN := \033[0;32m
YELLOW := \033[0;33m
BLUE := \033[0;34m
NC := \033[0m # No Color

# Default target
.DEFAULT_GOAL := help

##@ General

help: ## Display this help message
	@echo "$(BLUE)LLM Service Stack - Makefile Commands$(NC)"
	@echo ""
	@awk 'BEGIN {FS = ":.*##"; printf "Usage:\n  make $(YELLOW)<target>$(NC)\n"} /^[a-zA-Z_0-9-]+:.*?##/ { printf "  $(YELLOW)%-20s$(NC) %s\n", $$1, $$2 } /^##@/ { printf "\n$(BLUE)%s$(NC)\n", substr($$0, 5) } ' $(MAKEFILE_LIST)

##@ Docker Stack Operations

status: ## Show status of all services
	@echo "$(BLUE)==> Checking Docker services status...$(NC)"
	@docker-compose ps
	@echo ""
	@echo "$(BLUE)==> Checking service health...$(NC)"
	@docker-compose ps --format "table {{.Name}}\t{{.Status}}\t{{.Ports}}"

start: ## Start all services
	@echo "$(GREEN)==> Starting all services...$(NC)"
	@docker-compose up -d
	@echo "$(GREEN)==> Services started!$(NC)"
	@make status

stop: ## Stop all services
	@echo "$(YELLOW)==> Stopping all services...$(NC)"
	@docker-compose stop
	@echo "$(GREEN)==> Services stopped!$(NC)"

down: ## Stop and remove all containers
	@echo "$(RED)==> Stopping and removing all containers...$(NC)"
	@docker-compose down
	@echo "$(GREEN)==> Containers removed!$(NC)"

restart: ## Restart all services
	@echo "$(YELLOW)==> Restarting all services...$(NC)"
	@docker-compose restart
	@echo "$(GREEN)==> Services restarted!$(NC)"

build: ## Build or rebuild all services
	@echo "$(BLUE)==> Building all services...$(NC)"
	@docker-compose build --no-cache
	@echo "$(GREEN)==> Build complete!$(NC)"

rebuild: ## Rebuild and restart all services
	@make down
	@make build
	@make start

##@ Individual Service Operations

start-gateway: ## Start gateway service only
	@echo "$(GREEN)==> Starting gateway service...$(NC)"
	@docker-compose up -d gateway redis
	@docker-compose ps gateway

stop-gateway: ## Stop gateway service
	@echo "$(YELLOW)==> Stopping gateway service...$(NC)"
	@docker-compose stop gateway

restart-gateway: ## Restart gateway service
	@echo "$(YELLOW)==> Restarting gateway service...$(NC)"
	@docker-compose restart gateway

start-app-server: ## Start app-server service only
	@echo "$(GREEN)==> Starting app-server service...$(NC)"
	@docker-compose up -d app-server mongo
	@docker-compose ps app-server

stop-app-server: ## Stop app-server service
	@echo "$(YELLOW)==> Stopping app-server service...$(NC)"
	@docker-compose stop app-server

restart-app-server: ## Restart app-server service
	@echo "$(YELLOW)==> Restarting app-server service...$(NC)"
	@docker-compose restart app-server

start-playground: ## Start playground service only
	@echo "$(GREEN)==> Starting playground service...$(NC)"
	@docker-compose up -d playground
	@docker-compose ps playground

stop-playground: ## Stop playground service
	@echo "$(YELLOW)==> Stopping playground service...$(NC)"
	@docker-compose stop playground

restart-playground: ## Restart playground service
	@echo "$(YELLOW)==> Restarting playground service...$(NC)"
	@docker-compose restart playground

start-web-chat: ## Start web-chat service only
	@echo "$(GREEN)==> Starting web-chat service...$(NC)"
	@docker-compose up -d web-chat
	@docker-compose ps web-chat

stop-web-chat: ## Stop web-chat service
	@echo "$(YELLOW)==> Stopping web-chat service...$(NC)"
	@docker-compose stop web-chat

restart-web-chat: ## Restart web-chat service
	@echo "$(YELLOW)==> Restarting web-chat service...$(NC)"
	@docker-compose restart web-chat

##@ Database Operations

start-mongo: ## Start MongoDB only
	@echo "$(GREEN)==> Starting MongoDB...$(NC)"
	@docker-compose up -d mongo
	@docker-compose ps mongo

stop-mongo: ## Stop MongoDB
	@echo "$(YELLOW)==> Stopping MongoDB...$(NC)"
	@docker-compose stop mongo

mongo-shell: ## Connect to MongoDB shell
	@echo "$(BLUE)==> Connecting to MongoDB shell...$(NC)"
	@docker-compose exec mongo mongosh llm_service

mongo-backup: ## Backup MongoDB database
	@echo "$(BLUE)==> Backing up MongoDB...$(NC)"
	@mkdir -p ./backups
	@docker-compose exec -T mongo mongodump --db=llm_service --archive > ./backups/llm_service_$$(date +%Y%m%d_%H%M%S).archive
	@echo "$(GREEN)==> Backup saved to ./backups/$(NC)"

mongo-restore: ## Restore MongoDB from latest backup (requires BACKUP_FILE env var)
	@if [ -z "$(BACKUP_FILE)" ]; then \
		echo "$(RED)Error: Please specify BACKUP_FILE=path/to/backup.archive$(NC)"; \
		exit 1; \
	fi
	@echo "$(BLUE)==> Restoring MongoDB from $(BACKUP_FILE)...$(NC)"
	@docker-compose exec -T mongo mongorestore --db=llm_service --archive < $(BACKUP_FILE)
	@echo "$(GREEN)==> Restore complete!$(NC)"

migrate: ## Run database migrations (gateway SQLite)
	@echo "$(BLUE)==> Running gateway database migrations...$(NC)"
	@cd gateway && python migrate.py upgrade
	@echo "$(GREEN)==> Migrations complete!$(NC)"

migrate-status: ## Show current migration status
	@echo "$(BLUE)==> Current migration status:$(NC)"
	@cd gateway && python migrate.py current

migrate-history: ## Show migration history
	@echo "$(BLUE)==> Migration history:$(NC)"
	@cd gateway && python migrate.py history

migrate-create: ## Create a new migration (usage: make migrate-create MSG="description")
	@if [ -z "$(MSG)" ]; then \
		echo "$(RED)Error: Please specify MSG=\"your migration description\"$(NC)"; \
		exit 1; \
	fi
	@echo "$(BLUE)==> Creating new migration: $(MSG)$(NC)"
	@cd gateway && python migrate.py revision "$(MSG)"
	@echo "$(GREEN)==> Migration file created!$(NC)"

start-postgres: ## Start PostgreSQL only
	@echo "$(GREEN)==> Starting PostgreSQL...$(NC)"
	@docker-compose up -d postgres
	@docker-compose ps postgres

stop-postgres: ## Stop PostgreSQL
	@echo "$(YELLOW)==> Stopping PostgreSQL...$(NC)"
	@docker-compose stop postgres

postgres-shell: ## Connect to PostgreSQL shell
	@echo "$(BLUE)==> Connecting to PostgreSQL shell...$(NC)"
	@docker-compose exec postgres psql -U llm_user -d llm_templates

seed-templates: ## Seed template library with starter templates
	@echo "$(BLUE)==> Seeding template library...$(NC)"
	@docker-compose exec gateway python seed_templates.py
	@echo "$(GREEN)==> Template library seeded!$(NC)"

clean-templates: ## Delete all templates from PostgreSQL
	@echo "$(YELLOW)==> Cleaning template library...$(NC)"
	@docker-compose exec postgres psql -U llm_user -d llm_templates -c "DELETE FROM templates; DELETE FROM template_usage;"
	@echo "$(GREEN)==> Template library cleaned!$(NC)"

reseed-templates: clean-templates seed-templates ## Clean and reseed templates
	@echo "$(GREEN)==> Templates reseeded successfully!$(NC)"

list-templates: ## List all templates in PostgreSQL
	@echo "$(BLUE)==> Templates in library:$(NC)"
	@docker-compose exec postgres psql -U llm_user -d llm_templates -c "SELECT id, name, category, usage_count, ROUND(CAST(success_rate AS numeric), 2) as success_rate FROM templates ORDER BY usage_count DESC;"

template-stats: ## Show template usage statistics
	@echo "$(BLUE)==> Template statistics:$(NC)"
	@docker-compose exec postgres psql -U llm_user -d llm_templates -c "SELECT category, COUNT(*) as count, ROUND(AVG(usage_count)) as avg_usage, ROUND(CAST(AVG(success_rate) AS numeric), 2) as avg_success FROM templates GROUP BY category ORDER BY count DESC;"

start-adminer: ## Start Adminer (Database UI)
	@echo "$(GREEN)==> Starting Adminer...$(NC)"
	@docker-compose up -d adminer
	@echo "$(GREEN)==> Adminer available at http://localhost:8080$(NC)"

stop-adminer: ## Stop Adminer
	@echo "$(YELLOW)==> Stopping Adminer...$(NC)"
	@docker-compose stop adminer

start-redis: ## Start Redis only
	@echo "$(GREEN)==> Starting Redis...$(NC)"
	@docker-compose up -d redis
	@docker-compose ps redis

stop-redis: ## Stop Redis
	@echo "$(YELLOW)==> Stopping Redis...$(NC)"
	@docker-compose stop redis

redis-cli: ## Connect to Redis CLI
	@echo "$(BLUE)==> Connecting to Redis CLI...$(NC)"
	@docker-compose exec redis redis-cli

redis-flush: ## Flush all Redis cache
	@echo "$(RED)==> Flushing Redis cache...$(NC)"
	@docker-compose exec redis redis-cli FLUSHALL
	@echo "$(GREEN)==> Cache cleared!$(NC)"

##@ Logs and Monitoring

logs: ## Show logs for all services
	@docker-compose logs -f

logs-gateway: ## Show logs for gateway service
	@docker-compose logs -f gateway

logs-app-server: ## Show logs for app-server service
	@docker-compose logs -f app-server

logs-playground: ## Show logs for playground service
	@docker-compose logs -f playground

logs-web-chat: ## Show logs for web-chat service
	@docker-compose logs -f web-chat

logs-mongo: ## Show logs for MongoDB
	@docker-compose logs -f mongo

logs-redis: ## Show logs for Redis
	@docker-compose logs -f redis

##@ Development

dev-gateway: ## Run gateway in development mode (local, no Docker)
	@echo "$(BLUE)==> Starting gateway in development mode...$(NC)"
	@cd gateway && uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

dev-app-server: ## Run app-server in development mode (local, no Docker)
	@echo "$(BLUE)==> Starting app-server in development mode...$(NC)"
	@cd app-server && npm run dev

dev-playground: ## Run playground in development mode (local, no Docker)
	@echo "$(BLUE)==> Starting playground in development mode...$(NC)"
	@cd playground && PORT=3001 npm run dev

dev-web-chat: ## Run web-chat in development mode (local, no Docker)
	@echo "$(BLUE)==> Starting web-chat in development mode...$(NC)"
	@cd web-chat && npm start

install: ## Install dependencies for all services
	@echo "$(BLUE)==> Installing Python dependencies for gateway...$(NC)"
	@cd gateway && pip install -r requirements.txt
	@echo "$(BLUE)==> Installing Node dependencies for app-server...$(NC)"
	@cd app-server && npm install
	@echo "$(BLUE)==> Installing Node dependencies for playground...$(NC)"
	@cd playground && npm install
	@echo "$(BLUE)==> Installing Node dependencies for web-chat...$(NC)"
	@cd web-chat && npm install
	@echo "$(GREEN)==> All dependencies installed!$(NC)"

##@ Testing

test: ## Run tests for all services
	@echo "$(BLUE)==> Running gateway tests...$(NC)"
	@cd gateway && pytest
	@echo "$(BLUE)==> Running app-server tests...$(NC)"
	@cd app-server && npm test
	@echo "$(BLUE)==> Running playground tests...$(NC)"
	@cd playground && npm test
	@echo "$(BLUE)==> Running web-chat tests...$(NC)"
	@cd web-chat && npm test

test-gateway: ## Run gateway tests only
	@echo "$(BLUE)==> Running gateway tests...$(NC)"
	@cd gateway && pytest

test-app-server: ## Run app-server tests only
	@echo "$(BLUE)==> Running app-server tests...$(NC)"
	@cd app-server && npm test

##@ Cleanup

clean: ## Remove all containers, volumes, and build artifacts
	@echo "$(RED)==> WARNING: This will remove all containers, volumes, and data!$(NC)"
	@echo "$(RED)==> Press Ctrl+C to cancel, or wait 5 seconds to continue...$(NC)"
	@sleep 5
	@docker-compose down -v
	@rm -rf gateway/__pycache__ gateway/.pytest_cache
	@rm -rf app-server/.next app-server/node_modules
	@rm -rf playground/.next playground/node_modules
	@rm -rf web-chat/node_modules web-chat/build
	@echo "$(GREEN)==> Cleanup complete!$(NC)"

clean-cache: ## Clear all caches (Redis, Next.js, Python)
	@echo "$(YELLOW)==> Clearing all caches...$(NC)"
	@make redis-flush || true
	@rm -rf app-server/.next playground/.next
	@rm -rf gateway/__pycache__ gateway/.pytest_cache
	@echo "$(GREEN)==> Caches cleared!$(NC)"

##@ Quick Start

quickstart: ## Quick start: build and run entire stack
	@echo "$(GREEN)=====================================$(NC)"
	@echo "$(GREEN)  LLM Service Stack - Quick Start$(NC)"
	@echo "$(GREEN)=====================================$(NC)"
	@echo ""
	@echo "$(BLUE)==> Building services...$(NC)"
	@docker-compose build
	@echo ""
	@echo "$(BLUE)==> Starting services...$(NC)"
	@docker-compose up -d
	@echo ""
	@sleep 3
	@make status
	@echo ""
	@echo "$(GREEN)=====================================$(NC)"
	@echo "$(GREEN)  Stack is ready!$(NC)"
	@echo "$(GREEN)=====================================$(NC)"
	@echo ""
	@echo "Services available at:"
	@echo "  $(YELLOW)Gateway:    $(NC)http://localhost:8000"
	@echo "  $(YELLOW)App Server: $(NC)http://localhost:3000"
	@echo "  $(YELLOW)Playground: $(NC)http://localhost:3001"
	@echo "  $(YELLOW)Web Chat:   $(NC)http://localhost:3002"
	@echo "  $(YELLOW)Adminer:    $(NC)http://localhost:8080"
	@echo ""
	@echo "Next steps:"
	@echo "  $(YELLOW)make seed-templates$(NC) - Seed template library"
	@echo "  $(YELLOW)make logs$(NC)           - View all logs"
	@echo "  $(YELLOW)make status$(NC)         - Check service status"
	@echo "  $(YELLOW)make urls$(NC)           - Show all URLs"
	@echo "  $(YELLOW)make help$(NC)           - Show all commands"

##@ Health Checks

health: ## Check health of all services
	@echo "$(BLUE)==> Checking service health...$(NC)"
	@echo ""
	@echo "$(YELLOW)Gateway:$(NC)"
	@curl -s http://localhost:8000/ | jq '.' || echo "$(RED)Gateway not responding$(NC)"
	@echo ""
	@echo "$(YELLOW)MongoDB:$(NC)"
	@docker-compose exec mongo mongosh --eval "db.adminCommand('ping')" --quiet || echo "$(RED)MongoDB not responding$(NC)"
	@echo ""
	@echo "$(YELLOW)Redis:$(NC)"
	@docker-compose exec redis redis-cli ping || echo "$(RED)Redis not responding$(NC)"

urls: ## Show URLs for all services
	@echo "$(BLUE)Service URLs:$(NC)"
	@echo "  Gateway:    http://localhost:8000"
	@echo "  App Server: http://localhost:3000"
	@echo "  Playground: http://localhost:3001"
	@echo "  Web Chat:   http://localhost:3002"
	@echo "  Adminer:    http://localhost:8080 (Database UI)"
	@echo ""
	@echo "$(BLUE)API Endpoints:$(NC)"
	@echo "  Gateway Health:      http://localhost:8000/"
	@echo "  Gateway Models:      http://localhost:8000/v1/models"
	@echo "  Gateway Templates:   http://localhost:8000/v1/templates"
	@echo "  App Server Users:    http://localhost:3000/api/users"
	@echo "  App Server Sessions: http://localhost:3000/api/sessions"
	@echo "  App Server Keys:     http://localhost:3000/api/keys"
