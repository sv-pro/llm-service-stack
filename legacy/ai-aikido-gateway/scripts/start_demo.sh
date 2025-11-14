#!/bin/bash

# Start both the gateway and the client for easy testing

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Starting AI Aikido Gateway Demo${NC}"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${YELLOW}⚠️  .env file not found. Creating from .env.example...${NC}"
    cp .env.example .env
    echo -e "${YELLOW}⚠️  Please edit .env and add your API keys before making real requests${NC}"
    echo ""
fi

# Function to cleanup on exit
cleanup() {
    echo ""
    echo -e "${YELLOW}Stopping services...${NC}"
    kill $GATEWAY_PID 2>/dev/null
    kill $CLIENT_PID 2>/dev/null
    exit 0
}

trap cleanup SIGINT SIGTERM

# Start the gateway
echo -e "${GREEN}📡 Starting Gateway (port 8000)...${NC}"
uvicorn src.main:app --host 0.0.0.0 --port 8000 > /tmp/gateway.log 2>&1 &
GATEWAY_PID=$!

# Wait for gateway to start
sleep 2

# Check if gateway is running
if ! curl -s http://localhost:8000/health > /dev/null; then
    echo -e "${YELLOW}⚠️  Gateway failed to start. Check /tmp/gateway.log${NC}"
    cat /tmp/gateway.log
    exit 1
fi

echo -e "${GREEN}✅ Gateway started (PID: $GATEWAY_PID)${NC}"
echo ""

# Start the client
echo -e "${GREEN}🌐 Starting Client (port 3000)...${NC}"
cd client
npm start > /tmp/client.log 2>&1 &
CLIENT_PID=$!
cd ..

# Wait for client to start
sleep 2

echo -e "${GREEN}✅ Client started (PID: $CLIENT_PID)${NC}"
echo ""

echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo -e "${GREEN}✨ AI Aikido Gateway Demo Running!${NC}"
echo ""
echo -e "  ${BLUE}Gateway:${NC}     http://localhost:8000"
echo -e "  ${BLUE}API Docs:${NC}    http://localhost:8000/docs"
echo -e "  ${BLUE}Client UI:${NC}   http://localhost:3000"
echo ""
echo -e "${BLUE}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}"
echo ""
echo -e "${YELLOW}📝 Open http://localhost:3000 in your browser${NC}"
echo -e "${YELLOW}⌨️  Press Ctrl+C to stop both services${NC}"
echo ""

# Follow gateway logs
echo -e "${BLUE}Gateway logs:${NC}"
tail -f /tmp/gateway.log
