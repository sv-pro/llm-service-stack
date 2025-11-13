import { useState, useEffect, useRef, useCallback } from 'react';
import API_URL from '../config';

const sanitizeBase = (value, fallback) => {
  if (!value) return fallback;
  return value.replace(/\/$/, '');
};

const httpToWs = (base) => {
  if (!base) return 'ws://localhost:8000';

  try {
    const parsed = new URL(base);
    const protocol = parsed.protocol === 'https:' ? 'wss:' : 'ws:';
    return `${protocol}//${parsed.host}`;
  } catch {
    return base.replace(/^http/, 'ws');
  }
};

const API_BASE_URL = sanitizeBase(API_URL, 'http://localhost:8000');
const WS_OVERRIDE = sanitizeBase(import.meta.env.VITE_WS_URL, null);
const WS_BASE_URL = sanitizeBase(WS_OVERRIDE || httpToWs(API_BASE_URL), 'ws://localhost:8000');
const STATUS_ENDPOINT = `${API_BASE_URL}/v1/re-re/status`;
const EXECUTIONS_ENDPOINT = `${API_BASE_URL}/v1/re-re/executions`;
const PLAYBOOK_EXECUTE_ENDPOINT = `${API_BASE_URL}/v1/playbooks/execute`;

const fallbackId = () =>
  (typeof crypto !== 'undefined' && crypto.randomUUID
    ? crypto.randomUUID()
    : `event_${Date.now()}_${Math.random().toString(16).slice(2)}`);

const transformEvent = (raw) => {
  if (!raw) return null;

  const metadata = raw.metadata || {};
  return {
    id: raw.event_id || raw.eventId || fallbackId(),
    phase: raw.phase,
    status: raw.status,
    stepIndex: raw.step_index ?? raw.step ?? 0,
    node: raw.node,
    tool: raw.tool || metadata?.last_artifact?.tool,
    budgetUsed: raw.budget_used ?? metadata?.last_budget_event?.amount ?? 0,
    remainingBudget: raw.remaining_budget ?? 0,
    qualityScore: raw.quality_score ?? metadata?.last_decision?.data?.quality_score,
    reasoningTokens: raw.reasoning_tokens,
    timestamp: raw.created_at || metadata?.last_decision?.timestamp,
    metadata,
    stateSnapshot: raw.state_snapshot || metadata?.state_snapshot || null,
  };
};

/**
 * Hook for connecting to Re^Re workflow telemetry stream
 *
 * Provides:
 * - Real-time event streaming via WebSocket
 * - Execution state management
 * - Replay capability for historical executions
 * - Error handling and reconnection
 *
 * @param {string|null} executionId - Execution ID to monitor/replay
 * @param {boolean} isLive - Whether to connect to live stream
 * @returns {object} Telemetry state and control functions
 */
