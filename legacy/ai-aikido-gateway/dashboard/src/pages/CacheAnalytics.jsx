import React, { useState, useEffect } from 'react';
import './CacheAnalytics.css';
import SemanticStatsPanel from '../components/cache/SemanticStatsPanel';
import SemanticTimeSeriesChart from '../components/cache/SemanticTimeSeriesChart';

function CacheAnalytics() {
  const [stats, setStats] = useState(null);
  const [requests, setRequests] = useState([]);
  const [semanticStats, setSemanticStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [thresholdState, setThresholdState] = useState({
    updating: false,
    message: null,
    error: null,
  });

  useEffect(() => {
    fetchData();
    const interval = setInterval(fetchData, 5000); // Refresh every 5 seconds
    return () => clearInterval(interval);
  }, []);

  useEffect(() => {
    if (!thresholdState.message) return;
    const timer = setTimeout(() => {
      setThresholdState((prev) => ({ ...prev, message: null }));
    }, 4000);
    return () => clearTimeout(timer);
  }, [thresholdState.message]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [statsRes, requestsRes] = await Promise.all([
        fetch('http://localhost:8000/v1/history/stats'),
        fetch('http://localhost:8000/v1/history/requests?limit=100')
      ]);

      if (!statsRes.ok || !requestsRes.ok) {
        throw new Error('Failed to fetch data');
      }

      const statsData = await statsRes.json();
      const requestsData = await requestsRes.json();
      let semanticData = null;

      try {
        const semanticRes = await fetch('http://localhost:8000/v1/cache/semantic/stats');
        if (semanticRes.ok) {
          semanticData = await semanticRes.json();
        }
      } catch (semanticErr) {
        console.warn('Semantic stats unavailable:', semanticErr);
      }

      setStats(statsData);
      setRequests(requestsData.requests || []);
      setSemanticStats(semanticData);
      setError(null);
    } catch (err) {
      console.error('Error fetching data:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const formatPercent = (value) => {
    if (value === null || value === undefined) return '0.0%';
    return `${(value * 100).toFixed(1)}%`;
  };

  const formatCost = (cost) => {
    if (cost === null || cost === undefined) return '$0.000000';
    return `$${cost.toFixed(6)}`;
  };

  const formatDateTime = (timestamp) => {
    if (!timestamp) return 'Never';
    try {
      return new Date(timestamp).toLocaleString();
    } catch {
      return 'Invalid date';
    }
  };

  const formatDuration = (seconds) => {
    if (!seconds) return '0s';
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}m`;
    const hours = Math.floor(minutes / 60);
    return `${hours}h ${minutes % 60}m`;
  };

  if (loading && !stats) {
    return (
      <div className="cache-analytics">
        <div className="loading-state">Loading cache analytics...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="cache-analytics">
        <div className="error-state">Error: {error}</div>
      </div>
    );
  }

  const cacheMetrics = stats?.cache_metrics || {};
  const semanticMetrics =
    semanticStats?.semantic_cache_metrics
    || stats?.semantic_cache_metrics
    || { enabled: false };
  const avoidedCost = stats?.avoided_cost_total || cacheMetrics.estimated_savings || 0;
  const cacheHitRate = cacheMetrics.hit_rate || 0;
  const totalRequests = stats?.total_requests || 0;
  const cachedRequests = requests.filter(r => r.cached).length;

  // Calculate cache efficiency
  const cacheEfficiency = totalRequests > 0 ? (cachedRequests / totalRequests) : 0;

  // Calculate average cost per request
  const avgCostPerRequest = stats?.avg_cost_per_request || 0;

  // Calculate theoretical max savings if all requests were cached
  const theoreticalMaxSavings = avgCostPerRequest * totalRequests;

  // Calculate savings rate
  const savingsRate = theoreticalMaxSavings > 0 ? (avoidedCost / theoreticalMaxSavings) : 0;

  const handleThresholdChange = async (value) => {
    try {
      setThresholdState({ updating: true, message: null, error: null });
      const response = await fetch('http://localhost:8000/v1/cache/semantic/threshold', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ similarity_threshold: value }),
      });

      const payload = await response.json().catch(() => ({}));

      if (!response.ok) {
        throw new Error(payload.detail || 'Failed to update similarity threshold');
      }

      setStats((prev) => ({
        ...(prev || {}),
        semantic_cache_metrics: payload.semantic_cache_metrics
          || prev?.semantic_cache_metrics
          || {},
      }));

      setThresholdState({
        updating: false,
        message: 'Threshold updated',
        error: null,
      });
    } catch (err) {
      setThresholdState({
        updating: false,
        message: null,
        error: err.message || 'Failed to update threshold',
      });
    }
  };

  return (
    <div className="cache-analytics">
      <div className="page-header">
        <h1>⚡ Cache Analytics</h1>
        <p className="page-subtitle">Response caching performance and savings metrics</p>
      </div>

      {/* Overview Cards */}
      <div className="cache-overview-cards">
        <div className="cache-card primary">
          <div className="card-icon">💰</div>
          <div className="card-content">
            <div className="card-label">Total Savings</div>
            <div className="card-value">{formatCost(avoidedCost)}</div>
            <div className="card-meta">From {cacheMetrics.hits || 0} cache hits</div>
          </div>
        </div>

        <div className="cache-card success">
          <div className="card-icon">🎯</div>
          <div className="card-content">
            <div className="card-label">Hit Rate</div>
            <div className="card-value">{formatPercent(cacheHitRate)}</div>
            <div className="card-meta">{cacheMetrics.hits || 0} / {cacheMetrics.lookups || 0} lookups</div>
          </div>
        </div>

        <div className="cache-card info">
          <div className="card-icon">📦</div>
          <div className="card-content">
            <div className="card-label">Cache Size</div>
            <div className="card-value">{cacheMetrics.storage_entries || 0}</div>
            <div className="card-meta">Hot: {cacheMetrics.hot_cache_size || 0} entries</div>
          </div>
        </div>

        <div className="cache-card warning">
          <div className="card-icon">⏱️</div>
          <div className="card-content">
            <div className="card-label">Default TTL</div>
            <div className="card-value">{formatDuration(cacheMetrics.default_ttl_seconds || 0)}</div>
            <div className="card-meta">Backend: {cacheMetrics.backend || 'N/A'}</div>
          </div>
        </div>
      </div>

      {/* Performance Metrics */}
      <div className="cache-section">
        <h2>📊 Performance Metrics</h2>
        <div className="metrics-grid">
          <div className="metric-box">
            <div className="metric-label">Cache Efficiency</div>
            <div className="metric-value">{formatPercent(cacheEfficiency)}</div>
            <div className="metric-description">
              {cachedRequests} of {totalRequests} total requests served from cache
            </div>
          </div>

          <div className="metric-box">
            <div className="metric-label">Lookups</div>
            <div className="metric-value">{cacheMetrics.lookups || 0}</div>
            <div className="metric-breakdown">
              <span className="metric-hit">Hits: {cacheMetrics.hits || 0}</span>
              <span className="metric-miss">Misses: {cacheMetrics.misses || 0}</span>
            </div>
          </div>

          <div className="metric-box">
            <div className="metric-label">Cache Writes</div>
            <div className="metric-value">{cacheMetrics.writes || 0}</div>
            <div className="metric-description">
              Responses stored in cache
            </div>
          </div>

          <div className="metric-box">
            <div className="metric-label">Savings Rate</div>
            <div className="metric-value">{formatPercent(savingsRate)}</div>
            <div className="metric-description">
              Of theoretical max savings ({formatCost(theoreticalMaxSavings)})
            </div>
          </div>
        </div>
      </div>

      {/* Cache Health */}
      <div className="cache-section">
        <h2>🏥 Cache Health</h2>
        <div className="health-grid">
          <div className="health-item">
            <div className="health-label">Status</div>
            <div className={`health-badge ${cacheMetrics.lookups > 0 ? 'healthy' : 'idle'}`}>
              {cacheMetrics.lookups > 0 ? '✅ Active' : '⏸️ Idle'}
            </div>
          </div>

          <div className="health-item">
            <div className="health-label">Last Hit</div>
            <div className="health-value">{formatDateTime(cacheMetrics.last_hit_at)}</div>
          </div>

          <div className="health-item">
            <div className="health-label">Last Write</div>
            <div className="health-value">{formatDateTime(cacheMetrics.last_write_at)}</div>
          </div>

          <div className="health-item">
            <div className="health-label">Hit Rate Grade</div>
            <div className={`health-badge grade-${
              cacheHitRate >= 0.7 ? 'a' :
              cacheHitRate >= 0.5 ? 'b' :
              cacheHitRate >= 0.3 ? 'c' : 'd'
            }`}>
              {cacheHitRate >= 0.7 ? 'A - Excellent' :
               cacheHitRate >= 0.5 ? 'B - Good' :
               cacheHitRate >= 0.3 ? 'C - Fair' : 'D - Poor'}
            </div>
          </div>
        </div>
      </div>

      <SemanticStatsPanel
        metrics={semanticMetrics}
        cacheMetrics={cacheMetrics}
        histogram={semanticStats?.histogram}
        costSummary={semanticStats?.cost_summary}
        transparency={semanticStats?.transparency}
        onThresholdChange={handleThresholdChange}
        isUpdatingThreshold={thresholdState.updating}
        thresholdMessage={thresholdState.message}
        thresholdError={thresholdState.error}
      />

      {/* Semantic Time-Series Chart */}
      <SemanticTimeSeriesChart enabled={semanticMetrics?.enabled} />

      {/* Recommendations */}
      <div className="cache-section">
        <h2>💡 Recommendations</h2>
        <div className="recommendations-list">
          {cacheHitRate < 0.3 && cacheMetrics.lookups > 10 && (
            <div className="recommendation warning">
              <div className="rec-icon">⚠️</div>
              <div className="rec-content">
                <div className="rec-title">Low Hit Rate Detected</div>
                <div className="rec-description">
                  Your cache hit rate is below 30%. This suggests requests have high variability.
                  Consider increasing TTL values or reviewing request patterns.
                </div>
              </div>
            </div>
          )}

          {cacheHitRate >= 0.5 && cacheHitRate < 0.7 && (
            <div className="recommendation info">
              <div className="rec-icon">📈</div>
              <div className="rec-content">
                <div className="rec-title">Good Performance</div>
                <div className="rec-description">
                  Your cache is performing well with a {formatPercent(cacheHitRate)} hit rate.
                  Saved {formatCost(avoidedCost)} in API costs so far.
                </div>
              </div>
            </div>
          )}

          {cacheHitRate >= 0.7 && (
            <div className="recommendation success">
              <div className="rec-icon">🎉</div>
              <div className="rec-content">
                <div className="rec-title">Excellent Cache Performance</div>
                <div className="rec-description">
                  Outstanding! Your cache is operating at peak efficiency with a {formatPercent(cacheHitRate)} hit rate.
                  Keep up the great work!
                </div>
              </div>
            </div>
          )}

          {cacheMetrics.hot_cache_size === cacheMetrics.storage_entries && cacheMetrics.storage_entries > 0 && (
            <div className="recommendation info">
              <div className="rec-icon">💾</div>
              <div className="rec-content">
                <div className="rec-title">All Cache Entries Hot</div>
                <div className="rec-description">
                  All {cacheMetrics.storage_entries} cached entries are in hot cache.
                  This is optimal for performance. No additional tuning needed.
                </div>
              </div>
            </div>
          )}

          {cacheMetrics.lookups === 0 && (
            <div className="recommendation info">
              <div className="rec-icon">🚀</div>
              <div className="rec-content">
                <div className="rec-title">Cache Ready</div>
                <div className="rec-description">
                  Cache is configured and ready. Make some duplicate requests to see caching in action!
                </div>
              </div>
            </div>
          )}

          {avoidedCost > 0.01 && (
            <div className="recommendation success">
              <div className="rec-icon">💸</div>
              <div className="rec-content">
                <div className="rec-title">Significant Savings</div>
                <div className="rec-description">
                  You've saved {formatCost(avoidedCost)} through caching!
                  At this rate, you could save approximately {formatCost(avoidedCost * 30)} per month.
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Cache Configuration */}
      <div className="cache-section">
        <h2>⚙️ Configuration</h2>
        <div className="config-grid">
          <div className="config-item">
            <div className="config-label">Backend Type</div>
            <div className="config-value">{cacheMetrics.backend || 'N/A'}</div>
          </div>
          <div className="config-item">
            <div className="config-label">Default TTL</div>
            <div className="config-value">{formatDuration(cacheMetrics.default_ttl_seconds || 0)}</div>
          </div>
          <div className="config-item">
            <div className="config-label">Hot Cache Capacity</div>
            <div className="config-value">
              {cacheMetrics.hot_cache_size || 0} / ∞
            </div>
          </div>
          <div className="config-item">
            <div className="config-label">Storage Backend</div>
            <div className="config-value">
              {cacheMetrics.backend === 'sqlite' ? 'SQLite (Persistent)' :
               cacheMetrics.backend === 'memory' ? 'In-Memory (Volatile)' : 'N/A'}
            </div>
          </div>
        </div>
      </div>

      {/* Recent Activity */}
      <div className="cache-section">
        <h2>📜 Recent Cached Requests</h2>
        {cachedRequests.length === 0 ? (
          <div className="empty-state">
            <div className="empty-icon">📭</div>
            <div className="empty-message">No cached requests yet</div>
            <div className="empty-hint">Make duplicate requests to see cache hits</div>
          </div>
        ) : (
          <div className="cached-requests-table">
            <table>
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Model</th>
                  <th>Prompt Preview</th>
                  <th>Tokens</th>
                  <th>Cost Saved</th>
                  <th>Latency</th>
                </tr>
              </thead>
              <tbody>
                {requests.filter(r => r.cached).slice(0, 10).map(req => (
                  <tr key={req.id}>
                    <td>{new Date(req.timestamp).toLocaleString()}</td>
                    <td><span className="model-badge">{req.model}</span></td>
                    <td className="prompt-preview">
                      {req.messages?.[0]?.content?.substring(0, 50) || 'N/A'}
                      {req.messages?.[0]?.content?.length > 50 ? '...' : ''}
                    </td>
                    <td>{req.total_tokens || 0}</td>
                    <td className="cost-saved">{formatCost(req.estimated_cost || 0)}</td>
                    <td>{req.latency_ms ? `${Math.round(req.latency_ms)}ms` : 'N/A'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}

export default CacheAnalytics;
