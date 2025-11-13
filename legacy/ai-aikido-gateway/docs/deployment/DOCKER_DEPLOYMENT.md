# Docker Deployment Guide - AI Aikido Gateway

## Overview

The AI Aikido Gateway supports Docker deployment with a complete container orchestration setup. This guide covers everything from basic Docker usage to production deployment scenarios.

## 📦 What's Included

### Docker Files

- **`Dockerfile.gateway`** - Multi-stage FastAPI backend container
- **`Dockerfile.dashboard`** - Multi-stage React frontend container
- **`Dockerfile.dev.dashboard`** - Development version with hot reload
- **`docker-compose.yml`** - Main orchestration file
- **`docker-compose.dev.yml`** - Development overrides
- **`docker-compose.prod.yml`** - Production optimizations

### Configuration

- **`.env.docker.example`** - Environment template
- **`.dockerignore`** - Build optimization
- **`scripts/docker-setup.sh`** - Automated setup script

---

## 🚀 Quick Start (5 minutes)

### 1. Prerequisites

```bash
# Install Docker Desktop (Windows/Mac)
# Download from: https://docs.docker.com/desktop/

# Or install Docker Engine (Linux)
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Verify installation
docker --version
docker-compose --version  # or 'docker compose version'
```

### 2. Clone and Setup

```bash
# Clone repository
git clone <your-repo-url> ai-aikido-gateway
cd ai-aikido-gateway

# Run automated setup
./scripts/docker-setup.sh
```

The setup script will:

- ✅ Check Docker installation
- ✅ Create `.env.docker` from template
- ✅ Prompt for API keys
- ✅ Offer to start services immediately

### 3. Manual Setup (Alternative)

```bash
# 1. Create environment file
cp .env.docker.example .env.docker

# 2. Edit with your API keys
nano .env.docker  # Add your OPENAI_API_KEY and ANTHROPIC_API_KEY

# 3. Build and run
docker-compose up --build
```

### 4. Access Your Services

- **🌐 Gateway API**: http://localhost:8000
- **📊 Dashboard**: http://localhost:3000
- **📖 API Documentation**: http://localhost:8000/docs
- **❤️ Health Check**: http://localhost:8000/health

---

## 🔧 Configuration

### Environment Variables

Edit `.env.docker` with your configuration:

```bash
# Required API Keys
OPENAI_API_KEY=sk-your-openai-key-here
ANTHROPIC_API_KEY=sk-ant-your-anthropic-key-here

# Model Configuration
CLASSIFIER_MODEL=claude-3-haiku-20240307
CHEAP_MODEL=claude-3-haiku-20240307
EXPENSIVE_MODEL=gpt-4-turbo-preview

# Application Settings
LOG_LEVEL=INFO
GATEWAY_URL=http://localhost:8000  # Update for production
```

### Custom Configuration Files

Mount custom configs (optional):

```bash
# Place custom configs in ./config/
# They'll be mounted to /app/config/ in containers
```

---

## 🏃 Running Services

### Development Mode (Recommended for Development)

```bash
# Start with hot reload enabled
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# With custom env file
docker-compose --env-file .env.docker -f docker-compose.yml -f docker-compose.dev.yml up

# Rebuild and start
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build

# Run in background
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d
```

**Development Features:**

- ✅ Hot reload for backend (Python code changes)
- ✅ Hot reload for frontend (React code changes)
- ✅ Debug logging enabled
- ✅ Source code mounted as volumes

### Production Mode (Recommended for Production)

```bash
# Start production services
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# With custom env file
docker-compose --env-file .env.docker -f docker-compose.yml -f docker-compose.prod.yml up -d

# Build fresh images
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d
```

**Production Features:**

- ✅ Optimized Docker images
- ✅ Resource limits (CPU/Memory)
- ✅ Health checks with retries
- ✅ Automatic restart policies
- ✅ Structured logging with rotation
- ✅ Custom network with subnet

### Basic Mode (Simple Setup)

