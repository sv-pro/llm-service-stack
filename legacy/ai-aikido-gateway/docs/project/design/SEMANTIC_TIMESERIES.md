# Semantic Cache Time-Series Design

## Overview

Extend the semantic cache system to track metrics over time, enabling trend analysis and dashboard visualizations.

## Requirements

1. **Historical Tracking**: Record semantic cache metrics at regular intervals
2. **API Access**: Expose time-series data via REST endpoints
3. **Dashboard Visualization**: Display hit rate trends with charts
4. **Transparency**: Include semantic cache info in response headers
5. **Performance**: Minimal overhead, efficient queries

## Data Model

### Metrics Snapshot Schema

```sql
CREATE TABLE semantic_cache_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp INTEGER NOT NULL,           -- Unix timestamp
    hits INTEGER NOT NULL,                -- Total hits since startup
    misses INTEGER NOT NULL,              -- Total misses since startup
    hit_rate REAL NOT NULL,               -- Calculated hit rate (0.0-1.0)
    average_similarity REAL,              -- Average similarity score for hits
    similarity_threshold REAL NOT NULL,   -- Current threshold
    index_size INTEGER NOT NULL,          -- Number of entries in FAISS index
    evictions INTEGER NOT NULL,           -- Total evictions
    embedding_model TEXT NOT NULL         -- Model name (e.g., text-embedding-ada-002)
);

CREATE INDEX idx_semantic_metrics_timestamp ON semantic_cache_metrics(timestamp);
```

### Sample Intervals

- **Real-time**: Dashboard polls `/v1/history/stats` every 5 seconds for current state
- **Time-series**: Background task samples every 60 seconds, stores in DB
- **Retention**: Keep 24 hours (1440 samples), then aggregate to hourly for 7 days

## API Endpoints

### GET /v1/cache/semantic/timeseries

Query time-series data with time range and granularity.

**Query Parameters:**
- `start`: Start timestamp (ISO 8601 or Unix epoch)
- `end`: End timestamp (default: now)
- `granularity`: Sampling interval (`1m`, `5m`, `1h`, default: `1m`)
- `limit`: Max data points (default: 100)

**Response:**
```json
{
  "object": "timeseries",
  "granularity": "1m",
  "start": 1699564800,
  "end": 1699568400,
  "data": [
    {
      "timestamp": 1699564800,
      "hits": 42,
      "misses": 18,
      "hit_rate": 0.70,
      "average_similarity": 0.89,
      "similarity_threshold": 0.85,
      "index_size": 156,
      "evictions": 2,
      "embedding_model": "text-embedding-ada-002"
    }
  ],
  "count": 60
}
```

### PATCH /v1/history/stats (Enhancement)

Add time-series metadata to existing stats endpoint:

```json
{
  "total_requests": 1234,
  "cache_metrics": { ... },
  "semantic_cache_metrics": {
    "enabled": true,
    "hits": 42,
    "timeseries_available": true,
    "last_sample_time": 1699564800
  }
}
```

## Backend Implementation

### 1. Metrics Recorder Service

```python
# src/core/cache/semantic_timeseries.py

class SemanticMetricsRecorder:
    """Records semantic cache metrics to SQLite time-series DB."""

    def __init__(self, db_path: str, sample_interval: int = 60):
        self.db_path = db_path
        self.sample_interval = sample_interval
        self.task = None

    async def start(self, cache_backend: SemanticCacheBackend):
        """Start background sampling task."""
        self.task = asyncio.create_task(self._sample_loop(cache_backend))

    async def _sample_loop(self, cache_backend: SemanticCacheBackend):
        while True:
            await asyncio.sleep(self.sample_interval)
            stats = cache_backend.get_stats()
            await self._record_sample(stats)

    async def _record_sample(self, stats: Dict[str, Any]):
        """Insert metrics snapshot into DB."""
        # INSERT INTO semantic_cache_metrics ...

    async def query_timeseries(
        self,
        start: Optional[int] = None,
        end: Optional[int] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Query time-series data."""
        # SELECT * FROM semantic_cache_metrics WHERE timestamp BETWEEN ...
```

### 2. Integration with SemanticCachePlugin

```python
# src/plugins/semantic_cache.py

class SemanticCachePlugin(BasePlugin):
    def __init__(self, ...):
        # ... existing init ...

        # Initialize metrics recorder
        if config.get("enable_timeseries", True):
            db_path = config.get("timeseries_db", "./data/semantic_metrics.db")
            self.metrics_recorder = SemanticMetricsRecorder(db_path)

    async def on_startup(self):
        # ... existing startup ...

        if hasattr(self, "metrics_recorder"):
            await self.metrics_recorder.start(self.cache_backend)
```

