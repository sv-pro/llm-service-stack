import { test, expect } from '@playwright/test';

test.describe('Playground screen', () => {
  test('redirects / to playground and shows gateway status widget', async ({ page, baseURL }) => {
    if (!baseURL) {
      test.fail(true, 'Playwright baseURL is not configured');
      return;
    }

    await page.goto(baseURL);
    await expect(page).toHaveURL(/\/playground$/);
    await expect(page.getByRole('heading', { name: /playground/i })).toBeVisible();
    const status = page.locator('.gateway-status');
    await expect(status).toBeVisible();
    await expect(status).not.toHaveText(/Checking/i, { timeout: 7000 });
  });

  test('allows navigation back to playground from other tabs', async ({ page, baseURL }) => {
    if (!baseURL) {
      test.fail(true, 'Playwright baseURL is not configured');
      return;
    }

    await page.goto(baseURL);
    await page.getByRole('link', { name: /cost explorer/i }).click();
    await expect(page).toHaveURL(/\/costs$/);

    const playgroundLink = page.getByRole('link', { name: /playground/i });
    await playgroundLink.click();
    await expect(page).toHaveURL(/\/playground$/);
    await expect(playgroundLink).toHaveAttribute('aria-current', 'page');
  });
});
