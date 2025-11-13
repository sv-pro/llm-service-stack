import { NextRequest, NextResponse } from 'next/server';
import { connectDB } from '@/lib/db';
import { ApiKey, Message, User } from '@/lib/models';
import bcrypt from 'bcryptjs';

/**
 * Gateway proxy endpoint
 * Forwards LLM requests to the gateway service with API key authentication
 *
 * In development mode (ALLOW_LOCALHOST_BYPASS=true), localhost requests
 * bypass API key validation for easier testing.
 */

const GATEWAY_URL = process.env.GATEWAY_URL || 'http://localhost:8000';
const ALLOW_LOCALHOST_BYPASS = process.env.ALLOW_LOCALHOST_BYPASS === 'true';

/**
 * Check if request is from localhost
 */
function isLocalhostRequest(request: NextRequest): boolean {
  // Check X-Forwarded-For header first (for proxied requests)
  const forwardedFor = request.headers.get('x-forwarded-for');
  if (forwardedFor) {
    const ip = forwardedFor.split(',')[0].trim();
    if (ip === '127.0.0.1' || ip === '::1' || ip === 'localhost') {
      return true;
    }
  }

  // Check direct connection (when available in edge runtime)
  const host = request.headers.get('host');
  if (host?.startsWith('localhost:') || host?.startsWith('127.0.0.1:')) {
    return true;
  }

  return false;
}

/**
 * Get or create a dev user for localhost bypass requests
 */
async function getOrCreateDevUser() {
  try {
    let devUser = await User.findOne({ email: 'dev@localhost' });

    if (!devUser) {
      devUser = await User.create({
        email: 'dev@localhost',
        name: 'Development User (Localhost)',
      });
      console.log('Created development user for localhost bypass');
    }

    return devUser;
  } catch (error) {
    console.error('Error getting/creating dev user:', error);
    return null;
  }
}

export async function POST(request: NextRequest) {
  try {
    await connectDB();

    // Extract API key from request headers
    const apiKey = request.headers.get('Authorization')?.replace('Bearer ', '');

    // Check if localhost bypass is enabled and request is from localhost
    const isLocalhost = isLocalhostRequest(request);
    const bypassAuth = ALLOW_LOCALHOST_BYPASS && isLocalhost && !apiKey;

    let validKey = null;

    if (bypassAuth) {
      // Localhost bypass mode - create/use dev user for tracking
      console.log('Localhost bypass enabled - skipping API key validation');
      const devUser = await getOrCreateDevUser();

      if (devUser) {
        // Create a virtual key object for logging purposes
        validKey = {
          userId: devUser._id,
          name: 'Localhost Bypass',
          isActive: true,
        };
      }
    } else {
      // Normal authentication flow
      if (!apiKey) {
        return NextResponse.json(
          {
            error: 'Missing API key',
            hint: ALLOW_LOCALHOST_BYPASS
              ? 'Set ALLOW_LOCALHOST_BYPASS=true to bypass authentication for localhost'
              : 'Provide an API key in the Authorization header'
          },
          { status: 401 }
        );
      }

      // Validate API key against database
      validKey = await validateApiKey(apiKey);

      if (!validKey) {
        return NextResponse.json(
          { error: 'Invalid or revoked API key' },
          { status: 401 }
        );
      }
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
    if (validKey) {
      await logUsage(validKey, body, data);
    }

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
