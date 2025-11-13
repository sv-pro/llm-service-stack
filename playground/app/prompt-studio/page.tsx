/**
 * Prompt Studio Page
 * Interactive environment for testing and refining prompts
 */

export default function PromptStudioPage() {
  return (
    <div className="min-h-screen p-8">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">Prompt Studio</h1>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          {/* Prompt Editor */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">Prompt Editor</h2>
            <div className="space-y-4">
              {/* Model Selection */}
              <div>
                <label className="block text-sm font-medium mb-2">Model</label>
                <select className="w-full px-3 py-2 border rounded-md">
                  <option>gpt-4</option>
                  <option>gpt-3.5-turbo</option>
                  <option>claude-2</option>
                </select>
              </div>

              {/* System Prompt */}
              <div>
                <label className="block text-sm font-medium mb-2">System Prompt</label>
                <textarea 
                  className="w-full px-3 py-2 border rounded-md h-24"
                  placeholder="You are a helpful assistant..."
                />
              </div>

              {/* User Message */}
              <div>
                <label className="block text-sm font-medium mb-2">User Message</label>
                <textarea 
                  className="w-full px-3 py-2 border rounded-md h-32"
                  placeholder="Enter your prompt here..."
                />
              </div>

              {/* Parameters */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-2">Temperature</label>
                  <input 
                    type="number" 
                    className="w-full px-3 py-2 border rounded-md"
                    defaultValue="0.7"
                    step="0.1"
                    min="0"
                    max="2"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-2">Max Tokens</label>
                  <input 
                    type="number" 
                    className="w-full px-3 py-2 border rounded-md"
                    defaultValue="1000"
                  />
                </div>
              </div>

              {/* Submit Button */}
              <button className="w-full bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700">
                Generate Response
              </button>
            </div>
          </div>

          {/* Response Viewer */}
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow p-6">
            <h2 className="text-xl font-semibold mb-4">Response</h2>
            <div className="space-y-4">
              {/* Response Text */}
              <div>
                <div className="bg-gray-50 dark:bg-gray-900 rounded-md p-4 h-96 overflow-y-auto">
                  <p className="text-sm text-gray-500">
                    Response will appear here...
                  </p>
                </div>
              </div>

              {/* Metadata */}
              <div className="border-t pt-4">
                <h3 className="text-sm font-medium mb-2">Metadata</h3>
                <div className="grid grid-cols-3 gap-4 text-sm">
                  <div>
                    <span className="text-gray-500">Tokens:</span>
                    <span className="ml-2 font-medium">-</span>
                  </div>
                  <div>
                    <span className="text-gray-500">Latency:</span>
                    <span className="ml-2 font-medium">-</span>
                  </div>
                  <div>
                    <span className="text-gray-500">Cost:</span>
                    <span className="ml-2 font-medium">-</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Saved Prompts */}
        <div className="mt-8 bg-white dark:bg-gray-800 rounded-lg shadow p-6">
          <h2 className="text-xl font-semibold mb-4">Saved Prompts</h2>
          <div className="text-sm text-gray-500">
            Your saved prompts will appear here...
          </div>
        </div>
      </div>
    </div>
  );
}
