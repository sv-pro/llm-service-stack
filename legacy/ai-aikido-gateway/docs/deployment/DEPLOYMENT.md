# AI Aikido Gateway - Deployment Guide

## Deployment Options

Choose the deployment method that best fits your needs:

### 🐳 Docker Deployment (Recommended for Production)

**Best for**: Production servers, development teams, on-premise deployments

- ✅ **Full control** over the environment
- ✅ **Consistent across dev/staging/prod**
- ✅ **Easy scaling** and orchestration
- ✅ **Local development** with hot reload
- ✅ **No vendor lock-in**

**Quick Start**: See **[Docker Deployment Guide](DOCKER_DEPLOYMENT.md)** for complete instructions.

```bash
# Quick setup (5 minutes)
./scripts/docker-setup.sh

# Or manual setup
cp .env.docker.example .env.docker  # Add your API keys
docker-compose up --build
```

**Access**: Gateway at http://localhost:8000, Dashboard at http://localhost:3000

---

### ☁️ Render.com Deployment (Recommended for Beginners)

**Best for**: Quick deployments, beginners, free hosting

- ✅ **Free tier** (with sleep after 15 min inactivity)
- ✅ **Native Python + Node.js support**
- ✅ **Secure environment variables** (remote .env)
- ✅ **Auto-deploy from GitHub** (including private repos!)
- ✅ **SQLite persistence** (1GB free disk)
- ✅ **Zero Docker configuration**

---

## Quick Start (10 minutes)

### 1. Prerequisites

- GitHub account with your project pushed
- OpenAI API key (required)
- Anthropic API key (optional)

### 2. Sign Up at Render.com

1. Go to <https://render.com>
2. Click "Get Started" or "Sign Up"
3. Choose "Sign up with GitHub"
4. Authorize Render to access your repositories
5. ✅ **Private repos are fully supported!**

### 3. Create Backend Service (Gateway)

This is the FastAPI Python backend that handles all API requests.

#### Step 1: Create Web Service

1. Click **"New +"** button (top right)
2. Select **"Web Service"**
3. **Connect your repository**:
   - If first time: Click "Connect account" → Authorize GitHub
   - Find and select: `ai-aikido-gateway`
   - Click "Connect"

#### Step 2: Configure Backend Settings

Fill in these fields:

| Field              | Value                                              |
| ------------------ | -------------------------------------------------- |
| **Name**           | `aikido-gateway`                                   |
| **Region**         | Oregon (US West) or closest to you                 |
| **Branch**         | `dev` (or `main`)                                  |
| **Root Directory** | (leave blank)                                      |
| **Runtime**        | Python 3                                           |
| **Build Command**  | `pip install -r requirements.txt`                  |
| **Start Command**  | `uvicorn src.main:app --host 0.0.0.0 --port $PORT` |

#### Step 3: Add Environment Variables

Click **"Advanced"** button, then add these environment variables:

```bash
GATEWAY_HOST=0.0.0.0
LOG_LEVEL=INFO
DB_PATH=/var/data
OPENAI_API_KEY=sk-your-actual-openai-key-here
ANTHROPIC_API_KEY=sk-ant-your-actual-key-here  # Optional
CLASSIFIER_MODEL=claude-3-haiku-20240307
CLASSIFIER_MAX_TOKENS=100
```

⚠️ **Replace with your actual API keys!**

#### Step 4: Add Persistent Disk

Scroll down to **"Disk"** section and click **"Add Disk"**:

| Field          | Value         |
| -------------- | ------------- |
| **Name**       | `aikido-data` |
| **Mount Path** | `/var/data`   |
| **Size**       | 1 GB          |

This disk will store your SQLite database persistently.

#### Step 5: Select Plan and Deploy

1. Select **"Free"** plan
2. Click **"Create Web Service"**
3. ⏱️ Wait 5-8 minutes for build to complete
4. **IMPORTANT**: Copy your gateway URL (e.g., `https://aikido-gateway.onrender.com`)
   - You'll need this for the dashboard!

---

### 4. Create Frontend Service (Dashboard)

Now create the React dashboard that connects to your gateway.

#### Step 1: Create Another Web Service

1. Click **"New +"** button again
2. Select **"Web Service"**
3. **Connect the same repository**: `ai-aikido-gateway`

#### Step 2: Configure Frontend Settings

Fill in these fields:

| Field              | Value                        |
| ------------------ | ---------------------------- |
| **Name**           | `aikido-dashboard`           |
| **Region**         | Same as backend (Oregon)     |
| **Branch**         | `dev` (or `main`)            |
| **Root Directory** | `dashboard`                  |
| **Runtime**        | Node                         |
| **Build Command**  | `npm ci && npm run build`    |
| **Start Command**  | `npx serve -s dist -l $PORT` |

#### Step 3: Add Dashboard Environment Variables

Click **"Advanced"** button, then add:

```bash
NODE_VERSION=18
VITE_API_URL=https://aikido-gateway.onrender.com
```

⚠️ **Replace `https://aikido-gateway.onrender.com` with YOUR actual gateway URL from Step 3!**

