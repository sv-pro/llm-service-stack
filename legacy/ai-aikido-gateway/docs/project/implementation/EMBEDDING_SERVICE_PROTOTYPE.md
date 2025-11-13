# Embedding Service Prototype

**Status**: ✓ Prototype Complete and Tested
**Date**: 2025-11-07
**Type**: On-premise embedding generation using sentence-transformers

## Overview

This prototype validates the on-premise embedding approach using sentence-transformers as a replacement for OpenAI's embedding API. The service runs independently and provides REST API endpoints for embedding generation.

## Components

### 1. FastAPI Service
- **File**: [src/services/embeddings/server.py](../../../src/services/embeddings/server.py)
- **Model**: `all-MiniLM-L6-v2` (384 dimensions, fast and efficient)
- **Port**: 8001
- **Endpoints**:
  - `GET /health` - Health check and model status
  - `POST /embed` - Generate embeddings for text

### 2. Docker Support
- **Dockerfile**: [deployment/Dockerfile.embeddings](../../../deployment/Dockerfile.embeddings)
- **Compose**: [deployment/docker-compose.embeddings.yml](../../../deployment/docker-compose.embeddings.yml)
- **Requirements**: [deployment/requirements.embeddings.txt](../../../deployment/requirements.embeddings.txt)

### 3. Test Suite
- **Test Script**: [test_embedding_service.py](../../../test_embedding_service.py)
- **Tests**: Health check, embedding generation, consistency validation
- **Status**: All tests passing ✓

## Test Results

```
✓ Service started successfully
✓ Health check passed
  - Status: healthy
  - Model loaded: True
  - Model name: all-MiniLM-L6-v2

✓ Embedding generation successful
  - Dimensions: 384
  - Processing time: ~200ms
  - Vector sample: [0.048, 0.014, -0.024, 0.051, 0.022]...

✓ Embeddings are consistent
  - Same input produces identical embeddings
```

## Usage

### Local Development

```bash
# Install dependencies
pip install sentence-transformers fastapi uvicorn

# Start the service
python src/services/embeddings/server.py

# Test with curl
curl http://localhost:8001/health
curl -X POST http://localhost:8001/embed \
  -H "Content-Type: application/json" \
  -d '{"text": "Hello world", "model": "all-MiniLM-L6-v2"}'
```

### Docker

```bash
# Build the image
docker build -f deployment/Dockerfile.embeddings -t aikido-embeddings .

# Run with docker-compose
docker-compose -f deployment/docker-compose.embeddings.yml up
```

### Automated Testing

```bash
# Run the test suite
python test_embedding_service.py
```

## API Reference

### Health Check

```http
GET /health
```

**Response**:
```json
{
  "status": "healthy",
  "model_loaded": true,
  "model_name": "all-MiniLM-L6-v2"
}
```

### Generate Embedding

```http
POST /embed
Content-Type: application/json

{
  "text": "Your text here",
  "model": "all-MiniLM-L6-v2"
}
```

**Response**:
```json
{
  "embedding": [0.048, 0.014, -0.024, ...],
  "model": "all-MiniLM-L6-v2",
  "dimensions": 384,
  "processing_time_ms": 199.5
}
```

## Performance

- **Model Load Time**: ~2-3 seconds on first startup
- **Embedding Generation**: ~200ms per request
- **Dimensions**: 384 (compact and efficient)
- **Memory**: ~500MB (model + service)

## Model Characteristics

**all-MiniLM-L6-v2**:
- Fast and efficient for semantic similarity
- 384-dimensional embeddings
- Trained on 1B+ sentence pairs
- Excellent for semantic caching use case
- No API costs or rate limits

## Next Steps (Full Implementation)

1. **Integration**:
   - Create `SentenceTransformersProvider` class
   - Update semantic cache plugin to use new provider
   - Add configuration switching (OpenAI vs on-premise)

2. **Vector Database**:
   - Deploy Qdrant for persistent storage
   - Migrate FAISS cache to Qdrant
   - Implement collection management

3. **Docker Orchestration**:
   - Add to main docker-compose.yml
   - Configure networking between services
   - Add volume mounts for model persistence

4. **Testing**:
   - Integration tests with semantic cache
   - Performance benchmarks vs OpenAI
   - Load testing for concurrent requests

5. **Production Readiness**:
   - Add authentication/API keys
   - Implement rate limiting
   - Add monitoring and metrics
   - Configure auto-scaling

## Files Created

- `src/services/embeddings/server.py` - FastAPI service implementation
- `deployment/Dockerfile.embeddings` - Docker container definition
- `deployment/requirements.embeddings.txt` - Python dependencies
- `deployment/docker-compose.embeddings.yml` - Docker Compose service
- `test_embedding_service.py` - Automated test suite
- `docs/project/implementation/EMBEDDING_SERVICE_PROTOTYPE.md` - This documentation

## Validation

✓ Prototype validates the technical approach
✓ All tests passing
✓ Performance meets requirements
✓ Ready for full integration (Phase #1)
