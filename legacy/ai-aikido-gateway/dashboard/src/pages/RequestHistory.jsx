import React, { useState, useEffect } from 'react';
import './RequestHistory.css';
import API_URL from '../config';

const GATEWAY_URL = API_URL;

function RequestHistory() {
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [stats, setStats] = useState(null);
  
  // Filters
  const [modelFilter, setModelFilter] = useState('');
  const [cachedFilter, setCachedFilter] = useState('');
  const [cacheTypeFilter, setCacheTypeFilter] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  
  // Pagination
  const [limit] = useState(50);
  const [offset, setOffset] = useState(0);
  
  // Selected request for detail view
  const [selectedRequest, setSelectedRequest] = useState(null);

  useEffect(() => {
    fetchRequests();
    fetchStats();
  }, [offset, modelFilter, cachedFilter, cacheTypeFilter, searchQuery]);

  const fetchRequests = async () => {
    setLoading(true);
    setError(null);

    try {
      const params = new URLSearchParams({
        limit: limit.toString(),
        offset: offset.toString(),
      });

      if (modelFilter) params.append('model', modelFilter);
      if (cachedFilter) params.append('cached', cachedFilter);
      if (cacheTypeFilter) params.append('cache_type', cacheTypeFilter);
      if (searchQuery) params.append('search', searchQuery);

      const response = await fetch(`${GATEWAY_URL}/v1/history/requests?${params}`);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const data = await response.json();
      setRequests(data.requests || []);
    } catch (err) {
      console.error('Failed to fetch requests:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const fetchStats = async () => {
    try {
      const response = await fetch(`${GATEWAY_URL}/v1/history/stats`);
      if (response.ok) {
        const data = await response.json();
        setStats(data);
      }
    } catch (err) {
      console.error('Failed to fetch stats:', err);
    }
  };

  const fetchRequestDetails = async (requestId) => {
    try {
      const response = await fetch(`${GATEWAY_URL}/v1/history/requests/${requestId}`);
      if (response.ok) {
        const data = await response.json();
        setSelectedRequest(data);
      }
    } catch (err) {
      console.error('Failed to fetch request details:', err);
    }
  };

  const formatTimestamp = (timestamp) => {
    const date = new Date(timestamp);
    return date.toLocaleString();
  };

  const formatTokens = (tokens) => {
    if (!tokens) return '-';
    return tokens.toLocaleString();
  };

  const formatLatency = (ms) => {
    if (!ms) return '-';
    return `${ms}ms`;
  };

  const formatCost = (cost) => {
    if (cost === null || cost === undefined) return '$0.0000';
    return `$${cost.toFixed(4)}`;
  };

  const formatCostLong = (cost) => {
    if (cost === null || cost === undefined) return '$0.000000';
    return `$${cost.toFixed(6)}`;
  };

  const formatPercent = (value) => {
    if (value === null || value === undefined) return '-';
    return `${(value * 100).toFixed(1)}%`;
  };

  const truncateText = (text, maxLength = 100) => {
    if (!text) return '-';
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  };

  const getFirstMessage = (messagesJson) => {
    try {
      const messages = JSON.parse(messagesJson);
      if (messages && messages.length > 0) {
        return messages[messages.length - 1].content; // Get last user message
      }
    } catch (e) {
      return messagesJson;
    }
    return '-';
  };

  const handlePrevPage = () => {
    if (offset > 0) {
      setOffset(Math.max(0, offset - limit));
    }
  };

  const handleNextPage = () => {
    if (requests.length === limit) {
      setOffset(offset + limit);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    setOffset(0); // Reset to first page
    fetchRequests();
  };

  const getCacheTypeLabel = (type) => {
    switch ((type || '').toLowerCase()) {
      case 'verbatim':
        return { label: 'Verbatim Cache', className: 'badge-verbatim' };
      case 'semantic':
        return { label: 'Semantic Cache', className: 'badge-semantic' };
      default:
        return { label: 'API Call', className: 'badge-neutral' };
    }
  };

  return (
    <div className="request-history-page">
      <div className="page-header">
        <h1>📋 Request History</h1>
        <p className="page-subtitle">View and analyze all requests sent through the gateway</p>
      </div>

      {stats && (
        <div className="stats-cards">
          <div className="stat-card">
            <div className="stat-icon">💸</div>
            <div className="stat-value">{formatCostLong(stats.avoided_cost_total || 0)}</div>
            <div className="stat-label">Cost Avoided</div>
          </div>
          <div className="stat-card">
            <div className="stat-icon">📊</div>
            <div className="stat-value">{stats.total_requests || 0}</div>
            <div className="stat-label">Total Requests</div>
          </div>
          <div className="stat-card">
            <div className="stat-icon">🧠</div>
            <div className="stat-value">{formatCost(stats.embedding_cost_total || 0)}</div>
            <div className="stat-label">Embedding Spend</div>
          </div>
          <div className="stat-card">
            <div className="stat-icon">💰</div>
            <div className="stat-value">{formatCost(stats.net_cost_total ?? stats.total_cost ?? 0)}</div>
            <div className="stat-label">Total Cost (net)</div>
          </div>
          <div className="stat-card">
            <div className="stat-icon">⚡</div>
            <div className="stat-value">{stats.cached_requests || 0}</div>
            <div className="stat-label">Cached Requests</div>
          </div>
          <div className="stat-card">
            <div className="stat-icon">📈</div>
            <div className="stat-value">{formatPercent((stats.cache_metrics && stats.cache_metrics.hit_rate) || stats.cache_hit_rate || 0)}</div>
            <div className="stat-label">Cache Hit Rate</div>
          </div>
          <div className="stat-card">
            <div className="stat-icon">⏱️</div>
            <div className="stat-value">{stats.avg_latency_ms ? `${Math.round(stats.avg_latency_ms)}ms` : '-'}</div>
            <div className="stat-label">Avg Latency</div>
          </div>
          <div className="stat-card">
            <div className="stat-icon">🤖</div>
            <div className="stat-value">{stats.unique_models || 0}</div>
            <div className="stat-label">Models Used</div>
          </div>
        </div>
      )}

      {stats?.cache_metrics && (
        <div className="cache-metrics-panel">
          <div className="cache-metric-card">
            <div className="metric-label">Backend</div>
            <div className="metric-value">{stats.cache_metrics.backend}</div>
            <div className="metric-meta">Hot cache size: {stats.cache_metrics.hot_cache_size}</div>
          </div>
          <div className="cache-metric-card">
            <div className="metric-label">Lookups</div>
            <div className="metric-value">{stats.cache_metrics.lookups}</div>
            <div className="metric-meta">Hits: {stats.cache_metrics.hits} · Misses: {stats.cache_metrics.misses}</div>
          </div>
          <div className="cache-metric-card">
            <div className="metric-label">Estimated Savings</div>
            <div className="metric-value">{formatCostLong(stats.cache_metrics.estimated_savings || 0)}</div>
            <div className="metric-meta">Storage entries: {stats.cache_metrics.storage_entries}</div>
          </div>
        </div>
      )}

      <div className="filters-section">
        <form onSubmit={handleSearch} className="filters-form">
          <div className="filter-group">
            <label>Search</label>
            <input
              type="text"
              placeholder="Search in messages..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="filter-input"
            />
          </div>
          
          <div className="filter-group">
            <label>Model</label>
            <select
              value={modelFilter}
              onChange={(e) => setModelFilter(e.target.value)}
              className="filter-select"
            >
              <option value="">All Models</option>
              <option value="gpt-3.5-turbo">GPT-3.5 Turbo</option>
              <option value="gpt-4">GPT-4</option>
              <option value="gpt-4-turbo">GPT-4 Turbo</option>
            </select>
          </div>
          
          <div className="filter-group">
            <label>Cached</label>
            <select
              value={cachedFilter}
              onChange={(e) => setCachedFilter(e.target.value)}
              className="filter-select"
            >
              <option value="">All</option>
              <option value="true">Cached</option>
              <option value="false">Not Cached</option>
            </select>
          </div>

          <div className="filter-group">
            <label>Cache Source</label>
            <select
              value={cacheTypeFilter}
              onChange={(e) => setCacheTypeFilter(e.target.value)}
              className="filter-select"
            >
              <option value="">All</option>
              <option value="api">API Call</option>
              <option value="verbatim">Verbatim Cache</option>
              <option value="semantic">Semantic Cache</option>
            </select>
          </div>
          
          <button type="submit" className="filter-button">
            🔍 Search
          </button>
        </form>
      </div>

      {error && (
        <div className="error-banner">
          ⚠️ Error loading requests: {error}
        </div>
      )}

      {loading ? (
        <div className="loading-section">
          <div className="spinner-large"></div>
          <p>Loading request history...</p>
        </div>
      ) : (
        <>
          <div className="table-container">
            <table className="requests-table">
              <thead>
                <tr>
                  <th>Timestamp</th>
                  <th>Model</th>
                  <th>Prompt Preview</th>
                  <th>Tokens</th>
                  <th>Cost</th>
                  <th>Latency</th>
                  <th>Source</th>
                  <th>Actions</th>
                </tr>
              </thead>
              <tbody>
                {requests.length === 0 ? (
                  <tr>
                    <td colSpan="8" className="empty-state">
                      No requests found. Try adjusting your filters or make some requests in the Playground.
                    </td>
                  </tr>
                ) : (
                  requests.map((req) => (
                    <tr key={req.id}>
                      <td className="timestamp-cell">
                        {formatTimestamp(req.timestamp)}
                      </td>
                      <td className="model-cell">
                        <span className="model-badge">{req.model}</span>
                      </td>
                      <td className="prompt-cell">
                        {truncateText(getFirstMessage(req.messages))}
                      </td>
                      <td className="tokens-cell">
                        {formatTokens(req.total_tokens)}
                      </td>
                      <td className="cost-cell">
                        {formatCost((req.total_cost !== undefined && req.total_cost !== null) ? req.total_cost : req.estimated_cost)}
                      </td>
                      <td className="latency-cell">
                        {formatLatency(req.latency_ms)}
                      </td>
                      <td className="cached-cell">
                        {(() => {
                          const info = getCacheTypeLabel(req.cache_type);
                          const isCached = (req.cached ?? 0) === 1;
                          return (
                            <span className={`badge ${info.className}`}>
                              {isCached && info.label !== 'API Call' ? `✓ ${info.label}` : info.label}
                            </span>
                          );
                        })()}
                      </td>
                      <td className="actions-cell">
                        <button
                          className="btn-view"
                          onClick={() => fetchRequestDetails(req.request_id)}
                        >
                          View
                        </button>
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>

          <div className="pagination">
            <button
              className="btn-page"
              onClick={handlePrevPage}
              disabled={offset === 0}
            >
              ← Previous
            </button>
            <span className="page-info">
              Showing {offset + 1} - {offset + requests.length}
            </span>
            <button
              className="btn-page"
              onClick={handleNextPage}
              disabled={requests.length < limit}
            >
              Next →
            </button>
          </div>
        </>
      )}

      {selectedRequest && (
        <div className="modal-overlay" onClick={() => setSelectedRequest(null)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h2>Request Details</h2>
              <button className="modal-close" onClick={() => setSelectedRequest(null)}>
                ×
              </button>
            </div>
            <div className="modal-body">
              <div className="detail-section">
                <h3>Request Info</h3>
                <div className="detail-grid">
                  <div className="detail-item">
                    <span className="detail-label">ID:</span>
                    <span className="detail-value">{selectedRequest.request_id}</span>
                  </div>
                  <div className="detail-item">
                    <span className="detail-label">Timestamp:</span>
                    <span className="detail-value">{formatTimestamp(selectedRequest.timestamp)}</span>
                  </div>
                  <div className="detail-item">
                    <span className="detail-label">Model:</span>
                    <span className="detail-value">{selectedRequest.model}</span>
                  </div>
                  <div className="detail-item">
                    <span className="detail-label">Latency:</span>
                    <span className="detail-value">{formatLatency(selectedRequest.latency_ms)}</span>
                  </div>
                  <div className="detail-item">
                    <span className="detail-label">Tokens:</span>
                    <span className="detail-value">
                      {selectedRequest.total_tokens} 
                      (prompt: {selectedRequest.prompt_tokens}, completion: {selectedRequest.completion_tokens})
                    </span>
                  </div>
                  <div className="detail-item">
                    <span className="detail-label">Embedding Tokens:</span>
                    <span className="detail-value">
                      {selectedRequest.embedding_tokens || 0}
                    </span>
                  </div>
                  <div className="detail-item">
                    <span className="detail-label">Cached:</span>
                    <span className="detail-value">
                      {selectedRequest.cached ? '✓ Yes' : '✗ No'}
                    </span>
                  </div>
                  <div className="detail-item">
                    <span className="detail-label">Cache Source:</span>
                    <span className="detail-value">
                      {getCacheTypeLabel(selectedRequest.cache_type).label}
                    </span>
                  </div>
                  <div className="detail-item">
                    <span className="detail-label">Embedding Cost:</span>
                    <span className="detail-value">{formatCostLong(selectedRequest.embedding_cost || 0)}</span>
                  </div>
                  <div className="detail-item">
                    <span className="detail-label">Total Cost:</span>
                    <span className="detail-value">{formatCostLong(selectedRequest.total_cost || selectedRequest.estimated_cost || 0)}</span>
                  </div>
                </div>
              </div>

              <div className="detail-section">
                <h3>Messages</h3>
                <pre className="detail-code">{selectedRequest.messages}</pre>
              </div>

              <div className="detail-section">
                <h3>Response</h3>
                <div className="response-text">
                  {selectedRequest.response_text || 'No response available'}
                </div>
              </div>

              {selectedRequest.error && (
                <div className="detail-section">
                  <h3>Error</h3>
                  <div className="error-text">
                    {selectedRequest.error}
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

export default RequestHistory;
