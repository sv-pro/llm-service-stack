'use client';

/**
 * Dashboard Page
 * Overview of system status, usage, and key metrics
 */

import { useEffect, useState } from 'react';
import { fetchStats, fetchGatewayStats, checkServiceHealth } from '@/lib/api-client';

interface Stats {
  totalUsers: number;
  totalSessions: number;
  totalApiKeys: number;
  activeApiKeys: number;
  totalMessages: number;
}

interface RecentActivity {
  users: Array<{
    _id: string;
    email: string;
    name?: string;
    createdAt: string;
  }>;
  sessions: Array<{
    _id: string;
    title?: string;
    llmModel: string;
    userId: {
      _id: string;
      email: string;
      name?: string;
    };
    createdAt: string;
  }>;
  apiKeys: Array<{
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
  }>;
}

interface GatewayStats {
  total_requests: number;
  total_cost: number;
  total_tokens: number;
  cache_hit_rate: number;
  by_model: Record<string, {
    requests: number;
    cost: number;
    tokens: number;
  }>;
}

interface ServiceHealth {
  gateway: { status: string };
  appServer: { status: string };
}

export default function DashboardPage() {
  const [stats, setStats] = useState<Stats | null>(null);
  const [recentActivity, setRecentActivity] = useState<RecentActivity | null>(null);
  const [gatewayStats, setGatewayStats] = useState<GatewayStats | null>(null);
  const [serviceHealth, setServiceHealth] = useState<ServiceHealth | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const [statsData, gatewayData, healthData] = await Promise.all([
          fetchStats(),
          fetchGatewayStats(),
          checkServiceHealth(),
        ]);

        setStats(statsData.stats);
        setRecentActivity(statsData.recentActivity);
        setGatewayStats(gatewayData);
        setServiceHealth(healthData);
        setError(null);
      } catch (err) {
        console.error('Error loading dashboard data:', err);
        setError('Failed to load dashboard data. Make sure all services are running.');
      } finally {
        setLoading(false);
      }
    }

    loadData();
    // Refresh data every 30 seconds
    const interval = setInterval(loadData, 30000);
    return () => clearInterval(interval);
  }, []);

  if (loading && !stats) {
    return (
      <div className="min-h-screen p-8 flex items-center justify-center">
        <div className="text-center">
          <div className="text-2xl font-bold mb-4">Loading Dashboard...</div>
          <div className="text-gray-500">Fetching data from services</div>
        </div>
      </div>
    );
  }

  if (error && !stats) {
    return (
      <div className="min-h-screen p-8 flex items-center justify-center">
        <div className="text-center">
          <div className="text-2xl font-bold mb-4 text-red-600">Error</div>
          <div className="text-gray-500">{error}</div>
          <button
            onClick={() => window.location.reload()}
            className="mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
          >
            Retry
          </button>
        </div>
      </div>
    );
  }

  // Calculate model usage percentages
  const modelUsage = gatewayStats?.by_model
    ? Object.entries(gatewayStats.by_model).map(([model, data]) => ({
        model,
        requests: data.requests,
        percentage: gatewayStats.total_requests > 0
          ? (data.requests / gatewayStats.total_requests) * 100
          : 0,
      }))
    : [];

  // Sort by requests descending
  modelUsage.sort((a, b) => b.requests - a.requests);

  // Format time ago
  const timeAgo = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const seconds = Math.floor((now.getTime() - date.getTime()) / 1000);

    if (seconds < 60) return `${seconds}s ago`;
    if (seconds < 3600) return `${Math.floor(seconds / 60)}m ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)}h ago`;
    return `${Math.floor(seconds / 86400)}d ago`;
  };

  return (
    <div className="min-h-screen p-8">
      <div className="max-w-7xl mx-auto">
        <div className="flex items-center justify-between mb-8">
          <h1 className="text-3xl font-bold">Dashboard</h1>
          {loading && (
            <div className="text-sm text-gray-500">Refreshing...</div>
          )}
        </div>

        {/* Key Metrics */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-gray-500 mb-1">Total Users</div>
                <div className="text-2xl font-bold">{stats?.totalUsers || 0}</div>
              </div>
              <div className="bg-blue-100 dark:bg-blue-900 rounded-full p-3">
                <svg className="w-6 h-6 text-blue-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4.354a4 4 0 110 5.292M15 21H3v-1a6 6 0 0112 0v1zm0 0h6v-1a6 6 0 00-9-5.197M13 7a4 4 0 11-8 0 4 4 0 018 0z" />
                </svg>
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-gray-500 mb-1">Active Sessions</div>
                <div className="text-2xl font-bold">{stats?.totalSessions || 0}</div>
              </div>
              <div className="bg-green-100 dark:bg-green-900 rounded-full p-3">
                <svg className="w-6 h-6 text-green-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                </svg>
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-gray-500 mb-1">API Keys</div>
                <div className="text-2xl font-bold">{stats?.activeApiKeys || 0}</div>
                <div className="text-xs text-gray-400">
                  {stats?.totalApiKeys || 0} total
                </div>
              </div>
              <div className="bg-purple-100 dark:bg-purple-900 rounded-full p-3">
                <svg className="w-6 h-6 text-purple-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 7a2 2 0 012 2m4 0a6 6 0 01-7.743 5.743L11 17H9v2H7v2H4a1 1 0 01-1-1v-2.586a1 1 0 01.293-.707l5.964-5.964A6 6 0 1121 9z" />
                </svg>
              </div>
            </div>
          </div>

          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-gray-500 mb-1">Total Requests</div>
                <div className="text-2xl font-bold">{gatewayStats?.total_requests || 0}</div>
                <div className="text-xs text-gray-400">
                  {gatewayStats?.total_tokens ? `${(gatewayStats.total_tokens / 1000).toFixed(1)}K tokens` : '0 tokens'}
                </div>
              </div>
              <div className="bg-orange-100 dark:bg-orange-900 rounded-full p-3">
                <svg className="w-6 h-6 text-orange-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
                </svg>
              </div>
            </div>
          </div>
        </div>

        {/* Charts Row */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Cost Summary */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">Cost Summary</h2>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-500">Total Cost</span>
                <span className="text-2xl font-bold">
                  ${gatewayStats?.total_cost ? gatewayStats.total_cost.toFixed(4) : '0.00'}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-500">Cache Hit Rate</span>
                <span className="text-lg font-semibold">
                  {gatewayStats?.cache_hit_rate ? (gatewayStats.cache_hit_rate * 100).toFixed(1) : '0'}%
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm text-gray-500">Messages Stored</span>
                <span className="text-lg font-semibold">{stats?.totalMessages || 0}</span>
              </div>
            </div>
          </div>

          {/* Request Distribution */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">Request Distribution</h2>
            {gatewayStats?.total_requests ? (
              <div className="space-y-3">
                {Object.entries(gatewayStats.by_provider || {}).map(([provider, data]) => (
                  <div key={provider}>
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm font-medium capitalize">{provider}</span>
                      <span className="text-sm text-gray-500">
                        {data.requests} requests (${data.cost.toFixed(4)})
                      </span>
                    </div>
                    <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                      <div
                        className="bg-blue-600 h-2 rounded-full"
                        style={{
                          width: `${(data.requests / gatewayStats.total_requests) * 100}%`
                        }}
                      ></div>
                    </div>
                  </div>
                ))}
              </div>
            ) : (
              <div className="h-40 flex items-center justify-center text-gray-500">
                No request data yet
              </div>
            )}
          </div>
        </div>

        {/* System Status */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-8">
          {/* Service Status */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">Service Status</h2>
            <div className="space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-sm">Gateway Service</span>
                <span className={`flex items-center ${
                  serviceHealth?.gateway.status === 'running' ? 'text-green-600' : 'text-red-600'
                }`}>
                  <span className={`w-2 h-2 ${
                    serviceHealth?.gateway.status === 'running' ? 'bg-green-600' : 'bg-red-600'
                  } rounded-full mr-2`}></span>
                  {serviceHealth?.gateway.status === 'running' ? 'Running' : 'Error'}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">App Server</span>
                <span className={`flex items-center ${
                  serviceHealth?.appServer.status === 'running' ? 'text-green-600' : 'text-red-600'
                }`}>
                  <span className={`w-2 h-2 ${
                    serviceHealth?.appServer.status === 'running' ? 'bg-green-600' : 'bg-red-600'
                  } rounded-full mr-2`}></span>
                  {serviceHealth?.appServer.status === 'running' ? 'Running' : 'Error'}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">MongoDB</span>
                <span className="flex items-center text-green-600">
                  <span className="w-2 h-2 bg-green-600 rounded-full mr-2"></span>
                  Running
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-sm">Redis Cache</span>
                <span className="flex items-center text-green-600">
                  <span className="w-2 h-2 bg-green-600 rounded-full mr-2"></span>
                  Running
                </span>
              </div>
            </div>
          </div>

          {/* Recent Activity */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">Recent Activity</h2>
            <div className="space-y-3">
              {recentActivity?.users.slice(0, 1).map(user => (
                <div key={user._id} className="text-sm">
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-medium">New user registered</span>
                    <span className="text-gray-500">{timeAgo(user.createdAt)}</span>
                  </div>
                  <div className="text-gray-500">{user.email}</div>
                </div>
              ))}
              {recentActivity?.apiKeys.slice(0, 1).map(key => (
                <div key={key._id} className="text-sm">
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-medium">API key created</span>
                    <span className="text-gray-500">{timeAgo(key.createdAt)}</span>
                  </div>
                  <div className="text-gray-500">{key.name || key.keyPrefix}</div>
                </div>
              ))}
              {recentActivity?.sessions.slice(0, 1).map(session => (
                <div key={session._id} className="text-sm">
                  <div className="flex items-center justify-between mb-1">
                    <span className="font-medium">New session created</span>
                    <span className="text-gray-500">{timeAgo(session.createdAt)}</span>
                  </div>
                  <div className="text-gray-500">{session.title || session.llmModel}</div>
                </div>
              ))}
              {(!recentActivity?.users.length && !recentActivity?.apiKeys.length && !recentActivity?.sessions.length) && (
                <div className="text-sm text-gray-500 text-center py-4">
                  No recent activity
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Model Usage */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Model Usage</h2>
          {modelUsage.length > 0 ? (
            <div className="space-y-4">
              {modelUsage.map(({ model, requests, percentage }) => (
                <div key={model}>
                  <div className="flex items-center justify-between mb-2">
                    <span className="text-sm font-medium">{model}</span>
                    <span className="text-sm text-gray-500">
                      {percentage.toFixed(1)}% ({requests} requests)
                    </span>
                  </div>
                  <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                    <div
                      className="bg-blue-600 h-2 rounded-full"
                      style={{ width: `${percentage}%` }}
                    ></div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-500">
              No model usage data yet
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
