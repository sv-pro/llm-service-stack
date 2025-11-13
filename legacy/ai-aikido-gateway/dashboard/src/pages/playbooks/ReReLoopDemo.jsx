import React, { useEffect, useMemo, useState } from 'react';
import { useTelemetry } from '../../hooks/useTelemetry';
import ReReTimeline from '../../components/rere/ReReTimeline';
import BudgetGauge from '../../components/rere/BudgetGauge';
import ExecutionControls from '../../components/rere/ExecutionControls';
import './ReReLoopDemo.css';
import API_URL from '../../config';

/**
 * Re^Re Loop Demo Page
 *
 * Interactive demonstration of the Reflective Reasoning loop:
 * Reason → Act → Reflect → Re-reason → ∞
 *
 * Features:
 * - Live telemetry streaming via WebSocket
 * - Step-by-step timeline visualization
 * - Budget consumption tracking
 * - Quality score trends
 * - Decision log
 * - Replay and comparison modes
 */
const DEMO_ENABLED = (import.meta.env.VITE_ENABLE_RE_RE_DEMO ?? 'true') !== 'false';

function ReReLoopDemo() {
  const [executionId, setExecutionId] = useState(null);
  const [isLive, setIsLive] = useState(false);
  const [compareMode, setCompareMode] = useState(false);
  const [compareInput, setCompareInput] = useState('');
  const [activeCompareId, setActiveCompareId] = useState(null);
  const [infoMessage, setInfoMessage] = useState(null);
  const [comparisonSummary, setComparisonSummary] = useState(null);
  const [comparisonError, setComparisonError] = useState(null);
  const [scrubberStep, setScrubberStep] = useState(0);
  const [isPlaying, setIsPlaying] = useState(false);

  // Connect to telemetry stream
  console.log('ReReLoopDemo before TM: Using executionId=', executionId, 'isLive=', isLive, 'DEMO_ENABLED=', DEMO_ENABLED);
  const {
    events,
    currentState,
    isConnected,
    error,
    startExecution,
    loadExecution,
    diagnostics,
    serverStatus,
     statusError,
  } = useTelemetry(executionId, isLive && DEMO_ENABLED);
  // log the same info for comparison telemetry
  console.log('ReReLoopDemo after TM: Using executionId=', executionId, 'isLive=', isLive, 'DEMO_ENABLED=', DEMO_ENABLED);

  const {
    events: compareEvents,
    currentState: compareState,
    error: compareTelemetryError,
  } = useTelemetry(activeCompareId, false);

  const handleStartDemo = async () => {
    if (!DEMO_ENABLED) {
      setInfoMessage('Enable RE_RE_DEMO_ENABLED=true on the gateway to stream live telemetry.');
      return;
    }
    try {
      const newExecutionId = await startExecution({
        intent: "Demo: Calculate 10 + 20 and analyze the result",
        config: {
          max_steps: 3,
          budget_max: 0.05,
          quality_threshold: 0.7
        }
      });
      setExecutionId(newExecutionId);
      setIsLive(true);
      setInfoMessage(null);
    } catch (err) {
      console.error('Failed to start demo:', err);
    }
  };

  const handleLoadExecution = async (id) => {
    try {
      await loadExecution(id);
      setExecutionId(id);
      setIsLive(false);
      setInfoMessage(null);
    } catch (err) {
      console.error('Failed to load execution:', err);
    }
  };

  const handleToggleCompare = () => {
    setCompareMode(!compareMode);
    if (compareMode) {
      setActiveCompareId(null);
      setCompareInput('');
      setComparisonSummary(null);
      setComparisonError(null);
    }
  };

  const budgetMetrics = useMemo(() => {
    if (!currentState) {
      return {
        budgetUsed: 0,
        budgetMax: 1,
        budgetEvents: [],
        stepsCompleted: 0,
        qualityScore: 0,
        reasoningTokens: 0,
      };
    }

    const budgetMax =
      currentState.context?.budget_max ??
      currentState.context?.budgetMax ??
      currentState.budget_max ??
      1;

    return {
      budgetUsed: currentState.budget_used || 0,
      budgetMax: budgetMax || 1,
      budgetEvents: currentState.budget_events || [],
      stepsCompleted: (currentState.steps_completed || []).length,
      qualityScore: currentState.quality_score || 0,
      reasoningTokens: currentState.reasoning_tokens || 0,
    };
  }, [currentState]);

  const maxStep = useMemo(() => {
    if (!events.length) return 0;
    return events.reduce(
      (max, event) => Math.max(max, event.stepIndex ?? event.step ?? 0),
      0
    );
  }, [events]);

  useEffect(() => {
    if (maxStep > 0) {
      setScrubberStep(maxStep);
    } else {
      setScrubberStep(0);
      setIsPlaying(false);
    }
  }, [maxStep]);

  useEffect(() => {
    if (!isPlaying) return;
    if (scrubberStep >= maxStep) {
      setIsPlaying(false);
      return;
    }
    const timer = setTimeout(() => {
      setScrubberStep((prev) => Math.min(prev + 1, maxStep));
    }, 1000);
    return () => clearTimeout(timer);
  }, [isPlaying, scrubberStep, maxStep]);

  useEffect(() => {
    if (!executionId || !activeCompareId || executionId === activeCompareId) {
      setComparisonSummary(null);
      setComparisonError(null);
      return;
    }

    const controller = new AbortController();
    const fetchSummary = async () => {
      try {
        const base = API_URL.replace(/\/$/, '');
        const response = await fetch(
          `${base}/v1/re-re/executions/compare?a=${encodeURIComponent(
            executionId
          )}&b=${encodeURIComponent(activeCompareId)}`,
          { signal: controller.signal }
        );
        if (!response.ok) {
          throw new Error(await response.text());
        }
        const data = await response.json();
        setComparisonSummary(data);
        setComparisonError(null);
      } catch (err) {
        if (controller.signal.aborted) return;
        console.error('Failed to fetch comparison summary:', err);
        setComparisonSummary(null);
        setComparisonError('Failed to load comparison summary');
      }
    };

    fetchSummary();
    return () => controller.abort();
  }, [executionId, activeCompareId]);

  return (
    <div className="rere-demo-page">
      <div className="page-header">
        <h1>Re^Re Loop Demo</h1>
        <p className="subtitle">
          Reason → Act → Reflect → Re-reason → ∞
        </p>
        {!DEMO_ENABLED && (
          <div className="feature-flag-warning">
            Re^Re telemetry is disabled. Set <code>RE_RE_DEMO_ENABLED=true</code> and restart the gateway to stream live data.
          </div>
        )}
      </div>

      <div className="connection-status">
        {isConnected ? (
          <span className="status-badge connected">
            <span className="status-dot"></span>
            Live Connected
          </span>
        ) : isLive && executionId ? (
          <span className="status-badge disconnected">
            <span className="status-dot"></span>
            Disconnected
          </span>
        ) : executionId && !isLive ? (
          <span className="status-badge replay">
            <span className="status-dot"></span>
            Replay Mode
          </span>
        ) : (
          <span className="status-badge idle">
            <span className="status-dot"></span>
            Ready
          </span>
        )}
        {error && <span className="error-message">{error}</span>}
        {infoMessage && <span className="info-message">{infoMessage}</span>}
      </div>
      <div className="connection-console">
        <div className="console-header">
          <strong>Diagnostics</strong>
          <small>Last {diagnostics.length} events</small>
        </div>
        <div className="console-scroll">
          {diagnostics.length === 0 ? (
            <div className="console-empty">No telemetry events yet.</div>
          ) : (
            diagnostics.map((entry, idx) => (
              <div key={idx} className="console-line">
                <span className="console-timestamp">
                  {new Date(entry.timestamp).toLocaleTimeString()}
                </span>
                <span className="console-message">{entry.message}</span>
              </div>
            ))
          )}
        </div>
      </div>
      <div className="status-grid">
        <div className="status-card">
          <div className="status-label">Emitter Enabled</div>
          <div className="status-value">
            {serverStatus?.emitter?.status?.enabled ? 'Yes' : 'No'}
          </div>
        </div>
        <div className="status-card">
          <div className="status-label">Redis URL</div>
          <div className="status-value monospace">
            {serverStatus?.emitter?.status?.redis_url || '—'}
          </div>
        </div>
        <div className="status-card">
          <div className="status-label">Active WebSockets</div>
          <div className="status-value">
            {Object.values(serverStatus?.websockets?.connections || {}).reduce(
              (sum, count) => sum + count,
              0
            )}
          </div>
        </div>
        <div className="status-card">
          <div className="status-label">Status API</div>
          <div className="status-value">
            {statusError ? `Error: ${statusError}` : 'OK'}
          </div>
        </div>
      </div>

      <ExecutionControls
        onStartDemo={handleStartDemo}
        onLoadExecution={handleLoadExecution}
        onToggleCompare={handleToggleCompare}
        isLive={isLive}
        compareMode={compareMode}
        currentExecutionId={executionId}
        compareInput={compareInput}
        onCompareInputChange={setCompareInput}
        onLoadCompareExecution={() => {
          if (compareInput.trim()) {
            setActiveCompareId(compareInput.trim());
            setComparisonSummary(null);
          }
        }}
        compareExecutionId={activeCompareId}
        compareError={compareTelemetryError || comparisonError}
      />

      <div className="demo-grid">
        <div className="budget-panel">
          <BudgetGauge
            budgetUsed={budgetMetrics.budgetUsed}
            budgetMax={budgetMetrics.budgetMax}
            budgetEvents={budgetMetrics.budgetEvents}
          />
        </div>

        <div className="metrics-panel">
          <div className="metric-card">
            <div className="metric-label">Steps Completed</div>
            <div className="metric-value">
              {budgetMetrics.stepsCompleted}
            </div>
          </div>
          <div className="metric-card">
            <div className="metric-label">Quality Score</div>
            <div className="metric-value quality">
              {budgetMetrics.qualityScore.toFixed(2)}
            </div>
          </div>
          <div className="metric-card">
            <div className="metric-label">Reasoning Tokens</div>
            <div className="metric-value">
              {budgetMetrics.reasoningTokens}
            </div>
          </div>
        </div>
      </div>

      <div className="timeline-container">
        {events.length > 0 && (
          <div className="scrubber-controls">
            <button
              className="btn btn-secondary"
              onClick={() => setIsPlaying((prev) => !prev)}
              disabled={maxStep === 0}
            >
              {isPlaying ? 'Pause' : 'Play'}
            </button>
            <input
              type="range"
              min="0"
              max={maxStep || 0}
              value={scrubberStep}
              onChange={(e) => {
                setScrubberStep(Number(e.target.value));
                setIsPlaying(false);
              }}
            />
            <span className="scrubber-label">
              Step {scrubberStep}/{maxStep || 0}
            </span>
          </div>
        )}

        {compareMode ? (
          <div className="comparison-view">
            <div className="comparison-panel">
              <h3>Execution A: {executionId ? executionId.substring(0, 8) : 'N/A'}</h3>
              <ReReTimeline
                events={events}
                currentState={currentState}
                isLive={isLive}
                activeStep={scrubberStep || null}
              />
            </div>
            <div className="comparison-panel">
              <h3>Execution B: {activeCompareId ? activeCompareId.substring(0, 8) : 'N/A'}</h3>
              {activeCompareId && compareEvents.length > 0 ? (
                <ReReTimeline
                  events={compareEvents}
                  currentState={compareState}
                  isLive={false}
                />
              ) : (
                <p className="compare-placeholder">
                  Enter an execution ID to load a comparison timeline.
                </p>
              )}
            </div>
          </div>
        ) : (
          <ReReTimeline
            events={events}
            currentState={currentState}
            isLive={isLive}
            activeStep={scrubberStep || null}
          />
        )}
      </div>

      {compareMode && comparisonSummary && (
        <div className="comparison-summary">
          <h3>Comparison Summary</h3>
          <div className="comparison-grid">
            <div className="comparison-card">
              <span>Budget Δ</span>
              <strong>
                ${comparisonSummary.comparison.budget_delta.toFixed(4)}
              </strong>
            </div>
            <div className="comparison-card">
              <span>Quality Δ</span>
              <strong>
                {comparisonSummary.comparison.quality_delta.toFixed(3)}
              </strong>
            </div>
            <div className="comparison-card">
              <span>Events Δ</span>
              <strong>{comparisonSummary.comparison.event_count_delta}</strong>
            </div>
          </div>
        </div>
      )}

      {currentState?.decision_log && currentState.decision_log.length > 0 && (
        <div className="decision-log-panel">
          <h3>Decision Log</h3>
          <div className="decision-log-scroll">
            {currentState.decision_log.map((entry, index) => (
              <div key={index} className={`decision-entry phase-${entry.phase}`}>
                <div className="decision-header">
                  <span className="decision-phase">{entry.phase.toUpperCase()}</span>
                  {entry.step && (
                    <span className="decision-step">Step {entry.step}</span>
                  )}
                  {entry.timestamp && (
                    <span className="decision-time">
                      {new Date(entry.timestamp).toLocaleTimeString()}
                    </span>
                  )}
                </div>
                <div className="decision-message">{entry.message}</div>
                {entry.data && (
                  <div className="decision-data">
                    <pre>{JSON.stringify(entry.data, null, 2)}</pre>
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {currentState?.artifacts && currentState.artifacts.length > 0 && (
        <div className="artifacts-panel">
          <h3>Artifacts Generated</h3>
          <div className="artifacts-grid">
            {currentState.artifacts.map((artifact, index) => (
              <div key={index} className="artifact-card">
                <div className="artifact-header">
                  <span className="artifact-step">Step {artifact.step}</span>
                  <span className="artifact-tool">{artifact.tool}</span>
                </div>
                <div className="artifact-output">
                  <pre>{JSON.stringify(artifact.output, null, 2)}</pre>
                </div>
                <div className="artifact-meta">
                  Cost: ${artifact.cost?.toFixed(4) || '0.0000'}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

export default ReReLoopDemo;
