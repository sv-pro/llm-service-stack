#!/bin/bash

# End-to-End Test Script
# Tests the complete flow: Create user → API key → Session → Send message

set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

API_URL="http://localhost:3000/api"

echo -e "${BLUE}========================================${NC}"
echo -e "${BLUE}End-to-End Test${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""

# Step 1: Create a user
echo -e "${YELLOW}Step 1: Creating test user...${NC}"
USER_RESPONSE=$(curl -s -X POST "$API_URL/users" \
  -H "Content-Type: application/json" \
  -d '{"email": "test-'$(date +%s)'@example.com", "name": "Test User"}')

USER_ID=$(echo $USER_RESPONSE | jq -r '.user.id')

if [ "$USER_ID" == "null" ] || [ -z "$USER_ID" ]; then
    echo -e "${RED}✗ Failed to create user${NC}"
    echo "Response: $USER_RESPONSE"
    exit 1
fi

echo -e "${GREEN}✓ User created: $USER_ID${NC}"
echo ""

# Step 2: Create an API key
echo -e "${YELLOW}Step 2: Creating API key...${NC}"
KEY_RESPONSE=$(curl -s -X POST "$API_URL/keys" \
  -H "Content-Type: application/json" \
  -d "{\"userId\": \"$USER_ID\", \"name\": \"Test Key\"}")

API_KEY=$(echo $KEY_RESPONSE | jq -r '.apiKey')

if [ "$API_KEY" == "null" ] || [ -z "$API_KEY" ]; then
    echo -e "${RED}✗ Failed to create API key${NC}"
    echo "Response: $KEY_RESPONSE"
    exit 1
fi

echo -e "${GREEN}✓ API key created: ${API_KEY:0:20}...${NC}"
echo ""

# Step 3: Create a session
echo -e "${YELLOW}Step 3: Creating chat session...${NC}"
SESSION_RESPONSE=$(curl -s -X POST "$API_URL/sessions" \
  -H "Content-Type: application/json" \
  -d "{\"userId\": \"$USER_ID\", \"title\": \"E2E Test Session\", \"model\": \"gpt-3.5-turbo\"}")

SESSION_ID=$(echo $SESSION_RESPONSE | jq -r '.session.id')

if [ "$SESSION_ID" == "null" ] || [ -z "$SESSION_ID" ]; then
    echo -e "${RED}✗ Failed to create session${NC}"
    echo "Response: $SESSION_RESPONSE"
    exit 1
fi

echo -e "${GREEN}✓ Session created: $SESSION_ID${NC}"
echo ""

# Step 4: Test gateway health check
echo -e "${YELLOW}Step 4: Testing gateway health...${NC}"
GATEWAY_HEALTH=$(curl -s "$API_URL/gateway")

if echo "$GATEWAY_HEALTH" | jq -e '.gateway.service' > /dev/null 2>&1; then
    echo -e "${GREEN}✓ Gateway is healthy${NC}"
else
    echo -e "${RED}✗ Gateway health check failed${NC}"
    echo "Response: $GATEWAY_HEALTH"
    exit 1
fi
echo ""

# Step 5: Test prompt enhancement (Stage 2: Smart Prompts)
echo -e "${YELLOW}Step 5: Testing prompt enhancement...${NC}"
ENHANCE_RESPONSE=$(curl -s -X POST "http://localhost:8000/v1/prompts/enhance" \
  -H "Content-Type: application/json" \
  -d '{
    "system": "You are a helpful assistant.",
    "user": "Write code",
    "context": {"model": "gpt-3.5-turbo"}
  }')

# Check if we got a valid enhancement response
if echo "$ENHANCE_RESPONSE" | jq -e '.enhanced.user' > /dev/null 2>&1; then
    ENHANCED_USER=$(echo $ENHANCE_RESPONSE | jq -r '.enhanced.user')
    DETECTED_INTENT=$(echo $ENHANCE_RESPONSE | jq -r '.detected_intent')
    IMPROVEMENTS_COUNT=$(echo $ENHANCE_RESPONSE | jq -r '.improvements | length')
    echo -e "${GREEN}✓ Prompt enhancement successful${NC}"
    echo -e "${BLUE}Intent detected: $DETECTED_INTENT${NC}"
    echo -e "${BLUE}Improvements: $IMPROVEMENTS_COUNT${NC}"
    echo -e "${BLUE}Enhanced prompt (first 80 chars): ${ENHANCED_USER:0:80}...${NC}"
