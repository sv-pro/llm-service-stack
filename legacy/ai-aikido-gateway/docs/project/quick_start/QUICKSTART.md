# Quick Start Guide - AI Aikido Gateway

## 🚀 Get Started in 2 Steps

### Step 1: Configure API Keys

```bash
# Edit .env file and add your OpenAI API key
nano .env

# Add this line:
OPENAI_API_KEY=sk-your-actual-openai-key-here
```

### Step 2: Start the Unified Dashboard

```bash
# One command starts both gateway and unified dashboard
./start_unified_dashboard.sh
```

You'll see:
```
╔════════════════════════════════════════════════╗
║  🥋 AI Aikido Gateway - Starting System       ║
╚════════════════════════════════════════════════╝

1️⃣  Starting AI Aikido Gateway (port 8000)...
   ✅ Gateway is ready!

2️⃣  Starting Unified Dashboard (port 3000)...
   ✅ Dashboard is ready!

╔════════════════════════════════════════════════╗
║  ✅ System Ready!                              ║
╠════════════════════════════════════════════════╣
║  🎮 Dashboard:  http://localhost:3000         ║
║  🚀 Gateway:    http://localhost:8000         ║
║  📚 API Docs:   http://localhost:8000/docs    ║
╠════════════════════════════════════════════════╣
║  Screens Available:                            ║
║  • Playground  - Test requests                 ║
║  • Overview    - Coming soon                   ║
║  • Costs       - Coming soon                   ║
║  • Requests    - Coming soon                   ║
║  • Cache       - Coming soon                   ║
║  • Settings    - Coming soon                   ║
╠════════════════════════════════════════════════╣
║  Press Ctrl+C to stop all services             ║
╚════════════════════════════════════════════════╝
```

### Step 3: Explore the Dashboard!

Open your browser to: **<http://localhost:3000>**

You'll see the **Unified Dashboard** with:

- 🎨 Beautiful gradient sidebar navigation
- 🎮 **Playground** screen (fully functional)
- 📊 **Overview** screen (coming soon - cost insights)
- 💰 **Cost Explorer** (coming soon)
- 📋 **Request History** (coming soon)
- ⚡ **Cache Analytics** (coming soon)
- ⚙️ **Settings** (coming soon)

**The Playground Screen includes:**

- Model selector (GPT-3.5 Turbo, GPT-4, GPT-4 Turbo)
- Text input box with keyboard shortcuts (Enter to send, Shift+Enter for newline)
- Gateway health status indicator
- Response display with syntax highlighting
- Request metadata viewer (latency, tokens, model info)

**Try it:**

1. Navigate to the **Playground** screen (should open by default)
2. Type "Hello, how are you?" in the text box
3. Select "GPT-3.5 Turbo" from dropdown
4. Click "Send" (or press Enter)
5. Watch the response appear with metadata!

## 📖 What You'll See

### The Unified Dashboard

