import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import './Overview.css';
import API_URL from '../config';

function Overview() {
  const [health, setHealth] = useState(null);
  const [plugins, setPlugins] = useState([]);
  const [models, setModels] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadOverviewData();
  }, []);

  const loadOverviewData = async () => {
    setLoading(true);
    setError(null);

    try {
      // Fetch health status
      const healthRes = await fetch(`${API_URL}/health`);
      const healthData = await healthRes.json();
      setHealth(healthData);

      // Fetch plugins
      const pluginsRes = await fetch(`${API_URL}/plugins`);
      const pluginsData = await pluginsRes.json();
      setPlugins(pluginsData.plugins || []);

      // Fetch models
      const modelsRes = await fetch(`${API_URL}/v1/models`);
      const modelsData = await modelsRes.json();
      setModels(modelsData.data || []);

    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const getUptime = () => {
    if (!health?.timestamp) return 'Unknown';
    const now = new Date();
    const start = new Date(health.timestamp);
    const diff = Math.abs(now - start);
    const hours = Math.floor(diff / 3600000);
    const minutes = Math.floor((diff % 3600000) / 60000);

    if (hours === 0) return `${minutes}m`;
    return `${hours}h ${minutes}m`;
  };

  const availableModels = models.filter(m => m.available);
  const enabledPlugins = plugins.filter(p => p.enabled);

  if (loading) {
    return (
      <div className="overview-page">
        <div className="page-header">
          <h1>📊 Overview Dashboard</h1>
          <p className="page-subtitle">Gateway status and quick stats</p>
        </div>
        <div className="loading-state">Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="overview-page">
        <div className="page-header">
          <h1>📊 Overview Dashboard</h1>
          <p className="page-subtitle">Gateway status and quick stats</p>
        </div>
        <div className="error-state">Error: {error}</div>
      </div>
    );
  }

  return (
    <div className="overview-page">
      <div className="page-header">
        <h1>📊 Overview Dashboard</h1>
        <p className="page-subtitle">Gateway status and quick stats</p>
      </div>

      {/* Gateway Status Banner */}
      <div className={`status-banner ${health?.status === 'healthy' ? 'healthy' : 'error'}`}>
        <div className="banner-content">
          <div className="status-icon">
            {health?.status === 'healthy' ? '✅' : '❌'}
          </div>
          <div className="status-info">
            <h2>Gateway Status: {health?.status === 'healthy' ? 'Healthy' : 'Error'}</h2>
            <p>
              Service: {health?.service} v{health?.version} •
              Uptime: {getUptime()}
            </p>
          </div>
        </div>
      </div>

      {/* Status Cards */}
      <div className="stats-cards">
        <div className="stat-card">
          <div className="card-icon">🔌</div>
          <h3>Active Plugins</h3>
          <div className="card-value">{enabledPlugins.length}</div>
          <div className="card-subtitle">of {plugins.length} total</div>
        </div>

        <div className="stat-card">
          <div className="card-icon">🤖</div>
          <h3>Available Models</h3>
          <div className="card-value">{availableModels.length}</div>
          <div className="card-subtitle">of {models.length} total</div>
        </div>

        <div className="stat-card">
          <div className="card-icon">⚡</div>
          <h3>Gateway</h3>
          <div className="card-value" style={{ fontSize: '24px' }}>Running</div>
          <div className="card-subtitle">Port 8000</div>
        </div>

        <div className="stat-card">
          <div className="card-icon">🎯</div>
          <h3>Status</h3>
          <div className="card-value" style={{ fontSize: '24px' }}>Ready</div>
          <div className="card-subtitle">All systems go</div>
        </div>
      </div>

      {/* Plugins Section */}
      <div className="section">
        <h2>🔌 Active Plugins</h2>
        <div className="plugins-grid">
          {enabledPlugins.map((plugin, idx) => (
            <div key={idx} className="plugin-card">
              <div className="plugin-header">
                <span className="plugin-name">{plugin.name}</span>
                <span className="plugin-badge">Priority {plugin.priority}</span>
              </div>
              <div className="plugin-status">
                <span className="status-dot enabled"></span>
                Enabled
              </div>
            </div>
          ))}
          {enabledPlugins.length === 0 && (
            <div className="empty-state">No plugins enabled</div>
          )}
        </div>
      </div>

      {/* Models Section */}
      <div className="section">
        <h2>🤖 Available Models</h2>
        <div className="models-grid">
          {availableModels.map((model, idx) => (
            <div key={idx} className="model-card">
              <div className="model-name">{model.id}</div>
              <div className="model-provider">{model.provider}</div>
            </div>
          ))}
          {availableModels.length === 0 && (
            <div className="empty-state">No models available</div>
          )}
        </div>
      </div>

      {/* Quick Actions */}
      <div className="section">
        <h2>🚀 Quick Actions</h2>
        <div className="actions-grid">
          <Link to="/playground" className="action-card">
            <div className="action-icon">🎮</div>
            <h3>Playground</h3>
            <p>Test the gateway with different models</p>
          </Link>

          <Link to="/cost-explorer" className="action-card">
            <div className="action-icon">💰</div>
            <h3>Cost Explorer</h3>
            <p>Track and analyze API costs</p>
          </Link>

          <Link to="/request-history" className="action-card">
            <div className="action-icon">📋</div>
            <h3>Request History</h3>
            <p>View all API requests and responses</p>
          </Link>

          <Link to="/settings" className="action-card">
            <div className="action-icon">⚙️</div>
            <h3>Settings</h3>
            <p>Configure gateway preferences</p>
          </Link>
        </div>
      </div>

      {/* Coming Soon Notice */}
      <div className="info-banner">
        <div className="banner-content">
          <h3>📈 More Features Coming Soon</h3>
          <p>
            Future updates will include cost tracking, request history, cache analytics,
            and optimization recommendations when the Cost Monitor plugin is implemented.
          </p>
        </div>
      </div>
    </div>
  );
}

export default Overview;
