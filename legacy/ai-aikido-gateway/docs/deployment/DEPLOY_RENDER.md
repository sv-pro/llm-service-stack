# Deploy to Render.com - Quick Start

## 1. Sign Up at Render.com

1. Go to <https://render.com>
2. Sign up with GitHub
3. Authorize Render to access your repository

## 2. Create Backend Service (Gateway)

1. Click **"New +"** → **"Web Service"**
2. Connect repository: `ai-aikido-gateway`
3. Configure:
   - **Name**: `aikido-gateway`
   - **Branch**: `dev`
   - **Runtime**: Python 3
   - **Build**: `pip install -r requirements.txt`
   - **Start**: `uvicorn src.main:app --host 0.0.0.0 --port $PORT`
4. Click **"Advanced"** → Add environment variables:

```bash
GATEWAY_HOST=0.0.0.0
LOG_LEVEL=INFO
DB_PATH=/var/data
OPENAI_API_KEY=sk-your-actual-key-here
ANTHROPIC_API_KEY=sk-ant-your-key-here  # Optional
```

5. Scroll down and look for **"Persistent Disk"** or **"Volumes"** section:
   - If you see it: Add disk with mount path `/var/data` and 1GB size
   - If NOT visible: Skip this step (you can add it later from service settings)
6. Select **"Free"** plan → **"Create Web Service"**
7. ⚠️ **Copy your gateway URL** (e.g., `https://aikido-gateway.onrender.com`)

**Note**: If you don't see the disk option during creation, you can add it after:
1. Go to your service dashboard
2. Click "Disk" or "Volumes" in the left sidebar
3. Click "Add Disk"
4. Set mount path to `/var/data`, size 1GB

## 3. Create Frontend Service (Dashboard)

1. Click **"New +"** → **"Web Service"**
2. Connect same repository: `ai-aikido-gateway`
3. Configure:
   - **Name**: `aikido-dashboard`
   - **Branch**: `dev`
   - **Root Directory**: `dashboard`
   - **Runtime**: Node
   - **Build**: `npm ci && npm run build`
   - **Start**: `npx serve -s dist -l $PORT`
4. Click **"Advanced"** → Add environment variables:

```bash
NODE_VERSION=18
VITE_API_URL=https://your-gateway-url.onrender.com
```

⚠️ **Use YOUR actual gateway URL from step 2!**

5. Select **"Free"** plan → **"Create Web Service"**

## 4. Wait for Deploy (5-10 minutes)

Both services will build and deploy automatically.

## 5. Access Your App

- **Gateway**: `https://your-gateway-name.onrender.com/health`
- **Dashboard**: `https://your-dashboard-name.onrender.com`

## 6. Test It!

1. Open dashboard in browser
2. Go to Playground tab
3. Send a test message
4. Check Request History
5. Check Cost Explorer

## Troubleshooting

### Dashboard can't connect to Gateway

1. Go to Render dashboard
2. Find your `aikido-gateway` service
3. Copy the URL (e.g., `https://aikido-gateway.onrender.com`)
4. Go to `aikido-dashboard` service → Environment
5. Set `VITE_API_URL` to your gateway URL
6. Trigger a manual redeploy

### Gateway shows "Deploy Failed"

Check logs for missing dependencies or Python errors:
- Verify `requirements.txt` is complete
- Check Python version (should be 3.11+)

### Database not persisting

- Verify disk is mounted at `/var/data`
- Check `render.yaml` has disk configuration
- Restart service

---

**Full Documentation**: See [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)

**Questions?** Open an issue on GitHub!
