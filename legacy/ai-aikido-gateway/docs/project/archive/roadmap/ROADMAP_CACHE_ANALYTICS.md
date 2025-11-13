# Feature Roadmap: Cache & Analytics

## 🎯 Two-Track Development Plan

---

## Track 1: Caching System 🚀

### Phase 1: Simple In-Memory Cache (NOW)
**Goal:** Immediate cost savings on duplicate requests

**Implementation:**
- In-memory dictionary cache
- Cache key: `hash(model + messages_json)`
- Store full response object
- TTL: 1 hour (configurable)
- LRU eviction (max 1000 entries)

**Features:**
- ✅ Cache identical requests
- ✅ Instant responses on cache hits
- ✅ Track hit/miss statistics
- ✅ Plugin-based (enable/disable via config)
- ✅ Zero external dependencies

**Files to Create:**
- `src/plugins/cache.py` - CachePlugin implementation
- `tests/test_cache.py` - Comprehensive tests
- Update `config/plugins.yaml` - Add cache configuration

**Metrics to Track:**
```python
{
    "cache_hits": 0,
    "cache_misses": 0,
    "hit_rate": 0.0,
    "total_requests": 0,
    "cached_tokens_saved": 0,
    "estimated_cost_saved": 0.0
}
```

**Configuration:**
```yaml
- name: cache
  enabled: true
  priority: 5  # Run early in pipeline
  class: plugins.cache.CachePlugin
  config:
    backend: memory
    ttl_seconds: 3600
    max_entries: 1000
    eviction_policy: lru
```

---

### Phase 2: Redis-Backed Cache (NEXT)
**Goal:** Persistent, distributed caching across gateway instances

**Implementation:**
- Redis as cache backend
- Same cache key strategy
- Configurable TTL per model
- Support for cache invalidation
- Shared cache across multiple gateway instances

**Features:**
- ✅ Persistent cache (survives restarts)
- ✅ Distributed caching (multiple gateways)
- ✅ Pattern-based cache invalidation
- ✅ Per-model TTL configuration
- ✅ Cache warming strategies

**Configuration:**
```yaml
- name: cache
  enabled: true
  priority: 5
  class: plugins.cache.CachePlugin
  config:
    backend: redis  # or 'memory'
    redis_url: ${REDIS_URL}
    ttl_seconds: 3600
    max_entries: 10000
    eviction_policy: lru
    
    # Advanced: Per-model TTL
    model_ttl:
      gpt-4: 7200        # 2 hours for expensive models
      gpt-3.5-turbo: 1800  # 30 min for cheap models
      claude-3-opus: 7200
      claude-3-haiku: 1800
```

**Additional Features:**
- Cache warming on startup (preload common requests)
- Cache stats endpoints: `/v1/cache/stats`, `/v1/cache/clear`
- Configurable cache bypass headers: `X-Bypass-Cache: true`
- Smart invalidation (by model, by time range, by pattern)

**Files to Add:**
- `src/core/cache_backends.py` - Abstract backend interface
  - `MemoryCacheBackend`
  - `RedisCacheBackend`
- Update `src/plugins/cache.py` - Support multiple backends
- `requirements.txt` - Add `redis>=5.0.0` (optional)

**Redis Schema:**
```
Key format: aikido:cache:{model}:{content_hash}
Value: JSON serialized response
Expiry: TTL in seconds

Stats key: aikido:cache:stats
Value: Hash with hit/miss counts
```

---

## Track 2: Cost Monitoring & Analytics 📊

### Phase 1: Cost Monitor Plugin (PRIORITY)
**Goal:** Track both predicted and actual costs per request

**Implementation:**
- Plugin that runs `after_response`
- Calculate cost based on token usage + model pricing
- Store in SQLite database
- Track both predicted (upfront) and actual (from API response) costs

**Cost Calculation:**
```python
# Predicted (before request)
predicted_cost = estimate_tokens(messages) * model_price

# Actual (from response)
actual_cost = (
    response.usage.prompt_tokens * model.prompt_price +
    response.usage.completion_tokens * model.completion_price
)

# Variance tracking
variance = actual_cost - predicted_cost
```

**Features:**
- ✅ Track costs per request
- ✅ Compare predicted vs actual costs
- ✅ Store with metadata labels (app, user, model, api_key)
- ✅ Budget alerts (daily/weekly/monthly)
- ✅ Cost breakdown by model
- ✅ Identify cost optimization opportunities

