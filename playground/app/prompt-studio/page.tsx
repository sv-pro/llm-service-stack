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
  const [systemPrompt, setSystemPrompt] = useState('You are a helpful assistant, expert in modern web development.');
  const [userMessage, setUserMessage] = useState('Generate a prompt for building a modern React application');
  const [temperature, setTemperature] = useState(0.7);
  const [maxTokens, setMaxTokens] = useState(1000);
  const [response, setResponse] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Cache controls
  const [cacheEnabled, setCacheEnabled] = useState(true);
  const [cacheMode, setCacheMode] = useState<'auto' | 'verbatim-only' | 'no-cache'>('auto');
  const [cacheTTL, setCacheTTL] = useState(3600); // 1 hour default
  const [semanticThreshold, setSemanticThreshold] = useState(0.85);

  // Metadata
  const [metadata, setMetadata] = useState<{
    tokens?: number;
    latency?: number;
    cost?: number;
    cacheType?: string;
    cacheStatus?: string;
    cacheSimilarity?: number;
    promptTokens?: number;
    completionTokens?: number;
    provider?: string;
    model?: string;
  }>({});

  // Gateway health
  const [gatewayStatus, setGatewayStatus] = useState<'checking' | 'online' | 'offline'>('checking');

  // CLI panel
  const [showCopyFeedback, setShowCopyFeedback] = useState(false);

  // Stage 2: Smart Prompts
  const [enhancedPrompt, setEnhancedPrompt] = useState<{
    system: string;
    user: string;
    improvements: string[];
    intent: string;
    reasoning: string;
    confidence: number;
    experimental_recursive?: {
      iterations: number;
      converged: boolean;
      final_similarity: number;
      iteration_history: any[];
    };
  } | null>(null);
  const [enhancing, setEnhancing] = useState(false);

  // Experimental: Recursive enhancement controls
  const [recursiveEnabled, setRecursiveEnabled] = useState(false);
  const [maxIterations, setMaxIterations] = useState(5);
  const [similarityThreshold, setSimilarityThreshold] = useState(0.95);

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

  const handleEnhancePrompt = async () => {
    if (!userMessage.trim()) {
      setError('Please enter a user message to enhance');
      return;
    }

    setEnhancing(true);
    setError(null);
    setEnhancedPrompt(null);

    try {
      const res = await fetch(`${GATEWAY_URL}/v1/prompts/enhance`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          system: systemPrompt,
          user: userMessage,
          context: {
            model: selectedModel,
            temperature
          },
          // Experimental: Recursive enhancement
          experimental_recursive: recursiveEnabled,
          max_iterations: maxIterations,
          similarity_threshold: similarityThreshold
        })
      });

      if (!res.ok) {
        const errorData = await res.json().catch(() => ({ detail: res.statusText }));
        throw new Error(errorData.detail || `Enhancement failed: ${res.status}`);
      }

      const data = await res.json();

      setEnhancedPrompt({
        system: data.enhanced.system,
        user: data.enhanced.user,
        improvements: data.improvements,
        intent: data.detected_intent,
        reasoning: data.reasoning,
        confidence: data.confidence,
        experimental_recursive: data.experimental_recursive
      });

    } catch (err: any) {
      console.error('Error enhancing prompt:', err);
      setError(err.message || 'Failed to enhance prompt');
    } finally {
      setEnhancing(false);
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

      // Build headers with cache controls
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      };

      if (!cacheEnabled || cacheMode === 'no-cache') {
        headers['X-Cache-Control'] = 'no-cache';
      } else if (cacheMode === 'verbatim-only') {
        headers['X-Cache-Control'] = 'verbatim-only';
      } else {
        headers['X-Cache-Control'] = 'auto';
      }

      if (cacheEnabled && cacheMode === 'auto') {
        headers['X-Cache-Similarity-Threshold'] = semanticThreshold.toString();
      }

      if (cacheTTL > 0) {
        headers['X-Cache-TTL'] = cacheTTL.toString();
      }

      const res = await fetch(`${GATEWAY_URL}/v1/chat/completions`, {
        method: 'POST',
        headers,
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

      // Extract metadata from headers
      const cacheStatus = res.headers.get('X-Gateway-Cache-Status') || undefined;
      const cacheType = res.headers.get('X-Gateway-Cache-Type') || undefined;
      const cacheSimilarity = res.headers.get('X-Gateway-Cache-Similarity');
      const cost = data.usage ? calculateCost(selectedModel, data.usage) : 0;

      // Extract model info
      const modelInfo = models.find(m => m.id === selectedModel);

      // Debug logging
      console.log('Cache Headers:', {
        cacheStatus,
        cacheType,
        cacheSimilarity,
        allHeaders: Array.from(res.headers.entries())
      });

      setMetadata({
        tokens: data.usage?.total_tokens,
        promptTokens: data.usage?.prompt_tokens,
        completionTokens: data.usage?.completion_tokens,
        latency,
        cost,
        cacheStatus,
        cacheType,
        cacheSimilarity: cacheSimilarity ? parseFloat(cacheSimilarity) : undefined,
        provider: modelInfo?.vendor,
        model: data.model || selectedModel,
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
    if (!metadata.cacheType && !metadata.cacheStatus) return null;

    const badges: Record<string, { label: string; icon: string; color: string }> = {
      'semantic': { label: 'Semantic Cache', icon: '🧠', color: 'bg-purple-100 text-purple-800 border-purple-300' },
      'verbatim': { label: 'Simple Cache', icon: '⚡', color: 'bg-green-100 text-green-800 border-green-300' },
      'api': { label: 'API Call', icon: '🌐', color: 'bg-blue-100 text-blue-800 border-blue-300' },
    };

    const cacheType = metadata.cacheType || 'api';
    const badge = badges[cacheType] || { label: cacheType, icon: '❓', color: 'bg-gray-100 text-gray-800 border-gray-300' };

    let detailText = badge.label;

    // Add similarity score for semantic cache
    if (cacheType === 'semantic' && metadata.cacheSimilarity !== undefined) {
      const similarity = (metadata.cacheSimilarity * 100).toFixed(1);
      detailText = `${badge.label} (${similarity}% match)`;
    }

    // Add provider and model for API calls
    if (cacheType === 'api' && metadata.provider) {
      detailText = `${badge.label} (${metadata.provider})`;
    }

    return (
      <span className={`inline-flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-bold border-2 ${badge.color}`}>
        <span>{badge.icon}</span>
        <span>{detailText}</span>
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

                {/* Experimental: Recursive Enhancement Controls */}
                <div className="bg-blue-50 border-2 border-blue-200 rounded-lg p-3 space-y-2">
                  <div className="flex items-center gap-2">
                    <input
                      type="checkbox"
                      id="recursive-enhancement"
                      checked={recursiveEnabled}
                      onChange={(e) => setRecursiveEnabled(e.target.checked)}
                      className="w-4 h-4 text-blue-600 rounded focus:ring-blue-500"
                    />
                    <label htmlFor="recursive-enhancement" className="text-sm font-bold text-blue-900 cursor-pointer">
                      🔬 Recursive Enhancement (Experimental)
                    </label>
                  </div>

                  {recursiveEnabled && (
                    <div className="ml-6 space-y-3 mt-2">
                      <div className="space-y-1">
                        <div className="flex items-center justify-between">
                          <label className="text-xs font-semibold text-blue-800">Max Iterations:</label>
                          <span className="text-sm font-bold text-blue-900 bg-blue-100 px-2 py-0.5 rounded">{maxIterations}</span>
                        </div>
                        <input
                          type="range"
                          min="2"
                          max="10"
                          value={maxIterations}
                          onChange={(e) => setMaxIterations(parseInt(e.target.value))}
                          className="w-full h-2 bg-blue-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                        />
                        <div className="flex justify-between text-xs text-blue-600">
                          <span>2</span>
                          <span>10</span>
                        </div>
                      </div>

                      <div className="space-y-1">
                        <div className="flex items-center justify-between">
                          <label className="text-xs font-semibold text-blue-800">Similarity Threshold:</label>
                          <span className="text-sm font-bold text-blue-900 bg-blue-100 px-2 py-0.5 rounded">{similarityThreshold.toFixed(2)}</span>
                        </div>
                        <input
                          type="range"
                          min="0.80"
                          max="0.99"
                          step="0.01"
                          value={similarityThreshold}
                          onChange={(e) => setSimilarityThreshold(parseFloat(e.target.value))}
                          className="w-full h-2 bg-blue-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                        />
                        <div className="flex justify-between text-xs text-blue-600">
                          <span>0.80</span>
                          <span>0.99</span>
                        </div>
                      </div>

                      <p className="text-xs text-blue-700 mt-1">
                        💡 Enhances recursively until prompts converge or max iterations reached
                      </p>
                    </div>
                  )}
                </div>

                {/* Smart Prompts: Enhance Button */}
                <button
                  onClick={handleEnhancePrompt}
                  disabled={enhancing || !userMessage.trim()}
                  className="w-full bg-gradient-to-r from-purple-600 to-purple-700 text-white font-bold px-4 py-3 rounded-lg hover:from-purple-700 hover:to-purple-800 disabled:from-gray-300 disabled:to-gray-400 disabled:cursor-not-allowed transition-all duration-200 shadow-md hover:shadow-lg"
                >
                  {enhancing ? '✨ Enhancing...' : '✨ Enhance Prompt'}
                </button>

                {/* Enhanced Prompt Display */}
                {enhancedPrompt && (
                  <div className="mt-4 bg-purple-50 border-2 border-purple-200 rounded-lg p-5">
                    <div className="flex items-center justify-between mb-3">
                      <h3 className="text-lg font-bold text-purple-900">📝 Enhanced Prompt</h3>
                      <div className="flex items-center gap-2">
                        <span className="text-xs bg-purple-100 px-2 py-1 rounded border border-purple-300 font-semibold">
                          Intent: {enhancedPrompt.intent}
                        </span>
                        <span className="text-xs bg-purple-100 px-2 py-1 rounded border border-purple-300 font-semibold">
                          {(enhancedPrompt.confidence * 100).toFixed(0)}% confident
                        </span>
                      </div>
                    </div>

                    <div className="space-y-3">
                      <div>
                        <label className="block text-sm font-bold text-purple-900 mb-1">System:</label>
                        <div className="bg-white border border-purple-200 rounded p-3 text-sm text-gray-900 max-h-32 overflow-y-auto">
                          {enhancedPrompt.system}
                        </div>
                      </div>

                      <div>
                        <label className="block text-sm font-bold text-purple-900 mb-1">User:</label>
                        <div className="bg-white border border-purple-200 rounded p-3 text-sm text-gray-900 max-h-32 overflow-y-auto">
                          {enhancedPrompt.user}
                        </div>
                      </div>

                      <div>
                        <label className="block text-sm font-bold text-purple-900 mb-1">Improvements:</label>
                        <ul className="bg-white border border-purple-200 rounded p-3 text-sm text-gray-900 space-y-1">
                          {enhancedPrompt.improvements.map((improvement, i) => (
                            <li key={i} className="flex items-start">
                              <span className="text-green-600 mr-2">✓</span>
                              {improvement}
                            </li>
                          ))}
                        </ul>
                      </div>

                      {enhancedPrompt.reasoning && (
                        <div>
                          <label className="block text-sm font-bold text-purple-900 mb-1">Reasoning:</label>
                          <div className="bg-white border border-purple-200 rounded p-3 text-sm text-gray-700 italic">
                            {enhancedPrompt.reasoning}
                          </div>
                        </div>
                      )}

                      {/* Convergence Visualization (Experimental Recursive) */}
                      {enhancedPrompt.experimental_recursive && (
                        <div className="bg-blue-50 border-2 border-blue-200 rounded-lg p-3">
                          <label className="block text-sm font-bold text-blue-900 mb-2">🔬 Recursive Enhancement Results:</label>

                          <div className="space-y-2">
                            <div className="flex items-center gap-2">
                              <span className="text-xs font-semibold text-blue-800">Iterations:</span>
                              <span className="text-xs bg-blue-100 text-blue-900 px-2 py-1 rounded border border-blue-300 font-semibold">
                                {enhancedPrompt.experimental_recursive.iterations}
                              </span>
                              {enhancedPrompt.experimental_recursive.converged ? (
                                <span className="text-xs bg-green-100 text-green-800 px-2 py-1 rounded border border-green-300 font-semibold">
                                  ✓ Converged
                                </span>
                              ) : (
                                <span className="text-xs bg-yellow-100 text-yellow-800 px-2 py-1 rounded border border-yellow-300 font-semibold">
                                  ⚠ Max iterations reached
                                </span>
                              )}
                            </div>

                            {enhancedPrompt.experimental_recursive.final_similarity > 0 && (
                              <div className="flex items-center gap-2">
                                <span className="text-xs font-semibold text-blue-800">Final Similarity:</span>
                                <span className="text-xs bg-blue-100 text-blue-900 px-2 py-1 rounded border border-blue-300 font-semibold">
                                  {(enhancedPrompt.experimental_recursive.final_similarity * 100).toFixed(1)}%
                                </span>
                              </div>
                            )}

                            {enhancedPrompt.experimental_recursive.iteration_history.length > 1 && (
                              <div className="mt-2">
                                <p className="text-xs font-semibold text-blue-800 mb-1">Convergence Path:</p>
                                <div className="bg-white border border-blue-200 rounded p-2 text-xs space-y-1">
                                  {enhancedPrompt.experimental_recursive.iteration_history.map((iter: any, idx: number) => {
                                    const isLast = idx === enhancedPrompt.experimental_recursive!.iteration_history.length - 1;
                                    return (
                                      <div key={idx} className="flex items-center gap-2">
                                        <span className="font-semibold text-blue-700">Iteration {iter.iteration}</span>
                                        <span className="text-gray-600">→</span>
                                        <span className="text-gray-700">{iter.detected_intent}</span>
                                        {isLast && enhancedPrompt.experimental_recursive!.converged && (
                                          <span className="ml-auto text-green-600 font-semibold">✓</span>
                                        )}
                                      </div>
                                    );
                                  })}
                                </div>
                              </div>
                            )}
                          </div>
                        </div>
                      )}
                    </div>

                    <div className="flex gap-2 mt-4">
                      <button
                        onClick={() => {
                          setSystemPrompt(enhancedPrompt.system);
                          setUserMessage(enhancedPrompt.user);
                          setEnhancedPrompt(null);
                        }}
                        className="flex-1 bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 font-semibold transition-colors"
                      >
                        Use This
                      </button>
                      <button
                        onClick={() => {
                          // TODO: Stage 3 - Save as template
                          alert('Template saving coming in Stage 3!');
                        }}
                        className="flex-1 bg-white text-purple-600 border-2 border-purple-600 px-4 py-2 rounded-lg hover:bg-purple-50 font-semibold transition-colors"
                      >
                        Save as Template
                      </button>
                      <button
                        onClick={() => setEnhancedPrompt(null)}
                        className="px-4 py-2 text-gray-600 hover:text-gray-900 font-semibold transition-colors"
                      >
                        Cancel
                      </button>
                    </div>
                  </div>
                )}

                {/* Submit Button */}
                <button
                  className="w-full bg-gradient-to-r from-blue-600 to-blue-700 text-white font-bold px-4 py-3 rounded-lg hover:from-blue-700 hover:to-blue-800 disabled:from-gray-300 disabled:to-gray-400 disabled:cursor-not-allowed transition-all duration-200 shadow-md hover:shadow-lg"
                  onClick={handleGenerate}
                  disabled={loading || !userMessage.trim()}
                >
                  {loading ? 'Generating...' : 'Generate Response'}
                </button>

                {/* Advanced Settings Divider */}
                <div className="border-t-2 border-gray-300 pt-4">
                  <h3 className="text-sm font-bold text-gray-900 mb-4">Advanced Settings</h3>

                  {/* Parameters */}
                  <div className="grid grid-cols-2 gap-4 mb-5">
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
                </div>

                {/* Cache Controls */}
                <div className="border-t-2 border-gray-200 pt-4">
                  <div className="flex items-center justify-between mb-3">
                    <label className="block text-sm font-bold text-gray-900">Cache Configuration</label>
                    <button
                      onClick={() => setCacheEnabled(!cacheEnabled)}
                      className={`px-3 py-1 rounded-md text-xs font-bold transition-colors ${
                        cacheEnabled
                          ? 'bg-green-100 text-green-800 border-2 border-green-300'
                          : 'bg-gray-100 text-gray-600 border-2 border-gray-300'
                      }`}
                    >
                      {cacheEnabled ? '✓ Enabled' : '✗ Disabled'}
                    </button>
                  </div>

                  {cacheEnabled && (
                    <div className="space-y-3">
                      {/* Cache Mode */}
                      <div>
                        <label className="block text-xs font-semibold text-gray-700 mb-1.5">Cache Mode</label>
                        <select
                          className="w-full px-2.5 py-2 border-2 border-gray-300 rounded-lg text-sm font-medium text-gray-900 focus:border-blue-500 focus:ring-2 focus:ring-blue-200 transition-colors"
                          value={cacheMode}
                          onChange={(e) => setCacheMode(e.target.value as any)}
                        >
                          <option value="auto">🧠 Auto (Simple + Semantic)</option>
                          <option value="verbatim-only">⚡ Simple/Verbatim Only</option>
                          <option value="no-cache">🌐 No Cache (Always API)</option>
                        </select>
                      </div>

                      {/* Cache TTL */}
                      <div>
                        <label className="block text-xs font-semibold text-gray-700 mb-1.5">
                          Cache TTL (seconds): {cacheTTL}
                        </label>
                        <input
                          type="range"
                          className="w-full"
                          value={cacheTTL}
                          onChange={(e) => setCacheTTL(parseInt(e.target.value))}
                          min="60"
                          max="86400"
                          step="60"
                        />
                        <div className="flex justify-between text-xs text-gray-600 mt-1">
                          <span>1 min</span>
                          <span>{(cacheTTL / 3600).toFixed(1)}h</span>
                          <span>24h</span>
                        </div>
                      </div>

                      {/* Semantic Threshold (only for auto mode) */}
                      {cacheMode === 'auto' && (
                        <div>
                          <label className="block text-xs font-semibold text-gray-700 mb-1.5">
                            Semantic Similarity: {(semanticThreshold * 100).toFixed(0)}%
                          </label>
                          <input
                            type="range"
                            className="w-full"
                            value={semanticThreshold}
                            onChange={(e) => setSemanticThreshold(parseFloat(e.target.value))}
                            min="0.5"
                            max="1.0"
                            step="0.05"
                          />
                          <div className="flex justify-between text-xs text-gray-600 mt-1">
                            <span>50%</span>
                            <span>75%</span>
                            <span>100%</span>
                          </div>
                        </div>
                      )}
                    </div>
                  )}
                </div>
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
