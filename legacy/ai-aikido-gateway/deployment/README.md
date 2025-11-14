# Deployment Files

This directory contains all deployment-related files and configurations.

## 📁 Contents

### Docker Files

- `Dockerfile.gateway` - Production gateway container
- `Dockerfile.dashboard` - Production dashboard container
- `Dockerfile.dev.dashboard` - Development dashboard container
- `.dockerignore` - Files to exclude from Docker builds

### Docker Compose

- `docker-compose.yml` - Main orchestration file
- `docker-compose.dev.yml` - Development overrides
- `docker-compose.prod.yml` - Production configuration

### Environment Files

- `.env.docker` - Docker environment variables
- `.env.docker.example` - Docker environment template

### Cloud Deployment

- `render.yaml` - Render.com deployment configuration
- `.renderignore` - Files to exclude from Render builds

## 🚀 Quick Start

### Development

```bash
# From project root
docker-compose -f deployment/docker-compose.yml -f deployment/docker-compose.dev.yml up

# Or from deployment directory
cd deployment
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

### Production

```bash
# From project root
docker-compose -f deployment/docker-compose.yml -f deployment/docker-compose.prod.yml up -d

# Or from deployment directory
cd deployment
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## 📖 Documentation

See `../docs/deployment/` for detailed deployment guides and instructions.