export function useTelemetry(executionId, isLive = false) {
  const [events, setEvents] = useState([]);
  const [currentState, setCurrentState] = useState(null);
  const [isConnected, setIsConnected] = useState(false);
  const [error, setError] = useState(null);
  const [diagnostics, setDiagnostics] = useState([]);
  const [serverStatus, setServerStatus] = useState(null);
  const [statusError, setStatusError] = useState(null);

  const wsRef = useRef(null);
  const reconnectTimeoutRef = useRef(null);
  const reconnectAttempts = useRef(0);

  const logDiag = useCallback((message) => {
    const entry = {
      timestamp: new Date().toISOString(),
      message,
    };
    setDiagnostics((prev) => [...prev.slice(-9), entry]);
    console.debug('[ReRe Telemetry]', message);
  }, []);

  // Connect to WebSocket for live telemetry
  const connect = useCallback(() => {
    if (!isLive) {
      logDiag('Live mode disabled – websocket connection not attempted.');
      return;
    }
    if (!executionId) {
      logDiag('Waiting for execution ID before opening websocket.');
      return;
    }

    try {
      // Construct the correct WebSocket URL, ensuring the /v1 prefix is present.
      const wsUrl = `ws://127.0.0.1:8000/v1/ws/re-re/${executionId}`;
      console.log('Connecting to WebSocket at', wsUrl);
      logDiag(`Opening websocket → ${wsUrl}`);
      const ws = new WebSocket(wsUrl);

      ws.onopen = () => {
        logDiag('Websocket connected.');
        setIsConnected(true);
        setError(null);
        reconnectAttempts.current = 0;
      };

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data);

          if (data.type === 'workflow_event') {
            // Add event to timeline
            const transformed = transformEvent(data.event);
            if (transformed) {
              setEvents(prev => [...prev, transformed]);
            }

            // Update current state if included
            if (data.state) {
              setCurrentState(data.state);
            }
          } else if (data.type === 'state_update') {
            // Full state update
            setCurrentState(data.state);
          } else if (data.type === 'error') {
            setError(data.message);
          }
        } catch (err) {
          console.error('Failed to parse WebSocket message:', err);
        }
      };

      ws.onerror = (event) => {
        console.error('WebSocket error:', event);
            const errMsg = 'Websocket connection error.';
            setError(errMsg);
            logDiag(errMsg);
          };

          ws.onclose = () => {
        logDiag('Websocket disconnected.');
        setIsConnected(false);

        // Attempt reconnection with exponential backoff
        if (isLive && reconnectAttempts.current < 5) {
          const delay = Math.min(1000 * Math.pow(2, reconnectAttempts.current), 10000);
          logDiag(`Scheduling reconnect attempt #${reconnectAttempts.current + 1} in ${delay}ms`);
          reconnectTimeoutRef.current = setTimeout(() => {
            reconnectAttempts.current++;
            connect();
          }, delay);
        }
      };

      wsRef.current = ws;
    } catch (err) {
      console.error('Failed to create WebSocket:', err);
      const errMsg = 'Failed to create websocket connection.';
      setError(errMsg);
      logDiag(`${errMsg} ${err?.message || ''}`);
    }
  }, [executionId, isLive, logDiag]);

  // Disconnect WebSocket
  const disconnect = useCallback(() => {
    if (wsRef.current) {
      wsRef.current.close();
      wsRef.current = null;
    }
    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current);
      reconnectTimeoutRef.current = null;
    }
    setIsConnected(false);
  }, []);

  // Load historical execution data
  const loadExecution = useCallback(async (id) => {
    try {
      logDiag(`Loading execution from ${EXECUTIONS_ENDPOINT}/${id}`);
      const response = await fetch(`${EXECUTIONS_ENDPOINT}/${id}`);
      if (!response.ok) {
        throw new Error(`Failed to load execution: ${response.statusText}`);
      }

      const data = await response.json();
      const transformed = (data.events || []).map(transformEvent).filter(Boolean);
      setEvents(transformed);
      const latestState =
        data.final_state ||
        transformed[transformed.length - 1]?.stateSnapshot ||
        null;
      setCurrentState(latestState);
      setError(null);
      logDiag(`Executed playback fetch for execution ${id}`);
    } catch (err) {
      console.error('Failed to load execution:', err);
      setError(`Failed to load execution: ${err.message}`);
      logDiag(`Failed to load execution ${id}: ${err.message}`);
    }
  }, [logDiag]);

  // Start new execution
  const startExecution = useCallback(async (config) => {
    try {
      logDiag(`Starting new execution via ${PLAYBOOK_EXECUTE_ENDPOINT}`);
      const response = await fetch(PLAYBOOK_EXECUTE_ENDPOINT, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(config),
      });

      if (!response.ok) {
        throw new Error(`Failed to start execution: ${response.statusText}`);
      }

      const data = await response.json();
      const newExecutionId = data.execution_id;

      // Clear previous state
      setEvents([]);
      setCurrentState(null);
      setError(null);
      logDiag(`Started new execution ${newExecutionId}`);

      return newExecutionId;
    } catch (err) {
      console.error('Failed to start execution:', err);
      setError(`Failed to start execution: ${err.message}`);
      logDiag(`Failed to start execution: ${err.message}`);
      throw err;
    }
  }, [logDiag]);

  // Initial log + watch for state changes
  useEffect(() => {
    logDiag(`Telemetry hook initialized (isLive=${isLive}, executionId=${executionId || 'none'})`);
  }, [logDiag]);

  useEffect(() => {
    logDiag(`isLive changed → ${isLive}`);
  }, [isLive, logDiag]);

  useEffect(() => {
    logDiag(`executionId changed → ${executionId || 'none'}`);
  }, [executionId, logDiag]);

  useEffect(() => {
    logDiag(`API base URL → ${API_BASE_URL}`);
    logDiag(`Status endpoint → ${STATUS_ENDPOINT}`);
    logDiag(`WebSocket base → ${WS_BASE_URL}`);
  }, [logDiag]);

  // Connect/disconnect based on isLive flag
  useEffect(() => {
    if (isLive && executionId) {
      connect();
    } else {
      disconnect();
    }

    return () => {
      disconnect();
    };
  }, [executionId, isLive, connect, disconnect]);

  // Load execution data if not live
  useEffect(() => {
    if (!isLive && executionId) {
      loadExecution(executionId);
    }
  }, [executionId, isLive, loadExecution]);

  // Poll server-side telemetry status
  const fetchStatus = useCallback(async () => {
    try {
      logDiag(`Polling status endpoint → ${STATUS_ENDPOINT}`);
      const response = await fetch(STATUS_ENDPOINT);
      if (!response.ok) {
        throw new Error(response.statusText);
      }
      const data = await response.json();
      setServerStatus(data);
      setStatusError(null);
      logDiag(`Telemetry status ok (${response.status}) for ${STATUS_ENDPOINT}`);
    } catch (err) {
      setStatusError(err.message);
      logDiag(`Failed to fetch telemetry status (${STATUS_ENDPOINT}): ${err.message}`);
    }
  }, [logDiag]);

  useEffect(() => {
    fetchStatus();
    const interval = setInterval(fetchStatus, 5000);
    return () => clearInterval(interval);
  }, [fetchStatus]);

  return {
    events,
    currentState,
    isConnected,
    error,
    startExecution,
    loadExecution,
    disconnect,
    diagnostics,
    serverStatus,
    statusError,
  };
}

export default useTelemetry;
