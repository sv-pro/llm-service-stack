/**
 * ChatMessage Component
 * Displays a single chat message
 */

import React from 'react';
import { Message } from '../types/chat';

interface ChatMessageProps {
  message: Message;
}

const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const isUser = message.role === 'user';

  return (
    <div className={`flex ${isUser ? 'justify-end' : 'justify-start'} mb-5`}>
      <div
        className={`max-w-[70%] rounded-xl px-5 py-3 shadow-md ${
          isUser
            ? 'bg-gradient-to-r from-blue-600 to-blue-700 text-white'
            : 'bg-white text-gray-900 border-2 border-gray-200'
        }`}
      >
        <div className={`text-xs font-bold mb-2 ${isUser ? 'text-blue-100' : 'text-gray-700'}`}>
          {isUser ? '👤 You' : '🤖 Assistant'}
        </div>
        <div className={`text-sm whitespace-pre-wrap leading-relaxed ${isUser ? 'font-medium' : 'font-normal text-gray-900'}`}>
          {message.content}
        </div>
        <div className={`text-xs mt-2 font-medium ${isUser ? 'text-blue-200' : 'text-gray-500'}`}>
          {new Date(message.timestamp).toLocaleTimeString()}
        </div>
      </div>
    </div>
  );
};

export default ChatMessage;
