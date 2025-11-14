import { NextResponse } from 'next/server';

/**
 * Health check endpoint
 * Returns service status as JSON
 */
export async function GET() {
  return NextResponse.json({
    service: 'LLM App Server',
    version: '0.1.0',
    status: 'running',
    timestamp: new Date().toISOString(),
  });
}
