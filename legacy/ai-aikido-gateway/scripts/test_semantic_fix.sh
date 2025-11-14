#!/bin/bash

# Quick test to verify semantic cache is working after the fix

set -e

API_URL="http://localhost:8000/v1/chat/completions"
SEMANTIC_SEARCH_URL="http://localhost:8000/v1/cache/semantic/search"
SEMANTIC_ENTRIES_URL="http://localhost:8000/v1/cache/semantic/entries?limit=5"

echo "🔧 Testing Semantic Cache Fix"
echo "=============================="
echo ""
echo "Make sure you've restarted the gateway: uvicorn src.main:app --reload"
echo ""
read -p "Press Enter to continue..."
echo ""

# Function to send request
test_request() {
    local prompt="$1"
    local label="$2"

    echo "$label"
    echo "Prompt: \"$prompt\""

    response=$(curl -s -i -X POST "$API_URL" \
        -H "Content-Type: application/json" \
        -d "{
            \"model\": \"gpt-3.5-turbo\",
            \"messages\": [{\"role\": \"user\", \"content\": \"$prompt\"}],
            \"max_tokens\": 30
        }")

    cache_status=$(echo "$response" | grep -i "X-Gateway-Cache-Status:" | cut -d' ' -f2 | tr -d '\r')
    cache_type=$(echo "$response" | grep -i "X-Gateway-Cache-Type:" | cut -d' ' -f2 | tr -d '\r')
    cache_similarity=$(echo "$response" | grep -i "X-Gateway-Cache-Similarity:" | cut -d' ' -f2 | tr -d '\r')

    echo "  Status: ${cache_status:-MISS}"
    if [ "$cache_type" ]; then
        echo "  Type: $cache_type"
    fi
    if [ "$cache_similarity" ]; then
        echo "  Similarity: $cache_similarity ✨"
    fi

    show_semantic_candidates "$prompt"
    echo ""
}

show_semantic_candidates() {
    local prompt="$1"
    local payload
    payload=$(jq -nc --arg prompt "$prompt" '{prompt:$prompt, model:"gpt-3.5-turbo", limit:3}')
    local resp
    resp=$(curl -s -X POST "$SEMANTIC_SEARCH_URL" \
        -H "Content-Type: application/json" \
        -d "$payload")

    if echo "$resp" | jq -e '.candidates | length > 0' >/dev/null 2>&1; then
        echo "  Top Semantic Matches:"
        echo "$resp" | jq -r '.candidates[] | "    - sim: " + ((.similarity // 0) | tostring) + " | model: " + (.model // "unknown") + " | text: " + (.prompt_text // "N/A")'
    else
        echo "  Top Semantic Matches: (none)"
    fi
}

# Test sequence
test_request "What is the capital of France?" "1. First request (MISS expected)"
sleep 1

test_request "What is the capital of France?" "2. Exact same (verbatim HIT expected)"
sleep 1

test_request "Tell me the capital city of France" "3. Similar wording (SEMANTIC HIT expected! 🎯)"
sleep 1

test_request "What's the capital of France?" "4. Variation (SEMANTIC HIT expected! 🎯)"

echo ""
echo "✅ Check the stats:"
curl -s http://localhost:8000/v1/history/stats | jq '.semantic_cache_metrics | {size, hits, misses, hit_rate}'

echo ""
echo "🧠 Recent semantic cache entries:"
entries=$(curl -s "$SEMANTIC_ENTRIES_URL")
if echo "$entries" | jq -e '.entries | length > 0' >/dev/null 2>&1; then
    echo "$entries" | jq -r '.entries[] | "  - model: " + (.model // "unknown") + " | text: " + (.prompt_text // "N/A")'
else
    echo "  (semantic cache empty)"
fi
