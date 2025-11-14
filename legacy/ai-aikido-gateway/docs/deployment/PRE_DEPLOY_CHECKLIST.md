# Pre-Deployment Checklist ✅

Before deploying to Render.com, verify everything is ready:

## 1. Code Preparation

- [ ] All changes committed to Git
- [ ] `.env` file is in `.gitignore` (DO NOT commit secrets!)
- [ ] Code pushed to GitHub repository
- [ ] Repository can be private or public (both work on Render)

## 2. Configuration Files

- [ ] `render.yaml` exists in project root
- [ ] `dashboard/src/config.js` created (API URL configuration)
- [ ] `config/plugins.yaml` updated with `DB_PATH` env var
- [ ] `.renderignore` created (optional but recommended)

## 3. API Keys Ready

Gather these API keys before deployment:

- [ ] **OpenAI API Key** (REQUIRED)
  - Get from: https://platform.openai.com/api-keys
  - Format: `sk-...`
  - Test it works locally first!

- [ ] **Anthropic API Key** (OPTIONAL)
  - Get from: https://console.anthropic.com/
  - Format: `sk-ant-...`
  - Only needed if using Claude models

## 4. Local Testing

Before deploying, verify everything works locally:

### Backend Tests

```bash
# 1. Start gateway
make start-reload
# OR
uvicorn src.main:app --reload

# 2. Check health
curl http://localhost:8000/health

# 3. Test chat completion
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Hello!"}],
    "max_tokens": 10
  }'
```

Expected: Should get a successful response with usage tokens.

### Frontend Tests

```bash
# 1. Build dashboard
cd dashboard
npm install
npm run build

# 2. Check dist/ folder exists
ls dist/

# 3. Test production server
npx serve -s dist -l 3000
```

Expected: Dashboard should load at http://localhost:3000

### Full Integration Test

```bash
# In terminal 1
make start-reload  # Start gateway on port 8000

# In terminal 2
cd dashboard
npm run dev  # Start dashboard on port 3000

# In browser
# Open http://localhost:3000
# Go to Playground
# Send a test message
# Check Request History shows the request
# Check Cost Explorer shows the cost
```

Expected: All features work end-to-end.

## 5. GitHub Repository

- [ ] Repository exists on GitHub
- [ ] You have admin access to the repository
- [ ] Latest code is pushed
- [ ] No sensitive data in commit history

Check:
```bash
git remote -v
git log --oneline -5
git status
```

## 6. Render Account

- [ ] Render.com account created (free signup)
- [ ] GitHub connected to Render
- [ ] Billing set up (even for free tier, Render requires a card on file)

Note: Free tier is truly free, but Render requires payment method for verification.

## 7. Database Configuration

- [ ] `config/plugins.yaml` uses `${DB_PATH:-./data/history.db}`
- [ ] `render.yaml` has disk configuration with `/var/data` mount
- [ ] `DB_PATH` environment variable set to `/var/data` in render.yaml

Verify in `render.yaml`:
```yaml
disk:
  name: aikido-data
  mountPath: /var/data
  sizeGB: 1
```

And:
```yaml
envVars:
  - key: DB_PATH
    value: /var/data
```

## 8. Dependencies

- [ ] `requirements.txt` up to date (Python)
- [ ] `dashboard/package.json` has `serve` dependency
- [ ] All imports work locally

Verify:
```bash
# Python deps
pip freeze > requirements-check.txt
diff requirements.txt requirements-check.txt

# Node deps
cd dashboard
npm list --depth=0
```

## 9. Build Commands Tested

- [ ] Backend builds: `pip install -r requirements.txt`
- [ ] Frontend builds: `cd dashboard && npm ci && npm run build`
- [ ] Both succeed without errors

Test locally:
```bash
# Backend
pip install -r requirements.txt

# Frontend
cd dashboard
rm -rf node_modules
npm ci
npm run build
```

## 10. Documentation Review

- [ ] [DEPLOYMENT_SUMMARY.md](DEPLOYMENT_SUMMARY.md) reviewed
- [ ] [DEPLOY_RENDER.md](DEPLOY_RENDER.md) handy for deployment
- [ ] [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) read for troubleshooting

## Ready to Deploy? ✅

If all checkboxes above are checked, you're ready!

### Quick Deploy Commands

```bash
# 1. Final commit
git add .
git commit -m "chore: Ready for Render deployment"
git push origin main  # or dev, master, etc.

# 2. Go to Render.com
# - Click "New" → "Blueprint"
# - Select your repository
# - Apply configuration
# - Add API keys when prompted
# - Deploy!

# 3. Wait 5-10 minutes for initial build

# 4. Test deployment
curl https://aikido-gateway.onrender.com/health
curl https://aikido-dashboard.onrender.com
```

---

## Common Issues Before Deploy

### Issue: `render.yaml` not detected

**Solution**: Make sure file is in project root, not in a subdirectory.

```bash
ls -la render.yaml  # Should exist
```

### Issue: Build fails locally

**Solution**: Fix local issues before deploying. Render will fail too.

```bash
# Test Python
python -m pytest

# Test Node build
cd dashboard && npm run build
```

### Issue: Missing API key

**Solution**: Get keys before starting deployment:
- OpenAI: https://platform.openai.com/api-keys
- Anthropic: https://console.anthropic.com/

### Issue: Git repo not pushed

**Solution**:
```bash
git status  # Check for uncommitted changes
git push origin main  # Push to GitHub
```

---

## Post-Deployment Checklist

After Render deploys successfully:

- [ ] Gateway health check passes
- [ ] Dashboard loads
- [ ] Playground connects to gateway
- [ ] Can send test message
- [ ] Request appears in history
- [ ] Cost is calculated
- [ ] Cost Explorer shows data

If any fail, see [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md) troubleshooting section.

---

**All set? Let's deploy! 🚀**

See [DEPLOY_RENDER.md](DEPLOY_RENDER.md) for step-by-step instructions.
