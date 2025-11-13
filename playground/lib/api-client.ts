/**
 * API Client for Playground
 * Fetches data from App Server and Gateway services
 */

const APP_SERVER_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3000/api';
const GATEWAY_URL = process.env.NEXT_PUBLIC_GATEWAY_URL || 'http://localhost:8000';

interface Stats {
  totalUsers: number;
  totalSessions: number;
  totalApiKeys: number;
  activeApiKeys: number;
  totalMessages: number;
}

interface RecentUser {
  _id: string;
  email: string;
  name?: string;
  createdAt: string;
}

interface RecentSession {
  _id: string;
  title?: string;
  llmModel: string;
  userId: {
    _id: string;
    email: string;
    name?: string;
  };
  createdAt: string;
}

interface RecentApiKey {
  _id: string;
  name?: string;
  keyPrefix: string;
  userId: {
    _id: string;
    email: string;
    name?: string;
  };
  createdAt: string;
  lastUsedAt?: string;
}

interface StatsResponse {
  stats: Stats;
  recentActivity: {
    users: RecentUser[];
    sessions: RecentSession[];
    apiKeys: RecentApiKey[];
  };
  topSessions: Array<{
    _id: string;
    count: number;
  }>;
}

interface UsageLog {
  id: number;
  timestamp: string;
  model: string;
  provider: string;
  prompt_tokens: number;
  completion_tokens: number;
  total_tokens: number;
  cost: number;
  latency_ms: number;
  user_id?: string;
  api_key_id?: string;
  cache_hit: boolean;
}

interface UsageLogsResponse {
  logs: UsageLog[];
  total: number;
  limit: number;
  offset: number;
}

interface GatewayStats {
  total_requests: number;
  total_cost: number;
  total_tokens: number;
  by_model: Record<string, {
    requests: number;
    cost: number;
    tokens: number;
  }>;
}

/**
 * Fetch aggregated stats from app-server
 */
export async function fetchStats(): Promise<StatsResponse> {
  const response = await fetch(`${APP_SERVER_URL}/stats`);
  if (!response.ok) {
    throw new Error('Failed to fetch stats');
  }
  return response.json();
}

/**
 * Fetch usage logs from gateway
 */
export async function fetchUsageLogs(
  limit: number = 100,
  offset: number = 0,
  model?: string
): Promise<UsageLogsResponse> {
  const params = new URLSearchParams({
    limit: limit.toString(),
    offset: offset.toString(),
  });

  if (model) {
    params.append('model', model);
  }

  const response = await fetch(`${GATEWAY_URL}/v1/usage/logs?${params}`);
  if (!response.ok) {
    throw new Error('Failed to fetch usage logs');
  }
  return response.json();
}

/**
 * Fetch gateway usage statistics
 */
export async function fetchGatewayStats(): Promise<GatewayStats> {
  const response = await fetch(`${GATEWAY_URL}/v1/usage/stats`);
  if (!response.ok) {
    throw new Error('Failed to fetch gateway stats');
  }
  return response.json();
}

/**
 * Fetch all users from app-server
 */
export async function fetchUsers(limit: number = 10, offset: number = 0) {
  const params = new URLSearchParams({
    limit: limit.toString(),
    offset: offset.toString(),
  });

  const response = await fetch(`${APP_SERVER_URL}/users?${params}`);
  if (!response.ok) {
    throw new Error('Failed to fetch users');
  }
  return response.json();
}

/**
 * Fetch all sessions from app-server
 */
export async function fetchSessions(userId?: string) {
  const params = new URLSearchParams();
  if (userId) {
    params.append('userId', userId);
  }

  const url = `${APP_SERVER_URL}/sessions${params.toString() ? `?${params}` : ''}`;
  const response = await fetch(url);
  if (!response.ok) {
    throw new Error('Failed to fetch sessions');
  }
  return response.json();
}

/**
 * Fetch messages for a session
 */
export async function fetchMessages(sessionId: string) {
  const response = await fetch(`${APP_SERVER_URL}/messages?sessionId=${sessionId}`);
  if (!response.ok) {
    throw new Error('Failed to fetch messages');
  }
  return response.json();
}

/**
 * Check service health
 */
export async function checkServiceHealth() {
  try {
    const [gatewayHealth, appServerHealth] = await Promise.all([
      fetch(`${GATEWAY_URL}/`).then(r => r.json()),
      fetch(`${APP_SERVER_URL.replace('/api', '')}/`).then(r => r.json()),
    ]);

    return {
      gateway: {
        status: gatewayHealth.status === 'running' ? 'running' : 'error',
        ...gatewayHealth,
      },
      appServer: {
        status: appServerHealth.status === 'running' ? 'running' : 'error',
        ...appServerHealth,
      },
    };
  } catch (error) {
    console.error('Error checking service health:', error);
    return {
      gateway: { status: 'error' },
      appServer: { status: 'error' },
    };
  }
}
