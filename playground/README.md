# Playground - LLM Control Panel

Next.js-based developer control panel for managing and monitoring LLM services. Includes Prompt Studio, Usage Inspector, and Dashboard.

## Features

- 📊 **Dashboard**: Overview of system status, usage metrics, and key statistics
- 🎨 **Prompt Studio**: Interactive environment for testing and refining prompts
- 🔍 **Usage Inspector**: Detailed analytics for API usage, costs, and logs
- 📈 **Charts & Analytics**: Visual representation of usage patterns and costs
- 🎯 **Model Management**: Track usage across different LLM models

## Setup

### Prerequisites

- Node.js 18+
- npm or yarn

### Installation

1. Install dependencies:
```bash
npm install
```

2. Run the development server:
```bash
npm run dev
```

3. Open [http://localhost:3000](http://localhost:3000) with your browser.

## Pages

### Dashboard (`/dashboard`)
- System overview with key metrics
- Service status monitoring
- Recent activity feed
- Model usage statistics
- Real-time charts and graphs

### Prompt Studio (`/prompt-studio`)
- Interactive prompt editor
- Model and parameter configuration
- Real-time response preview
- Token and cost tracking
- Save and manage prompts

### Usage Inspector (`/usage-inspector`)
- Detailed usage logs
- Advanced filtering (date, model, user, status)
- Cost analysis and breakdowns
- Export capabilities
- Performance metrics

## Configuration

The playground connects to the app-server API to retrieve data. Configure the API endpoint in your environment variables:

```env
NEXT_PUBLIC_API_URL=http://localhost:3000/api
```

## Development

Build the application:
```bash
npm run build
```

Run in production mode:
```bash
npm start
```

## Architecture

```
┌─────────────┐
│  Playground │
│  (Next.js)  │
└──────┬──────┘
       │
       ▼
┌─────────────┐      ┌──────────┐
│ App Server  │─────▶│ Gateway  │
└─────────────┘      └──────────┘
```