**Database Schema:**
```sql
CREATE TABLE cost_records (
    id INTEGER PRIMARY KEY,
    request_id TEXT UNIQUE,
    timestamp DATETIME,
    model TEXT,
    
    -- Token usage
    prompt_tokens INTEGER,
    completion_tokens INTEGER,
    total_tokens INTEGER,
    
    -- Costs
    predicted_cost REAL,
    actual_cost REAL,
    variance REAL,
    
    -- Metadata labels
    app_label TEXT,
    user_label TEXT,
    api_key_hash TEXT,
    environment TEXT,
    
    -- Request details
    cached BOOLEAN DEFAULT FALSE,
    latency_ms INTEGER,
    error BOOLEAN DEFAULT FALSE
);

CREATE INDEX idx_timestamp ON cost_records(timestamp);
CREATE INDEX idx_model ON cost_records(model);
CREATE INDEX idx_app_label ON cost_records(app_label);
CREATE INDEX idx_api_key ON cost_records(api_key_hash);
```

**Configuration:**
```yaml
- name: cost_monitor
  enabled: true
  priority: 30  # Run after cache, after response
  class: plugins.cost_monitor.CostMonitorPlugin
  config:
    storage_backend: sqlite
    db_path: ./data/costs.db
    
    # Model pricing (USD per 1M tokens)
    pricing:
      gpt-4:
        prompt: 30.00
        completion: 60.00
      gpt-4-turbo:
        prompt: 10.00
        completion: 30.00
      gpt-3.5-turbo:
        prompt: 0.50
        completion: 1.50
      claude-3-opus-20240229:
        prompt: 15.00
        completion: 75.00
      claude-3-sonnet-20240229:
        prompt: 3.00
        completion: 15.00
      claude-3-haiku-20240307:
        prompt: 0.25
        completion: 1.25
    
    # Budget alerts
    budgets:
      daily: 100.00    # $100/day
      weekly: 500.00   # $500/week
      monthly: 2000.00 # $2000/month
    
    alert_threshold: 0.8  # Alert at 80% of budget
```

**API Endpoints:**
```python
GET /v1/costs/summary
  # Overall cost summary
  
GET /v1/costs/daily?start=2025-10-01&end=2025-10-31
  # Daily breakdown
  
GET /v1/costs/by-model
  # Cost grouped by model
  
GET /v1/costs/by-label?label=app&value=my-app
  # Cost grouped by metadata label
  
GET /v1/costs/records?limit=100&offset=0
  # Paginated cost records
  
POST /v1/costs/export
  # Export to CSV/JSON
```

**Files to Create:**
- `src/plugins/cost_monitor.py` - Cost tracking plugin
- `src/core/cost_calculator.py` - Cost calculation logic
- `src/core/database.py` - SQLite connection management
- `tests/test_cost_monitor.py` - Cost tracking tests

---

### Phase 2: Analytics Plugin (Dashboard Backend)
**Goal:** Aggregate and analyze request/cost data by metadata labels

**Implementation:**
- Separate analytics plugin or extend cost monitor
- Query data grouped by: app, api_key, model, environment, time
- Calculate metrics: total cost, requests, avg latency, error rate
- Support time-series queries for trending

**Features:**
- ✅ Group by any metadata label
- ✅ Time-series data (hourly, daily, weekly, monthly)
- ✅ Cost attribution (which app/user costs most?)
- ✅ Model usage patterns
- ✅ Cache effectiveness per app
- ✅ Anomaly detection (sudden cost spikes)

**Query Examples:**
```python
# Cost by app
GET /v1/analytics/cost?group_by=app_label&period=7d

# Requests by model over time
GET /v1/analytics/requests?group_by=model&period=30d&granularity=daily

# Top cost drivers
GET /v1/analytics/top-costs?limit=10&period=7d

# Cache effectiveness
GET /v1/analytics/cache-stats?group_by=app_label

# Cost trends
GET /v1/analytics/trends?metric=cost&period=90d
```

**Response Format:**
```json
{
  "period": "7d",
  "group_by": "app_label",
  "data": [
    {
      "label": "mobile-app",
      "total_cost": 450.23,
      "total_requests": 12450,
      "avg_cost_per_request": 0.036,
      "cached_requests": 3200,
      "cache_hit_rate": 0.257,
      "cost_saved_by_cache": 115.20,
      "models_used": ["gpt-3.5-turbo", "gpt-4"],
      "error_rate": 0.002
    },
    {
      "label": "web-app",
      "total_cost": 312.45,
      "total_requests": 8900,
      "avg_cost_per_request": 0.035,
      "cached_requests": 1800,
      "cache_hit_rate": 0.202,
      "cost_saved_by_cache": 63.40,
      "models_used": ["claude-3-sonnet"],
      "error_rate": 0.001
    }
  ]
}
```

**Configuration:**
```yaml
- name: analytics
  enabled: true
  priority: 35
  class: plugins.analytics.AnalyticsPlugin
  config:
    db_path: ./data/costs.db  # Share with cost_monitor
    
    # Metadata labels to track
    track_labels:
      - app_label
      - user_label
      - environment
      - api_key_hash
    
    # Aggregation intervals
    aggregation_intervals:
      - hourly
      - daily
      - weekly
      - monthly
    
    # Alert thresholds
    anomaly_detection:
      enabled: true
      cost_spike_threshold: 2.0  # 2x normal
      error_rate_threshold: 0.05  # 5%
```

