#!/bin/bash

# AI Aikido Gateway - Docker Setup Script
# This script helps set up the Docker environment for the first time

set -e  # Exit on any error

echo "🐳 AI Aikido Gateway - Docker Setup"
echo "=================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed. Please install Docker first:${NC}"
    echo "   - Windows/Mac: https://docs.docker.com/desktop/"
    echo "   - Linux: https://docs.docker.com/engine/install/"
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null && ! docker compose version &> /dev/null; then
    echo -e "${RED}❌ Docker Compose is not available. Please install Docker Compose.${NC}"
    exit 1
fi

# Determine docker-compose command
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
else
    DOCKER_COMPOSE="docker compose"
fi

echo -e "${GREEN}✅ Docker is installed and available${NC}"

# Check if .env.docker exists
if [ ! -f ".env.docker" ]; then
    echo -e "${YELLOW}⚠️  .env.docker not found. Creating from template...${NC}"
    
    if [ -f ".env.docker.example" ]; then
        cp .env.docker.example .env.docker
        echo -e "${GREEN}✅ Created .env.docker from template${NC}"
        echo ""
        echo -e "${YELLOW}🔑 IMPORTANT: Please edit .env.docker and add your API keys:${NC}"
        echo "   - OPENAI_API_KEY=sk-your-openai-key-here"
        echo "   - ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here"
        echo ""
        echo -e "${BLUE}📝 You can edit the file with: nano .env.docker${NC}"
        echo ""
        
        # Ask if user wants to edit now
        read -p "Would you like to edit .env.docker now? (y/n): " edit_env
        if [[ $edit_env =~ ^[Yy]$ ]]; then
            ${EDITOR:-nano} .env.docker
        fi
    else
        echo -e "${RED}❌ .env.docker.example not found. Cannot create .env.docker${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✅ .env.docker found${NC}"
fi

# Function to show usage options
show_usage() {
    echo ""
    echo -e "${BLUE}🚀 Available Commands:${NC}"
    echo ""
    echo "  Development (with hot reload):"
    echo "    $DOCKER_COMPOSE -f docker-compose.yml -f docker-compose.dev.yml up"
    echo ""
    echo "  Production:"
    echo "    $DOCKER_COMPOSE -f docker-compose.yml -f docker-compose.prod.yml up -d"
    echo ""
    echo "  Basic setup:"
    echo "    $DOCKER_COMPOSE up"
    echo ""
    echo "  Build and run:"
    echo "    $DOCKER_COMPOSE up --build"
    echo ""
    echo "  Run in background:"
    echo "    $DOCKER_COMPOSE up -d"
    echo ""
    echo "  Stop services:"
    echo "    $DOCKER_COMPOSE down"
    echo ""
    echo "  View logs:"
    echo "    $DOCKER_COMPOSE logs -f"
    echo ""
    echo "  Clean up (remove volumes):"
    echo "    $DOCKER_COMPOSE down -v"
    echo ""
}

# Ask what the user wants to do
echo ""
echo -e "${BLUE}What would you like to do?${NC}"
echo "1) Run development setup (with hot reload)"
echo "2) Run production setup"
echo "3) Just build the images"
echo "4) Show all available commands"
echo "5) Exit"
echo ""

read -p "Enter your choice (1-5): " choice

case $choice in
    1)
        echo -e "${GREEN}🔥 Starting development environment...${NC}"
        echo "This includes hot reload for both gateway and dashboard."
        $DOCKER_COMPOSE --env-file .env.docker -f docker-compose.yml -f docker-compose.dev.yml up --build
        ;;
    2)
        echo -e "${GREEN}🚀 Starting production environment...${NC}"
        echo "This will run in the background with optimized settings."
        $DOCKER_COMPOSE --env-file .env.docker -f docker-compose.yml -f docker-compose.prod.yml up --build -d
        echo ""
        echo -e "${GREEN}✅ Services started in background!${NC}"
        echo "   Gateway: http://localhost:8000"
        echo "   Dashboard: http://localhost:3000"
        echo ""
        echo "To view logs: $DOCKER_COMPOSE logs -f"
        echo "To stop: $DOCKER_COMPOSE down"
        ;;
    3)
        echo -e "${GREEN}🔨 Building Docker images...${NC}"
        $DOCKER_COMPOSE --env-file .env.docker build --no-cache
        echo -e "${GREEN}✅ Images built successfully!${NC}"
        show_usage
        ;;
    4)
        show_usage
        ;;
    5)
        echo -e "${GREEN}👋 Goodbye!${NC}"
        exit 0
        ;;
    *)
        echo -e "${RED}❌ Invalid choice. Please run the script again.${NC}"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}🎉 Setup complete!${NC}"
echo ""
echo "Access your services:"
echo "  🌐 Gateway API: http://localhost:8000"
echo "  📊 Dashboard: http://localhost:3000"
echo "  📖 API Docs: http://localhost:8000/docs"
echo "  ❤️  Health Check: http://localhost:8000/health"