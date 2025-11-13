/**
 * API service for communicating with the LLM backend
 */

import { ChatCompletionRequest, ChatCompletionResponse } from '../types/chat';

const API_URL = process.env.REACT_APP_API_URL || 'http://localhost:3000/api';
const API_KEY = process.env.REACT_APP_API_KEY || '';

export class ApiService {
  private apiUrl: string;
  private apiKey: string;

  constructor(apiUrl: string = API_URL, apiKey: string = API_KEY) {
    this.apiUrl = apiUrl;
    this.apiKey = apiKey;
  }

  /**
   * Send a chat completion request to the API
   */
  async sendMessage(request: ChatCompletionRequest): Promise<ChatCompletionResponse> {
    const response = await fetch(`${this.apiUrl}/gateway`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${this.apiKey}`,
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      throw new Error(`API request failed: ${response.statusText}`);
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
}

export const apiService = new ApiService();