---

### Phase 3: Unified Dashboard UI (Merged with Reference Client)
**Goal:** Single web application for both testing and analytics/monitoring

**Why Merge?**
- Same workflow: test → monitor costs → analyze
- Shared authentication/session
- Consistent UI/UX
- Less context switching
- Simpler deployment (one app instead of two)

**Implementation:**
- Evolve existing `client/` into full-featured dashboard
- Keep Node.js/Express backend (or upgrade to Next.js)
- Add navigation between screens
- Real-time updates via Server-Sent Events (SSE)
- Interactive charts and analytics

**Application Structure:**

```
dashboard/  (evolved from client/)
├── package.json
├── server.js (or next.config.js if upgrading to Next.js)
├── public/
│   ├── index.html           # Main app shell (SPA)
│   ├── app.js              # Main app logic + routing
│   ├── styles.css          # Global styles
│   └── screens/            # Individual screen modules
│       ├── playground.js   # Chat playground (current client)
│       ├── overview.js     # Dashboard overview
│       ├── costs.js        # Cost analytics
│       ├── requests.js     # Request history
│       ├── cache.js        # Cache analytics
│       └── settings.js     # Configuration
└── README.md
```

**Navigation Structure:**

```
┌─────────────────────────────────────────┐
│  🥋 AI Aikido Gateway Dashboard         │
├─────────────────────────────────────────┤
│  [Playground] [Overview] [Costs]        │
│  [Requests] [Cache] [Settings]          │
├─────────────────────────────────────────┤
│                                         │
│         SCREEN CONTENT HERE             │
│                                         │
└─────────────────────────────────────────┘
```

**Screen 1: Playground (Current Reference Client)**
- Keep existing chat interface
- Add "View in History" button after each request
- Show mini-stats widget (cost, tokens, cached?)
- Quick access to recent requests

**Screen 2: Overview Dashboard (PRIMARY FOCUS)**

**Goal:** Actionable insights for cost optimization with clear recommendations

**Core Philosophy:**
- Show what's costing money (top requests/groups)
- Show optimization opportunities (caching potential)
- Give clear recommendations on what to fix
- Warn about anomalies or wasteful patterns

**Layout:**

