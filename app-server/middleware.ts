import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

/**
 * Middleware to handle CORS for all API routes
 * Allows requests from web-chat and playground origins
 */
export function middleware(request: NextRequest) {
  // Get the origin from the request
  const origin = request.headers.get('origin');

  // List of allowed origins
  const allowedOrigins = [
    'http://localhost:3002', // web-chat
    'http://localhost:3001', // playground
    'http://localhost:3000', // app-server itself
  ];

  // Handle preflight requests
  if (request.method === 'OPTIONS') {
    const response = new NextResponse(null, { status: 204 });

    if (origin && allowedOrigins.includes(origin)) {
      response.headers.set('Access-Control-Allow-Origin', origin);
    } else if (!origin) {
      // Same-origin requests don't have Origin header
      response.headers.set('Access-Control-Allow-Origin', '*');
    }

    response.headers.set('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
    response.headers.set('Access-Control-Allow-Headers', 'Content-Type, Authorization');
    response.headers.set('Access-Control-Max-Age', '86400');

    return response;
  }

  // Handle actual requests - add CORS headers to response
  const response = NextResponse.next();

  if (origin && allowedOrigins.includes(origin)) {
    response.headers.set('Access-Control-Allow-Origin', origin);
  } else if (!origin) {
    // Same-origin requests don't have Origin header
    response.headers.set('Access-Control-Allow-Origin', '*');
  }

  response.headers.set('Access-Control-Allow-Methods', 'GET, POST, PUT, DELETE, OPTIONS');
  response.headers.set('Access-Control-Allow-Headers', 'Content-Type, Authorization');

  return response;
}

// Apply middleware to API routes
export const config = {
  matcher: '/api/:path*',
};
