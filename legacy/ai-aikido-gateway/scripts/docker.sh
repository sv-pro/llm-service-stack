#!/bin/bash

# AI Aikido Gateway - Docker Management Script
# Run from project root directory

set -e

DEPLOYMENT_DIR="deployment"
ENV_FILE=".env"
ENV_FLAG=""

if [ ! -d "$DEPLOYMENT_DIR" ]; then
    echo "Error: deployment/ directory not found. Run this script from the project root."
    exit 1
fi

# Check if .env file exists
if [ -f "$ENV_FILE" ]; then
    ENV_FLAG="--env-file $ENV_FILE"
else
    echo "⚠️  Warning: .env file not found. API keys may not be configured."
    echo "   Export OPENAI_API_KEY / ANTHROPIC_API_KEY or use docker compose --env-file manually if needed."
fi

# Default action
ACTION=${1:-"help"}

case "$ACTION" in
    "dev")
        echo "🚀 Starting development environment..."
        docker-compose ${ENV_FLAG} -f ${DEPLOYMENT_DIR}/docker-compose.yml -f ${DEPLOYMENT_DIR}/docker-compose.dev.yml up
        ;;
    "prod")
        echo "🚀 Starting production environment..."
        docker-compose ${ENV_FLAG} -f ${DEPLOYMENT_DIR}/docker-compose.yml -f ${DEPLOYMENT_DIR}/docker-compose.prod.yml up -d
        ;;
    "stop")
        echo "🛑 Stopping services..."
        docker-compose ${ENV_FLAG} -f ${DEPLOYMENT_DIR}/docker-compose.yml -f ${DEPLOYMENT_DIR}/docker-compose.dev.yml down 2>/dev/null || true
        docker-compose ${ENV_FLAG} -f ${DEPLOYMENT_DIR}/docker-compose.yml -f ${DEPLOYMENT_DIR}/docker-compose.prod.yml down 2>/dev/null || true
        ;;
    "build")
        echo "🔨 Building containers..."
        docker-compose ${ENV_FLAG} -f ${DEPLOYMENT_DIR}/docker-compose.yml build
        ;;
    "clean")
        echo "🧹 Cleaning up containers and images..."
        docker-compose ${ENV_FLAG} -f ${DEPLOYMENT_DIR}/docker-compose.yml down --rmi all --volumes --remove-orphans
        ;;
    "logs")
        echo "📋 Showing logs..."
        docker-compose ${ENV_FLAG} -f ${DEPLOYMENT_DIR}/docker-compose.yml logs -f
        ;;
    "help"|*)
        echo "AI Aikido Gateway - Docker Management"
        echo ""
        echo "Usage: $0 [command]"
        echo ""
        echo "Commands:"
        echo "  dev     - Start development environment (with hot reload)"
        echo "  prod    - Start production environment (detached)"
        echo "  stop    - Stop all services"
        echo "  build   - Build container images"
        echo "  clean   - Remove containers, images, and volumes"
        echo "  logs    - Show service logs"
        echo "  help    - Show this help message"
        echo ""
        echo "Examples:"
        echo "  $0 dev      # Start dev environment"
        echo "  $0 prod     # Start production environment"
        echo "  $0 stop     # Stop all services"
        ;;
esac