```
┌─────────────────────────────────────────────────────────────┐
│  Overview Dashboard                         [Last 7 days ▼] │
├─────────────────────────────────────────────────────────────┤
│  💰 Total Cost: $234.56    📊 Requests: 12,450             │
│  ⚡ Cache Saved: $89.12    📈 Cache Hit: 38%               │
├─────────────────────────────────────────────────────────────┤
│  🎯 Top Optimization Opportunities                          │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ ⚠️  "Write blog post about X" - $45.23/week         │   │
│  │    → 23 identical requests, 0% cached               │   │
│  │    → 💡 Enable caching to save $45/week             │   │
│  │    [View Details] [Enable Cache for This]           │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │ 🔥 App: "mobile-app" using GPT-4 for simple tasks   │   │
│  │    → $89/week, avg 150 tokens/request               │   │
│  │    → 💡 Switch to GPT-3.5-turbo to save $67/week    │   │
│  │    [View All Requests] [Add Routing Rule]           │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │ ⚡ Frequent pattern: "Summarize this: ..."          │   │
│  │    → $34/week, 156 similar requests                 │   │
│  │    → 💡 Cache similar summaries to save $28/week    │   │
│  │    [View Pattern] [Configure Smart Cache]           │   │
│  └─────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│  📊 Top Requests by Cost                                    │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Request Pattern              Total   Avg/Call  Cached│   │
│  ├─────────────────────────────────────────────────────┤   │
│  │ "Write blog about X"        $45.23   $1.97    0%   │   │
│  │ "Translate X to Y"          $38.90   $0.15    45%  │   │
│  │ "Code review for X"         $34.56   $2.88    12%  │   │
│  │ "Summarize article X"       $28.12   $0.18    67%  │   │
│  │ "Generate test cases"       $23.45   $1.56    0%   │   │
│  └─────────────────────────────────────────────────────┘   │
├─────────────────────────────────────────────────────────────┤
│  📈 Top Groups by Cost                                      │
│  ┌─────────────────────────────────────────────────────┐   │
│  │ Group By: [App] [Model] [User] [Request Type]       │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │ Group               Total   Avg/Call  Non-Cache  💰  │   │
│  ├─────────────────────────────────────────────────────┤   │
│  │ App: mobile-app    $123.45   $0.24    $0.45   $34  │   │
│  │ App: web-app        $89.12   $0.18    $0.32   $28  │   │
│  │ Model: gpt-4        $78.90   $1.85    $1.85    $0  │   │
│  │ Model: gpt-3.5      $45.67   $0.12    $0.19   $18  │   │
│  │ User: user-123      $34.56   $0.15    $0.28   $12  │   │
│  └─────────────────────────────────────────────────────┘   │
│  💰 = Money saved by caching                                │
├─────────────────────────────────────────────────────────────┤
│  📊 Cost Breakdown & Savings                                │
│  ┌────────────┬────────────┬────────────────────────────┐  │
│  │ Pie Chart  │ Line Chart │ Bar Chart                  │  │
│  │ Cost by    │ Cost over  │ Cache savings by group     │  │
│  │ Model      │ time       │                            │  │
│  └────────────┴────────────┴────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

**Key Metrics to Display:**

**1. Total Cost Metrics**
```javascript
{
  total_cost: 234.56,              // Total spend in period
  total_requests: 12450,           // All requests
  cached_requests: 4730,           // Cache hits
  api_requests: 7720,              // Actual API calls
  cache_hit_rate: 0.38,            // 38%
  cache_savings: 89.12,            // Money saved by cache
  avg_cost_per_request: 0.019,    // $234.56 / 12450
  avg_cost_per_api_call: 0.030    // $234.56 / 7720 (non-cached)
}
```

**2. Top Requests by Cost**
```javascript
[
  {
    pattern: "Write blog post about X",  // Detected pattern
    request_count: 23,
    total_cost: 45.23,
    avg_cost_per_call: 1.97,           // Total / all calls
    avg_cost_per_api_call: 1.97,       // Total / non-cached calls
    cached_count: 0,
    cache_hit_rate: 0.0,
    cache_savings: 0.0,
    potential_savings: 45.23,           // If 100% cached after first
    
    // Optimization recommendations
    recommendation: {
      type: "enable_caching",
      priority: "high",
      message: "23 identical requests with 0% cache hit rate",
      action: "Enable caching to save $45/week",
      potential_savings_weekly: 45.23
    },
    
    // For drilling down
    sample_request_ids: ["req-123", "req-456"],
    groups: {
      by_app: {"mobile-app": 15, "web-app": 8},
      by_model: {"gpt-4": 23}
    }
  }
]
```

**3. Top Groups by Cost**
```javascript
{
  group_by: "app_label",  // or "model", "user_label", etc.
  groups: [
    {
      label: "mobile-app",
      total_cost: 123.45,
      request_count: 515,
      cached_count: 234,
      api_call_count: 281,
      
      // Key metrics
      avg_cost_per_call: 0.24,        // Total / all requests
      avg_cost_per_api_call: 0.44,    // Total / non-cached
      cache_hit_rate: 0.45,
      cache_savings: 34.12,            // Actual savings
      
      // Model breakdown
      models_used: {
        "gpt-4": {cost: 89.23, count: 78},
        "gpt-3.5": {cost: 34.22, count: 437}
      },
      
      // Warnings & recommendations
      warnings: [
        {
          type: "expensive_model_for_simple_tasks",
          message: "Using GPT-4 for 78 requests averaging 150 tokens",
          potential_savings: 67.00,
          recommendation: "Switch simple requests to GPT-3.5-turbo"
        }
      ]
    }
  ]
}
```

**4. Optimization Recommendations (Priority Sorted)**
```javascript
{
  recommendations: [
    {
      id: "rec-1",
      priority: "high",          // high, medium, low
      type: "caching",           // caching, model_routing, rate_limiting
      title: "Enable caching for repeated requests",
      description: "23 identical 'Write blog post' requests with 0% cache hit",
      
      // Impact
      current_cost_weekly: 45.23,
      potential_savings_weekly: 45.23,
      savings_percentage: 100,
      affected_requests: 23,
      
      // Context
      pattern: "Write blog post about X",
      apps_affected: ["mobile-app"],
      models_affected: ["gpt-4"],
      
      // Actions
      actions: [
        {
          label: "View Requests",
          link: "/requests?pattern=write-blog"
        },
        {
          label: "Configure Cache",
          link: "/settings/cache"
        }
      ]
    },
    {
      id: "rec-2",
      priority: "high",
      type: "model_routing",
      title: "Switch to cheaper model for simple tasks",
      description: "mobile-app using GPT-4 for requests averaging 150 tokens",
      
      current_cost_weekly: 89.00,
      potential_savings_weekly: 67.00,
      savings_percentage: 75,
      affected_requests: 78,
      
      current_model: "gpt-4",
      recommended_model: "gpt-3.5-turbo",
      
      actions: [
        {
          label: "View Affected Requests",
          link: "/requests?app=mobile-app&model=gpt-4&tokens<200"
        },
        {
          label: "Add Routing Rule",
          link: "/settings/routing"
        }
      ]
    },
    {
      id: "rec-3",
      priority: "medium",
      type: "caching",
      title: "Improve cache hit rate for translations",
      description: "Translation requests only 45% cached, potential for more",
      
      current_cost_weekly: 38.90,
      potential_savings_weekly: 21.40,
      savings_percentage: 55,
      affected_requests: 259,
      
      current_cache_hit_rate: 0.45,
      potential_cache_hit_rate: 0.80,
      
      actions: [
        {
          label: "View Translation Pattern",
          link: "/requests?pattern=translate"
        },
        {
          label: "Configure Smart Cache",
          link: "/settings/cache/patterns"
        }
      ]
    }
  ]
}
```

**5. Warnings & Anomalies**
```javascript
{
  warnings: [
    {
      type: "cost_spike",
      severity: "high",
      message: "Cost increased 250% in last 24h",
      current: 89.45,
      previous: 25.67,
      increase_percentage: 248,
      likely_cause: "App: mobile-app started using GPT-4",
      affected_group: "mobile-app"
    },
    {
      type: "cache_effectiveness_drop",
      severity: "medium",
      message: "Cache hit rate dropped from 45% to 28%",
      current_hit_rate: 0.28,
      previous_hit_rate: 0.45,
      likely_cause: "New request patterns not matching cache",
      affected_group: "web-app"
    },
    {
      type: "expensive_repeated_requests",
      severity: "high",
      message: "Same expensive request called 45 times",
      request_pattern: "Generate comprehensive report for X",
      cost_per_request: 3.45,
      total_cost: 155.25,
      cached: false,
      recommendation: "Enable caching or review if all calls necessary"
    }
  ]
}
```

**Recommendation Engine Logic:**

**Opportunity #1: Low Cache Hit Rate**
```python
if request_count > 10 and cache_hit_rate < 0.2:
    potential_savings = total_cost * 0.9  # 90% of first request
    recommendation = {
        "type": "enable_caching",
        "priority": "high" if potential_savings > 20 else "medium",
        "message": f"{request_count} requests with {cache_hit_rate:.0%} cache hit",
        "action": "Enable caching to save ${potential_savings:.2f}/week"
    }
