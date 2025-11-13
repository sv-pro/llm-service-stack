import React, { useEffect, useRef, useState } from 'react';

const SemanticStatsPanel = ({
  metrics,
  cacheMetrics,
  histogram,
  costSummary,
  transparency,
  onThresholdChange,
  isUpdatingThreshold = false,
  thresholdMessage,
  thresholdError,
}) => {
  const enabled = metrics?.enabled;

  const [thresholdValue, setThresholdValue] = useState(
    metrics?.similarity_threshold ?? 0.85
  );
  const lastCommittedRef = useRef(thresholdValue);

  useEffect(() => {
    if (typeof metrics?.similarity_threshold === 'number') {
      const rounded = Number(metrics.similarity_threshold.toFixed(2));
      setThresholdValue(rounded);
      lastCommittedRef.current = rounded;
    }
  }, [metrics?.similarity_threshold]);

  const semanticHitRate = metrics?.hit_rate ?? 0;
  const verbatimHitRate = cacheMetrics?.hit_rate ?? 0;
  const combinedHitRate = 1 - (1 - verbatimHitRate) * (1 - semanticHitRate);

  const formatPercent = (value) => {
    if (value === null || value === undefined) return '0.0%';
    return `${(value * 100).toFixed(1)}%`;
  };

  const formatNumber = (value) => {
    if (value === null || value === undefined) return '0';
    if (typeof value === 'number') {
      return value.toLocaleString();
    }
    return value;
  };

  const formatCurrency = (value) => {
    if (value === null || value === undefined) return '$0.000000';
    return `$${Number(value).toFixed(6)}`;
  };

  const formatDuration = (seconds) => {
    if (!seconds) return '0s';
    if (seconds < 60) return `${seconds}s`;
    const minutes = Math.floor(seconds / 60);
    if (minutes < 60) return `${minutes}m`;
    const hours = Math.floor(minutes / 60);
    return `${hours}h ${minutes % 60}m`;
  };

  const commitThreshold = () => {
    if (!onThresholdChange) return;
    if (Math.abs(thresholdValue - (lastCommittedRef.current ?? 0)) < 0.001) {
      return;
    }
    lastCommittedRef.current = thresholdValue;
    onThresholdChange(Number(thresholdValue.toFixed(2)));
  };

  if (!enabled) {
    return (
      <div className="cache-section">
        <h2>🧠 Semantic Cache</h2>
        <div className="semantic-status">
          <div className="semantic-status-icon">🛑</div>
          <div>
            <div className="semantic-status-title">Semantic cache is disabled</div>
            <div className="semantic-status-subtitle">
              Provide an `OPENAI_API_KEY` for embeddings and enable the `semantic_cache`
              plugin to start collecting metrics.
            </div>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="cache-section">
      <h2>🧠 Semantic Cache</h2>

      <div className="semantic-card-grid">
        <div className="semantic-card">
          <div className="semantic-card-label">Semantic Hit Rate</div>
          <div className="semantic-card-value">{formatPercent(semanticHitRate)}</div>
          <div className="semantic-card-meta">
            Hits {formatNumber(metrics.hits)} · Misses {formatNumber(metrics.misses)}
          </div>
          <div className="semantic-progress">
            <div
              className="semantic-progress-bar"
              style={{ width: `${semanticHitRate * 100}%` }}
            />
          </div>
        </div>

        <div className="semantic-card">
          <div className="semantic-card-label">Verbatim Hit Rate</div>
          <div className="semantic-card-value">{formatPercent(verbatimHitRate)}</div>
          <div className="semantic-card-meta">
            Lookups {formatNumber(cacheMetrics?.lookups || 0)}
          </div>
          <div className="semantic-progress secondary">
            <div
              className="semantic-progress-bar"
              style={{ width: `${(verbatimHitRate || 0) * 100}%` }}
            />
          </div>
        </div>

        <div className="semantic-card">
          <div className="semantic-card-label">Combined Hit Rate</div>
          <div className="semantic-card-value">{formatPercent(combinedHitRate)}</div>
          <div className="semantic-card-meta">
            Est. savings boost {(combinedHitRate - verbatimHitRate > 0)
              ? formatPercent(combinedHitRate - verbatimHitRate)
              : '0.0%'}
          </div>
          <div className="semantic-progress success">
            <div
              className="semantic-progress-bar"
              style={{ width: `${combinedHitRate * 100}%` }}
            />
          </div>
        </div>

        <div className="semantic-card">
          <div className="semantic-card-label">Avg Similarity Score</div>
          <div className="semantic-card-value">
            {(metrics.average_similarity ?? 0).toFixed(3)}
          </div>
          <div className="semantic-card-meta">
            Threshold {formatPercent(metrics.similarity_threshold || 0)}
          </div>
        </div>
      </div>

      <div className="threshold-control">
        <div className="threshold-header">
          <div>
            <div className="threshold-label">Similarity Threshold</div>
            <div className="threshold-value">{thresholdValue.toFixed(2)}</div>
          </div>
          <div className="threshold-hints">
            <span>Loose</span>
            <span>Balanced</span>
            <span>Strict</span>
          </div>
        </div>
        <input
          type="range"
          min="0.50"
          max="0.99"
          step="0.01"
          value={thresholdValue}
          onChange={(event) => setThresholdValue(parseFloat(event.target.value))}
          onPointerUp={commitThreshold}
          onTouchEnd={commitThreshold}
          onKeyUp={(event) => {
            if (event.key === 'Enter' || event.key === ' ') {
              commitThreshold();
            }
          }}
          className="threshold-slider"
        />
        <div className="threshold-scale">
          <span>0.50</span>
          <span>0.75</span>
          <span>0.99</span>
        </div>
        <div className="threshold-status">
          {isUpdatingThreshold && <span>Updating threshold…</span>}
          {!isUpdatingThreshold && thresholdMessage && (
            <span className="threshold-success">{thresholdMessage}</span>
          )}
          {thresholdError && (
            <span className="threshold-error">{thresholdError}</span>
          )}
        </div>
      </div>

      <div className="metrics-grid">
        <div className="metric-box">
          <div className="metric-label">Index Size</div>
          <div className="metric-value">{formatNumber(metrics.size)}</div>
          <div className="metric-description">
            Capacity: {formatNumber(metrics.max_entries)} embeddings
          </div>
        </div>

        <div className="metric-box">
          <div className="metric-label">TTL</div>
          <div className="metric-value">{formatDuration(metrics.ttl_seconds)}</div>
          <div className="metric-description">
            Evictions: {formatNumber(metrics.evictions)}
          </div>
        </div>

        <div className="metric-box">
          <div className="metric-label">Embedding Model</div>
          <div className="metric-value small">
            {metrics.embedding_model} · {metrics.embedding_dimension} dims
          </div>
          <div className="metric-description">
            Provider: {transparency?.provider || metrics.provider || 'unknown'} · Backend: {transparency?.backend || metrics.backend || 'n/a'}
          </div>
        </div>
      </div>

      {costSummary && (
        <div className="semantic-cost-summary">
          <div className="cost-card">
            <div className="cost-label">Net Spend</div>
            <div className="cost-value">{formatCurrency(costSummary.net_cost_total || 0)}</div>
            <div className="cost-meta">Completion + embeddings</div>
          </div>
          <div className="cost-card">
            <div className="cost-label">Embedding Spend</div>
            <div className="cost-value">{formatCurrency(costSummary.embedding_cost_total || 0)}</div>
            <div className="cost-meta">Tracked via ledger</div>
          </div>
          <div className="cost-card">
            <div className="cost-label">Avoided Cost</div>
            <div className="cost-value">{formatCurrency(costSummary.avoided_cost_total || 0)}</div>
            <div className="cost-meta">Cache savings to date</div>
          </div>
        </div>
      )}

      {histogram?.buckets?.length > 0 && (
        <div className="semantic-histogram">
          <div className="histogram-header">
            <h3>Similarity Distribution</h3>
            <span>{histogram.total_samples} samples</span>
          </div>
          <div className="histogram-bars">
            {histogram.buckets.map((bucket) => {
              const maxCount = Math.max(...histogram.buckets.map((b) => b.count || 0), 1);
              const height = ((bucket.count || 0) / maxCount) * 100;
              return (
                <div className="histogram-bar" key={bucket.label}>
                  <div
                    className="histogram-bar-fill"
                    style={{ height: `${height}%` }}
                    title={`${bucket.label}: ${bucket.count || 0}`}
                  />
                  <div className="histogram-bar-label">{bucket.label}</div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
};

export default SemanticStatsPanel;