```bash
# Default configuration
docker-compose up

# With rebuild
docker-compose up --build

# Background mode
docker-compose up -d
```

---

## 📊 Service Management

### Starting Services

```bash
# Start all services
docker-compose up

# Start specific service
docker-compose up gateway
docker-compose up dashboard

# Start with rebuild
docker-compose up --build

# Start in background (detached)
docker-compose up -d
```

### Stopping Services

```bash
# Stop all services (keeps data)
docker-compose down

# Stop and remove volumes (loses data)
docker-compose down -v

# Stop specific service
docker-compose stop gateway
docker-compose stop dashboard
```

### Viewing Logs

```bash
# View all logs
docker-compose logs

# Follow logs in real-time
docker-compose logs -f

# View specific service logs
docker-compose logs gateway
docker-compose logs dashboard

# Last 100 lines
docker-compose logs --tail=100 gateway

# Logs with timestamps
docker-compose logs -t
```

### Service Status

```bash
# Check running services
docker-compose ps

# Check service health
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Detailed inspection
docker inspect aikido-gateway
docker inspect aikido-dashboard
```

---

## 💾 Data Persistence

### SQLite Database Storage

The gateway stores request history and cache data in SQLite databases. These are automatically persisted by binding the repository `data/` directory into the container.

```yaml
# In docker-compose.yml
volumes:
  - ../data:/app/data  # Persistent storage
```

### Backup Data

```bash
# Create backup of persistent data (from repository root)
tar czf gateway-data-backup.tar.gz data/

# Restore from backup
tar xzf gateway-data-backup.tar.gz
```

### Volume Management

```bash
# Ensure host data directory exists (run from repo root)
mkdir -p data

# Clear persisted data (⚠️ loses all history/cache)
rm -rf data/*
```

---

## 🔍 Debugging

### Container Shell Access

```bash
# Access gateway container
docker-compose exec gateway bash

# Access dashboard container
docker-compose exec dashboard sh

# Run commands in container
docker-compose exec gateway python -c "import sys; print(sys.version)"
docker-compose exec gateway curl http://localhost:8000/health
```

### Debug Build Issues

```bash
# Build without cache
docker-compose build --no-cache

# Build specific service
docker-compose build gateway
docker-compose build dashboard

# View build output
docker-compose build --progress=plain

# Debug image layers
docker history aikido-gateway-gateway:latest
```

### Network Debugging

```bash
# Check container connectivity
docker-compose exec gateway ping dashboard
docker-compose exec dashboard wget -O- http://gateway:8000/health

# Inspect network
docker network ls
docker network inspect aikido-gateway_aikido-network
```

### Performance Monitoring

```bash
# Container resource usage
docker stats

# Service-specific stats
docker stats aikido-gateway aikido-dashboard

# Container logs with timing
docker-compose logs -t -f gateway
```

---

## 🏭 Production Deployment

### Server Requirements

**Minimum Requirements:**

- 2 CPU cores
- 4GB RAM
- 20GB disk space
- Docker 20.10+
- Docker Compose 2.0+

**Recommended Production:**

- 4 CPU cores
- 8GB RAM
- 50GB SSD storage
- Load balancer (nginx/traefik)
- Monitoring (Prometheus/Grafana)

### Production Checklist

#### 1. Security Setup

```bash
# Create dedicated user
sudo useradd -m -s /bin/bash aikido
sudo usermod -aG docker aikido

# Set up directory
sudo mkdir -p /opt/ai-aikido-gateway
sudo chown aikido:aikido /opt/ai-aikido-gateway
```

#### 2. Environment Configuration

```bash
# Production environment file
cp .env.docker.example .env.production

# Edit production settings
nano .env.production
```

Key production settings:

```bash
# Use production API endpoints
GATEWAY_URL=https://your-domain.com
LOG_LEVEL=INFO

# Production model settings
CLASSIFIER_MODEL=claude-3-haiku-20240307
EXPENSIVE_MODEL=gpt-4-turbo-preview

# Security
PYTHONPATH=/app
```