### 3. API Route

```python
# src/api/routes.py

@router.get("/cache/semantic/timeseries")
async def get_semantic_timeseries(
    request: Request,
    start: Optional[int] = None,
    end: Optional[int] = None,
    limit: int = 100,
):
    semantic_cache_plugin = getattr(request.app.state, "semantic_cache_plugin", None)

    if not semantic_cache_plugin or not semantic_cache_plugin.enabled:
        raise HTTPException(503, "Semantic cache not available")

    recorder = getattr(semantic_cache_plugin, "metrics_recorder", None)
    if not recorder:
        raise HTTPException(503, "Time-series tracking not enabled")

    data = await recorder.query_timeseries(start, end, limit)

    return {
        "object": "timeseries",
        "start": start or (int(time.time()) - 3600),
        "end": end or int(time.time()),
        "data": data,
        "count": len(data)
    }
```

## Transparency Headers

Add semantic cache info to response headers when semantic cache is involved:

```python
# src/plugins/semantic_cache.py

async def before_request(self, ctx: RequestContext):
    # ... existing logic ...

    if result:  # Cache hit
        # Add transparency header
        ctx.metadata["semantic_cache_hit"] = True
        ctx.metadata["semantic_similarity"] = similarity_score
```

```python
# src/plugins/transparency.py

async def after_response(self, ctx: RequestContext):
    headers = {}

    # ... existing headers ...

    # Semantic cache headers
    if ctx.metadata.get("semantic_cache_hit"):
        headers["X-Cache-Type"] = "semantic"
        headers["X-Cache-Similarity"] = f"{ctx.metadata.get('semantic_similarity', 0):.3f}"

    ctx.metadata["transparency_headers"] = headers
```

## Dashboard Updates

### 1. Time-Series Chart Component

```jsx
// dashboard/src/components/cache/SemanticTimeSeriesChart.jsx

import { LineChart, Line, XAxis, YAxis, Tooltip, Legend } from 'recharts';

const SemanticTimeSeriesChart = ({ data }) => {
  return (
    <div className="timeseries-chart">
      <h3>Semantic Cache Hit Rate (Last Hour)</h3>
      <LineChart width={600} height={300} data={data}>
        <XAxis dataKey="timestamp" tickFormatter={formatTime} />
        <YAxis />
        <Tooltip />
        <Legend />
        <Line
          type="monotone"
          dataKey="hit_rate"
          stroke="#8884d8"
          name="Hit Rate"
        />
        <Line
          type="monotone"
          dataKey="average_similarity"
          stroke="#82ca9d"
          name="Avg Similarity"
        />
      </LineChart>
    </div>
  );
};
```

### 2. Integrate into Cache Analytics

```jsx
// dashboard/src/pages/CacheAnalytics.jsx

const CacheAnalytics = () => {
  const [timeseriesData, setTimeseriesData] = useState([]);

  useEffect(() => {
    const fetchTimeseries = async () => {
      const response = await fetch('/v1/cache/semantic/timeseries?limit=60');
      const data = await response.json();
      setTimeseriesData(data.data);
    };

    fetchTimeseries();
    const interval = setInterval(fetchTimeseries, 30000); // Refresh every 30s

    return () => clearInterval(interval);
  }, []);

  return (
    <div>
      <SemanticStatsPanel {...existingProps} />
      {timeseriesData.length > 0 && (
        <SemanticTimeSeriesChart data={timeseriesData} />
      )}
    </div>
  );
};
```

## Testing Strategy

1. **Unit Tests**: Test metrics recorder sampling and queries
2. **Integration Tests**: Verify API endpoints return correct data
3. **E2E Tests**: Dashboard loads and displays charts
4. **Load Tests**: Ensure minimal overhead from sampling

## Performance Considerations

- **Sampling Overhead**: ~1ms per sample (DB insert), runs in background
- **Query Performance**: Index on timestamp enables fast range queries
- **Storage**: ~100 bytes/sample × 1440/day = ~140KB/day
- **Retention**: Auto-purge data older than 7 days

## Future Enhancements

1. **Aggregation**: Hourly/daily rollups for long-term trends
2. **Alerts**: Notify when hit rate drops below threshold
3. **Comparison**: Show semantic vs verbatim hit rates side-by-side
4. **Export**: CSV/JSON export for external analysis