```

**Opportunity #2: Expensive Model for Simple Tasks**
```python
if model == "gpt-4" and avg_tokens < 300:
    cost_gpt4 = total_cost
    cost_gpt35 = total_cost * (0.5 / 30.0)  # Price ratio
    potential_savings = cost_gpt4 - cost_gpt35
    
    recommendation = {
        "type": "model_routing",
        "priority": "high" if potential_savings > 50 else "medium",
        "message": f"Using GPT-4 for {request_count} simple requests",
        "action": f"Switch to GPT-3.5-turbo to save ${potential_savings:.2f}/week"
    }
```

**Opportunity #3: Repeated Similar Requests**
```python
# Detect similar requests (fuzzy matching)
similar_groups = group_by_similarity(requests, threshold=0.8)

for group in similar_groups:
    if len(group) > 5 and group.cache_hit_rate < 0.5:
        potential_savings = sum(r.cost for r in group[1:])  # All but first
        
        recommendation = {
            "type": "smart_caching",
            "priority": "medium",
            "message": f"{len(group)} similar requests, only {group.cache_hit_rate:.0%} cached",
            "action": f"Configure smart cache to save ${potential_savings:.2f}/week"
        }
```

**Opportunity #4: Unused API Keys / Apps**
```python
for api_key in api_keys:
    if api_key.cost < 1.0 and api_key.last_used > 30_days_ago:
        recommendation = {
            "type": "cleanup",
            "priority": "low",
            "message": f"API key '{api_key.name}' unused for 30+ days",
            "action": "Review and potentially deactivate"
        }
```

**Implementation Priority:**

1. **Data Collection** (Backend - Phase 3)
   - Store requests with metadata (app, user, model, cost)
   - Calculate cache savings per request
   - Aggregate by patterns/groups
   - Detect similar requests

2. **Analytics Queries** (Backend - Phase 3)
   - Top requests by cost
   - Top groups by cost (app/model/user)
   - Cache effectiveness metrics
   - Cost trends and anomalies

3. **Recommendation Engine** (Backend - Phase 3)
   - Analyze patterns
   - Generate recommendations
   - Calculate potential savings
   - Priority scoring

4. **Dashboard UI** (Frontend - Phase 3B)
   - Display recommendations prominently
   - Show top requests/groups tables
   - Drill-down to details
   - Action buttons for optimizations

**API Endpoints Needed:**

```python
# Main dashboard data
GET /v1/dashboard/overview?period=7d
Response: {
  metrics: {...},           # Total cost, requests, cache stats
  recommendations: [...],   # Prioritized recommendations
  warnings: [...],          # Anomalies and alerts
  top_requests: [...],      # Top 10 by cost
  top_groups: {            # By app, model, user
    by_app: [...],
    by_model: [...],
    by_user: [...]
  },
  charts_data: {...}       # For visualizations
}

