#!/bin/bash

# LLM Service Stack - Startup Verification Script
# This script helps verify all services start correctly and can communicate

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}LLM Service Stack - Startup Verification${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Function to check if a service is running
check_service() {
    local name=$1
    local url=$2
    local max_attempts=${3:-30}
    local attempt=1

    echo -e "${YELLOW}Checking $name at $url...${NC}"

    while [ $attempt -le $max_attempts ]; do
        http_code=$(curl -s -o /dev/null -w "%{http_code}" "$url")
        # Accept 2xx and 3xx status codes (success and redirects)
        if [[ $http_code =~ ^[23] ]]; then
            echo -e "${GREEN}✓ $name is running (HTTP $http_code)${NC}"
            return 0
        fi
        echo -n "."
        sleep 2
        ((attempt++))
    done

    echo -e "${RED}✗ $name failed to start (timeout after ${max_attempts} attempts)${NC}"
    return 1
}

# Function to test endpoint
test_endpoint() {
    local name=$1
    local url=$2
    local expected=$3

    echo -e "${YELLOW}Testing $name...${NC}"
    response=$(curl -s "$url")

    if echo "$response" | grep -q "$expected"; then
        echo -e "${GREEN}✓ $name responded correctly${NC}"
        return 0
    else
        echo -e "${RED}✗ $name unexpected response${NC}"
        echo "Response: $response"
        return 1
    fi
}

echo -e "${BLUE}Step 1: Starting Docker services${NC}"
echo "Running: make start"
make start
echo ""

echo -e "${BLUE}Step 2: Waiting for services to be ready...${NC}"
sleep 5
echo ""

# Check each service
echo -e "${BLUE}Step 3: Verifying service health${NC}"
echo ""

# Check MongoDB
echo -e "${YELLOW}Checking MongoDB...${NC}"
if docker-compose ps mongo | grep -q "Up"; then
    echo -e "${GREEN}✓ MongoDB container is running${NC}"
else
    echo -e "${RED}✗ MongoDB container is not running${NC}"
    exit 1
fi
echo ""

# Check Redis
echo -e "${YELLOW}Checking Redis...${NC}"
if docker-compose ps redis | grep -q "Up"; then
    echo -e "${GREEN}✓ Redis container is running${NC}"
else
    echo -e "${RED}✗ Redis container is not running${NC}"
    exit 1
fi
echo ""

# Check Gateway
check_service "Gateway" "http://localhost:8000/"
if [ $? -ne 0 ]; then
    echo -e "${RED}Gateway logs:${NC}"
    docker-compose logs --tail=50 gateway
    exit 1
fi
echo ""

# Check App Server
check_service "App Server" "http://localhost:3000/api/gateway"
if [ $? -ne 0 ]; then
    echo -e "${RED}App Server logs:${NC}"
    docker-compose logs --tail=50 app-server
    exit 1
fi
echo ""

# Check Playground
check_service "Playground" "http://localhost:3001/"
if [ $? -ne 0 ]; then
    echo -e "${RED}Playground logs:${NC}"
    docker-compose logs --tail=50 playground
    exit 1
fi
echo ""

# Check Web Chat
check_service "Web Chat" "http://localhost:3002/"
if [ $? -ne 0 ]; then
    echo -e "${RED}Web Chat logs:${NC}"
    docker-compose logs --tail=50 web-chat
    exit 1
fi
echo ""

echo -e "${BLUE}Step 4: Testing inter-service communication${NC}"
echo ""

# Test Gateway endpoints
test_endpoint "Gateway health" "http://localhost:8000/" "LLM Gateway"
test_endpoint "Gateway models" "http://localhost:8000/v1/models" "gpt-3.5-turbo"
echo ""

# Test App Server endpoints
test_endpoint "App Server health" "http://localhost:3000/api/gateway" "Gateway proxy"
echo ""

echo -e "${BLUE}Step 5: Testing database connections${NC}"
echo ""

# Test MongoDB connection
echo -e "${YELLOW}Testing MongoDB connection...${NC}"
if docker-compose exec -T mongo mongosh --eval "db.adminCommand('ping')" --quiet; then
    echo -e "${GREEN}✓ MongoDB is accessible${NC}"
else
    echo -e "${RED}✗ MongoDB connection failed${NC}"
    exit 1
fi
echo ""

# Test Redis connection
echo -e "${YELLOW}Testing Redis connection...${NC}"
if docker-compose exec -T redis redis-cli ping | grep -q "PONG"; then
    echo -e "${GREEN}✓ Redis is accessible${NC}"
else
    echo -e "${RED}✗ Redis connection failed${NC}"
    exit 1
fi
echo ""

echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}All services are running successfully!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "Service URLs:"
echo -e "  ${YELLOW}Gateway:${NC}    http://localhost:8000"
echo -e "  ${YELLOW}App Server:${NC} http://localhost:3000"
echo -e "  ${YELLOW}Playground:${NC} http://localhost:3001"
echo -e "  ${YELLOW}Web Chat:${NC}   http://localhost:3002"
echo ""
echo -e "Next steps:"
echo -e "  1. Open http://localhost:3001 to access the Playground"
echo -e "  2. Open http://localhost:3002 to access the Web Chat"
echo -e "  3. Run ${YELLOW}make logs${NC} to view all service logs"
echo -e "  4. Run ${YELLOW}bash scripts/test-e2e.sh${NC} for end-to-end testing"
echo ""
