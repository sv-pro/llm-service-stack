# 🎯 Semantic Cache Demo Guide

This guide shows you how to see the semantic cache in action with real examples.

---

## Prerequisites

1. **OpenAI API Key** - Set your key:
   ```bash
   export OPENAI_API_KEY="sk-..."
   # Or add to .env file
   ```

2. **Gateway Running** - Start the gateway:
   ```bash
   uvicorn src.main:app --reload
   ```

3. **Semantic Cache Enabled** - Already done! ✅ (see [config/plugins.yaml](config/plugins.yaml))

---

## 🚀 Quick Demo (Automated)

Run the demo script to see semantic cache in action:

```bash
# Python version (recommended - colorful output)
python demo_semantic_cache.py

# OR bash version
./demo_semantic_cache.sh
```

### What the Demo Shows

The script sends 6 requests with similar but different wording:

| Request | Prompt | Expected Result |
|---------|--------|----------------|
| 1 | "What is the capital of France?" | ❌ MISS (first request) |
| 2 | "What is the capital of France?" | ✅ HIT (verbatim cache) |
| 3 | "Tell me the capital city of France" | ✅ HIT (semantic ~95%) |
| 4 | "What's the capital of France?" | ✅ HIT (semantic ~98%) |
| 5 | "Which city is the capital of France?" | ✅ HIT (semantic ~92%) |
| 6 | "Can you name the capital city of the French Republic?" | ✅ HIT (semantic ~88%) |

### Example Output

```
🚀 Semantic Cache Demo - AI Aikido Gateway
==================================================

Step 1: Initial request (will be a MISS)

📝 Request 1
Prompt: "What is the capital of France?"

Response: Paris is the capital of France...

📊 Cache Status: MISS
   Latency: 1245.32ms

---

Step 2: Exact same request (verbatim cache HIT)

📝 Request 2 (identical)
Prompt: "What is the capital of France?"

Response: Paris is the capital of France...

📊 Cache Status: HIT
   Cache Type: 📝 verbatim
   Latency: 12.45ms

---

Step 3: Similar but different wording (semantic cache HIT)

📝 Request 3 (similar)
Prompt: "Tell me the capital city of France"

Response: Paris is the capital of France...

📊 Cache Status: HIT
   Cache Type: 🎯 semantic
   Similarity: 0.943 (94.3%) - excellent match!
   Latency: 45.23ms

---
```

---

## 🔬 Manual Testing (Step-by-Step)

### 1. First Request (Cache MISS)

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "What is the capital of France?"}],
    "max_tokens": 50
  }' -i | grep -E "(X-Gateway|HTTP)"
```

**Expected Headers:**
```
HTTP/1.1 200 OK
X-Gateway-Cache-Status: MISS
X-Gateway-Latency-Ms: 1245.32
```

### 2. Second Request - Exact Same (Verbatim Cache HIT)

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "What is the capital of France?"}],
    "max_tokens": 50
  }' -i | grep -E "(X-Gateway|HTTP)"
```

**Expected Headers:**
```
HTTP/1.1 200 OK
X-Gateway-Cache-Status: HIT
X-Gateway-Cache-Type: verbatim
X-Gateway-Latency-Ms: 12.45
```

### 3. Third Request - Similar Wording (Semantic Cache HIT)

```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Tell me the capital city of France"}],
    "max_tokens": 50
  }' -i | grep -E "(X-Gateway|HTTP)"
```

**Expected Headers:**
```
HTTP/1.1 200 OK
X-Gateway-Cache-Status: HIT
X-Gateway-Cache-Type: semantic
X-Gateway-Cache-Similarity: 0.943
X-Gateway-Latency-Ms: 45.23
```

---

## 📊 View Metrics & Analytics

### 1. Check Current Stats

```bash
curl http://localhost:8000/v1/history/stats | jq '.semantic_cache_metrics'
```

**Example Response:**
```json
{
  "enabled": true,
  "embedding_model": "text-embedding-ada-002",
  "embedding_dimension": 1536,
  "size": 5,
  "max_entries": 10000,
  "hits": 4,
  "misses": 1,
  "hit_rate": 0.8,
  "average_similarity": 0.923,
  "evictions": 0,
  "similarity_threshold": 0.85,
  "ttl_seconds": 3600,
  "timeseries": {
    "running": true,
    "sample_interval": 60,
    "retention_hours": 168,
    "total_samples": 12,
    "last_sample_time": 1699564800
  },
  "timeseries_available": true
}
```

### 2. View Time-Series Data (Last Hour)

```bash
curl "http://localhost:8000/v1/cache/semantic/timeseries?limit=60" | jq
```

### 3. View Dashboard

Open your browser:
- **Cache Analytics:** http://localhost:3000/cache-analytics
- **Semantic Time-Series Chart:** Scroll down to "📈 Hit Rate Trends"

---

## 🎛️ Interactive Experiments

### Experiment 1: Adjust Similarity Threshold

**Lower threshold (more permissive):**
```bash
curl -X POST http://localhost:8000/v1/cache/semantic/threshold \
  -H "Content-Type: application/json" \
  -d '{"similarity_threshold": 0.75}'
```

