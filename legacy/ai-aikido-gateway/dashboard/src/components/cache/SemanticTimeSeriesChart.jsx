import React, { useEffect, useState } from 'react';
import './SemanticTimeSeriesChart.css';

const SemanticTimeSeriesChart = ({ enabled }) => {
  const [timeseriesData, setTimeseriesData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [timeRange, setTimeRange] = useState('1h'); // 1h, 6h, 24h

  useEffect(() => {
    if (!enabled) {
      setLoading(false);
      return;
    }

    fetchTimeseries();
    const interval = setInterval(fetchTimeseries, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, [enabled, timeRange]);

  const fetchTimeseries = async () => {
    try {
      setLoading(true);

      // Calculate time range in seconds
      const ranges = {
        '1h': 3600,
        '6h': 21600,
        '24h': 86400
      };
      const seconds = ranges[timeRange] || 3600;
      const end = Math.floor(Date.now() / 1000);
      const start = end - seconds;

      const response = await fetch(
        `http://localhost:8000/v1/cache/semantic/timeseries?start=${start}&end=${end}&limit=100`
      );

      if (!response.ok) {
        throw new Error('Failed to fetch timeseries data');
      }

      const data = await response.json();

      // Reverse data to show oldest first (for left-to-right chart)
      const reversed = (data.data || []).reverse();
      setTimeseriesData(reversed);
      setError(null);
    } catch (err) {
      console.error('Error fetching timeseries:', err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const formatTime = (timestamp) => {
    const date = new Date(timestamp * 1000);
    return date.toLocaleTimeString('en-US', {
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const formatPercent = (value) => {
    return `${(value * 100).toFixed(1)}%`;
  };

  if (!enabled) {
    return (
      <div className="timeseries-chart disabled">
        <h3>📈 Hit Rate Trends</h3>
        <div className="timeseries-status">
          <p>Semantic cache is disabled. Enable to see time-series metrics.</p>
        </div>
      </div>
    );
  }

  if (loading && timeseriesData.length === 0) {
    return (
      <div className="timeseries-chart">
        <h3>📈 Hit Rate Trends</h3>
        <div className="timeseries-status">Loading...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="timeseries-chart">
        <h3>📈 Hit Rate Trends</h3>
        <div className="timeseries-status error">{error}</div>
      </div>
    );
  }

  if (timeseriesData.length === 0) {
    return (
      <div className="timeseries-chart">
        <h3>📈 Hit Rate Trends</h3>
        <div className="timeseries-controls">
          <button
            className={timeRange === '1h' ? 'active' : ''}
            onClick={() => setTimeRange('1h')}
          >
            1 Hour
          </button>
          <button
            className={timeRange === '6h' ? 'active' : ''}
            onClick={() => setTimeRange('6h')}
          >
            6 Hours
          </button>
          <button
            className={timeRange === '24h' ? 'active' : ''}
            onClick={() => setTimeRange('24h')}
          >
            24 Hours
          </button>
        </div>
        <div className="timeseries-status">
          No data available yet. Metrics are recorded every 60 seconds.
        </div>
      </div>
    );
  }

  // Find min/max values for scaling
  const hitRates = timeseriesData.map((d) => d.hit_rate || 0);
  const similarities = timeseriesData.map((d) => d.average_similarity || 0);
  const maxHitRate = Math.max(...hitRates, 0.1);
  const maxSimilarity = Math.max(...similarities, 0.1);

  // Calculate chart dimensions
  const chartWidth = 800;
  const chartHeight = 300;
  const padding = { top: 20, right: 50, bottom: 50, left: 50 };
  const innerWidth = chartWidth - padding.left - padding.right;
  const innerHeight = chartHeight - padding.top - padding.bottom;

  // Generate path data for lines
  const generatePath = (data, key, maxValue) => {
    if (data.length === 0) return '';

    const points = data.map((d, i) => {
      const x = padding.left + (i / (data.length - 1)) * innerWidth;
      const y = padding.top + innerHeight - (d[key] / maxValue) * innerHeight;
      return `${x},${y}`;
    });

    return `M ${points.join(' L ')}`;
  };

  const hitRatePath = generatePath(timeseriesData, 'hit_rate', 1.0);
  const similarityPath = generatePath(timeseriesData, 'average_similarity', 1.0);

  // Generate grid lines
  const gridLines = [0, 0.25, 0.5, 0.75, 1.0].map((value) => {
    const y = padding.top + innerHeight - value * innerHeight;
    return { y, value };
  });

  // Sample time labels (show ~5 labels)
  const timeLabels = [];
  const step = Math.max(1, Math.floor(timeseriesData.length / 5));
  for (let i = 0; i < timeseriesData.length; i += step) {
    const d = timeseriesData[i];
    const x = padding.left + (i / (timeseriesData.length - 1)) * innerWidth;
    timeLabels.push({ x, label: formatTime(d.timestamp) });
  }

  return (
    <div className="timeseries-chart">
      <div className="timeseries-header">
        <h3>📈 Hit Rate Trends</h3>
        <div className="timeseries-controls">
          <button
            className={timeRange === '1h' ? 'active' : ''}
            onClick={() => setTimeRange('1h')}
          >
            1 Hour
          </button>
          <button
            className={timeRange === '6h' ? 'active' : ''}
            onClick={() => setTimeRange('6h')}
          >
            6 Hours
          </button>
          <button
            className={timeRange === '24h' ? 'active' : ''}
            onClick={() => setTimeRange('24h')}
          >
            24 Hours
          </button>
        </div>
      </div>

      <div className="chart-legend">
        <div className="legend-item">
          <span className="legend-color hit-rate"></span>
          <span className="legend-label">Hit Rate</span>
        </div>
        <div className="legend-item">
          <span className="legend-color similarity"></span>
          <span className="legend-label">Avg Similarity</span>
        </div>
      </div>

      <svg
        className="chart-svg"
        width={chartWidth}
        height={chartHeight}
        viewBox={`0 0 ${chartWidth} ${chartHeight}`}
      >
        {/* Grid lines */}
        {gridLines.map((line, i) => (
          <g key={i}>
            <line
              x1={padding.left}
              y1={line.y}
              x2={chartWidth - padding.right}
              y2={line.y}
              className="grid-line"
            />
            <text
              x={padding.left - 10}
              y={line.y + 5}
              className="axis-label"
              textAnchor="end"
            >
              {formatPercent(line.value)}
            </text>
          </g>
        ))}

        {/* Time labels */}
        {timeLabels.map((label, i) => (
          <text
            key={i}
            x={label.x}
            y={chartHeight - padding.bottom + 20}
            className="time-label"
            textAnchor="middle"
          >
            {label.label}
          </text>
        ))}

        {/* Similarity line (behind) */}
        <path
          d={similarityPath}
          className="chart-line similarity-line"
          fill="none"
        />

        {/* Hit rate line (front) */}
        <path
          d={hitRatePath}
          className="chart-line hit-rate-line"
          fill="none"
        />

        {/* Data points */}
        {timeseriesData.map((d, i) => {
          const x = padding.left + (i / (timeseriesData.length - 1)) * innerWidth;
          const yHit = padding.top + innerHeight - (d.hit_rate / 1.0) * innerHeight;
          const ySim = padding.top + innerHeight - (d.average_similarity / 1.0) * innerHeight;

          return (
            <g key={i}>
              <circle
                cx={x}
                cy={yHit}
                r="3"
                className="data-point hit-rate-point"
              >
                <title>
                  {formatTime(d.timestamp)}: Hit Rate {formatPercent(d.hit_rate)}
                </title>
              </circle>
              <circle
                cx={x}
                cy={ySim}
                r="3"
                className="data-point similarity-point"
              >
                <title>
                  {formatTime(d.timestamp)}: Avg Similarity {(d.average_similarity || 0).toFixed(3)}
                </title>
              </circle>
            </g>
          );
        })}
      </svg>

      <div className="chart-summary">
        <div className="summary-item">
          <span className="summary-label">Samples:</span>
          <span className="summary-value">{timeseriesData.length}</span>
        </div>
        <div className="summary-item">
          <span className="summary-label">Latest Hit Rate:</span>
          <span className="summary-value">
            {formatPercent(timeseriesData[timeseriesData.length - 1]?.hit_rate || 0)}
          </span>
        </div>
        <div className="summary-item">
          <span className="summary-label">Latest Similarity:</span>
          <span className="summary-value">
            {(timeseriesData[timeseriesData.length - 1]?.average_similarity || 0).toFixed(3)}
          </span>
        </div>
      </div>
    </div>
  );
};

export default SemanticTimeSeriesChart;
