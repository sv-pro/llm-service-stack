#!/bin/bash

# Demo script to showcase semantic cache functionality
# This script sends similar but not identical prompts to show semantic matching

set -e

API_URL="http://localhost:8000/v1/chat/completions"

echo "🚀 Semantic Cache Demo - AI Aikido Gateway"
echo "=========================================="
echo ""

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to send request and show headers
send_request() {
    local prompt="$1"
    local label="$2"

    echo -e "${BLUE}$label${NC}"
    echo "Prompt: \"$prompt\""
    echo ""

    response=$(curl -s -i -X POST "$API_URL" \
        -H "Content-Type: application/json" \
        -d "{
            \"model\": \"gpt-3.5-turbo\",
            \"messages\": [{\"role\": \"user\", \"content\": \"$prompt\"}],
            \"max_tokens\": 50
        }")

    # Extract headers
    cache_status=$(echo "$response" | grep -i "X-Gateway-Cache-Status:" | cut -d' ' -f2 | tr -d '\r')
    cache_type=$(echo "$response" | grep -i "X-Gateway-Cache-Type:" | cut -d' ' -f2 | tr -d '\r')
    cache_similarity=$(echo "$response" | grep -i "X-Gateway-Cache-Similarity:" | cut -d' ' -f2 | tr -d '\r')
    latency=$(echo "$response" | grep -i "X-Gateway-Latency-Ms:" | cut -d' ' -f2 | tr -d '\r')

    # Extract response body
    body=$(echo "$response" | sed -n '/^{/,$p')
    content=$(echo "$body" | jq -r '.choices[0].message.content' 2>/dev/null || echo "N/A")

    echo -e "${GREEN}Response:${NC} ${content:0:100}..."
    echo ""
    echo "📊 Cache Status: ${cache_status:-MISS}"

    if [ "$cache_type" ]; then
        echo "   Cache Type: ${cache_type}"
    fi

    if [ "$cache_similarity" ]; then
        echo -e "   ${YELLOW}Similarity: ${cache_similarity}${NC} (semantic match!)"
    fi

    if [ "$latency" ]; then
        echo "   Latency: ${latency}ms"
    fi

    echo ""
    echo "---"
    echo ""
}

echo "Step 1: Initial request (will be a MISS)"
echo ""
send_request "What is the capital of France?" "📝 Request 1"
sleep 1

echo "Step 2: Exact same request (verbatim cache HIT)"
echo ""
send_request "What is the capital of France?" "📝 Request 2 (identical)"
sleep 1

echo "Step 3: Similar but different wording (semantic cache HIT)"
echo ""
send_request "Tell me the capital city of France" "📝 Request 3 (similar)"
sleep 1

echo "Step 4: Another variation (semantic cache HIT)"
echo ""
send_request "What's the capital of France?" "📝 Request 4 (variation)"
sleep 1

echo "Step 5: Related but different question (may or may not hit)"
echo ""
send_request "Which city is the capital of France?" "📝 Request 5 (related)"
sleep 1

echo ""
echo "✅ Demo Complete!"
echo ""
echo "💡 Key Observations:"
echo "   - Request 2: Verbatim cache hit (exact match)"
echo "   - Requests 3-5: Semantic cache hits (similar meaning)"
echo "   - Check the similarity scores to see how close the match was"
echo ""
echo "📈 View metrics:"
echo "   - Dashboard: http://localhost:3000/cache-analytics"
echo "   - API: curl http://localhost:8000/v1/history/stats"
echo "   - Time-series: curl http://localhost:8000/v1/cache/semantic/timeseries"
echo ""
