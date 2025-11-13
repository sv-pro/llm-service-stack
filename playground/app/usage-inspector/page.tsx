'use client';

/**
 * Usage Inspector Page
 * View and analyze API usage, costs, and logs
 */

import { useEffect, useState } from 'react';
import { fetchUsageLogs, fetchGatewayStats } from '@/lib/api-client';

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

export default function UsageInspectorPage() {
  const [logs, setLogs] = useState<UsageLog[]>([]);
  const [stats, setStats] = useState<GatewayStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [total, setTotal] = useState(0);
  const [limit] = useState(50);
  const [offset, setOffset] = useState(0);
  const [selectedModel, setSelectedModel] = useState<string>('');

  useEffect(() => {
    async function loadData() {
      try {
        setLoading(true);
        const [logsData, statsData] = await Promise.all([
          fetchUsageLogs(limit, offset, selectedModel || undefined),
          fetchGatewayStats(),
        ]);

        setLogs(logsData.logs);
        setTotal(logsData.total);
        setStats(statsData);
        setError(null);
      } catch (err) {
        console.error('Error loading usage data:', err);
        setError('Failed to load usage data. Make sure all services are running.');
      } finally {
        setLoading(false);
      }
    }

    loadData();
  }, [limit, offset, selectedModel]);

  const formatTimestamp = (timestamp: string) => {
    const date = new Date(timestamp);
    return date.toLocaleString();
  };

  const formatCost = (cost: number) => {
    return `$${cost.toFixed(6)}`;
  };

  const formatLatency = (latency: number) => {
    return `${latency.toFixed(0)}ms`;
  };

  const handlePreviousPage = () => {
    if (offset > 0) {
      setOffset(Math.max(0, offset - limit));
    }
  };

  const handleNextPage = () => {
    if (offset + limit < total) {
      setOffset(offset + limit);
    }
  };

  const uniqueModels = stats
    ? [...new Set(Object.keys(stats.by_model))]
    : [];

  if (loading && !logs.length) {
    return (
      <div className="min-h-screen p-8 flex items-center justify-center">
        <div className="text-center">
          <div className="text-2xl font-bold mb-4">Loading Usage Data...</div>
          <div className="text-gray-500">Fetching logs from gateway</div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">Usage Inspector</h1>

        {error && (
          <div className="bg-red-100 border border-red-400 text-red-700 px-4 py-3 rounded mb-6">
            {error}
          </div>
        )}

        {/* Filters */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Filters</h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">Date Range</label>
              <select className="w-full px-3 py-2 border rounded-md">
                <option>All Time</option>
                <option>Last 24 hours</option>
                <option>Last 7 days</option>
                <option>Last 30 days</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Model</label>
              <select
                className="w-full px-3 py-2 border rounded-md"
                value={selectedModel}
                onChange={(e) => {
                  setSelectedModel(e.target.value);
                  setOffset(0); // Reset to first page when filtering
                }}
              >
                <option value="">All Models</option>
                {uniqueModels.map(model => (
                  <option key={model} value={model}>{model}</option>
                ))}
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">User</label>
              <select className="w-full px-3 py-2 border rounded-md">
                <option>All Users</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Status</label>
              <select className="w-full px-3 py-2 border rounded-md">
                <option>All</option>
                <option>Success</option>
                <option>Error</option>
                <option>Cached</option>
              </select>
            </div>
          </div>
        </div>

        {/* Summary Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-6">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="text-sm text-gray-500 mb-1">Total Requests</div>
            <div className="text-3xl font-bold">{stats?.total_requests || 0}</div>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="text-sm text-gray-500 mb-1">Total Tokens</div>
            <div className="text-3xl font-bold">
              {stats?.total_tokens ? (stats.total_tokens / 1000).toFixed(1) + 'K' : '0'}
            </div>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="text-sm text-gray-500 mb-1">Total Cost</div>
            <div className="text-3xl font-bold">
              ${stats?.total_cost ? stats.total_cost.toFixed(4) : '0.00'}
            </div>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="text-sm text-gray-500 mb-1">Cache Hit Rate</div>
            <div className="text-3xl font-bold">
              {stats?.cache_hit_rate ? (stats.cache_hit_rate * 100).toFixed(1) : '0'}%
            </div>
          </div>
        </div>

        {/* Usage Logs Table */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow">
          <div className="p-6 border-b">
            <h2 className="text-xl font-semibold">Usage Logs</h2>
          </div>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead className="bg-gray-50 dark:bg-gray-900">
                <tr>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Timestamp
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Model
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Provider
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Tokens
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Latency
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Cost
                  </th>
                  <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                    Status
                  </th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                {logs.length > 0 ? (
                  logs.map(log => (
                    <tr key={log.id} className="hover:bg-gray-50 dark:hover:bg-gray-700">
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        {formatTimestamp(log.timestamp)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        {log.model}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <span className="capitalize">{log.provider}</span>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        <div className="text-xs text-gray-500">
                          P: {log.prompt_tokens} / C: {log.completion_tokens}
                        </div>
                        <div className="font-medium">{log.total_tokens}</div>
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        {formatLatency(log.latency_ms)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm font-medium">
                        {formatCost(log.cost)}
                      </td>
                      <td className="px-6 py-4 whitespace-nowrap text-sm">
                        {log.cache_hit ? (
                          <span className="px-2 py-1 bg-blue-100 text-blue-800 rounded-full text-xs">
                            Cached
                          </span>
                        ) : (
                          <span className="px-2 py-1 bg-green-100 text-green-800 rounded-full text-xs">
                            Success
                          </span>
                        )}
                      </td>
                    </tr>
                  ))
                ) : (
                  <tr>
                    <td className="px-6 py-4 whitespace-nowrap text-sm" colSpan={7}>
                      <div className="text-gray-500 text-center py-8">
                        {selectedModel
                          ? `No usage logs found for model "${selectedModel}"`
                          : 'No usage logs found. Try sending some requests through the gateway.'}
                      </div>
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
          <div className="px-6 py-4 border-t">
            <div className="flex items-center justify-between">
              <div className="text-sm text-gray-500">
                Showing {offset + 1} to {Math.min(offset + limit, total)} of {total} results
              </div>
              <div className="flex gap-2">
                <button
                  onClick={handlePreviousPage}
                  disabled={offset === 0}
                  className={`px-3 py-1 border rounded-md text-sm ${
                    offset === 0
                      ? 'opacity-50 cursor-not-allowed'
                      : 'hover:bg-gray-50 dark:hover:bg-gray-700'
                  }`}
                >
                  Previous
                </button>
                <button
                  onClick={handleNextPage}
                  disabled={offset + limit >= total}
                  className={`px-3 py-1 border rounded-md text-sm ${
                    offset + limit >= total
                      ? 'opacity-50 cursor-not-allowed'
                      : 'hover:bg-gray-50 dark:hover:bg-gray-700'
                  }`}
                >
                  Next
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
