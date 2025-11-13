/**
 * Navigation Component
 * Main navigation for the playground control panel
 */

import Link from 'next/link';

export default function Navigation() {
  return (
    <nav className="bg-white dark:bg-gray-800 shadow">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex">
            <div className="flex-shrink-0 flex items-center">
              <h1 className="text-xl font-bold">LLM Control Panel</h1>
            </div>
            <div className="hidden sm:ml-6 sm:flex sm:space-x-8">
              <Link
                href="/dashboard"
                className="inline-flex items-center px-1 pt-1 text-sm font-medium border-b-2 border-transparent hover:border-gray-300"
              >
                Dashboard
              </Link>
              <Link
                href="/prompt-studio"
                className="inline-flex items-center px-1 pt-1 text-sm font-medium border-b-2 border-transparent hover:border-gray-300"
              >
                Prompt Studio
              </Link>
              <Link
                href="/usage-inspector"
                className="inline-flex items-center px-1 pt-1 text-sm font-medium border-b-2 border-transparent hover:border-gray-300"
              >
                Usage Inspector
              </Link>
            </div>
          </div>
        </div>
      </div>
    </nav>
  );
}
