/**
 * ChatWindow Component
 * Main chat interface container
 */

import React, { useState, useEffect, useRef } from 'react';
import ChatMessage from './ChatMessage';
import ChatInput from './ChatInput';
import { Message, ModelInfo } from '../types/chat';
import { apiService } from '../services/api';

const ChatWindow: React.FC = () => {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [apiKey, setApiKey] = useState('');
  // Check if API key is already configured in environment
  const hasEnvApiKey = process.env.REACT_APP_API_KEY && process.env.REACT_APP_API_KEY.trim() !== '';
  const [showApiKeyInput, setShowApiKeyInput] = useState(!hasEnvApiKey);
  const [models, setModels] = useState<ModelInfo[]>([]);
  const [selectedModel, setSelectedModel] = useState('gpt-3.5-turbo');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  // Fetch available models on mount
  useEffect(() => {
    const loadModels = async () => {
      try {
        const availableModels = await apiService.fetchModels();
        setModels(availableModels);

        // Select first available model
        const firstAvailableModel = availableModels.find(m => m.available);
        if (firstAvailableModel) {
          setSelectedModel(firstAvailableModel.id);
        } else if (availableModels.length > 0) {
          // If no models available, select first one anyway (it will show as unavailable)
          setSelectedModel(availableModels[0].id);
        }
      } catch (error) {
        console.error('Error loading models:', error);
      }
    };

    if (!showApiKeyInput) {
      loadModels();
    }
  }, [showApiKeyInput]);

  const handleSetApiKey = () => {
    if (apiKey.trim()) {
      apiService.setApiKey(apiKey);
    }
    setShowApiKeyInput(false);
  };

  const handleSkipApiKey = () => {
    // Allow proceeding without API key (for localhost development)
    setShowApiKeyInput(false);
  };

  const handleSendMessage = async (content: string) => {
    // Check if selected model is available
    const selectedModelInfo = apiService.getModelInfo(selectedModel);
    if (selectedModelInfo && !selectedModelInfo.available) {
      // Show error message for unavailable model
      const errorMessage: Message = {
        id: Date.now().toString(),
        role: 'assistant',
        content: `Cannot use model "${selectedModel}": ${selectedModelInfo.unavailable_reason || 'Model unavailable'}. Please select an available model.`,
        timestamp: new Date(),
      };
      setMessages((prev) => [...prev, errorMessage]);
      return;
    }

    // Add user message
    const userMessage: Message = {
      id: Date.now().toString(),
      role: 'user',
      content,
      timestamp: new Date(),
    };

    setMessages((prev) => [...prev, userMessage]);
    setIsLoading(true);

    try {
      // Send to API with selected model
      const response = await apiService.sendMessage({
        model: selectedModel,
        messages: [
          ...messages.map((m) => ({ role: m.role, content: m.content })),
          { role: 'user', content },
        ],
      });

      // Add assistant response
      const assistantMessage: Message = {
        id: response.id,
        role: 'assistant',
        content: response.choices[0].message.content,
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (error) {
      console.error('Error sending message:', error);

      // Add error message
      const errorMessage: Message = {
        id: Date.now().toString(),
        role: 'assistant',
        content: 'Sorry, there was an error processing your request. Please try again.',
        timestamp: new Date(),
      };

      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleNewChat = () => {
    setMessages([]);
  };

  if (showApiKeyInput) {
    return (
      <div className="flex items-center justify-center h-screen bg-gray-100">
        <div className="bg-white p-8 rounded-lg shadow-lg max-w-md w-full">
          <h2 className="text-2xl font-bold mb-4">API Key (Optional)</h2>
          <p className="text-gray-600 mb-4">
            Enter your API key or continue without one for localhost development.
          </p>
          <input
            type="password"
            value={apiKey}
            onChange={(e) => setApiKey(e.target.value)}
            placeholder="sk_... (optional)"
            className="w-full px-4 py-2 border border-gray-300 rounded-lg mb-4 focus:outline-none focus:ring-2 focus:ring-blue-500"
            onKeyPress={(e) => e.key === 'Enter' && handleSetApiKey()}
          />
          <div className="flex gap-2">
            <button
              onClick={handleSkipApiKey}
              className="flex-1 px-4 py-2 bg-gray-200 text-gray-800 rounded-lg hover:bg-gray-300"
            >
              Skip
            </button>
            <button
              onClick={handleSetApiKey}
              disabled={!apiKey.trim()}
              className="flex-1 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-blue-300 disabled:cursor-not-allowed"
            >
              Set API Key
            </button>
          </div>
          <p className="text-xs text-gray-500 mt-4 text-center">
            For localhost development, the app-server can bypass API key validation.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-screen bg-gradient-to-br from-gray-50 to-blue-50">
      {/* Header */}
      <div className="bg-white border-b-2 border-gray-300 px-6 py-4 flex justify-between items-center shadow-md">
        <div className="flex items-center gap-3">
          <div className="w-12 h-12 bg-gradient-to-br from-blue-600 to-blue-700 rounded-xl flex items-center justify-center text-white font-bold text-xl shadow-md">
            AI
          </div>
          <div>
            <h1 className="text-xl font-bold text-gray-900">LLM Chat</h1>
            <p className="text-xs text-gray-700 font-semibold">Powered by OpenAI & Anthropic</p>
          </div>
        </div>
        <button
          onClick={handleNewChat}
          className="px-5 py-2.5 bg-gradient-to-r from-blue-600 to-blue-700 text-white font-bold rounded-lg hover:from-blue-700 hover:to-blue-800 transition-all duration-200 shadow-md hover:shadow-lg"
        >
          + New Chat
        </button>
      </div>

      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-6">
        {messages.length === 0 && (
          <div className="text-center text-gray-500 mt-20">
            <div className="mb-6">
              <div className="w-20 h-20 bg-gradient-to-br from-blue-500 to-purple-600 rounded-full flex items-center justify-center text-white text-4xl mx-auto mb-4 shadow-lg">
                🤖
              </div>
              <p className="text-2xl font-bold mb-2 text-gray-700">Welcome to LLM Chat!</p>
              <p className="text-gray-500">Select a model and send a message to start a conversation.</p>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 max-w-3xl mx-auto mt-8">
              <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
                <div className="text-2xl mb-2">💡</div>
                <p className="text-sm font-medium text-gray-700">Quick Questions</p>
                <p className="text-xs text-gray-500 mt-1">Ask about anything</p>
              </div>
              <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
                <div className="text-2xl mb-2">🎨</div>
                <p className="text-sm font-medium text-gray-700">Creative Writing</p>
                <p className="text-xs text-gray-500 mt-1">Generate content</p>
              </div>
              <div className="bg-white p-4 rounded-lg shadow-sm border border-gray-200">
                <div className="text-2xl mb-2">💻</div>
                <p className="text-sm font-medium text-gray-700">Code Help</p>
                <p className="text-xs text-gray-500 mt-1">Debug & learn</p>
              </div>
            </div>
          </div>
        )}
        {messages.map((message) => (
          <ChatMessage key={message.id} message={message} />
        ))}
        {isLoading && (
          <div className="flex justify-start mb-5">
            <div className="bg-white text-gray-900 rounded-xl px-5 py-3 shadow-md border-2 border-gray-200">
              <div className="text-xs font-bold mb-2 text-gray-700">
                🤖 Assistant
              </div>
              <div className="flex space-x-2">
                <div className="w-3 h-3 bg-blue-600 rounded-full animate-bounce"></div>
                <div className="w-3 h-3 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '0.2s' }}></div>
                <div className="w-3 h-3 bg-blue-600 rounded-full animate-bounce" style={{ animationDelay: '0.4s' }}></div>
              </div>
            </div>
          </div>
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input */}
      <ChatInput
        onSendMessage={handleSendMessage}
        disabled={isLoading}
        models={models}
        selectedModel={selectedModel}
        onModelChange={setSelectedModel}
      />
    </div>
  );
};

export default ChatWindow;
