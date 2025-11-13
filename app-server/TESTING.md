# App Server API Testing Guide

This guide provides examples for testing all implemented API endpoints.

## Prerequisites

1. **Start MongoDB**:
   ```bash
   # Using Docker Compose
   docker-compose up -d mongo

   # Or locally
   mongod --dbpath /path/to/data
   ```

2. **Start the App Server**:
   ```bash
   cd app-server
   npm install
   npm run dev
   ```

The server should be running on `http://localhost:3000`.

## API Endpoints

### 1. Users API

#### Create a User
```bash
curl -X POST http://localhost:3000/api/users \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "name": "Test User"
  }'
```

**Expected Response**:
```json
{
  "message": "User created successfully",
  "user": {
    "id": "65f...",
    "email": "test@example.com",
    "name": "Test User",
    "createdAt": "2024-01-01T00:00:00.000Z"
  }
}
```

#### Get All Users (with pagination)
```bash
curl "http://localhost:3000/api/users?page=1&limit=10"
```

#### Get Specific User
```bash
curl "http://localhost:3000/api/users?id=USER_ID"
```

#### Update User
```bash
curl -X PUT http://localhost:3000/api/users \
  -H "Content-Type: application/json" \
  -d '{
    "id": "USER_ID",
    "name": "Updated Name"
  }'
```

#### Delete User
```bash
curl -X DELETE "http://localhost:3000/api/users?id=USER_ID"
```

---

### 2. Sessions API

#### Create a Session
```bash
curl -X POST http://localhost:3000/api/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "userId": "USER_ID",
    "title": "My First Chat",
    "model": "gpt-4",
    "metadata": {
      "tags": ["test", "demo"]
    }
  }'
```

**Expected Response**:
```json
{
  "message": "Session created successfully",
  "session": {
    "id": "65f...",
    "userId": "65f...",
    "title": "My First Chat",
    "model": "gpt-4",
    "metadata": {
      "tags": ["test", "demo"]
    },
    "createdAt": "2024-01-01T00:00:00.000Z",
    "updatedAt": "2024-01-01T00:00:00.000Z"
  }
}
```

#### Get User's Sessions
```bash
curl "http://localhost:3000/api/sessions?userId=USER_ID&page=1&limit=20"
```

#### Get Specific Session (with messages)
```bash
curl "http://localhost:3000/api/sessions?id=SESSION_ID"
```

#### Update Session
```bash
curl -X PUT http://localhost:3000/api/sessions \
  -H "Content-Type: application/json" \
  -d '{
    "id": "SESSION_ID",
    "title": "Updated Chat Title"
  }'
```

#### Delete Session
```bash
curl -X DELETE "http://localhost:3000/api/sessions?id=SESSION_ID"
```

---

### 3. API Keys

#### Create an API Key
```bash
curl -X POST http://localhost:3000/api/keys \
  -H "Content-Type: application/json" \
  -d '{
    "userId": "USER_ID",
    "name": "My API Key"
  }'
```

**Expected Response**:
```json
{
  "message": "API key created successfully",
  "apiKey": "sk_abcdefghijklmnopqrstuvwxyz123456789...",
  "keyInfo": {
    "id": "65f...",
    "name": "My API Key",
    "keyPrefix": "sk_abcdefghi",
    "isActive": true,
    "createdAt": "2024-01-01T00:00:00.000Z"
  },
  "warning": "Save this API key now. You will not be able to see it again."
}
```

**IMPORTANT**: Save the `apiKey` value immediately! It's only shown once.

#### Get User's API Keys
```bash
curl "http://localhost:3000/api/keys?userId=USER_ID"
```

**Response** (note: actual key is never returned, only metadata):
```json
{
  "apiKeys": [
    {
      "id": "65f...",
      "name": "My API Key",
      "keyPrefix": "sk_abcdefghi",
      "isActive": true,
      "lastUsedAt": null,
      "createdAt": "2024-01-01T00:00:00.000Z",
      "revokedAt": null
    }
  ]
}
```

#### Revoke API Key
```bash
curl -X DELETE "http://localhost:3000/api/keys?id=KEY_ID"
```

---

## Complete Test Flow

Here's a complete workflow to test all endpoints:

```bash
# 1. Create a user
USER_RESPONSE=$(curl -s -X POST http://localhost:3000/api/users \
  -H "Content-Type: application/json" \
  -d '{"email": "demo@example.com", "name": "Demo User"}')

USER_ID=$(echo $USER_RESPONSE | jq -r '.user.id')
echo "Created user: $USER_ID"

# 2. Create an API key for the user
KEY_RESPONSE=$(curl -s -X POST http://localhost:3000/api/keys \
  -H "Content-Type: application/json" \
  -d "{\"userId\": \"$USER_ID\", \"name\": \"Demo Key\"}")

API_KEY=$(echo $KEY_RESPONSE | jq -r '.apiKey')
echo "Created API key: $API_KEY"

# 3. Create a chat session
SESSION_RESPONSE=$(curl -s -X POST http://localhost:3000/api/sessions \
  -H "Content-Type: application/json" \
  -d "{\"userId\": \"$USER_ID\", \"title\": \"Test Chat\", \"model\": \"gpt-3.5-turbo\"}")

SESSION_ID=$(echo $SESSION_RESPONSE | jq -r '.session.id')
echo "Created session: $SESSION_ID"

# 4. Get user's sessions
curl -s "http://localhost:3000/api/sessions?userId=$USER_ID" | jq

# 5. Get user's API keys
curl -s "http://localhost:3000/api/keys?userId=$USER_ID" | jq

# 6. Clean up (optional)
# curl -X DELETE "http://localhost:3000/api/sessions?id=$SESSION_ID"
# curl -X DELETE "http://localhost:3000/api/keys?id=$KEY_ID"
# curl -X DELETE "http://localhost:3000/api/users?id=$USER_ID"
```

## Error Responses

All endpoints return appropriate error responses:

**400 Bad Request** - Missing required fields:
```json
{
  "error": "Email is required"
}
```

**404 Not Found** - Resource doesn't exist:
```json
{
  "error": "User not found"
}
```

**409 Conflict** - Duplicate resource:
```json
{
  "error": "User with this email already exists"
}
```

**500 Internal Server Error** - Server error:
```json
{
  "error": "Failed to create user"
}
```

## Testing with Postman

Import the following collection into Postman:

1. Create environment variables:
   - `BASE_URL`: `http://localhost:3000`
   - `USER_ID`: (set after creating a user)
   - `SESSION_ID`: (set after creating a session)
   - `KEY_ID`: (set after creating a key)

2. Use the collection to test all endpoints systematically.

## Database Verification

Verify data directly in MongoDB:

```bash
# Connect to MongoDB
mongosh mongodb://localhost:27017/llm_service

# List collections
show collections

# View users
db.users.find().pretty()

# View sessions
db.sessions.find().pretty()

# View API keys (note: keyHash is bcrypt-hashed)
db.apikeys.find().pretty()

# Count documents
db.users.countDocuments()
db.sessions.countDocuments()
db.apikeys.countDocuments()
```

## Performance Testing

Use Apache Bench or similar tools to test performance:

```bash
# Test user creation endpoint
ab -n 100 -c 10 -T application/json -p user.json \
  http://localhost:3000/api/users

# Where user.json contains:
# {"email": "test@example.com", "name": "Test User"}
```

## Security Notes

- API keys are hashed with bcrypt before storage
- Never log or expose full API keys except on creation
- The `keyPrefix` field allows users to identify keys without exposing the full value
- Implement rate limiting in production
- Add authentication middleware before deploying