```
┌──────────────────┬────────────────────────────────────────┐
│ 🥋 AI Aikido     │  🎮 Playground                         │
│ Gateway          │                                        │
│ Dashboard        │  Gateway Status: ✅ Gateway Online     │
├──────────────────┤                                        │
│                  │  Model: [GPT-3.5 Turbo ▾]             │
│ 🎮 Playground    │                                        │
│ 📊 Overview      │  Message:                              │
│ 💰 Cost Explorer │  ┌────────────────────────────────┐   │
│ 📋 Requests      │  │ Type your message here...      │   │
│ ⚡ Cache         │  │ (Shift+Enter for new line)     │   │
│ ⚙️ Settings      │  └────────────────────────────────┘   │
│                  │                                        │
│ ┌──────────────┐ │  [🚀 Send Message]                    │
│ │🟢 Gateway    │ │                                        │
│ │  Online      │ │  Response:                             │
│ └──────────────┘ │  ┌────────────────────────────────┐   │
└──────────────────┤  │ Hello! I'm doing well...       │   │
                   │  └────────────────────────────────┘   │
                   │                                        │
                   │  Metadata:                             │
                   │  {                                     │
                   │    "model": "gpt-3.5-turbo",          │
                   │    "latency_ms": 1234,                │
```
┌───────────────────────────────────────────┐
│         🥋 AI Aikido Gateway              │
│           Reference Client                │
├───────────────────────────────────────────┤
│ Gateway: http://localhost:8000      ● 🟢 │
├───────────────────────────────────────────┤
│                                           │
│ Your Message:                             │
│ ┌───────────────────────────────────────┐ │
│ │ Type your message here...             │ │
│ │                                       │ │
│ └───────────────────────────────────────┘ │
│                                           │
│ [GPT-3.5 Turbo ▾]         [Send]         │
│                                           │
│ Response:                                 │
│ ┌───────────────────────────────────────┐ │
│ │ Hello! I'm doing well, thank you...   │ │
│ └───────────────────────────────────────┘ │
│                                           │
│ Request Metadata:                         │
│ ┌───────────────────────────────────────┐ │
│ │ {                                     │ │
│ │   "model": "gpt-3.5-turbo",          │ │
│ │   "latency_ms": 1234,                │ │
│ │   "usage": {                         │ │
│ │     "prompt_tokens": 10,             │ │
│ │     "completion_tokens": 15          │ │
│ │   }                                  │ │
│ │ }                                    │ │
│ └───────────────────────────────────────┘ │
└───────────────────────────────────────────┘
```

## 🧪 Alternative Ways to Test

### Option 1: Use the Interactive API Docs

Visit: <http://localhost:8000/docs>

1. Click on **POST /v1/chat/completions**
2. Click **"Try it out"**
3. Edit the JSON request
4. Click **"Execute"**
5. See the response!

### Option 2: Use curl

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [
      {"role": "user", "content": "Tell me a joke"}
    ],
    "temperature": 0.7,
    "max_tokens": 100
  }'
```

### Option 3: Use Python

```python
import requests

response = requests.post(
    "http://localhost:8000/v1/chat/completions",
    json={
        "model": "gpt-3.5-turbo",
        "messages": [
            {"role": "user", "content": "Hello!"}
        ]
    }
)

print(response.json())
```

## 🎯 What's Happening Behind the Scenes

```
1. You type in the browser
   ↓
2. JavaScript sends POST request to gateway
   ↓
3. Gateway receives request at /v1/chat/completions
   ↓
4. Gateway forwards to OpenAI API
   ↓
5. OpenAI processes and responds
   ↓
6. Gateway returns response (OpenAI format)
   ↓
7. Client displays response + metadata
```

## 🔧 Troubleshooting

### "Gateway not reachable"

**Solution:**
```bash
# Check if gateway is running
curl http://localhost:8000/health

# If not, start it
make start-reload
```

### "Error: OPENAI_API_KEY missing"

**Solution:**
```bash
# Edit .env file
nano .env

# Add your key
OPENAI_API_KEY=sk-your-key-here

# Restart gateway
```

### Port 3000 already in use

**Solution:**
```bash
# Use a different port
PORT=3001 npm start

# Or kill the process using port 3000
lsof -i :3000
kill -9 <PID>
```

## 📚 Next Steps

Once you have it working:

1. ✅ Try different models (GPT-4, etc.)
2. ✅ Check the API docs at /docs
3. ✅ Look at the code in `client/` and `src/api/`
4. ✅ Read the architecture in `docs/ARCHITECTURE.md`
5. 🔜 Wait for Phase 3: Cost Monitor Plugin!

## 🎓 Learning Resources

- **Architecture:** `docs/ARCHITECTURE.md`
- **API Models:** `src/api/models.py`
- **API Routes:** `src/api/routes.py`
- **Client Code:** `client/public/app.js`
- **Phase 2.5 Summary:** `docs/PHASE_2.5_SUMMARY.md`

## 💡 Pro Tips

1. **Keyboard Shortcuts:**
   - `Enter` to send message
   - `Shift + Enter` for new line in text box

2. **Watch Gateway Logs:**
   ```bash
   # In a separate terminal
   tail -f /tmp/gateway.log
   ```

3. **Test Different Models:**
   - GPT-3.5 Turbo (cheap, fast)
   - GPT-4 (expensive, smart)
   - Try the dropdown!

4. **Check Health Anytime:**
   - Click "Check Gateway Health" button
   - Or visit <http://localhost:8000/health>

---

**Happy Testing! 🎉**

Questions? Check `README.md` or `docs/` folder.
