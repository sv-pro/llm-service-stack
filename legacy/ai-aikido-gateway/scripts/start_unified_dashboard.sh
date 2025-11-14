#!/bin/bash

# AI Aikido Gateway - Unified Dashboard Start Script
# Starts both the gateway and the unified dashboard

set -e

echo "╔════════════════════════════════════════════════╗"
echo "║  🥋 AI Aikido Gateway - Starting System       ║"
echo "╚════════════════════════════════════════════════╝"
echo ""

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found"
    echo "   Please create a .env file with your API keys"
    echo "   Example: cp .env.example .env"
    exit 1
fi

# Check if dashboard dependencies are installed
if [ ! -d "dashboard/node_modules" ]; then
    echo "📦 Installing dashboard dependencies..."
    cd dashboard
    npm install
    cd ..
fi

# Function to cleanup on exit
cleanup() {
    echo ""
    echo "🛑 Shutting down services..."
    kill $GATEWAY_PID 2>/dev/null || true
    kill $DASHBOARD_PID 2>/dev/null || true
    exit 0
}

trap cleanup SIGINT SIGTERM

echo "1️⃣  Starting AI Aikido Gateway (port 8000)..."
uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload > /tmp/gateway.log 2>&1 &
GATEWAY_PID=$!

# Wait for gateway to start
echo "   Waiting for gateway to be ready..."
sleep 3

# Check if gateway is running
if ! curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "❌ Gateway failed to start. Check /tmp/gateway.log"
    cat /tmp/gateway.log
    exit 1
fi

echo "   ✅ Gateway is ready!"
echo ""

echo "2️⃣  Starting Unified Dashboard (port 3000)..."
cd dashboard
npm run dev > /tmp/dashboard.log 2>&1 &
DASHBOARD_PID=$!
cd ..

# Wait for dashboard to start
echo "   Waiting for dashboard to be ready..."
sleep 5

echo "   ✅ Dashboard is ready!"
echo ""

echo "╔════════════════════════════════════════════════╗"
echo "║  ✅ System Ready!                              ║"
echo "╠════════════════════════════════════════════════╣"
echo "║  🎮 Dashboard:  http://localhost:3000         ║"
echo "║  🚀 Gateway:    http://localhost:8000         ║"
echo "║  📚 API Docs:   http://localhost:8000/docs    ║"
echo "╠════════════════════════════════════════════════╣"
echo "║  Screens Available:                            ║"
echo "║  • Playground  - Test requests                 ║"
echo "║  • Overview    - Coming soon                   ║"
echo "║  • Costs       - Coming soon                   ║"
echo "║  • Requests    - Coming soon                   ║"
echo "║  • Cache       - Coming soon                   ║"
echo "║  • Settings    - Coming soon                   ║"
echo "╠════════════════════════════════════════════════╣"
echo "║  Press Ctrl+C to stop all services             ║"
echo "╚════════════════════════════════════════════════╝"
echo ""

# Keep script running
wait
