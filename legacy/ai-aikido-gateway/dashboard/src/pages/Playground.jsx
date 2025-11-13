import React, { useState, useEffect, useMemo, useCallback } from 'react';
import './Playground.css';
import API_URL from '../config';

const GATEWAY_URL = API_URL;

const DEFAULT_PROMPT = 'Explain what a REST API is in simple terms.';

function Playground() {
  const [message, setMessage] = useState(DEFAULT_PROMPT);
  const [model, setModel] = useState('gpt-3.5-turbo');
  const [response, setResponse] = useState(null);
  const [metadata, setMetadata] = useState(null);
  const [responseSource, setResponseSource] = useState(null);
  const [semanticCandidates, setSemanticCandidates] = useState([]);
  const [semanticEntries, setSemanticEntries] = useState([]);
  const [semanticLoading, setSemanticLoading] = useState(false);
  const [semanticError, setSemanticError] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [gatewayStatus, setGatewayStatus] = useState({ status: 'checking', text: 'Checking...' });
  const [copyFeedback, setCopyFeedback] = useState('');

  useEffect(() => {
    checkHealth();
    fetchSemanticEntries();
  }, []);

  useEffect(() => {
    if (!copyFeedback) {
      return undefined;
    }
    const timer = setTimeout(() => setCopyFeedback(''), 2000);
    return () => clearTimeout(timer);
  }, [copyFeedback]);

  const checkHealth = async () => {
    try {
      setGatewayStatus({ status: 'checking', text: 'Checking...' });
      console.log('Checking gateway health at', `${GATEWAY_URL}/health`);
      const response = await fetch(`${GATEWAY_URL}/health`);
      const data = await response.json();

      if (data.status === 'healthy') {
        setGatewayStatus({
          status: 'online',
          text: `✅ ${data.service} v${data.version}`,
        });
      } else {
        setGatewayStatus({
          status: 'warning',
          text: '⚠️ Gateway responded but status unknown',
        });
      }
    } catch (err) {
      setGatewayStatus({
        status: 'offline',
        text: '❌ Gateway not reachable',
      });
      console.error('Health check failed:', err);
    }
  };

  const fetchSemanticEntries = async (limit = 10) => {
    try {
      const response = await fetch(`${GATEWAY_URL}/v1/cache/semantic/entries?limit=${limit}`);
      if (!response.ok) {
        return;
      }
      const data = await response.json();
      setSemanticEntries(data.entries || []);
    } catch (err) {
      console.error('Failed to fetch semantic cache entries:', err);
    }
  };

  const fetchSemanticCandidates = async (promptText, selectedModel) => {
    try {
      setSemanticLoading(true);
      setSemanticError(null);
      const response = await fetch(`${GATEWAY_URL}/v1/cache/semantic/search`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          prompt: promptText,
          model: selectedModel,
          limit: 3,
        }),
      });

      if (!response.ok) {
        throw new Error(`Semantic cache unavailable (${response.status})`);
      }

      const data = await response.json();
      setSemanticCandidates(data.candidates || []);
    } catch (err) {
      setSemanticCandidates([]);
      setSemanticError(err.message);
    } finally {
      setSemanticLoading(false);
    }
  };

  const createRequestPayload = useCallback(
    () => ({
      model,
      messages: [
        {
          role: 'user',
          content: message,
        },
      ],
      temperature: 0.7,
      max_completion_tokens: 1000,
    }),
    [model, message],
  );

  const requestPayload = useMemo(() => createRequestPayload(), [createRequestPayload]);
  const requestJson = useMemo(() => JSON.stringify(requestPayload, null, 2), [requestPayload]);
  const curlCommand = useMemo(() => {
    const sanitizedJson = requestJson.replace(/'/g, "\\'");
    return [
      `curl -i ${GATEWAY_URL}/v1/chat/completions \\`,
      '  -H "Content-Type: application/json" \\',
      '  -H "Authorization: Bearer $OPENAI_API_KEY" \\',
      `  -d '${sanitizedJson}'`,
    ].join('\n');
  }, [requestJson]);

  const handleCopy = useCallback(async (text) => {
    try {
      await navigator.clipboard.writeText(text);
      setCopyFeedback('Copied to clipboard');
    } catch (err) {
      console.error('Copy failed:', err);
      setCopyFeedback('Copy failed');
    }
  }, []);

  const handleSend = async (e) => {
    e.preventDefault();

    if (!message.trim()) {
      alert('Please enter a message');
      return;
    }

    setLoading(true);
    setError(null);
    setResponse(null);
    setMetadata(null);
    setResponseSource(null);
    setSemanticCandidates([]);
    setSemanticError(null);
    setResponseSource(null);

    const payload = createRequestPayload();
    const startTime = Date.now();

    try {
      const res = await fetch(`${GATEWAY_URL}/v1/chat/completions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
      });

      const endTime = Date.now();
      const latency = endTime - startTime;

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      }

      const headerCacheType = (res.headers.get('X-Gateway-Cache-Type') || 'api').toLowerCase();
      const headerLatency = res.headers.get('X-Gateway-Latency-Ms');
      const data = await res.json();
      const content = data.choices?.[0]?.message?.content || 'No content in response';
      setResponse(content);

      setMetadata({
        model: data.model || model,
        latency_ms: latency,
        usage: data.usage || 'Not provided',
        finish_reason: data.choices?.[0]?.finish_reason || 'unknown',
        timestamp: new Date().toISOString(),
        cache_type: headerCacheType,
        gateway_latency_ms: headerLatency ? parseFloat(headerLatency) : null,
      });

      const sourceLabel = formatCacheSource(headerCacheType);
      setResponseSource({
        type: headerCacheType,
        label: sourceLabel,
        latency: headerLatency ? parseFloat(headerLatency) : latency,
      });

      fetchSemanticCandidates(payload.messages[payload.messages.length - 1].content, model);
      fetchSemanticEntries();
    } catch (err) {
      console.error('Error sending message:', err);
      setError(err.message);
      setMetadata({
        error: err.message,
        timestamp: new Date().toISOString(),
      });
    } finally {
      setLoading(false);
    }
  };

  const formatCacheSource = (type) => {
    switch (type) {
      case 'semantic':
        return 'Semantic Cache';
      case 'verbatim':
        return 'Verbatim Cache';
      default:
        return 'API Call';
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend(e);
    }
  };

  return (
    <div className="playground-page">
      <div className="page-header">
        <h1>🎮 Playground</h1>
        <p className="page-subtitle">Test the AI Aikido Gateway</p>
        <div className={`gateway-status status-${gatewayStatus.status}`}>
          <span className="status-dot" />
          {gatewayStatus.text}
        </div>
      </div>

      <div className="playground-grid">
        <div className="playground-container">
          <div className="input-section">
            <form onSubmit={handleSend}>
              <div className="form-group">
                <label htmlFor="model-select">Model</label>
                <select
                  id="model-select"
                  value={model}
                  onChange={(e) => setModel(e.target.value)}
                  className="form-control"
                >
                  <option value="gpt-5">GPT-5 (Reasoning Model, Advanced)</option>
                  <option value="gpt-5-mini">GPT-5 Mini (Reasoning, Efficient)</option>
                  <option value="gpt-5-nano">GPT-5 Nano (Reasoning, Lightweight)</option>
                  <option value="gpt-4o">GPT-4o (Optimized, Multimodal)</option>
                  <option value="gpt-4-turbo">GPT-4 Turbo (Fast & Capable)</option>
                  <option value="gpt-4">GPT-4 (Highly Capable)</option>
                  <option value="gpt-3.5-turbo">GPT-3.5 Turbo (Fast & Cheap)</option>
                </select>
              </div>

              <div className="form-group">
                <label htmlFor="message-input">Message</label>
                <textarea
                  id="message-input"
                  value={message}
                  onChange={(e) => setMessage(e.target.value)}
                  onKeyDown={handleKeyDown}
                  placeholder={DEFAULT_PROMPT}
                  className="form-control"
                  rows="5"
                />
              </div>

              <button type="submit" className="btn btn-primary" disabled={loading}>
                {loading ? (
                  <>
                    <span className="spinner" />
                    Sending...
                  </>
                ) : (
                  <>
                    <span>🚀</span>
                    Send Message
                  </>
                )}
              </button>
            </form>
          </div>

          <div className="output-section">
            <div className="response-card">
              <h3>Response</h3>
              <div className="response-meta">
                <span className={`meta-pill source-${responseSource?.type || 'api'}`}>
                  {responseSource ? responseSource.label : 'Awaiting Response'}
                </span>
                <span className="meta-pill latency-pill">
                  Latency: {responseSource?.latency ? `${responseSource.latency.toFixed(2)} ms` : '—'}
                </span>
              </div>
              <div className={`response-display ${response ? 'has-content' : ''} ${error ? 'error' : ''}`}>
                {loading && <p className="placeholder">Waiting for response...</p>}
                {error && (
                  <p>
                    <strong>Error:</strong> {error}
                  </p>
                )}
                {response && <p>{response}</p>}
                {!loading && !response && !error && <p className="placeholder">Response will appear here...</p>}
              </div>
            </div>

            <div className="metadata-card">
              <h3>Response Metadata</h3>
              <pre className="metadata-display">
{metadata ? JSON.stringify(metadata, null, 2) : '{\n  "model": null,\n  "latency_ms": null,\n  "usage": null,\n  "finish_reason": null,\n  "cache_type": null\n}'}
              </pre>
            </div>

            <div className="semantic-card">
              <h3>Semantic Cache Insights</h3>

              <div className="semantic-section">
                <div className="semantic-section-header">
                  <h4>Top Matches for this Prompt</h4>
                  {semanticLoading && <span className="semantic-status">Crunching embeddings…</span>}
                </div>
                {semanticError && <div className="semantic-error">⚠️ {semanticError}</div>}
                {semanticCandidates.length > 0 ? (
                  <ul className="semantic-list">
                    {semanticCandidates.map((candidate, idx) => (
                      <li key={`${candidate.prompt_text}-${idx}`} className="semantic-entry">
                        <strong>{candidate.prompt_text || '—'}</strong>
                        <div className="semantic-meta">
                          <span>Similarity: {(candidate.similarity || 0).toFixed(3)}</span>
                          <span>Model: {candidate.model || 'unknown'}</span>
                        </div>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="semantic-empty">No similar prompts yet.</p>
                )}
              </div>

              <div className="semantic-section">
                <div className="semantic-section-header">
                  <h4>Recent Cache Entries</h4>
                  <button type="button" className="cli-button" onClick={() => fetchSemanticEntries()}>
                    Refresh
                  </button>
                </div>
                {semanticEntries.length > 0 ? (
                  <ul className="semantic-list">
                    {semanticEntries.map((entry, idx) => (
                      <li key={`${entry.prompt_text}-${idx}`} className="semantic-entry">
                        <strong>{entry.prompt_text || 'Unknown prompt'}</strong>
                        <div className="semantic-meta">
                          <span>Model: {entry.model || 'unknown'}</span>
                          <span>{entry.timestamp || ''}</span>
                        </div>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="semantic-empty">Semantic cache is empty.</p>
                )}
              </div>
            </div>
          </div>
        </div>

        <aside className="cli-panel">
          <div>
            <h2>CLI Request Preview</h2>
            <p className="cli-description">
              The gateway receives OpenAI-compatible payloads. Copy the curl snippet or JSON body to reuse the request.
            </p>
          </div>
          <div className="cli-actions">
            <button type="button" className="cli-button" onClick={() => handleCopy(curlCommand)}>
              Copy curl command
            </button>
            <button type="button" className="cli-button" onClick={() => handleCopy(requestJson)}>
              Copy JSON body
            </button>
            {copyFeedback && <span className="cli-feedback">{copyFeedback}</span>}
          </div>
          <pre className="cli-preview">
            <code>{curlCommand}</code>
          </pre>
          <hr className="cli-section-divider" />
          <pre className="cli-json">
            <code>{requestJson}</code>
          </pre>
        </aside>
      </div>
    </div>
  );
}

export default Playground;
