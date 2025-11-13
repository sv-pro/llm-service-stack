#!/bin/bash

# Start server in background
echo "Starting AI Aikido Gateway..."
uvicorn src.main:app --host 0.0.0.0 --port 8000 > /tmp/aikido.log 2>&1 &
SERVER_PID=$!

# Wait for server to start
echo "Waiting for server to start..."
sleep 3

# Test endpoints
echo ""
echo "=== Testing /health endpoint ==="
curl -s http://localhost:8000/health | python -m json.tool

echo ""
echo "=== Testing / (root) endpoint ==="
curl -s http://localhost:8000/ | python -m json.tool

echo ""
echo "=== Server is running on http://localhost:8000 ==="
echo "View API docs at: http://localhost:8000/docs"
echo ""
echo "Server PID: $SERVER_PID"
echo "To stop the server, run: kill $SERVER_PID"
echo "Or use: make start-reload (for development with hot reload)"