# Detailed request pattern analysis
GET /v1/analytics/patterns?min_count=5&cache_rate<0.5

# Group analysis
GET /v1/analytics/groups?group_by=app_label&sort=cost

# Recommendation details
GET /v1/analytics/recommendations/{rec_id}
```

**Database Schema Addition:**

```sql
-- Request patterns (aggregated)
CREATE TABLE request_patterns (
    id INTEGER PRIMARY KEY,
    pattern_hash TEXT UNIQUE,
    pattern_description TEXT,
    
    -- Counts
    total_count INTEGER,
    cached_count INTEGER,
    api_call_count INTEGER,
    
    -- Costs
    total_cost REAL,
    avg_cost_per_call REAL,
    avg_cost_per_api_call REAL,
    cache_savings REAL,
    
    -- Metadata
    models_used JSON,  -- {"gpt-4": 23, "gpt-3.5": 45}
    apps_using JSON,   -- {"mobile-app": 34, "web-app": 12}
    
    -- Timestamps
    first_seen DATETIME,
    last_seen DATETIME,
    period_start DATETIME,
    period_end DATETIME
);

CREATE INDEX idx_pattern_cost ON request_patterns(total_cost DESC);
CREATE INDEX idx_pattern_cache_rate ON request_patterns(cached_count * 1.0 / total_count);

-- Recommendations (cached)
CREATE TABLE optimization_recommendations (
    id INTEGER PRIMARY KEY,
    rec_id TEXT UNIQUE,
    
    -- Type and priority
    type TEXT,  -- caching, model_routing, etc.
    priority TEXT,  -- high, medium, low
    
    -- Content
    title TEXT,
    description TEXT,
    
    -- Impact
    current_cost_weekly REAL,
    potential_savings_weekly REAL,
    savings_percentage REAL,
    affected_requests INTEGER,
    
    -- Context
    context_json JSON,
    actions_json JSON,
    
    -- Status
    status TEXT,  -- active, dismissed, implemented
    created_at DATETIME,
    updated_at DATETIME
);
```

**Screen 3: Cost Explorer**
- **Filters**
  - Date range picker
  - Model selector (multi-select)
  - App label filter
  - User label filter
- **Grouping Options**
  - By model
  - By app label
  - By user label
  - By date (hourly/daily/weekly)
- **Visualizations**
  - Time-series chart (cost over time)
  - Bar chart (cost by group)
  - Pie chart (cost distribution)
- **Data Table**
  - Sortable columns
  - Export to CSV/JSON
- **Metrics**
  - Total cost
  - Average cost per request
  - Predicted vs actual variance
  - Cost savings from cache

**Screen 4: Request History**
- **Searchable Table**
  - Request ID, timestamp, model
  - Prompt preview (truncated)
  - Response preview (truncated)
  - Cost, tokens, latency
  - Cached indicator
  - Error indicator
- **Filters**
  - Date range
  - Model
  - Cached/not cached
  - Success/error
  - App/user labels
- **Actions per Row**
  - View full details (modal)
  - Copy request ID
  - Replay request
  - View in Playground
- **Details Modal**
  - Full request (formatted JSON)
  - Full response (formatted)
  - Metadata (all labels)
  - Cost breakdown
  - Timeline (request → cache check → API call → response)

**Screen 5: Cache Analytics**
- **Summary Stats**
  - Current cache size
  - Total hits/misses
  - Hit rate (%)
  - Estimated cost saved
  - Tokens saved
- **Charts**
  - Hit rate over time
  - Cache size over time
  - Top cached queries
  - Cost savings over time
- **Cache Contents**
  - List of cached entries
  - Model, prompt preview, cached at, expires at
  - Actions: View, Evict
- **Cache Management**
  - Clear all cache button
  - Clear by model
  - Configure TTL
  - Configure max size

**Screen 6: Settings**
- **Gateway Configuration**
  - Gateway URL
  - API key (for dashboard auth)
  - Connection status
- **Plugin Configuration**
  - Enable/disable cache
  - Cache TTL
  - Cache max size
- **Cost Tracking**
  - Model pricing table (editable)
  - Budget configuration
  - Alert thresholds
- **Display Preferences**
  - Theme (light/dark)
  - Date format
  - Currency
  - Refresh interval
- **Export/Import**
  - Export all data
  - Import configuration

**Tech Stack:**

**Option A: Keep Simple (Current Stack + Routing)**
- Vanilla JS with client-side routing
- Express backend (stays simple)
- Chart.js for visualizations
- Fetch API for backend calls
- LocalStorage for preferences
- **Pros:** Simple, no build step, fast iteration
- **Cons:** Manual routing, no reactivity framework

**Option B: Upgrade to Modern SPA (Recommended)**
- Vue.js or React (lightweight SPA framework)
- Express backend (or upgrade to Next.js)
- Chart.js or Recharts
- Vue Router / React Router
- Component-based architecture
- **Pros:** Better structure, reusable components, easier to maintain
- **Cons:** Requires build step (Vite/Webpack)

**Option C: Full Next.js (Future-Proof)**
- Next.js (React + SSR + API routes)
- No separate backend needed
- Recharts for visualizations
- Built-in routing
- API routes replace Express server
- **Pros:** Modern, scalable, great DX, all-in-one
- **Cons:** More complex, learning curve

**Recommended: Option B (Vue.js + Express)**
- Good balance of simplicity and power
- Vue.js is easier to learn than React
- Keep existing Express backend
- Vite for fast builds
- Gradual migration from current client

**Implementation Plan:**

**Step 1: Setup SPA Framework (Vue.js + Vite)**
```bash
cd dashboard/  # rename from client/
npm install vue@3 vue-router@4 vite @vitejs/plugin-vue
npm install chart.js vue-chartjs
npm install axios  # for API calls
```

**Step 2: Create App Shell**
- Main app component with navigation
- Router setup for screens
- Shared layout component
- Navigation menu component

**Step 3: Migrate Playground Screen**
- Convert current client UI to Vue component
- Keep all existing functionality
- Add mini-stats widget
- Add "View in History" button

**Step 4: Build Overview Screen**
- Create dashboard widgets
- Integrate with analytics API
- Add charts for cost/requests
- Real-time updates

**Step 5: Build Other Screens**
- Cost Explorer (charts + filters)
- Request History (table + details modal)
- Cache Analytics (stats + management)
- Settings (configuration forms)

**Step 6: Add Real-Time Updates**
- Server-Sent Events (SSE) endpoint in gateway
- Auto-refresh dashboard metrics
- Live request log
- Toast notifications for errors

**Directory Structure (Vue.js + Express):**

```
dashboard/  (renamed from client/)
├── package.json
├── vite.config.js
├── server.js                 # Express backend (static file serving)
├── index.html                # Main HTML entry point
├── src/
│   ├── main.js              # Vue app initialization
│   ├── App.vue              # Root component
│   ├── router.js            # Vue Router configuration
│   ├── api/
│   │   └── gateway.js       # Gateway API client
│   ├── components/
│   │   ├── Layout.vue       # Main layout with nav
│   │   ├── Navigation.vue   # Top navigation menu
│   │   ├── charts/
│   │   │   ├── LineChart.vue
│   │   │   ├── PieChart.vue
│   │   │   └── BarChart.vue
│   │   ├── tables/
│   │   │   └── DataTable.vue
│   │   └── widgets/
│   │       ├── StatCard.vue
│   │       └── MiniStats.vue
│   └── screens/
│       ├── Playground.vue   # Chat playground
│       ├── Overview.vue     # Dashboard overview
│       ├── Costs.vue        # Cost analytics
│       ├── Requests.vue     # Request history
│       ├── Cache.vue        # Cache analytics
│       └── Settings.vue     # Configuration
├── public/
│   └── assets/
└── README.md
```

**API Endpoints Needed (Gateway):**

```python
# Overview metrics
GET /v1/dashboard/overview?period=24h

