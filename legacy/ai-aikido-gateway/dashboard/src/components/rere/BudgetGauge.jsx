import React from 'react';
import './BudgetGauge.css';

/**
 * Budget Gauge Component
 *
 * Displays budget consumption with:
 * - Circular progress gauge
 * - Budget events breakdown
 * - Warning indicators for budget limits
 *
 * @param {number} budgetUsed - Amount of budget used (USD)
 * @param {number} budgetMax - Maximum budget allowed (USD)
 * @param {Array} budgetEvents - Array of budget events
 */
function BudgetGauge({ budgetUsed = 0, budgetMax = 1.0, budgetEvents = [] }) {
  const safeMax = budgetMax > 0 ? budgetMax : 1;
  const percentage = Math.min((budgetUsed / safeMax) * 100, 999);
  const remaining = Math.max(budgetMax - budgetUsed, 0);

  // Determine gauge color based on usage
  const getGaugeColor = (pct) => {
    if (pct >= 90) return '#ef4444'; // red
    if (pct >= 75) return '#f59e0b'; // orange
    if (pct >= 50) return '#eab308'; // yellow
    return '#10b981'; // green
  };

  const gaugeColor = getGaugeColor(percentage);

  // Calculate circle properties for SVG
  const radius = 80;
  const circumference = 2 * Math.PI * radius;
  const offset = circumference - (percentage / 100) * circumference;

  return (
    <div className="budget-gauge">
      <h3>Budget Tracking</h3>

      <div className="gauge-container">
        <svg className="gauge-svg" viewBox="0 0 200 200">
          {/* Background circle */}
          <circle
            className="gauge-bg"
            cx="100"
            cy="100"
            r={radius}
            fill="none"
            stroke="#e5e7eb"
            strokeWidth="12"
          />

          {/* Progress circle */}
          <circle
            className="gauge-progress"
            cx="100"
            cy="100"
            r={radius}
            fill="none"
            stroke={gaugeColor}
            strokeWidth="12"
            strokeDasharray={circumference}
            strokeDashoffset={offset}
            transform="rotate(-90 100 100)"
            strokeLinecap="round"
          />

          {/* Center text */}
          <text x="100" y="90" textAnchor="middle" className="gauge-value">
            {percentage.toFixed(0)}%
          </text>
          <text x="100" y="115" textAnchor="middle" className="gauge-label">
            Budget Used
          </text>
        </svg>
      </div>

      <div className="budget-stats">
        <div className="stat-row">
          <span className="stat-label">Used:</span>
          <span className="stat-value">${budgetUsed.toFixed(4)}</span>
        </div>
        <div className="stat-row">
          <span className="stat-label">Remaining:</span>
          <span className="stat-value remaining">${remaining.toFixed(4)}</span>
        </div>
        <div className="stat-row">
          <span className="stat-label">Max:</span>
          <span className="stat-value">${budgetMax.toFixed(4)}</span>
        </div>
      </div>

      {budgetEvents.length > 0 && (
        <div className="budget-events">
          <h4>Budget Events</h4>
          <div className="events-list">
            {budgetEvents.map((event, index) => (
              <div
                key={index}
                className={`budget-event ${event.event_type || event.reason}`}
              >
                <div className="event-header">
                  <span className="event-tool">{event.tool}</span>
                  <span className="event-amount">
                    ${Number(event.amount || 0).toFixed(4)}
                  </span>
                </div>
                {(event.event_type === 'budget_guardrail' || event.reason === 'budget_guardrail') && (
                  <div className="event-warning">⚠️ Budget limit prevented execution</div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {percentage >= 90 && (
        <div className="budget-warning">
          <span className="warning-icon">⚠️</span>
          <span className="warning-text">Budget nearly exhausted!</span>
        </div>
      )}
    </div>
  );
}

export default BudgetGauge;
