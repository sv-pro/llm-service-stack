/**
 * Type definitions for chat functionality
 */

export interface Message {
  id: string;
  role: 'user' | 'assistant' | 'system';
  content: string;
  timestamp: Date;
}

export interface ChatSession {
  id: string;
  messages: Message[];
  createdAt: Date;
}

export type ModelVendor = 'openai' | 'anthropic' | 'ollama';
export type ModelType = 'simple' | 'reasoning';
export type ModelEndpoint = 'chat' | 'messages';

export interface ModelInfo {
  id: string;
  object: string;
  owned_by: string;
  vendor: ModelVendor;
  type: ModelType;
  endpoint: ModelEndpoint;
  available: boolean;
  unavailable_reason?: string | null;
}

export interface ChatCompletionRequest {
  model: string;
  messages: Array<{
    role: string;
    content: string;
  }>;
  temperature?: number;
  max_tokens?: number;
}

export interface ChatCompletionResponse {
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
  usage: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
}
