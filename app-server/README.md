# App Server

Next.js backend API for managing users, chat sessions, and API keys. This service acts as the main application server and forwards LLM requests to the gateway service.

## Features

- 👤 **User Management**: Create and manage user accounts
- 💬 **Chat Sessions**: Store and retrieve chat conversations
- 🔑 **API Key Management**: Generate and manage API keys for users
- 🔀 **Gateway Proxy**: Forward authenticated requests to the LLM gateway

## Setup

### Prerequisites

- Node.js 18+
- npm or yarn

### Installation

1. Install dependencies:
```bash
npm install
```

2. Configure environment variables:
```bash
cp .env.example .env.local
# Edit .env.local with your settings
```

3. Run the development server:
```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) with your browser.

## API Endpoints

### Users
- `GET /api/users?id=<userId>` - Get user(s)
- `POST /api/users` - Create new user
- `PUT /api/users` - Update user
- `DELETE /api/users?id=<userId>` - Delete user

### Chat Sessions
- `GET /api/sessions?userId=<userId>` - Get sessions for user
- `POST /api/sessions` - Create new chat session
- `PUT /api/sessions` - Update session
- `DELETE /api/sessions?id=<sessionId>` - Delete session

### API Keys
- `GET /api/keys?userId=<userId>` - Get API keys for user
- `POST /api/keys` - Create new API key
- `DELETE /api/keys?id=<keyId>` - Revoke API key

### Gateway Proxy
- `POST /api/gateway` - Forward LLM request to gateway
- `GET /api/gateway` - Health check

## Database Schema

This service requires a database for storing:

### Users
- id, email, name
- created_at, updated_at

### ChatSessions
- id, user_id, title
- messages (JSON)
- created_at, updated_at

### ApiKeys
- id, user_id, key_hash, name
- last_used, created_at, revoked

## Development

The service includes placeholder implementations in `lib/db.ts`. Integrate with your preferred database solution (Prisma, Drizzle, etc.)

## Architecture

```
┌──────────┐
│  Client  │
└────┬─────┘
     │
     ▼
┌────────────┐      ┌──────────┐
│ App Server │─────▶│ Gateway  │
│  (Next.js) │      │ (FastAPI)│
└────┬───────┘      └──────────┘
     │
     ▼
┌──────────┐
│ Database │
└──────────┘
```
