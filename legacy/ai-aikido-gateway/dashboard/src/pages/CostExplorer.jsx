import React, { useState, useEffect } from 'react';
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer
} from 'recharts';
import './CostExplorer.css';
import API_URL from '../config';

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884d8', '#82ca9d', '#ffc658'];

function CostExplorer() {
  const [stats, setStats] = useState(null);
  const [requests, setRequests] = useState([]);
  const [loading, setLoading] = useState(true);
  const [timeRange, setTimeRange] = useState('7d'); // 24h, 7d, 30d, all
  const [groupBy, setGroupBy] = useState('day'); // hour, day, week

  useEffect(() => {
    fetchData();
  }, [timeRange]);

  const fetchData = async () => {
    try {
      setLoading(true);

      // Fetch stats
      const statsRes = await fetch(`${API_URL}/v1/history/stats`);
      const statsData = await statsRes.json();
      setStats(statsData);

      // Fetch all requests for trend analysis
      const requestsRes = await fetch(`${API_URL}/v1/history/requests?limit=1000`);
      const requestsData = await requestsRes.json();
      setRequests(requestsData.requests || []);

      setLoading(false);
    } catch (error) {
      console.error('Error fetching cost data:', error);
      setLoading(false);
    }
  };

  const formatCost = (cost) => {
    if (cost === null || cost === undefined) return '$0.000000';
    return `$${cost.toFixed(6)}`;
  };

  const formatCostShort = (cost) => {
    if (cost === null || cost === undefined) return '$0.00';
    if (cost < 0.01) return `$${cost.toFixed(6)}`;
    return `$${cost.toFixed(4)}`;
  };

  const formatPercent = (value) => {
    if (value === null || value === undefined) return '0.0%';
    return `${(value * 100).toFixed(1)}%`;
  };

  // Process data for cost trends chart
  const getCostTrends = () => {
    if (!requests.length) return [];

    const now = new Date();
    const cutoffMap = {
      '24h': new Date(now - 24 * 60 * 60 * 1000),
      '7d': new Date(now - 7 * 24 * 60 * 60 * 1000),
      '30d': new Date(now - 30 * 24 * 60 * 60 * 1000),
      'all': new Date(0)
    };
    const cutoff = cutoffMap[timeRange];

    // Filter requests by time range
    const filtered = requests.filter(r => new Date(r.timestamp) >= cutoff);

    // Group by time period
    const grouped = {};
    filtered.forEach(req => {
      const date = new Date(req.timestamp);
      let key;

      if (groupBy === 'hour') {
        key = `${date.getMonth() + 1}/${date.getDate()} ${date.getHours()}:00`;
      } else if (groupBy === 'day') {
        key = `${date.getMonth() + 1}/${date.getDate()}`;
      } else if (groupBy === 'week') {
        const weekStart = new Date(date);
        weekStart.setDate(date.getDate() - date.getDay());
        key = `${weekStart.getMonth() + 1}/${weekStart.getDate()}`;
      }

      if (!grouped[key]) {
        grouped[key] = { period: key, cost: 0, requests: 0 };
      }
      grouped[key].cost += req.estimated_cost || 0;
      grouped[key].requests += 1;
    });

    return Object.values(grouped).sort((a, b) => {
      // Simple sort by period string (works for our format)
      return a.period.localeCompare(b.period);
    });
  };

  // Process data for cost by model chart
  const getCostByModel = () => {
    if (!stats?.cost_by_model) return [];

    return stats.cost_by_model
      .map(item => ({
        name: item.model,
        cost: item.total_cost || 0,
        requests: item.request_count || 0,
        avgCost: item.avg_cost || 0
      }))
      .sort((a, b) => b.cost - a.cost);
  };

  if (loading) {
    return <div className="cost-explorer"><div className="loading">Loading cost data...</div></div>;
  }

  const costTrends = getCostTrends();
  const costByModel = getCostByModel();
  const totalCost = stats?.total_cost || 0;
  const avgCost = stats?.avg_cost_per_request || 0;
  const cacheStats = stats?.cache_metrics || {};
  const avoidedCost = stats?.avoided_cost_total || cacheStats.estimated_savings || 0;
  const cacheHitRate = cacheStats.hit_rate || stats?.cache_hit_rate || 0;

  return (
    <div className="cost-explorer">
      <div className="cost-explorer-header">
        <h1>💰 Cost Explorer</h1>
        <p className="subtitle">Analyze and optimize your API costs</p>
      </div>

      {/* Summary Cards */}
      <div className="cost-summary-cards">
        <div className="cost-card">
          <div className="cost-card-label">Cost Avoided</div>
          <div className="cost-card-value">{formatCostShort(avoidedCost)}</div>
          <div className="cost-card-detail">Via response cache</div>
        </div>
        <div className="cost-card">
          <div className="cost-card-label">Total Cost</div>
          <div className="cost-card-value">{formatCostShort(totalCost)}</div>
          <div className="cost-card-detail">Across {stats?.total_requests || 0} requests</div>
        </div>
        <div className="cost-card">
          <div className="cost-card-label">Average Cost</div>
          <div className="cost-card-value">{formatCostShort(avgCost)}</div>
          <div className="cost-card-detail">Per request</div>
        </div>
        <div className="cost-card">
          <div className="cost-card-label">Most Expensive</div>
          <div className="cost-card-value">{costByModel[0]?.name || 'N/A'}</div>
          <div className="cost-card-detail">{formatCostShort(costByModel[0]?.cost || 0)} total</div>
        </div>
        <div className="cost-card">
          <div className="cost-card-label">Most Economical</div>
          <div className="cost-card-value">{costByModel[costByModel.length - 1]?.name || 'N/A'}</div>
          <div className="cost-card-detail">{formatCostShort(costByModel[costByModel.length - 1]?.cost || 0)} total</div>
        </div>
        <div className="cost-card">
          <div className="cost-card-label">Cache Hit Rate</div>
          <div className="cost-card-value">{formatPercent(cacheHitRate)}</div>
          <div className="cost-card-detail">{cacheStats.lookups || 0} lookups</div>
        </div>
      </div>

      {/* Time Range Selector */}
      <div className="cost-controls">
        <div className="control-group">
          <label>Time Range:</label>
          <select value={timeRange} onChange={(e) => setTimeRange(e.target.value)}>
            <option value="24h">Last 24 Hours</option>
            <option value="7d">Last 7 Days</option>
            <option value="30d">Last 30 Days</option>
            <option value="all">All Time</option>
          </select>
        </div>
        <div className="control-group">
          <label>Group By:</label>
          <select value={groupBy} onChange={(e) => setGroupBy(e.target.value)}>
            <option value="hour">Hour</option>
            <option value="day">Day</option>
            <option value="week">Week</option>
          </select>
        </div>
      </div>

      {/* Cost Trends Chart */}
      <div className="chart-section">
        <h2>Cost Trends</h2>
        {costTrends.length > 0 ? (
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={costTrends}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="period" />
              <YAxis />
              <Tooltip
                formatter={(value, name) => {
                  if (name === 'cost') return [formatCost(value), 'Cost'];
                  return [value, 'Requests'];
                }}
              />
              <Legend />
              <Line type="monotone" dataKey="cost" stroke="#8884d8" name="Cost ($)" />
              <Line type="monotone" dataKey="requests" stroke="#82ca9d" name="Requests" />
            </LineChart>
          </ResponsiveContainer>
        ) : (
          <div className="no-data">No cost data available for selected time range</div>
        )}
      </div>

      {/* Cost by Model Charts */}
      <div className="charts-row">
        <div className="chart-section half">
          <h2>Cost by Model (Bar Chart)</h2>
          {costByModel.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={costByModel}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip formatter={(value) => formatCost(value)} />
                <Legend />
                <Bar dataKey="cost" fill="#8884d8" name="Total Cost ($)" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div className="no-data">No model cost data available</div>
          )}
        </div>

        <div className="chart-section half">
          <h2>Cost Distribution (Pie Chart)</h2>
          {costByModel.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={costByModel}
                  dataKey="cost"
                  nameKey="name"
                  cx="50%"
                  cy="50%"
                  outerRadius={80}
                  label={(entry) => `${entry.name}: ${formatCostShort(entry.cost)}`}
                >
                  {costByModel.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip formatter={(value) => formatCost(value)} />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div className="no-data">No model cost data available</div>
          )}
        </div>
      </div>

      {/* Cost by Model Table */}
      <div className="chart-section">
        <h2>Detailed Breakdown by Model</h2>
        {costByModel.length > 0 ? (
          <table className="cost-table">
            <thead>
              <tr>
                <th>Model</th>
                <th>Requests</th>
                <th>Total Cost</th>
                <th>Avg Cost/Request</th>
                <th>% of Total</th>
              </tr>
            </thead>
            <tbody>
              {costByModel.map((item, index) => (
                <tr key={index}>
                  <td><strong>{item.name}</strong></td>
                  <td>{item.requests}</td>
                  <td>{formatCost(item.cost)}</td>
                  <td>{formatCost(item.avgCost)}</td>
                  <td>{((item.cost / totalCost) * 100).toFixed(1)}%</td>
                </tr>
              ))}
            </tbody>
            <tfoot>
              <tr>
                <td><strong>Total</strong></td>
                <td><strong>{stats?.total_requests || 0}</strong></td>
                <td><strong>{formatCost(totalCost)}</strong></td>
                <td><strong>{formatCost(avgCost)}</strong></td>
                <td><strong>100%</strong></td>
              </tr>
            </tfoot>
          </table>
        ) : (
          <div className="no-data">No model cost data available</div>
        )}
      </div>

      {/* Insights Section */}
      <div className="insights-section">
        <h2>💡 Insights & Recommendations</h2>
        <div className="insights-grid">
          {costByModel.length > 0 && (
            <>
              <div className="insight-card">
                <div className="insight-icon">📊</div>
                <div className="insight-content">
                  <h3>Most Used Model</h3>
                  <p><strong>{costByModel[0]?.name}</strong> accounts for {((costByModel[0]?.cost / totalCost) * 100).toFixed(1)}% of total costs</p>
                </div>
              </div>

              {avgCost > 0.001 && (
                <div className="insight-card">
                  <div className="insight-icon">💡</div>
                  <div className="insight-content">
                    <h3>Optimization Tip</h3>
                    <p>Consider using gpt-3.5-turbo or gpt-5-nano for simple tasks to reduce costs</p>
                  </div>
                </div>
              )}

              {cacheStats.lookups > 0 && (
                <div className="insight-card">
                  <div className="insight-icon">🛡️</div>
                  <div className="insight-content">
                    <h3>Cache Savings</h3>
                    <p>Saved {formatCostShort(avoidedCost)} with a {formatPercent(cacheHitRate)} hit rate</p>
                  </div>
                </div>
              )}

              <div className="insight-card">
                <div className="insight-icon">📈</div>
                <div className="insight-content">
                  <h3>Request Efficiency</h3>
                  <p>Average cost per request: {formatCostShort(avgCost)}</p>
                </div>
              </div>

              {costByModel.length > 1 && (
                <div className="insight-card">
                  <div className="insight-icon">🎯</div>
                  <div className="insight-content">
                    <h3>Model Diversity</h3>
                    <p>Using {costByModel.length} different models across your requests</p>
                  </div>
                </div>
              )}
            </>
          )}
        </div>
      </div>
    </div>
  );
}

export default CostExplorer;
