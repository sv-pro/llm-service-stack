# Web Chat Client

Minimal React-based chat client for interacting with the LLM service. Provides a clean, user-friendly interface for conversations powered by various LLM models.

## Features

- 💬 **Clean Chat Interface**: Modern, responsive design
- 🔑 **API Key Authentication**: Secure access to the service
- ⚡ **Real-time Responses**: Async communication with the backend
- 📝 **Message History**: View conversation context
- 🎨 **TypeScript Support**: Full type safety

## Setup

### Prerequisites

- Node.js 16+
- npm or yarn
- Valid API key from the app-server

### Installation

1. Install dependencies:
```bash
npm install
```

2. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your API URL and key
```

3. Start the development server:
```bash
npm start
```

4. Open [http://localhost:3000](http://localhost:3000) to view the app.

## Configuration

Edit `.env` to configure the API connection:

```env
REACT_APP_API_URL=http://localhost:3000/api
REACT_APP_API_KEY=your_api_key_here
```

Alternatively, you can enter your API key in the app interface when it starts.

## Usage

1. **Enter API Key**: When you first open the app, enter your API key
2. **Start Chatting**: Type your message in the input field
3. **View Responses**: See AI responses in real-time
4. **New Chat**: Click "New Chat" to start a fresh conversation

## Components

- **ChatWindow**: Main container for the chat interface
- **ChatMessage**: Individual message display component
- **ChatInput**: Message input field with send functionality

## API Integration

The app connects to the app-server API gateway endpoint:

```typescript
POST /api/gateway
Authorization: Bearer <your-api-key>

{
  "model": "gpt-3.5-turbo",
  "messages": [
    { "role": "user", "content": "Hello!" }
  ]
}
```

## Build for Production

Build the app for deployment:

```bash
npm run build
```

The optimized production build will be in the `build/` folder.

## Architecture

```
┌──────────┐      ┌─────────────┐      ┌──────────┐
│ Web Chat │─────▶│ App Server  │─────▶│ Gateway  │
│ (React)  │      │  (Next.js)  │      │ (FastAPI)│
└──────────┘      └─────────────┘      └──────────┘
```
