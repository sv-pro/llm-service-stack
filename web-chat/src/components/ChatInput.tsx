/**
 * ChatInput Component
 * Input field for sending messages with model selector
 */

import React, { useState, KeyboardEvent, useEffect } from 'react';
import ModelSelector from './ModelSelector';
import { ModelInfo } from '../types/chat';

interface ChatInputProps {
  onSendMessage: (message: string) => void;
  disabled?: boolean;
  models: ModelInfo[];
  selectedModel: string;
  onModelChange: (model: string) => void;
  defaultPrompt?: string;
}

const ChatInput: React.FC<ChatInputProps> = ({
  onSendMessage,
  disabled = false,
  models,
  selectedModel,
  onModelChange,
  defaultPrompt = 'What is LLM?',
}) => {
  const [message, setMessage] = useState(defaultPrompt);

  // Update message when defaultPrompt changes
  useEffect(() => {
    setMessage(defaultPrompt);
  }, [defaultPrompt]);

  const handleSend = () => {
    if (message.trim() && !disabled) {
      onSendMessage(message);
      setMessage('');
    }
  };

  const handleKeyPress = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <div className="border-t border-gray-300 bg-white p-4 shadow-lg">
      {/* Model Selector Row */}
      <div className="mb-3 flex justify-between items-center">
        <ModelSelector
          models={models}
          selectedModel={selectedModel}
          onModelChange={onModelChange}
          disabled={disabled}
        />
        <div className="text-xs text-gray-500">
          Press Enter to send, Shift+Enter for new line
        </div>
      </div>

      {/* Input Row */}
      <div className="flex gap-3">
        <textarea
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyPress={handleKeyPress}
          placeholder="Type your message..."
          disabled={disabled}
          className="flex-1 px-4 py-3 border border-gray-300 rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-transparent disabled:bg-gray-50 disabled:text-gray-500"
          rows={3}
        />
        <button
          onClick={handleSend}
          disabled={disabled || !message.trim()}
          className="px-8 py-3 bg-gradient-to-r from-blue-600 to-blue-700 text-white font-medium rounded-lg hover:from-blue-700 hover:to-blue-800 disabled:from-gray-300 disabled:to-gray-400 disabled:cursor-not-allowed transition-all duration-200 shadow-md hover:shadow-lg"
        >
          Send
        </button>
      </div>
    </div>
  );
};

export default ChatInput;
