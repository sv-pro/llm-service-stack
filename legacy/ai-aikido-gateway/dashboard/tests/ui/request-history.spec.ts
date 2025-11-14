import { test, expect } from '@playwright/test';

test.describe('Request History screen', () => {
  test('navigates via sidebar and highlights active link', async ({ page, baseURL }) => {
    if (!baseURL) {
      test.fail(true, 'Playwright baseURL is not configured');
      return;
    }

    await page.goto(baseURL);

    const historyLink = page.getByRole('link', { name: /request history/i });
    await historyLink.click();

    await expect(page).toHaveURL(/\/requests$/);
    await expect(historyLink).toHaveAttribute('aria-current', 'page');
    await expect(page.getByRole('heading', { name: /request history/i })).toBeVisible();
  });

  test('shows stats cards or error banner', async ({ page, baseURL }) => {
    if (!baseURL) {
      test.fail(true, 'Playwright baseURL is not configured');
      return;
    }

    await page.goto(`${baseURL}/requests`);

    const heading = page.getByRole('heading', { name: /request history/i });
    await expect(heading).toBeVisible();

    const loader = page.locator('.loading-section');
    await loader.waitFor({ state: 'hidden', timeout: 7000 }).catch(() => null);

    const outcome = page.locator('.stat-card, .error-banner, .empty-state');
    await expect(outcome.first()).toBeVisible({ timeout: 7000 });
  });
});
