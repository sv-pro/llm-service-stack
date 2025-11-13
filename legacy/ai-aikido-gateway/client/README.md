# AI Aikido Gateway - Reference Client

A simple web-based client to test the AI Aikido Gateway.

## Features

- Clean, minimal chat interface
- Send messages to the gateway
- Select different AI models
- View responses in real-time
- Display request metadata (latency, tokens, etc.)
- Check gateway health status

## Installation

```bash
cd client
npm install
```

## Usage

### Start the client

```bash
npm start
```

The client will run on `http://localhost:3000`

### Prerequisites

Make sure the AI Aikido Gateway is running:

```bash
# In the main project directory
make start-reload
# or
uvicorn src.main:app --reload
```

The gateway should be running on `http://localhost:8000`

## How It Works

1. **User enters a message** in the text box
2. **Selects a model** from the dropdown (GPT-3.5, GPT-4, Claude, etc.)
3. **Clicks Send** button
4. **Client sends request** to `http://localhost:8000/v1/chat/completions`
5. **Gateway processes** the request (applies plugins, forwards to LLM provider)
6. **Response is displayed** in the response box
7. **Metadata shown** (latency, token usage, model used, etc.)

## Architecture

```
┌─────────────────┐
│  Browser UI     │
│  (port 3000)    │
└────────┬────────┘
         │ HTTP POST /v1/chat/completions
         ▼
┌─────────────────┐
│  AI Aikido      │
│  Gateway        │
│  (port 8000)    │
└────────┬────────┘
         │ Forward request
         ▼
┌─────────────────┐
│  OpenAI /       │
│  Anthropic API  │
└─────────────────┘
```

## Files

- `server.js` - Express server to serve static files
- `public/index.html` - Main HTML interface
- `public/styles.css` - Styling
- `public/app.js` - Client-side JavaScript logic
- `package.json` - Node.js dependencies

## Customization

To change the gateway URL, edit `app.js`:

```javascript
const GATEWAY_URL = 'http://your-gateway-url:8000';
```

## Troubleshooting

### Client can't reach gateway

1. Check if gateway is running: `curl http://localhost:8000/health`
2. Check CORS settings in gateway (should allow requests from localhost:3000)
3. Check browser console for errors

### Port 3000 already in use

Change the port in `server.js` or set environment variable:

```bash
PORT=3001 npm start
```