Now try very different wording:
```bash
curl -X POST http://localhost:8000/v1/chat/completions \
  -H "Content-Type: application/json" \
  -d '{
    "model": "gpt-3.5-turbo",
    "messages": [{"role": "user", "content": "Name the capital of the French nation"}],
    "max_tokens": 50
  }' -i | grep "X-Gateway-Cache"
```

### Experiment 2: Test Language Variations

Send requests in different styles:
- "What is the capital of France?"
- "Tell me France's capital"
- "Capital of France?"
- "Which city is France's capital?"
- "France capital city name?"

All should hit the semantic cache with varying similarity scores!

### Experiment 3: Watch Metrics Accumulate

```bash
# Run demo
python demo_semantic_cache.py

# Wait 60 seconds for metrics to be sampled
sleep 60

# Query time-series
curl "http://localhost:8000/v1/cache/semantic/timeseries?limit=10" | jq '.data[] | {timestamp: .timestamp, hit_rate: .hit_rate, similarity: .average_similarity}'
```

---

## 🎨 Dashboard Visualization

### Start the Dashboard

```bash
cd dashboard
npm install  # First time only
npm run dev
```

Open http://localhost:3000/cache-analytics

### What You'll See

1. **Semantic Cache Stats Panel**
   - Current hit rate
   - Average similarity score
   - Index size and evictions
   - Interactive threshold slider

2. **Time-Series Chart** (NEW!)
   - Blue line: Hit rate over time
   - Green line: Average similarity score
   - Time range selector (1h, 6h, 24h)
   - Auto-refreshes every 30 seconds

3. **Transparency Headers in Browser DevTools**
   - Open Network tab
   - Look for `X-Gateway-Cache-*` headers

---

## 🔍 Understanding Results

### Cache Types

| Type | Description | When It Happens |
|------|-------------|----------------|
| **verbatim** | Exact match | Request is 100% identical (same JSON) |
| **semantic** | Similarity match | Request has similar meaning (>85% similarity) |

### Similarity Scores

| Score | Quality | Meaning |
|-------|---------|---------|
| 1.00 | Perfect | Identical semantic meaning |
| 0.95+ | Excellent | Very similar questions |
| 0.90-0.94 | Very Good | Similar with minor variations |
| 0.85-0.89 | Good | Related questions (default threshold) |
| 0.80-0.84 | Acceptable | Somewhat related |
| <0.80 | Poor | Different questions (MISS) |

### Latency Impact

| Operation | Typical Latency |
|-----------|----------------|
| Cache MISS (LLM call) | 1000-3000ms |
| Verbatim Cache HIT | 5-20ms |
| Semantic Cache HIT | 40-100ms (includes embedding + FAISS search) |

**Savings:** Even semantic cache hits are **10-75x faster** than LLM calls!

---

## 🐛 Troubleshooting

### Problem: "Semantic cache plugin is not available"

**Solution:** Check if semantic cache is enabled:
```bash
grep "enabled:" config/plugins.yaml | grep -A 5 semantic_cache
```

Ensure `enabled: true` on line 79.

### Problem: No semantic hits, only verbatim

**Possible causes:**
1. **Threshold too high** - Lower it:
   ```bash
   curl -X POST http://localhost:8000/v1/cache/semantic/threshold \
     -d '{"similarity_threshold": 0.80}'
   ```

2. **Not enough data** - Send more similar requests

3. **Questions too different** - Try more similar wording

### Problem: "OPENAI_API_KEY not set"

**Solution:**
```bash
export OPENAI_API_KEY="sk-..."
# Then restart gateway
```

### Problem: Dashboard shows "No data available"

**Solution:** Wait at least 60 seconds after first request for metrics to be sampled.

---

## 📈 Real-World Use Cases

### 1. Customer Support Chatbot
```bash
# These all hit the same cache entry:
"How do I reset my password?"
"I forgot my password, what should I do?"
"Password reset instructions please"
"Can you help me reset my password?"
```

### 2. Product Recommendations
```bash
# Similar intent, semantic cache match:
"Recommend a laptop for programming"
"Best laptop for software development?"
"What laptop should I buy for coding?"
```

### 3. FAQ Matching
```bash
# All match the same FAQ:
"What are your shipping rates?"
"How much does shipping cost?"
"Shipping price?"
"Cost of delivery?"
```

---

## 🎓 Key Takeaways

1. ✅ **Semantic cache catches similar questions** - Not just exact matches!
2. ✅ **Massive latency reduction** - 40-100ms vs 1000-3000ms
3. ✅ **Cost savings** - Same response reused for similar questions
4. ✅ **Tunable threshold** - Adjust strictness without code changes
5. ✅ **Full transparency** - Headers show cache type and similarity score
6. ✅ **Time-series tracking** - Monitor cache performance over time

---

## 🚀 Next Steps

1. **Try your own prompts** - Test with domain-specific questions
2. **Tune the threshold** - Find the sweet spot for your use case
3. **Monitor the dashboard** - Watch hit rates improve over time
4. **Check the logs** - See semantic cache decisions in real-time:
   ```bash
   tail -f logs/gateway.log | grep semantic
   ```

---

**Need Help?** Check [docs/project/design/SEMANTIC_TIMESERIES.md](docs/project/design/SEMANTIC_TIMESERIES.md) for full technical details.