# Cost analytics
GET /v1/costs/summary?start=2025-10-01&end=2025-10-31
GET /v1/costs/by-model?period=7d
GET /v1/costs/by-label?label=app&period=30d
GET /v1/costs/trend?period=90d&granularity=daily

# Request history
GET /v1/requests/history?limit=100&offset=0&filter=...
GET /v1/requests/{request_id}

# Cache analytics
GET /v1/cache/stats
GET /v1/cache/contents?limit=50
POST /v1/cache/clear
DELETE /v1/cache/entry/{key}

# Real-time updates
GET /v1/events/stream  # Server-Sent Events (SSE)
```

**Shared State Management:**

```javascript
// Use Pinia (Vue) or Zustand (React) for shared state
{
  gateway: {
    url: 'http://localhost:8000',
    connected: true,
  },
  cache: {
    enabled: true,
    hitRate: 0.45,
    size: 234,
  },
  costs: {
    today: 12.34,
    week: 89.45,
  },
  settings: {
    theme: 'light',
    refreshInterval: 5000,
  }
}
```

**Migration Strategy:**

1. **Phase 3A: Setup & Playground** (2-3 hours)
   - Install Vue.js + Vite
   - Create app shell
   - Migrate current client to Playground screen
   - Test that existing functionality works

2. **Phase 3B: Overview Dashboard** (3-4 hours)
   - Create Overview screen
   - Add summary stats widgets
   - Add basic charts
   - Connect to mock data

3. **Phase 3C: Cost Explorer** (4-5 hours)
   - Create Cost Explorer screen
   - Add filters and grouping
   - Add charts and data table
   - Connect to real analytics API

4. **Phase 3D: Request History** (3-4 hours)
   - Create Request History screen
   - Add searchable table
   - Add details modal
   - Add replay functionality

5. **Phase 3E: Cache Analytics** (2-3 hours)
   - Create Cache Analytics screen
   - Add cache stats
   - Add cache management
   - Connect to cache API

6. **Phase 3F: Settings** (2-3 hours)
   - Create Settings screen
   - Add configuration forms
   - Add preferences
   - Add export/import

7. **Phase 3G: Polish** (2-3 hours)
   - Real-time updates (SSE)
   - Loading states
   - Error handling
   - Responsive design
   - Dark mode

**Total Time Estimate: 18-25 hours** (spread over multiple sessions)

**Benefits of Unified Dashboard:**

✅ Single app to deploy
✅ Consistent navigation
✅ Shared authentication
✅ Better UX (no tab switching)
✅ Test → View Cost → Analyze in one flow
✅ Reusable components
✅ Easier to maintain
✅ Professional appearance

---

## 🎯 Implementation Order

### Sprint 1: Foundation (This Week)
1. ✅ **Simple Cache Plugin** (in-memory)
   - Implement `CachePlugin`
   - Add tests
   - Configure in `plugins.yaml`
   - Verify cost savings on duplicate requests

### Sprint 2: Cost Tracking (Next Week)
2. **Cost Monitor Plugin**
   - Implement `CostMonitorPlugin`
   - SQLite database setup
   - Basic API endpoints
   - Predicted vs actual cost tracking

3. **Metadata Labels**
   - Add label extraction from requests (headers)
   - Store labels with cost records
   - Support custom labels

### Sprint 3: Advanced Cache (Week 3)
4. **Redis Cache Backend**
   - Implement `RedisCacheBackend`
   - Distributed cache support
   - Cache admin endpoints

### Sprint 4: Analytics (Week 4)
5. **Analytics Plugin**
   - Implement aggregation queries
   - Time-series endpoints
   - Cost attribution by label

6. **Dashboard UI**
   - Build Next.js dashboard
   - Connect to analytics API
   - Deploy dashboard

---

## 📊 Success Metrics

**Cache:**
- Cache hit rate > 20%
- Cost savings > $50/month
- Response time < 50ms for cached requests

**Cost Monitoring:**
- 100% request cost tracking
- < 5% variance between predicted/actual
- Alert response time < 1 minute

**Analytics:**
- Query response time < 500ms
- Support 10,000+ records
- 99.9% uptime

**Dashboard:**
- Page load time < 2 seconds
- Real-time updates (< 5 second lag)
- Mobile responsive

---

## 🔧 Technical Considerations

### Cache
- **Cache key collision**: Use cryptographic hash (SHA256)
- **Memory limits**: Implement LRU eviction
- **Stale data**: Configurable TTL per model
- **Cache warming**: Preload on startup

### Cost Monitoring
- **High volume**: Batch inserts to SQLite
- **Query performance**: Proper indexing
- **Storage growth**: Implement data retention policy
- **Accuracy**: Validate against provider bills

### Analytics
- **Aggregation performance**: Pre-compute daily summaries
- **Real-time updates**: Use triggers or background jobs
- **Data retention**: Archive old records to separate tables
- **Scaling**: Consider TimescaleDB or ClickHouse for large scale

### Dashboard
- **Authentication**: API key or OAuth
- **Authorization**: Role-based access (admin, viewer)
- **Rate limiting**: Prevent dashboard API abuse
- **Caching**: Cache dashboard API responses

---

## 📝 Metadata Label Strategy

Labels are extracted from request headers and stored with each record:

```python
# Client sends request with custom headers
headers = {
    "X-Aikido-App": "mobile-app",
    "X-Aikido-User": "user-123",
    "X-Aikido-Environment": "production",
    "X-Aikido-Version": "1.2.3"
}

# Gateway extracts and stores labels
labels = {
    "app_label": "mobile-app",
    "user_label": "user-123",
    "environment": "production",
    "version": "1.2.3",
    "api_key_hash": hash(api_key)
}

# Analytics can then group by any label
```

**Standard Labels:**
- `app_label` - Application name
- `user_label` - User/tenant ID
- `environment` - prod/staging/dev
- `version` - App version
- `api_key_hash` - Hashed API key (for multi-tenant)
- `team_label` - Team/department
- `cost_center` - Cost center for billing

---

## 🚀 Let's Start!

**Next Step:** Implement the Simple Cache Plugin (Sprint 1, Task 1)

This will:
- Show immediate value (cost savings)
- Prove the plugin architecture works
- Generate data for future analytics
- Set foundation for Redis cache

Ready to begin? 🎯
