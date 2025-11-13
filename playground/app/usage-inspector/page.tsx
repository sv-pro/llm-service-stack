/**
 * Usage Inspector Page
 * View and analyze API usage, costs, and logs
 */

export default function UsageInspectorPage() {
  return (
    <div className="min-h-screen p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">Usage Inspector</h1>

        {/* Filters */}
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Filters</h2>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium mb-2">Date Range</label>
              <select className="w-full px-3 py-2 border rounded-md">
                <option>Last 24 hours</option>
                <option>Last 7 days</option>
                <option>Last 30 days</option>
                <option>Custom</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-2">Model</label>
              <select className="w-full px-3 py-2 border rounded-md">
                <option>All Models</option>
                <option>gpt-4</option>
                <option>gpt-3.5-turbo</option>
                <option>claude-2</option>
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
            <div className="text-3xl font-bold">1,234</div>
            <div className="text-sm text-green-600 mt-1">+12% from last period</div>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="text-sm text-gray-500 mb-1">Total Tokens</div>
            <div className="text-3xl font-bold">456K</div>
            <div className="text-sm text-green-600 mt-1">+8% from last period</div>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="text-sm text-gray-500 mb-1">Total Cost</div>
            <div className="text-3xl font-bold">$78.90</div>
            <div className="text-sm text-red-600 mt-1">+15% from last period</div>
          </div>
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <div className="text-sm text-gray-500 mb-1">Cache Hit Rate</div>
            <div className="text-3xl font-bold">34%</div>
            <div className="text-sm text-gray-500 mt-1">Average: 30%</div>
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
                    User
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
                <tr>
                  <td className="px-6 py-4 whitespace-nowrap text-sm" colSpan={7}>
                    <div className="text-gray-500 text-center py-8">
                      No usage logs found for the selected filters
                    </div>
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
          <div className="px-6 py-4 border-t">
            <div className="flex items-center justify-between">
              <div className="text-sm text-gray-500">
                Showing 0 of 0 results
              </div>
              <div className="flex gap-2">
                <button className="px-3 py-1 border rounded-md text-sm hover:bg-gray-50 dark:hover:bg-gray-700">
                  Previous
                </button>
                <button className="px-3 py-1 border rounded-md text-sm hover:bg-gray-50 dark:hover:bg-gray-700">
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
