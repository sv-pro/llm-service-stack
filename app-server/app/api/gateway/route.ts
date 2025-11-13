import { NextRequest, NextResponse } from 'next/server';

/**
 * Gateway proxy endpoint
 * Forwards LLM requests to the gateway service
 */

const GATEWAY_URL = process.env.GATEWAY_URL || 'http://localhost:8000';

export async function POST(request: NextRequest) {
  try {
    // Extract API key from request headers
    const apiKey = request.headers.get('Authorization')?.replace('Bearer ', '');

    if (!apiKey) {
      return NextResponse.json(
        { error: 'Missing API key' },
        { status: 401 }
      );
    }

    // TODO: Validate API key against database

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

    // TODO: Log usage for this API key/user

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
