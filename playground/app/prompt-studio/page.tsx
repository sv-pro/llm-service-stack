'use client';

/**
 * Prompt Studio Page
 * Interactive environment for testing and refining prompts
 * Inspired by the legacy AI Aikido Gateway playground
 */

import { useEffect, useState } from 'react';

interface Model {
  id: string;
  object: string;
  owned_by: string;
  vendor: string;
  type: string;
  endpoint: string;
  available: boolean;
  unavailable_reason?: string;
}

interface Message {
  role: 'system' | 'user' | 'assistant';
  content: string;
}

interface ChatResponse {
  id: string;
  object: string;
  created: number;
  model: string;
  choices: Array<{
    index: number;
    message: {
      role: string;
      content: string;
    };
    finish_reason: string;
  }>;
  usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
}

const GATEWAY_URL = process.env.NEXT_PUBLIC_GATEWAY_URL || 'http://localhost:8000';

export default function PromptStudioPage() {
  // State
  const [models, setModels] = useState<Model[]>([]);
  const [selectedModel, setSelectedModel] = useState('gpt-3.5-turbo');
  const [systemPrompt, setSystemPrompt] = useState('You are a helpful assistant.');
  const [userMessage, setUserMessage] = useState('');
  const [temperature, setTemperature] = useState(0.7);
  const [maxTokens, setMaxTokens] = useState(1000);
  const [response, setResponse] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Metadata
  const [metadata, setMetadata] = useState<{
    tokens?: number;
    latency?: number;
    cost?: number;
    cacheType?: string;
    promptTokens?: number;
    completionTokens?: number;
  }>({});

  // Gateway health
  const [gatewayStatus, setGatewayStatus] = useState<'checking' | 'online' | 'offline'>('checking');

  // CLI panel
  const [showCopyFeedback, setShowCopyFeedback] = useState(false);

  // Load models on mount
  useEffect(() => {
    loadModels();
    checkGatewayHealth();
  }, []);

  const checkGatewayHealth = async () => {
    try {
      const response = await fetch(`${GATEWAY_URL}/`);
      if (response.ok) {
        setGatewayStatus('online');
      } else {
        setGatewayStatus('offline');
      }
    } catch (error) {
      setGatewayStatus('offline');
    }
  };

  const loadModels = async () => {
    try {
      const response = await fetch(`${GATEWAY_URL}/v1/models`);
      if (response.ok) {
        const data = await response.json();
        setModels(data.data || []);
      }
    } catch (error) {
      console.error('Failed to load models:', error);
    }
  };

  const handleGenerate = async () => {
    if (!userMessage.trim()) {
      setError('Please enter a user message');
      return;
    }

    setLoading(true);
    setError(null);
    setResponse('');
    const startTime = Date.now();

    try {
      const messages: Message[] = [];
      if (systemPrompt.trim()) {
        messages.push({ role: 'system', content: systemPrompt });
      }
      messages.push({ role: 'user', content: userMessage });

      const requestBody = {
        model: selectedModel,
        messages,
        temperature,
        max_tokens: maxTokens,
      };

      const res = await fetch(`${GATEWAY_URL}/v1/chat/completions`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(requestBody),
      });

      const latency = Date.now() - startTime;

      if (!res.ok) {
        throw new Error(`HTTP ${res.status}: ${res.statusText}`);
      }

      const data: ChatResponse = await res.json();

      // Extract response
      const assistantMessage = data.choices[0]?.message?.content || 'No response';
      setResponse(assistantMessage);

      // Extract metadata
      const cacheType = res.headers.get('X-Gateway-Cache-Type') || undefined;
      const cost = data.usage ? calculateCost(selectedModel, data.usage) : 0;

      setMetadata({
        tokens: data.usage?.total_tokens,
        promptTokens: data.usage?.prompt_tokens,
        completionTokens: data.usage?.completion_tokens,
        latency,
        cost,
        cacheType,
      });

    } catch (err: any) {
      console.error('Error generating response:', err);
      setError(err.message || 'Failed to generate response');
    } finally {
      setLoading(false);
    }
  };

  const calculateCost = (model: string, usage: any): number => {
    const pricing: Record<string, { prompt: number; completion: number }> = {
      'gpt-4': { prompt: 30, completion: 60 },
      'gpt-4-turbo': { prompt: 10, completion: 30 },
      'gpt-3.5-turbo': { prompt: 0.5, completion: 1.5 },
      'claude-3-opus-20240229': { prompt: 15, completion: 75 },
      'claude-3-sonnet-20240229': { prompt: 3, completion: 15 },
    };

    const modelPricing = pricing[model] || { prompt: 1, completion: 2 };
    const promptCost = (usage.prompt_tokens / 1000000) * modelPricing.prompt;
    const completionCost = (usage.completion_tokens / 1000000) * modelPricing.completion;

    return promptCost + completionCost;
  };

  const getCurlCommand = () => {
    const messages: Message[] = [];
    if (systemPrompt.trim()) {
      messages.push({ role: 'system', content: systemPrompt });
    }
    messages.push({ role: 'user', content: userMessage || 'Your message here' });

    const requestBody = {
      model: selectedModel,
      messages,
      temperature,
      max_tokens: maxTokens,
    };

    return `curl ${GATEWAY_URL}/v1/chat/completions \\
  -H "Content-Type: application/json" \\
  -d '${JSON.stringify(requestBody, null, 2)}'`;
  };

  const copyToClipboard = async (text: string) => {
    try {
      await navigator.clipboard.writeText(text);
      setShowCopyFeedback(true);
      setTimeout(() => setShowCopyFeedback(false), 2000);
    } catch (err) {
      console.error('Failed to copy:', err);
    }
  };

  const getSourceBadge = () => {
    if (!metadata.cacheType) return null;

    const badges: Record<string, { label: string; color: string }> = {
      'semantic': { label: 'Semantic Cache', color: 'bg-purple-100 text-purple-800' },
      'verbatim': { label: 'Verbatim Cache', color: 'bg-green-100 text-green-800' },
      'api': { label: 'API Call', color: 'bg-red-100 text-red-800' },
    };

    const badge = badges[metadata.cacheType] || { label: metadata.cacheType, color: 'bg-gray-100 text-gray-800' };

    return (
      <span className={`inline-block px-2 py-1 rounded text-xs font-medium ${badge.color}`}>
        {badge.label}
      </span>
    );
  };

  return (
    <div className="min-h-screen p-8 bg-gradient-to-br from-gray-50 to-gray-100">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <h1 className="text-3xl font-bold text-gray-900">Prompt Studio</h1>

            {/* Gateway Status */}
            <div className="flex items-center gap-2 bg-white px-4 py-2 rounded-lg shadow-sm border border-gray-200">
              <div className={`w-2.5 h-2.5 rounded-full ${
                gatewayStatus === 'online' ? 'bg-green-500 animate-pulse' :
                gatewayStatus === 'offline' ? 'bg-red-500' :
                'bg-yellow-500 animate-pulse'
              }`} />
              <span className="text-sm font-medium text-gray-900">
                {gatewayStatus === 'online' ? 'Gateway Online' :
                 gatewayStatus === 'offline' ? 'Gateway Offline' :
                 'Checking...'}
              </span>
            </div>
          </div>
          <p className="text-gray-700 mt-2 font-medium">Test and refine your prompts with real-time feedback</p>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Left Column: Prompt Editor */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
              <h2 className="text-xl font-bold mb-5 text-gray-900">Input</h2>
              <div className="space-y-5">
                {/* Model Selection */}
                <div>
                  <label className="block text-sm font-semibold text-gray-900 mb-2">Model</label>
                  <select
                    className="w-full px-3 py-2.5 border-2 border-gray-300 rounded-lg text-gray-900 font-medium focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-colors"
                    value={selectedModel}
                    onChange={(e) => setSelectedModel(e.target.value)}
                  >
                    {models.filter(m => m.available).map(model => (
                      <option key={model.id} value={model.id}>
                        {model.id} ({model.vendor})
                      </option>
                    ))}
                    {models.filter(m => !m.available).length > 0 && (
                      <optgroup label="Unavailable">
                        {models.filter(m => !m.available).map(model => (
                          <option key={model.id} value={model.id} disabled>
                            {model.id} - {model.unavailable_reason}
                          </option>
                        ))}
                      </optgroup>
                    )}
                  </select>
                  <p className="text-xs text-gray-700 mt-2 font-medium">
                    {models.find(m => m.id === selectedModel)?.type === 'reasoning' ? '🧠 Advanced reasoning model' : '💬 Standard chat model'}
                  </p>
                </div>

                {/* System Prompt */}
                <div>
                  <label className="block text-sm font-semibold text-gray-900 mb-2">System Prompt</label>
                  <textarea
                    className="w-full px-3 py-2.5 border-2 border-gray-300 rounded-lg h-24 text-sm font-mono text-gray-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-colors"
                    placeholder="You are a helpful assistant..."
                    value={systemPrompt}
                    onChange={(e) => setSystemPrompt(e.target.value)}
                  />
                </div>

                {/* User Message */}
                <div>
                  <label className="block text-sm font-semibold text-gray-900 mb-2">User Message</label>
                  <textarea
                    className="w-full px-3 py-2.5 border-2 border-gray-300 rounded-lg h-32 text-sm font-mono text-gray-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-colors"
                    placeholder="Enter your prompt here..."
                    value={userMessage}
                    onChange={(e) => setUserMessage(e.target.value)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' && (e.metaKey || e.ctrlKey)) {
                        handleGenerate();
                      }
                    }}
                  />
                  <p className="text-xs text-gray-700 mt-2 font-semibold">⌘/Ctrl+Enter to submit</p>
                </div>

                {/* Parameters */}
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <label className="block text-sm font-semibold text-gray-900 mb-2">Temperature</label>
                    <input
                      type="number"
                      className="w-full px-3 py-2.5 border-2 border-gray-300 rounded-lg text-gray-900 font-medium focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-colors"
                      value={temperature}
                      onChange={(e) => setTemperature(parseFloat(e.target.value))}
                      step="0.1"
                      min="0"
                      max="2"
                    />
                  </div>
                  <div>
                    <label className="block text-sm font-semibold text-gray-900 mb-2">Max Tokens</label>
                    <input
                      type="number"
                      className="w-full px-3 py-2.5 border-2 border-gray-300 rounded-lg text-gray-900 font-medium focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-colors"
                      value={maxTokens}
                      onChange={(e) => setMaxTokens(parseInt(e.target.value))}
                    />
                  </div>
                </div>

                {/* Submit Button */}
                <button
                  className="w-full bg-gradient-to-r from-blue-600 to-blue-700 text-white font-bold px-4 py-3 rounded-lg hover:from-blue-700 hover:to-blue-800 disabled:from-gray-300 disabled:to-gray-400 disabled:cursor-not-allowed transition-all duration-200 shadow-md hover:shadow-lg"
                  onClick={handleGenerate}
                  disabled={loading || !userMessage.trim()}
                >
                  {loading ? 'Generating...' : 'Generate Response'}
                </button>
              </div>
            </div>
          </div>

          {/* Middle Column: Response Viewer */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200">
              <div className="flex items-center justify-between mb-5">
                <h2 className="text-xl font-bold text-gray-900">Output</h2>
                {getSourceBadge()}
              </div>

              <div className="space-y-4">
                {/* Error Display */}
                {error && (
                  <div className="bg-red-50 border-2 border-red-300 text-red-900 px-4 py-3 rounded-lg font-medium">
                    {error}
                  </div>
                )}

                {/* Response Text */}
                <div>
                  <div className="bg-gray-50 border-2 border-gray-200 rounded-lg p-4 min-h-96 max-h-96 overflow-y-auto">
                    {loading ? (
                      <div className="flex items-center justify-center h-full">
                        <div className="flex space-x-2">
                          <div className="w-3 h-3 bg-blue-600 rounded-full animate-bounce" />
                          <div className="w-3 h-3 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }} />
                          <div className="w-3 h-3 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }} />
                        </div>
                      </div>
                    ) : response ? (
                      <p className="text-sm text-gray-900 whitespace-pre-wrap leading-relaxed">{response}</p>
                    ) : (
                      <p className="text-sm text-gray-500 font-medium">Response will appear here...</p>
                    )}
                  </div>
                </div>

                {/* Metadata */}
                {response && (
                  <div className="border-t-2 border-gray-200 pt-4">
                    <h3 className="text-sm font-bold text-gray-900 mb-3">Metadata</h3>
                    <div className="grid grid-cols-2 gap-3 text-sm">
                      {metadata.tokens !== undefined && (
                        <div className="bg-blue-50 border border-blue-200 rounded-lg px-3 py-2">
                          <span className="text-gray-700 font-medium">Total Tokens:</span>
                          <span className="ml-2 font-bold text-gray-900">{metadata.tokens}</span>
                        </div>
                      )}
                      {metadata.promptTokens !== undefined && (
                        <div className="bg-purple-50 border border-purple-200 rounded-lg px-3 py-2">
                          <span className="text-gray-700 font-medium">Prompt:</span>
                          <span className="ml-2 font-bold text-gray-900">{metadata.promptTokens}</span>
                        </div>
                      )}
                      {metadata.completionTokens !== undefined && (
                        <div className="bg-green-50 border border-green-200 rounded-lg px-3 py-2">
                          <span className="text-gray-700 font-medium">Completion:</span>
                          <span className="ml-2 font-bold text-gray-900">{metadata.completionTokens}</span>
                        </div>
                      )}
                      {metadata.latency !== undefined && (
                        <div className="bg-yellow-50 border border-yellow-200 rounded-lg px-3 py-2">
                          <span className="text-gray-700 font-medium">Latency:</span>
                          <span className="ml-2 font-bold text-gray-900">{metadata.latency}ms</span>
                        </div>
                      )}
                      {metadata.cost !== undefined && (
                        <div className="bg-red-50 border border-red-200 rounded-lg px-3 py-2 col-span-2">
                          <span className="text-gray-700 font-medium">Est. Cost:</span>
                          <span className="ml-2 font-bold text-gray-900">${metadata.cost.toFixed(6)}</span>
                        </div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </div>

          {/* Right Column: CLI Panel */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow-md p-6 border border-gray-200 sticky top-8">
              <h2 className="text-xl font-bold mb-5 text-gray-900">Developer Tools</h2>

              <div className="space-y-5">
                {/* Curl Command */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <label className="block text-sm font-bold text-gray-900">cURL Command</label>
                    <button
                      onClick={() => copyToClipboard(getCurlCommand())}
                      className="text-xs font-semibold text-blue-600 hover:text-blue-800 hover:underline transition-colors"
                    >
                      {showCopyFeedback ? '✓ Copied!' : 'Copy'}
                    </button>
                  </div>
                  <pre className="bg-gray-900 text-green-400 p-3 rounded-lg text-xs overflow-x-auto border-2 border-gray-700 font-mono">
                    {getCurlCommand()}
                  </pre>
                </div>

                {/* JSON Body */}
                <div>
                  <div className="flex items-center justify-between mb-2">
                    <label className="block text-sm font-bold text-gray-900">JSON Body</label>
                    <button
                      onClick={() => {
                        const messages: Message[] = [];
                        if (systemPrompt.trim()) messages.push({ role: 'system', content: systemPrompt });
                        messages.push({ role: 'user', content: userMessage || 'Your message here' });
                        copyToClipboard(JSON.stringify({ model: selectedModel, messages, temperature, max_tokens: maxTokens }, null, 2));
                      }}
                      className="text-xs font-semibold text-blue-600 hover:text-blue-800 hover:underline transition-colors"
                    >
                      {showCopyFeedback ? '✓ Copied!' : 'Copy'}
                    </button>
                  </div>
                  <pre className="bg-gray-900 text-yellow-300 p-3 rounded-lg text-xs overflow-x-auto max-h-64 border-2 border-gray-700 font-mono">
                    {JSON.stringify({
                      model: selectedModel,
                      messages: [
                        ...(systemPrompt.trim() ? [{ role: 'system', content: systemPrompt }] : []),
                        { role: 'user', content: userMessage || 'Your message here' }
                      ],
                      temperature,
                      max_tokens: maxTokens
                    }, null, 2)}
                  </pre>
                </div>

                {/* Quick Tips */}
                <div className="border-t-2 border-gray-200 pt-4">
                  <h3 className="text-sm font-bold text-gray-900 mb-3">Quick Tips</h3>
                  <ul className="text-xs text-gray-700 space-y-2 font-medium">
                    <li>💡 Use ⌘/Ctrl+Enter to submit</li>
                    <li>🏷️ Watch for cache badges above</li>
                    <li>🔄 Try similar prompts to test semantic cache</li>
                    <li>🎯 Lower temperature for deterministic outputs</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