#### Step 4: Select Plan and Deploy

1. Select **"Free"** plan
2. Click **"Create Web Service"**
3. ⏱️ Wait 3-5 minutes for build to complete

---

### 5. Access Your Deployed Application

Once both services show "Live" status:

**Gateway API:**

- URL: `https://your-gateway-name.onrender.com`
- Health check: `https://your-gateway-name.onrender.com/health`
- API docs: `https://your-gateway-name.onrender.com/docs`

**Dashboard:**

- URL: `https://your-dashboard-name.onrender.com`
- Should show navigation with 6 tabs
- Playground should connect to gateway automatically

### 6. Verify Deployment

Test that everything works:

```bash
# Test gateway health
curl https://your-gateway-name.onrender.com/health

# Test chat completion
curl -X POST https://your-gateway-name.onrender.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Hello!"}],
    "max_tokens": 50
  }'
```

Then open your dashboard in a browser and:

1. Go to **Playground** tab
2. Verify gateway shows "Online" status
3. Send a test message
4. Check **Request History** tab for your request
5. Check **Cost Explorer** tab for cost tracking

---

## Configuration Details

### Environment Variables

#### Backend (`aikido-gateway`)

| Variable            | Required | Default   | Description               |
| ------------------- | -------- | --------- | ------------------------- |
| `OPENAI_API_KEY`    | **Yes**  | -         | Your OpenAI API key       |
| `ANTHROPIC_API_KEY` | No       | -         | Your Anthropic API key    |
| `GATEWAY_HOST`      | No       | `0.0.0.0` | Host to bind to           |
| `GATEWAY_PORT`      | No       | `$PORT`   | Port (auto-set by Render) |
| `LOG_LEVEL`         | No       | `INFO`    | Logging level             |

#### Frontend (`aikido-dashboard`)

| Variable       | Required | Default     | Description                                    |
| -------------- | -------- | ----------- | ---------------------------------------------- |
| `VITE_API_URL` | Auto     | Gateway URL | Backend API URL (auto-configured in blueprint) |

---

## SQLite Database Persistence

The gateway uses SQLite for request history and cost tracking. On Render:

1. **Free tier includes 1GB persistent disk**
2. Database is stored in `/var/data/request_history.db`
3. Data persists across deployments
4. **Important**: Database resets if service is deleted

To backup your database:

```bash
# Download from Render dashboard
# Services → aikido-gateway → Shell → Run:
cat /var/data/request_history.db | base64
# Copy output and decode locally
```

---

## Render Free Tier Limitations

### What You Get (Free)

- ✅ 750 hours/month (enough for continuous running)
- ✅ 512MB RAM per service
- ✅ 1GB persistent disk per service
- ✅ Automatic HTTPS
- ✅ Custom domains
- ✅ Auto-deploys from Git

### Limitations

- ⚠️ **Services sleep after 15 minutes of inactivity**
- ⚠️ **Cold start takes 30-60 seconds** when waking up
- ⚠️ Limited to 500MB build size
- ⚠️ No SSH access (use web shell instead)

**For demos**: Free tier is perfect!
**For production**: Upgrade to $7/month per service for:

- No sleeping
- Faster CPUs
- More RAM (2GB+)
- Priority support

---

## Testing Your Deployment

### 1. Check Gateway Health

```bash
curl https://aikido-gateway.onrender.com/health
```

Expected response:

```json
{
  "status": "healthy",
  "service": "AI Aikido Gateway",
  "version": "0.1.0"
}
```

### 2. Test Chat Completion

```bash
curl -X POST https://aikido-gateway.onrender.com/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Hello!"}],
    "max_tokens": 50
  }'
```

### 3. Access Dashboard

Open in browser: `https://aikido-dashboard.onrender.com`

- Should see all 6 tabs (Overview, Playground, etc.)
- Playground should show "Gateway Online" status
- Try sending a test message

### 4. Check Request History

After sending requests:

- Go to "Request History" tab
- Should see your test requests
- Cost tracking should show calculated costs

---

## Updating Your Deployment

Render **auto-deploys** when you push to GitHub:

```bash
# Make changes locally
git add .
git commit -m "Update feature X"
git push origin main

# Render automatically:
# 1. Detects the push
# 2. Builds your services
# 3. Deploys new version
# 4. Zero downtime (for paid plans)
```

### Manual Redeploy

If needed:

1. Go to Render Dashboard
2. Select your service
3. Click "Manual Deploy" → "Deploy latest commit"

---

## Monitoring & Logs

### View Logs

1. **Render Dashboard** → Select service → "Logs"
2. Real-time log streaming
3. Filter by severity (info, warning, error)

### Common Issues

#### 1. Service Won't Start

**Symptom**: Deploy fails, service shows "Deploy failed"

**Solutions**:

- Check logs for Python/Node errors
- Verify `requirements.txt` is up to date
- Ensure `src/` directory structure is correct

#### 2. Dashboard Can't Reach Gateway

**Symptom**: Dashboard shows "Gateway Offline"

**Solutions**:

