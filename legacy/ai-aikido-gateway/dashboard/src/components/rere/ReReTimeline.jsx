import React, { useEffect, useMemo, useRef } from 'react';
import './ReReTimeline.css';

const PHASE_CONFIG = {
  reason: {
    label: 'REASON',
    icon: '🧠',
    color: '#3b82f6',
    description: 'Analyze intent and plan next step'
  },
  act: {
    label: 'ACT',
    icon: '⚡',
    color: '#10b981',
    description: 'Execute tool and capture result'
  },
  reflect: {
    label: 'REFLECT',
    icon: '💭',
    color: '#f59e0b',
    description: 'Evaluate quality and extract insights'
  },
  're-reason': {
    label: 'RE-REASON',
    icon: '🔄',
    color: '#8b5cf6',
    description: 'Decide whether to continue or complete'
  }
};

/**
 * Re^Re Timeline Component
 *
 * Visualizes the Reflective Reasoning loop execution:
 * - Timeline of events grouped by Re^Re phase
 * - Step-by-step progression
 * - Phase indicators with icons and colors
 * - Event details and metadata
 *
 * @param {Array} events - Array of workflow events
 * @param {Object} currentState - Current execution state
 * @param {boolean} isLive - Whether timeline is streaming live
 */
function ReReTimeline({ events = [], currentState, isLive = false, activeStep = null }) {
  const timelineEndRef = useRef(null);

  // Auto-scroll to latest event in live mode
  useEffect(() => {
    if (isLive && timelineEndRef.current) {
      timelineEndRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [events, isLive]);

  const groupedEvents = useMemo(() => {
    return events.reduce((acc, event) => {
      const step = (event.stepIndex ?? event.step ?? 0) || 0;
      if (!acc[step]) {
        acc[step] = [];
      }
      acc[step].push(event);
      return acc;
    }, {});
  }, [events]);

  const steps = useMemo(
    () => Object.keys(groupedEvents).map(Number).sort((a, b) => a - b),
    [groupedEvents]
  );

  const visibleSteps = useMemo(() => {
    if (!activeStep) return steps;
    return steps.filter((step) => step <= activeStep);
  }, [steps, activeStep]);

  const renderSummary = (event, phaseConfig) => {
    return (
      event.metadata?.last_decision?.message ||
      event.metadata?.summary ||
      phaseConfig.description
    );
  };

  const renderDataItems = (event) => {
    const artifact = event.metadata?.last_artifact;
    const budgetEvent = event.metadata?.last_budget_event;
    const toolInput = event.metadata?.tool_input;

    return (
      <>
        {event.tool && (
          <div className="data-item">
            <span className="data-label">Tool:</span>
            <span className="data-value">{event.tool}</span>
          </div>
        )}
        {budgetEvent && (
          <div className="data-item">
            <span className="data-label">Budget:</span>
            <span className="data-value">
              {budgetEvent.reason || budgetEvent.event_type} (${Number(budgetEvent.amount || 0).toFixed(4)})
            </span>
          </div>
        )}
        {event.qualityScore !== undefined && (
          <div className="data-item">
            <span className="data-label">Quality:</span>
            <span className="data-value quality">
              {Number(event.qualityScore || 0).toFixed(2)}
            </span>
          </div>
        )}
        {event.remainingBudget !== undefined && (
          <div className="data-item">
            <span className="data-label">Remaining Budget:</span>
            <span className="data-value">
              ${Number(event.remainingBudget || 0).toFixed(4)}
            </span>
          </div>
        )}
        {artifact && artifact.output && (
          <details className="event-metadata">
            <summary>Artifact Output</summary>
            <pre>{JSON.stringify(artifact.output, null, 2)}</pre>
          </details>
        )}
        {toolInput && (
          <details className="event-metadata">
            <summary>Tool Input</summary>
            <pre>{JSON.stringify(toolInput, null, 2)}</pre>
          </details>
        )}
      </>
    );
  };

  if (events.length === 0) {
    return (
      <div className="timeline-empty">
        <div className="empty-icon">🎬</div>
        <div className="empty-message">
          {isLive ? 'Waiting for execution events...' : 'No events to display'}
        </div>
        {!isLive && (
          <div className="empty-hint">
            Start a demo execution to see the Re^Re loop in action
          </div>
        )}
      </div>
    );
  }

  return (
    <div className="rere-timeline">
      <div className="timeline-header">
        <h3>Execution Timeline</h3>
        {isLive && <span className="live-indicator">● LIVE</span>}
      </div>

      <div className="timeline-scroll">
        {visibleSteps.map((step) => {
          const stepEvents = groupedEvents[step];

          return (
            <div
              key={step}
              className={`timeline-step ${activeStep === step ? 'step-active' : ''}`}
            >
              <div className="step-header">
                <div className="step-number">Step {step}</div>
                <div className="step-count">{stepEvents.length} events</div>
              </div>

              <div className="step-events">
                {stepEvents.map((event, index) => {
                  const phaseConfig = PHASE_CONFIG[event.phase] || {
                    label: event.phase.toUpperCase(),
                    icon: '•',
                    color: '#6b7280',
                    description: event.phase
                  };

                  return (
                    <div
                      key={index}
                      className={`timeline-event phase-${event.phase}`}
                      style={{ borderLeftColor: phaseConfig.color }}
                    >
                      <div className="event-header">
                        <div className="event-phase">
                          <span className="phase-icon">{phaseConfig.icon}</span>
                          <span className="phase-label">{phaseConfig.label}</span>
                        </div>
                        <div className="event-time">
                          {event.timestamp ? new Date(event.timestamp).toLocaleTimeString() : ''}
                        </div>
                      </div>

                      <div className="event-description">
                        {renderSummary(event, phaseConfig)}
                      </div>

                      <div className="event-data">
                        {renderDataItems(event)}
                      </div>

                      {event.metadata && Object.keys(event.metadata).length > 0 && (
                        <details className="event-metadata">
                          <summary>Raw Metadata</summary>
                          <pre>{JSON.stringify(event.metadata, null, 2)}</pre>
                        </details>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          );
        })}
        <div ref={timelineEndRef} />
      </div>

      {currentState && (
        <div className="timeline-footer">
          <div className="footer-stat">
            <span className="stat-label">Total Steps:</span>
            <span className="stat-value">{steps.length}</span>
          </div>
          <div className="footer-stat">
            <span className="stat-label">Status:</span>
            <span className={`stat-value ${currentState.should_continue ? 'running' : 'complete'}`}>
              {currentState.should_continue ? 'Running' : 'Complete'}
            </span>
          </div>
          {currentState.error && (
            <div className="footer-error">
              Error: {currentState.error}
            </div>
          )}
        </div>
      )}
    </div>
  );
}

export default ReReTimeline;
