#!/bin/bash

echo "🔄 Restarting Gateway & Testing Semantic Cache"
echo "==============================================="
echo ""

# Kill existing gateway
echo "1. Stopping gateway..."
pkill -f "uvicorn src.main:app" || true
sleep 2

# Start gateway in background
echo "2. Starting gateway..."
cd "$(dirname "$0")"
nohup uvicorn src.main:app --reload --log-level info > gateway.log 2>&1 &
GATEWAY_PID=$!

echo "   Gateway PID: $GATEWAY_PID"
echo "   Waiting for startup (5 seconds)..."
sleep 5

# Check if gateway is running
if ! curl -s http://localhost:8000/v1/history/stats > /dev/null; then
    echo "❌ Gateway failed to start!"
    echo "   Check gateway.log for errors"
    exit 1
fi

echo "✅ Gateway started successfully!"
echo ""

# Clear any existing cache
echo "3. Clearing caches..."
rm -f data/cache.db data/semantic_metrics.db
echo "   Caches cleared"
echo ""

# Run test sequence
echo "4. Running test sequence..."
echo ""

API_URL="http://localhost:8000/v1/chat/completions"

test_req() {
    local prompt="$1"
    local label="$2"

    echo "$label: \"$prompt\""
    curl -s -X POST "$API_URL" \
        -H "Content-Type: application/json" \
        -d "{
            \"model\": \"gpt-3.5-turbo\",
            \"messages\": [{\"role\": \"user\", \"content\": \"$prompt\"}],
            \"max_tokens\": 20
        }" > /dev/null

    # Check stats
    size=$(curl -s http://localhost:8000/v1/history/stats | jq -r '.semantic_cache_metrics.size')
    hits=$(curl -s http://localhost:8000/v1/history/stats | jq -r '.semantic_cache_metrics.hits')
    echo "   → Semantic cache size: $size, hits: $hits"
    echo ""
}

test_req "What is 2+2?" "Request 1 (new)"
sleep 1

test_req "What is 2+2?" "Request 2 (identical)"
sleep 1

test_req "Calculate 2 plus 2" "Request 3 (similar)"
sleep 1

echo ""
echo "5. Final stats:"
curl -s http://localhost:8000/v1/history/stats | jq '{
  verbatim: .cache_metrics | {hits, misses, size: .storage_entries},
  semantic: .semantic_cache_metrics | {hits, misses, size}
}'

echo ""
echo "📋 Check gateway.log for detailed semantic cache logging"
echo "   tail -f gateway.log | grep -i semantic"
