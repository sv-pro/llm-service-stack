// @ts-check
import { defineConfig } from '@playwright/test';

const baseURL = process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:3000';
const slowMo = process.env.PLAYWRIGHT_SLOWMO ? Number(process.env.PLAYWRIGHT_SLOWMO) : undefined;
const testTimeout = process.env.PLAYWRIGHT_TEST_TIMEOUT ? Number(process.env.PLAYWRIGHT_TEST_TIMEOUT) : undefined;
const reporter = process.env.PLAYWRIGHT_REPORTER ? process.env.PLAYWRIGHT_REPORTER.split(',').map((name) => name.trim()) : undefined;
const webServer =
  process.env.PLAYWRIGHT_WEB_SERVER === 'true'
    ? {
        command: 'npm run dev -- --host --port 3000',
        url: baseURL,
        reuseExistingServer: true,
        stdout: 'pipe',
        stderr: 'pipe',
      }
    : undefined;

export default defineConfig({
  testDir: './tests/ui',
  timeout: testTimeout ?? 30 * 1000,
  retries: process.env.CI ? 2 : 0,
  reporter: reporter?.length ? reporter : 'list',
  use: {
    baseURL,
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
    launchOptions: slowMo ? { slowMo } : {},
  },
  webServer,
});