#### 3. SSL/TLS Setup

For production, use a reverse proxy like nginx:

```nginx
# /etc/nginx/sites-available/aikido-gateway
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:3000;  # Dashboard
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /v1/ {
        proxy_pass http://localhost:8000;  # Gateway API
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    location /health {
        proxy_pass http://localhost:8000;
    }

    location /docs {
        proxy_pass http://localhost:8000;
    }
}
```

#### 4. Start Production Services

```bash
# Deploy production stack
docker-compose --env-file .env.production \
  -f docker-compose.yml \
  -f docker-compose.prod.yml \
  up -d

# Verify deployment
curl https://your-domain.com/health
curl https://your-domain.com/
```

#### 5. Monitoring Setup

```bash
# View production logs
docker-compose logs -f --tail=100

# Set up log rotation (handled by Docker in prod compose)
# Monitor resource usage
docker stats --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"
```

---

## 🔄 Updates and Maintenance

### Updating the Application

```bash
# 1. Pull latest code
git pull origin main

# 2. Stop services
docker-compose down

# 3. Rebuild and restart
docker-compose up --build -d

# 4. Verify update
curl http://localhost:8000/health
```

### Database Migrations

Currently using SQLite with automatic schema management. For major updates:

```bash
# 1. Backup data first (from repository root)
tar czf pre-update-backup.tar.gz data/

# 2. Update application
docker-compose up --build -d

# 3. Check logs for any migration messages
docker-compose logs gateway | grep -i migration
```

### Cleanup Old Images

```bash
# Remove unused images
docker image prune

# Remove unused volumes (⚠️ careful!)
docker volume prune

# Full cleanup (⚠️ removes everything unused)
docker system prune -a
```

---

## 🐛 Troubleshooting

### Common Issues

#### 1. Services Won't Start

**Issue**: `ERROR: Couldn't connect to Docker daemon`

```bash
# Solution: Start Docker service
sudo systemctl start docker

# Or Docker Desktop on Windows/Mac
```

**Issue**: `ERROR: Port already in use`

```bash
# Solution: Check what's using the port
lsof -i :8000
lsof -i :3000

# Kill conflicting process or change ports in docker-compose.yml
```

**Issue**: `ERROR: No such file or directory .env.docker`

```bash
# Solution: Create environment file
cp .env.docker.example .env.docker
# Edit with your API keys
```

#### 2. Build Failures

**Issue**: `ERROR: failed to solve: requirements.txt: not found`

```bash
# Solution: Ensure you're in the project root directory
pwd  # Should end with /ai-aikido-gateway
ls requirements.txt  # Should exist
```

**Issue**: `ERROR: Package installation failed`

```bash
# Solution: Clear Docker cache and rebuild
docker-compose build --no-cache
```

#### 3. Runtime Issues

**Issue**: Dashboard shows "Gateway Offline"

```bash
# Solution: Check gateway health
curl http://localhost:8000/health

# Check logs
docker-compose logs gateway

# Verify network connectivity
docker-compose exec dashboard wget -O- http://gateway:8000/health
```

**Issue**: API returns authentication errors

```bash
# Solution: Check environment variables
docker-compose exec gateway env | grep API_KEY

# Verify .env.docker file
cat .env.docker | grep API_KEY
```

#### 4. Performance Issues

**Issue**: Services running slowly

```bash
# Solution: Check resource usage
docker stats

# Increase resources in Docker Desktop settings
# Or adjust limits in docker-compose.prod.yml
```

**Issue**: Database locks or errors

```bash
# Solution: Check database permissions
docker-compose exec gateway ls -la /app/data/

# Restart gateway service
docker-compose restart gateway
```

### Getting Help

1. **Check the logs first:**

   ```bash
   docker-compose logs -f
   ```

2. **Verify service health:**

   ```bash
   curl http://localhost:8000/health
   docker-compose ps
   ```

3. **Test individual components:**

   ```bash
   # Test gateway directly
   docker-compose up gateway

   # Test dashboard separately
   docker-compose up dashboard
   ```

