import React, { useState } from 'react';
import './ExecutionControls.css';
import API_URL from '../../config';

/**
 * Execution Controls Component
 *
 * Provides controls for:
 * - Starting new demo executions
 * - Loading historical executions
 * - Toggling comparison mode
 * - Exporting execution data
 *
 * @param {Function} onStartDemo - Handler for starting new execution
 * @param {Function} onLoadExecution - Handler for loading historical execution
 * @param {Function} onToggleCompare - Handler for toggling comparison mode
 * @param {boolean} isLive - Whether currently in live mode
 * @param {boolean} compareMode - Whether in comparison mode
 * @param {string} currentExecutionId - Current execution ID
 */
function ExecutionControls({
  onStartDemo,
  onLoadExecution,
  onToggleCompare,
  isLive,
  compareMode,
  currentExecutionId,
  compareInput,
  onCompareInputChange,
  onLoadCompareExecution,
  compareExecutionId,
  compareError,
}) {
  const [loadId, setLoadId] = useState('');
  const [showLoadInput, setShowLoadInput] = useState(false);

  const handleLoad = () => {
    if (loadId.trim()) {
      onLoadExecution(loadId.trim());
      setShowLoadInput(false);
      setLoadId('');
    }
  };

  const handleExport = () => {
    if (!currentExecutionId) return;

    const base = API_URL.replace(/\/$/, '');
    const url = `${base}/v1/re-re/executions/${currentExecutionId}/export`;
    window.open(url, '_blank', 'noopener');
  };

  return (
    <div className="execution-controls">
      <div className="controls-group">
        <button
          className="btn btn-primary"
          onClick={onStartDemo}
          disabled={isLive}
        >
          <span className="btn-icon">▶️</span>
          Start Demo
        </button>

        {!showLoadInput ? (
          <button
            className="btn btn-secondary"
            onClick={() => setShowLoadInput(true)}
          >
            <span className="btn-icon">📂</span>
            Load Execution
          </button>
        ) : (
          <div className="load-input-group">
            <input
              type="text"
              className="load-input"
              placeholder="Execution ID..."
              value={loadId}
              onChange={(e) => setLoadId(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleLoad()}
            />
            <button className="btn btn-sm" onClick={handleLoad}>
              Load
            </button>
            <button
              className="btn btn-sm btn-cancel"
              onClick={() => {
                setShowLoadInput(false);
                setLoadId('');
              }}
            >
              Cancel
            </button>
          </div>
        )}
      </div>

      <div className="controls-group">
        <button
          className={`btn ${compareMode ? 'btn-active' : 'btn-secondary'}`}
          onClick={onToggleCompare}
          disabled={!currentExecutionId}
        >
          <span className="btn-icon">⚖️</span>
          {compareMode ? 'Exit Compare' : 'Compare'}
        </button>

        <button
          className="btn btn-secondary"
          onClick={handleExport}
          disabled={!currentExecutionId}
        >
          <span className="btn-icon">💾</span>
          Export
        </button>
      </div>

      {compareMode && (
        <div className="compare-controls">
          <div className="compare-input">
            <label>Execution B</label>
            <div className="compare-input-row">
              <input
                type="text"
                placeholder="Enter execution ID..."
                value={compareInput}
                onChange={(e) => onCompareInputChange(e.target.value)}
              />
              <button
                className="btn btn-sm"
                onClick={onLoadCompareExecution}
                disabled={!compareInput.trim()}
              >
                Load
              </button>
            </div>
            {compareExecutionId && (
              <div className="compare-loaded">
                Loaded: <span>{compareExecutionId.substring(0, 12)}</span>
              </div>
            )}
            {compareError && <div className="compare-error">{compareError}</div>}
          </div>
        </div>
      )}
    </div>
  );
}

export default ExecutionControls;