else
    echo -e "${RED}✗ Prompt enhancement failed${NC}"
    echo "Response: $ENHANCE_RESPONSE"

    # Check if it's an API key error
    if echo "$ENHANCE_RESPONSE" | jq -e '.detail' | grep -q "API key"; then
        echo -e "${YELLOW}This may be due to missing OpenAI API keys in gateway/.env${NC}"
    fi
fi
echo ""

# Step 6: Send a chat completion (this will test authentication and LLM routing)
echo -e "${YELLOW}Step 6: Sending chat completion request...${NC}"
echo -e "${BLUE}Note: This will use your OpenAI/Anthropic API key${NC}"

CHAT_RESPONSE=$(curl -s -X POST "$API_URL/gateway" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $API_KEY" \
  -d "{
    \"model\": \"gpt-3.5-turbo\",
    \"messages\": [{\"role\": \"user\", \"content\": \"Say 'Hello World' and nothing else.\"}],
    \"sessionId\": \"$SESSION_ID\",
    \"temperature\": 0.7
  }")

# Check if we got a valid response
if echo "$CHAT_RESPONSE" | jq -e '.choices[0].message.content' > /dev/null 2>&1; then
    RESPONSE_TEXT=$(echo $CHAT_RESPONSE | jq -r '.choices[0].message.content')
    echo -e "${GREEN}✓ Chat completion successful${NC}"
    echo -e "${BLUE}Response: $RESPONSE_TEXT${NC}"
else
    echo -e "${RED}✗ Chat completion failed${NC}"
    echo "Response: $CHAT_RESPONSE"

    # Check if it's an auth error
    if echo "$CHAT_RESPONSE" | jq -e '.error' | grep -q "API key"; then
        echo -e "${YELLOW}This may be due to missing OpenAI/Anthropic API keys in gateway/.env${NC}"
    fi
fi
echo ""

# Step 7: Verify messages were stored
echo -e "${YELLOW}Step 7: Verifying messages were stored...${NC}"
MESSAGES_RESPONSE=$(curl -s "$API_URL/messages?sessionId=$SESSION_ID")

MESSAGE_COUNT=$(echo $MESSAGES_RESPONSE | jq -r '.count')

if [ "$MESSAGE_COUNT" -ge 2 ]; then
    echo -e "${GREEN}✓ Messages stored correctly ($MESSAGE_COUNT messages)${NC}"
else
    echo -e "${YELLOW}⚠ Expected 2 messages, found $MESSAGE_COUNT${NC}"
    echo "This is OK if the chat completion failed"
fi
echo ""

# Step 8: Verify API key was used
echo -e "${YELLOW}Step 8: Verifying API key last used timestamp...${NC}"
KEYS_RESPONSE=$(curl -s "$API_URL/keys?userId=$USER_ID")

LAST_USED=$(echo $KEYS_RESPONSE | jq -r '.apiKeys[0].lastUsedAt')

if [ "$LAST_USED" != "null" ] && [ -n "$LAST_USED" ]; then
    echo -e "${GREEN}✓ API key lastUsedAt updated: $LAST_USED${NC}"
else
    echo -e "${YELLOW}⚠ API key lastUsedAt not updated${NC}"
fi
echo ""

# Step 9: Test MongoDB directly
echo -e "${YELLOW}Step 9: Verifying data in MongoDB...${NC}"
if command -v docker-compose &> /dev/null; then
    USER_COUNT=$(docker-compose exec -T mongo mongosh llm_service --quiet --eval "db.users.countDocuments()" 2>/dev/null | tail -1)
    SESSION_COUNT=$(docker-compose exec -T mongo mongosh llm_service --quiet --eval "db.sessions.countDocuments()" 2>/dev/null | tail -1)

    echo -e "${GREEN}✓ MongoDB contains:${NC}"
    echo -e "  Users: $USER_COUNT"
    echo -e "  Sessions: $SESSION_COUNT"
else
    echo -e "${YELLOW}⚠ docker-compose not available, skipping MongoDB verification${NC}"
fi
echo ""

# Cleanup prompt
echo -e "${BLUE}========================================${NC}"
echo -e "${GREEN}Test completed!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo -e "Test artifacts created:"
echo -e "  User ID:    $USER_ID"
echo -e "  API Key:    ${API_KEY:0:20}..."
echo -e "  Session ID: $SESSION_ID"
echo ""
echo -e "To clean up test data:"
echo -e "  ${YELLOW}curl -X DELETE \"$API_URL/sessions?id=$SESSION_ID\"${NC}"
echo -e "  ${YELLOW}curl -X DELETE \"$API_URL/users?id=$USER_ID\"${NC}"
echo ""
echo -e "To view logs:"
echo -e "  ${YELLOW}make logs${NC}"
echo ""