4. **Clean slate restart:**
   ```bash
   docker-compose down -v
   docker-compose up --build
   ```

---

## 📚 Advanced Usage

### Custom Networks

```yaml
# Advanced networking setup
networks:
  frontend:
    driver: bridge
  backend:
    driver: bridge
    internal: true # No external access

services:
  gateway:
    networks:
      - frontend
      - backend
  dashboard:
    networks:
      - frontend
```

### Multi-Environment Setup

```bash
# Development
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up

# Staging
docker-compose -f docker-compose.yml -f docker-compose.staging.yml up

# Production
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up
```

### Scaling Services

```bash
# Scale gateway service (behind load balancer)
docker-compose up --scale gateway=3

# Note: Dashboard should remain single instance
```

### External Database

For production, consider using external PostgreSQL:

```yaml
# docker-compose.prod.yml
services:
  gateway:
    environment:
      - DATABASE_URL=postgresql://user:pass@db-host:5432/aikido
    depends_on:
      - postgres

  postgres:
    image: postgres:15-alpine
    environment:
      POSTGRES_DB: aikido
      POSTGRES_USER: user
      POSTGRES_PASSWORD: password
    volumes:
      - postgres_data:/var/lib/postgresql/data
```

---

## 🔗 Integration with CI/CD

### GitHub Actions Example

```yaml
# .github/workflows/docker.yml
name: Docker Build and Deploy

on:
  push:
    branches: [main]

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Build Docker images
        run: |
          docker-compose build

      - name: Test deployment
        run: |
          docker-compose up -d
          sleep 30
          curl http://localhost:8000/health
          docker-compose down
```

### GitLab CI Example

```yaml
# .gitlab-ci.yml
stages:
  - build
  - test
  - deploy

build:
  stage: build
  script:
    - docker-compose build

test:
  stage: test
  script:
    - docker-compose up -d
    - curl http://localhost:8000/health
    - docker-compose down

deploy:
  stage: deploy
  script:
    - docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
  only:
    - main
```

---

## 🔄 Migration from Render.com

If you're currently using Render.com and want to migrate to Docker:

### 1. Export Data

```bash
# If you have existing data on Render, download it first
# This depends on your Render setup
```

### 2. Update Environment

```bash
# Copy Render environment variables to .env.docker
# Update GATEWAY_URL to your new Docker setup
```

### 3. Deploy Docker Version

```bash
# Start Docker deployment
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Import any existing data
# Update DNS to point to new server
```

---

## 📈 Performance Tuning

### Gateway Optimization

```yaml
# docker-compose.prod.yml
services:
  gateway:
    deploy:
      resources:
        limits:
          memory: 1G
          cpus: "1.0"
    environment:
      - WORKERS=4 # Adjust based on CPU cores
```

### Dashboard Optimization

```yaml
services:
  dashboard:
    deploy:
      resources:
        limits:
          memory: 512M
          cpus: "0.5"
```

### Database Optimization

```bash
# For high-traffic deployments, consider:
# 1. External Redis for caching
# 2. PostgreSQL instead of SQLite
# 3. Read replicas for analytics
```

---

## 🔐 Security Best Practices

### 1. Container Security

```dockerfile
# Run as non-root user (already implemented)
USER aikido

# Use specific image tags
FROM python:3.11-slim

# Scan images for vulnerabilities
docker scan aikido-gateway-gateway:latest
```

### 2. Network Security

```yaml
# Isolate internal services
networks:
  internal:
    driver: bridge
    internal: true
```

### 3. Secrets Management

```bash
# Use Docker secrets instead of environment variables
echo "sk-your-api-key" | docker secret create openai_key -

# Reference in compose file
secrets:
  - openai_key
```

### 4. Regular Updates

```bash
# Update base images regularly
docker-compose build --no-cache
docker image prune -f
```

---

This completes the comprehensive Docker deployment guide. The setup provides a production-ready containerized deployment with all the necessary tools, configurations, and documentation for successful operation.
