import { NextRequest, NextResponse } from 'next/server';
import { connectDB } from '@/lib/db';
import { ApiKey, Message } from '@/lib/models';
import bcrypt from 'bcryptjs';

/**
 * Gateway proxy endpoint
 * Forwards LLM requests to the gateway service with API key authentication
 */

const GATEWAY_URL = process.env.GATEWAY_URL || 'http://localhost:8000';

export async function POST(request: NextRequest) {
  try {
    await connectDB();

    // Extract API key from request headers
    const apiKey = request.headers.get('Authorization')?.replace('Bearer ', '');

    if (!apiKey) {
      return NextResponse.json(
        { error: 'Missing API key' },
        { status: 401 }
      );
    }

    // Validate API key against database
    const validKey = await validateApiKey(apiKey);

    if (!validKey) {
      return NextResponse.json(
        { error: 'Invalid or revoked API key' },
        { status: 401 }
      );
    }

    // Get request body
    const body = await request.json();

    // Forward request to gateway service
    const gatewayResponse = await fetch(`${GATEWAY_URL}/v1/chat/completions`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(body),
    });

    const data = await gatewayResponse.json();

    // Log usage for this API key/user
    await logUsage(validKey, body, data);

    return NextResponse.json(data, {
      status: gatewayResponse.status,
    });
  } catch (error) {
    console.error('Gateway proxy error:', error);
    return NextResponse.json(
      { error: 'Failed to forward request to gateway' },
      { status: 500 }
    );
  }
}

/**
 * Validate API key and return key document if valid
 */
async function validateApiKey(apiKey: string) {
  try {
    // Get all active API keys
    const activeKeys = await ApiKey.find({ isActive: true });

    // Check each key's hash
    for (const keyDoc of activeKeys) {
      const isValid = await bcrypt.compare(apiKey, keyDoc.keyHash);
      if (isValid) {
        // Update last used timestamp
        await ApiKey.findByIdAndUpdate(keyDoc._id, {
          lastUsedAt: new Date(),
        });
        return keyDoc;
      }
    }

    return null;
  } catch (error) {
    console.error('Error validating API key:', error);
    return null;
  }
}

/**
 * Log usage to database
 */
async function logUsage(keyDoc: any, request: any, response: any) {
  try {
    const sessionId = request.sessionId; // Optional session ID from request

    // Extract the last user message for storage
    const lastMessage = request.messages?.[request.messages.length - 1];
    const assistantMessage = response.choices?.[0]?.message;

    if (sessionId && lastMessage) {
      // Store user message
      await Message.create({
        sessionId,
        role: lastMessage.role,
        content: lastMessage.content,
        tokens: response.usage?.prompt_tokens,
      });

      // Store assistant response
      if (assistantMessage) {
        await Message.create({
          sessionId,
          role: assistantMessage.role,
          content: assistantMessage.content,
          tokens: response.usage?.completion_tokens,
          cost: calculateCost(request.model, response.usage),
        });
      }
    }
  } catch (error) {
    console.error('Error logging usage:', error);
    // Don't fail the request if logging fails
  }
}

/**
 * Calculate approximate cost based on model and token usage
 */
function calculateCost(model: string, usage: any): number {
  if (!usage) return 0;

  // Pricing per 1M tokens (as of 2024)
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
}

// Health check
export async function GET() {
  try {
    const response = await fetch(`${GATEWAY_URL}/`);
    const data = await response.json();

    return NextResponse.json({
      message: 'Gateway proxy is running',
      gateway: data,
    });
  } catch (error) {
    return NextResponse.json(
      { error: 'Gateway not reachable' },
      { status: 503 }
    );
  }
}
