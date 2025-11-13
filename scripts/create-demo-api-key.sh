#!/bin/bash

# Create a demo API key for testing the web-chat
# This script creates a user and an API key, then outputs the key for use in .env files

set -e

GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${BLUE}Creating demo API key for web-chat...${NC}"
echo ""

# API endpoints
APP_SERVER="http://localhost:3000/api"

# Step 1: Create a demo user
echo -e "${YELLOW}Step 1: Creating demo user...${NC}"
USER_RESPONSE=$(curl -s -X POST "${APP_SERVER}/users" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "demo@example.com",
    "name": "Demo User"
  }')

USER_ID=$(echo $USER_RESPONSE | jq -r '.user._id // .user.id // empty')

if [ -z "$USER_ID" ]; then
  echo -e "${YELLOW}User might already exist, fetching existing user...${NC}"
  # Try to get existing user
  USERS=$(curl -s "${APP_SERVER}/users?limit=100")
  USER_ID=$(echo $USERS | jq -r '.users[] | select(.email=="demo@example.com") | ._id')
fi

if [ -z "$USER_ID" ]; then
  echo "Error: Could not create or find demo user"
  exit 1
fi

echo -e "${GREEN}✓ User ID: ${USER_ID}${NC}"

# Step 2: Create an API key for this user
echo -e "${YELLOW}Step 2: Creating API key...${NC}"
KEY_RESPONSE=$(curl -s -X POST "${APP_SERVER}/keys" \
  -H "Content-Type: application/json" \
  -d "{
    \"userId\": \"${USER_ID}\",
    \"name\": \"Web Chat Demo Key\"
  }")

API_KEY=$(echo $KEY_RESPONSE | jq -r '.apiKey // empty')

if [ -z "$API_KEY" ]; then
  echo "Error: Could not create API key"
  echo "Response: $KEY_RESPONSE"
  exit 1
fi

echo -e "${GREEN}✓ API Key created successfully!${NC}"
echo ""
echo "================================================"
echo -e "${GREEN}Your API Key:${NC}"
echo -e "${BLUE}${API_KEY}${NC}"
echo "================================================"
echo ""
echo "To use this key with the web-chat:"
echo "1. Create or edit web-chat/.env.local:"
echo "   echo 'REACT_APP_API_KEY=${API_KEY}' > web-chat/.env.local"
echo ""
echo "2. Restart the web-chat service:"
echo "   make restart-web-chat"
echo ""
echo -e "${YELLOW}Note: This key is stored securely (hashed) in the database.${NC}"
echo -e "${YELLOW}Keep it safe - it won't be shown again!${NC}"