- Check `VITE_API_URL` is set correctly
- Verify gateway is deployed and healthy
- Check gateway logs for startup errors

#### 3. Cold Start Timeout

**Symptom**: First request after inactivity fails

**Solutions**:

- This is normal on free tier
- Retry after 30-60 seconds
- Consider upgrading to paid plan ($7/mo) to prevent sleeping

#### 4. SQLite Database Missing

**Symptom**: No request history showing

**Solutions**:

- Database needs persistent disk (configured in `render.yaml`)
- Check disk is mounted at `/var/data`
- Restart service to recreate database

---

## Cost Considerations

### Free Tier (Both Services)

- **Cost**: $0/month
- **Build time**: ~5 min per deploy
- **Sleeping**: After 15 min inactivity
- **Best for**: Demos, testing, development

### Paid Tier (Recommended for Production)

- **Cost**: $7/month per service = $14/month total
- **Benefits**:
  - No sleeping (always available)
  - Faster response times
  - More resources (2GB RAM)
  - Priority support

### Comparison with Alternatives

| Platform   | Free Tier | Sleep?    | Setup Time |
| ---------- | --------- | --------- | ---------- |
| **Render** | ✅        | Yes (15m) | 5 min      |
| Railway    | $5 credit | No        | 3 min      |
| Fly.io     | 3 VMs     | No        | 15 min     |
| Heroku     | ❌        | -         | 10 min     |

---

## Security Best Practices

### 1. Environment Variables

- ✅ **Never commit** `.env` file to Git
- ✅ **Always use** Render dashboard for secrets
- ✅ **Rotate keys** regularly

### 2. API Keys

- ✅ Use **separate keys** for dev/prod
- ✅ Set **spending limits** in OpenAI dashboard
- ✅ Monitor usage via OpenAI/Anthropic dashboards

### 3. Rate Limiting

Consider adding rate limiting for production:

```python
# Future: Add rate limiting plugin
# See docs/ROADMAP.md
```

---

## Troubleshooting

### Check Service Status

```bash
# Gateway health
curl https://your-gateway.onrender.com/health

# API docs (interactive)
https://your-gateway.onrender.com/docs
```

### Access Web Shell

1. Render Dashboard → Service → "Shell"
2. Run commands directly on server
3. Check file system, logs, environment

### Get Support

- **Render Docs**: https://render.com/docs
- **Community**: https://community.render.com
- **Project Issues**: https://github.com/your-username/ai-aikido-gateway/issues

---

## Deployment Comparison

### When to Choose Docker 🐳

**Choose Docker if you:**

- Need full control over the deployment environment
- Want to run on your own servers or cloud VMs
- Have a DevOps team or Docker experience
- Need guaranteed uptime (no sleeping)
- Want to scale horizontally
- Prefer self-hosting and avoiding vendor lock-in
- Need custom networking or security configurations

**Docker Pros:**

- ✅ Complete control and customization
- ✅ Consistent across all environments
- ✅ No cold starts or sleeping
- ✅ Easy to scale and monitor
- ✅ Works on any cloud provider or on-premise
- ✅ Great for development teams

**Docker Cons:**

- ❌ Requires server management
- ❌ You handle updates, security, backups
- ❌ Monthly server costs ($5-50+/month)
- ❌ Requires Docker knowledge

### When to Choose Render.com ☁️

**Choose Render if you:**

- Want the fastest deployment (5 minutes)
- Prefer managed hosting with zero maintenance
- Are new to deployment/DevOps
- Need a free tier for testing/demos
- Want automatic deployments from GitHub
- Don't mind occasional cold starts

**Render Pros:**

- ✅ Zero configuration required
- ✅ Free tier available
- ✅ Automatic SSL, backups, monitoring
- ✅ GitHub integration
- ✅ No server management needed
- ✅ Perfect for beginners

**Render Cons:**

- ❌ Free tier sleeps after 15 minutes
- ❌ Limited customization options
- ❌ Vendor lock-in
- ❌ Cold start delays on free tier

### Recommended Approach

1. **Start with Render.com** for quick testing and demos
2. **Move to Docker** when you need production reliability
3. **Use Docker for development** to match production environment

### Migration Path

You can easily migrate from Render to Docker later:

```bash
# Export your data from Render (if needed)
# Set up Docker deployment
# Update DNS to point to new server
```

---

## Next Steps

After successful deployment:

1. ✅ **Test all features** (Playground, History, Cost Explorer)
2. ✅ **Share the dashboard URL** with your team
3. ✅ **Set up monitoring** (Render has built-in metrics)
4. ✅ **Configure custom domain** (optional, available on all plans)
5. ✅ **Upgrade to paid plan** if you need 24/7 availability

---

## Alternative Platforms

If Render doesn't work for you:

- **Railway.app** - Similar setup, $5/month credit
- **Fly.io** - More complex, but generous free tier
- **DigitalOcean App Platform** - $5/month minimum

See [CLAUDE.md](../CLAUDE.md) for platform comparisons.

---

**Questions?** Open an issue on GitHub or check the [Render documentation](https://render.com/docs).
