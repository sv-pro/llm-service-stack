/**
 * API service for communicating with the LLM backend
 *
 * API Key is optional for localhost development when ALLOW_LOCALHOST_BYPASS
 * is enabled on the server. For production, always provide an API key.
 */

import { ChatCompletionRequest, ChatCompletionResponse, ModelInfo } from '../types/chat';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:3000/api';
const API_KEY = process.env.REACT_APP_API_KEY || '';

export class ApiService {
  private apiUrl: string;
  private apiKey: string;
  private modelsCache: ModelInfo[] = [];

  constructor(apiUrl: string = API_URL, apiKey: string = API_KEY) {
    this.apiUrl = apiUrl;
    this.apiKey = apiKey;
  }

  /**
   * Send a chat completion request to the API
   */
  async sendMessage(request: ChatCompletionRequest): Promise<ChatCompletionResponse> {
    // Build headers - only include Authorization if API key is provided
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
    };

    if (this.apiKey) {
      headers['Authorization'] = `Bearer ${this.apiKey}`;
    }

    const response = await fetch(`${this.apiUrl}/gateway`, {
      method: 'POST',
      headers,
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      const errorMessage = errorData.error || response.statusText;
      const hint = errorData.hint || '';
      throw new Error(`API request failed: ${errorMessage}${hint ? ` (${hint})` : ''}`);
    }

    return response.json();
  }

  /**
   * Set the API key for authentication
   */
  setApiKey(apiKey: string): void {
    this.apiKey = apiKey;
  }

  /**
   * Check API health
   */
  async healthCheck(): Promise<boolean> {
    try {
      const response = await fetch(`${this.apiUrl}/gateway`);
      return response.ok;
    } catch (error) {
      return false;
    }
  }

  /**
   * Fetch available models with full metadata from the gateway
   */
  async fetchModels(): Promise<ModelInfo[]> {
    try {
      // Build headers - only include Authorization if API key is provided
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      };

      if (this.apiKey) {
        headers['Authorization'] = `Bearer ${this.apiKey}`;
      }

      const gatewayUrl = this.apiUrl.replace('/api', '');
      const response = await fetch(`${gatewayUrl}:8000/v1/models`, {
        method: 'GET',
        headers,
      });

      if (!response.ok) {
        throw new Error('Failed to fetch models');
      }

      const data = await response.json();
      this.modelsCache = data.data as ModelInfo[];
      return this.modelsCache;
    } catch (error) {
      console.error('Error fetching models:', error);
      // Return default models as fallback (all marked as unavailable)
      const fallbackModels: ModelInfo[] = [
        {
          id: 'gpt-4',
          object: 'model',
          owned_by: 'openai',
          vendor: 'openai',
          type: 'simple',
          endpoint: 'chat',
          available: false,
          unavailable_reason: 'Unable to fetch models'
        },
        {
          id: 'gpt-3.5-turbo',
          object: 'model',
          owned_by: 'openai',
          vendor: 'openai',
          type: 'simple',
          endpoint: 'chat',
          available: false,
          unavailable_reason: 'Unable to fetch models'
        },
        {
          id: 'claude-3-opus-20240229',
          object: 'model',
          owned_by: 'anthropic',
          vendor: 'anthropic',
          type: 'simple',
          endpoint: 'messages',
          available: false,
          unavailable_reason: 'Unable to fetch models'
        },
        {
          id: 'claude-3-sonnet-20240229',
          object: 'model',
          owned_by: 'anthropic',
          vendor: 'anthropic',
          type: 'simple',
          endpoint: 'messages',
          available: false,
          unavailable_reason: 'Unable to fetch models'
        },
      ];
      this.modelsCache = fallbackModels;
      return fallbackModels;
    }
  }

  /**
   * Get model info by ID from cache
   */
  getModelInfo(modelId: string): ModelInfo | undefined {
    return this.modelsCache.find(m => m.id === modelId);
  }
}

export const apiService = new ApiService();
