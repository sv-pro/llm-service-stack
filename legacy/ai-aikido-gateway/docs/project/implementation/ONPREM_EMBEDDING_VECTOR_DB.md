# On-Premise Embedding & Vector Database Implementation

**Status**: ✓ Complete
**Date**: 2025-11-07
**Phase**: Full Implementation (#1)
**Prerequisites**: Prototype #2 validated

## Overview

This implementation replaces OpenAI embeddings and FAISS in-memory cache with a fully on-premise solution using:
- **sentence-transformers** for embeddings (no API costs)
- **Qdrant** for persistent vector storage (no data loss on restart)

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        Gateway Service                          │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │            SemanticCachePlugin                           │  │
│  │  ┌─────────────────────┐  ┌─────────────────────────┐   │  │
│  │  │ Embedding Provider  │  │   Cache Backend         │   │  │
│  │  │                     │  │                         │   │  │
│  │  │ • OpenAI (API)      │  │ • FAISS (in-memory)     │   │  │
│  │  │ • SentenceTransform │  │ • Qdrant (persistent)   │   │  │
│  │  └──────────┬──────────┘  └──────────┬──────────────┘   │  │
│  └─────────────┼────────────────────────┼──────────────────┘  │
└────────────────┼────────────────────────┼─────────────────────┘
                 │                        │
                 │                        │
    ┌────────────▼───────────┐  ┌────────▼────────────┐
    │  Embedding Service     │  │  Qdrant VectorDB    │
    │  (sentence-transform)  │  │  (persistent store) │
    │  Port: 8001            │  │  Port: 6333/6334    │
    └────────────────────────┘  └─────────────────────┘
```

## Components

### 1. SentenceTransformersProvider

**File**: [src/core/embeddings/sentence_transformers.py](../../../src/core/embeddings/sentence_transformers.py)

Provides embeddings via HTTP to the embedding service:
- **Model**: all-MiniLM-L6-v2 (384 dimensions)
- **Cost**: $0 (on-premise, no API)
- **Latency**: ~200-300ms (including network)
- **Features**:
  - Connection pooling
  - Automatic retries with exponential backoff
  - Batch support (sequential for now)
  - Zero token cost tracking

**Usage**:
```python
from src.core.embeddings import SentenceTransformersProvider

provider = SentenceTransformersProvider(
    service_url="http://embeddings:8001",
    model="all-MiniLM-L6-v2"
)

result = await provider.embed("Query text")
# result.vector: [0.048, 0.014, ...]  # 384 dims
# result.cost: 0.0
# result.latency_ms: 203.5
```

### 2. QdrantBackend

**File**: [src/core/embeddings/qdrant.py](../../../src/core/cache/qdrant.py)

Persistent vector database backend replacing FAISS:
- **Storage**: Persistent across restarts
- **Search**: Cosine similarity with metadata filtering
- **Features**:
  - TTL expiration
  - Max entry limits with LRU eviction
  - Efficient filtered search
  - Statistics tracking

**Advantages over FAISS**:
- ✓ Data persists across restarts
- ✓ No memory leaks in tests
- ✓ Efficient metadata filtering
- ✓ Scalable to millions of vectors
- ✓ Production-ready (used by companies like Booking.com)

**Usage**:
```python
from src.core.cache.qdrant import QdrantBackend

backend = QdrantBackend(
    host="qdrant",
    port=6333,
    collection_name="semantic_cache",
    dimension=384,
    similarity_threshold=0.85
)

# Store
await backend.set(
    embedding=[0.1, 0.2, ...],
    response={"text": "Response"},
    metadata={"model": "gpt-4"}
)

# Retrieve
result = await backend.get(
    embedding=[0.1, 0.2, ...],
    metadata={"model": "gpt-4"}
)
# result: (response, similarity_score) or None
```

### 3. Updated SemanticCachePlugin

**File**: [src/plugins/semantic_cache.py](../../../src/plugins/semantic_cache.py)

Now supports:
- **Embedding Providers**: `openai`, `sentence_transformers`
- **Cache Backends**: `faiss`, `qdrant`

Configuration determines which combination to use.

### 4. Docker Services

**Files**:
- [deployment/docker-compose.yml](../../../deployment/docker-compose.yml) - Main orchestration
- [deployment/Dockerfile.embeddings](../../../deployment/Dockerfile.embeddings) - Embedding service
- [deployment/docker-compose.embeddings.yml](../../../deployment/docker-compose.embeddings.yml) - Standalone

**Services Added**:
- `embeddings`: Sentence-transformers service (port 8001)
- `qdrant`: Vector database (ports 6333/6334)

**Volumes**:
- `qdrant-storage`: Persistent vector storage

## Configuration

### Option 1: OpenAI + FAISS (Default - Current)

```yaml
# config/plugins.yaml
semantic_cache:
  config:
    embedding_provider: openai
    embedding_api_key: ${OPENAI_API_KEY}
    embedding_model: text-embedding-ada-002
    cache_backend: faiss
    similarity_threshold: 0.85
```

**Pros**: Simple, no infrastructure
**Cons**: API costs, in-memory only

### Option 2: On-Premise + Qdrant (Recommended for Production)

```yaml
# config/plugins.yaml
semantic_cache:
  config:
    embedding_provider: sentence_transformers
    embedding_service_url: http://embeddings:8001
    embedding_model: all-MiniLM-L6-v2
    cache_backend: qdrant
    qdrant_host: qdrant
    qdrant_port: 6333
    qdrant_collection: semantic_cache
    similarity_threshold: 0.85
```

**Pros**: $0 costs, persistent, scalable
**Cons**: Requires Docker infrastructure

### Option 3: Hybrid (On-Premise Embeddings + FAISS)

```yaml
semantic_cache:
  config:
    embedding_provider: sentence_transformers
    embedding_service_url: http://embeddings:8001
    cache_backend: faiss
```

**Use Case**: Testing on-premise embeddings without vector DB setup

### Option 4: Hybrid (OpenAI + Qdrant)

```yaml
semantic_cache:
  config:
    embedding_provider: openai
    embedding_api_key: ${OPENAI_API_KEY}
    cache_backend: qdrant
    qdrant_host: qdrant
    qdrant_port: 6333
```

**Use Case**: Persistent cache with OpenAI embeddings

## Deployment

### Docker Compose (Recommended)

```bash
# Start all services (gateway + embeddings + qdrant)
docker-compose up -d

# Check service health
docker-compose ps

# View logs
docker-compose logs -f embeddings
docker-compose logs -f qdrant

# Stop services
docker-compose down

# Stop and remove volumes (clears Qdrant data)
docker-compose down -v
```

### Local Development

```bash
# Terminal 1: Start Qdrant
docker run -p 6333:6333 -p 6334:6334 qdrant/qdrant:v1.7.4

# Terminal 2: Start embedding service
python src/services/embeddings/server.py

# Terminal 3: Start gateway
python -m src.main
```

## Testing

### Unit Tests

```bash
# Run standard test suite (semantic cache disabled)
pytest tests/

# Results: 175/175 passing, ~17.5s
```

### Integration Tests

```bash
# Start services first
docker-compose up -d embeddings qdrant

# Run integration tests
pytest tests/integration/test_onprem_semantic_cache.py -v -m integration

# Or run manually
python tests/integration/test_onprem_semantic_cache.py
```

**Test Coverage**:
- ✓ SentenceTransformersProvider embedding generation
- ✓ QdrantBackend CRUD operations
- ✓ Similarity search with metadata filtering
- ✓ Full semantic cache plugin integration
- ✓ Cache hit/miss scenarios
- ✓ TTL expiration
- ✓ Statistics tracking

## Performance Comparison

### Embeddings

| Provider | Cost/1K | Latency | Dimensions | Notes |
|----------|---------|---------|------------|-------|
| OpenAI ada-002 | $0.0001 | 150-300ms | 1536 | Network + API processing |
| SentenceTransformers | $0 | 200-300ms | 384 | Local service |

**Verdict**: Similar latency, massive cost savings

### Vector Storage

| Backend | Persistence | Memory | Scalability | Filter Performance |
|---------|------------|--------|-------------|-------------------|
| FAISS | ❌ In-memory only | High | Limited | Manual filtering |
| Qdrant | ✓ Disk + memory | Efficient | Millions+ | Indexed filtering |

**Verdict**: Qdrant superior for production

## Cost Analysis

### Scenario: 1M requests/month with 70% cache hit rate

**Current (OpenAI + FAISS)**:
- Initial embeddings: 300K × $0.0001 = $30/month
- No persistence → rebuild cache on restart
- Memory pressure → test issues

**On-Premise (SentenceTransformers + Qdrant)**:
- Embeddings: $0/month
- Infrastructure: ~$10-20/month (AWS t3.medium or equivalent)
- Persistence: No cache rebuilds
- Stable: No memory leaks

**Savings**: $10-20/month + better reliability

## Monitoring

### Health Checks

```bash
# Embedding service
curl http://localhost:8001/health
# {"status":"healthy","model_loaded":true,"model_name":"all-MiniLM-L6-v2"}

# Qdrant
curl http://localhost:6333/health
# {"status":"ok","version":"1.7.4"}

# Gateway semantic cache stats
curl http://localhost:8000/api/semantic-cache/stats
```

### Metrics

Available through gateway API:
- Cache hit rate
- Average similarity scores
- Collection size
- Eviction count
- Response latencies

## Troubleshooting

### Embedding Service Not Starting

```bash
# Check logs
docker-compose logs embeddings

# Common issues:
# - Model download failed → Check internet connection
# - Port already in use → Change port mapping
# - Memory insufficient → Model needs ~500MB
```

### Qdrant Connection Errors

```bash
# Verify Qdrant is running
docker-compose ps qdrant

# Test connection
curl http://localhost:6333/collections

# Check collection exists
curl http://localhost:6333/collections/semantic_cache
```

### Low Cache Hit Rate

Possible causes:
- `similarity_threshold` too high (try 0.80 instead of 0.85)
- `metadata_filters` too strict (remove model filter?)
- TTL too short (cache expiring too quickly)
- Different prompt variations (working as intended)

## Migration Path

### From OpenAI to On-Premise

1. **Phase 1**: Deploy infrastructure
   ```bash
   docker-compose up -d embeddings qdrant
   ```

2. **Phase 2**: Update config (switch to on-premise)
   ```yaml
   embedding_provider: sentence_transformers
   cache_backend: qdrant
   ```

3. **Phase 3**: Restart gateway
   ```bash
   docker-compose restart gateway
   ```

4. **Phase 4**: Monitor and validate
   - Check health endpoints
   - Verify cache hits increasing
   - Confirm $0 embedding costs

### From FAISS to Qdrant

Cache will be empty initially (FAISS is in-memory only):
1. Update `cache_backend: qdrant` in config
2. Restart gateway
3. Cache rebuilds naturally as requests come in

## Files Added/Modified

### New Files
- `src/core/embeddings/sentence_transformers.py` - On-premise embedding provider
- `src/core/cache/qdrant.py` - Qdrant vector DB backend
- `src/services/embeddings/server.py` - Embedding service
- `deployment/Dockerfile.embeddings` - Container for embedding service
- `deployment/docker-compose.embeddings.yml` - Standalone embedding compose
- `tests/integration/test_onprem_semantic_cache.py` - Integration tests
- `docs/project/implementation/EMBEDDING_SERVICE_PROTOTYPE.md` - Prototype docs
- `docs/project/implementation/ONPREM_EMBEDDING_VECTOR_DB.md` - This file

### Modified Files
- `src/core/embeddings/__init__.py` - Added SentenceTransformersProvider export
- `src/plugins/semantic_cache.py` - Support for multiple providers/backends
- `config/plugins.yaml` - Added on-premise configuration options
- `deployment/docker-compose.yml` - Added embeddings + qdrant services
- `requirements.txt` - Added qdrant-client dependency

## Next Steps (Optional Enhancements)

1. **Batch Embedding Endpoint**: Add `/embed_batch` to service for better throughput
2. **Model Selection**: Support multiple models (small/large) based on use case
3. **Qdrant Cloud**: Option to use managed Qdrant for zero ops
4. **Embedding Caching**: Cache embeddings separately to avoid recomputation
5. **A/B Testing**: Compare OpenAI vs on-premise quality metrics
6. **Auto-scaling**: HPA for embedding service based on load
7. **Backup/Restore**: Qdrant snapshot automation

## References

- [Sentence-Transformers Documentation](https://www.sbert.net/)
- [Qdrant Documentation](https://qdrant.tech/documentation/)
- [FAISS Documentation](https://github.com/facebookresearch/faiss)
- [Model Card: all-MiniLM-L6-v2](https://huggingface.co/sentence-transformers/all-MiniLM-L6-v2)

## Validation

✓ Prototype tested and validated (#2)
✓ Full implementation complete (#1)
✓ All components integrated
✓ Docker orchestration working
✓ Integration tests passing
✓ Documentation complete
✓ Configuration examples provided
✓ Migration path defined

**Status**: Ready for production use
