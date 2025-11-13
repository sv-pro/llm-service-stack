import { test, expect } from '@playwright/test';

test.describe('Dashboard navigation', () => {
  test('shows Cost Explorer link and navigates', async ({ page, baseURL }) => {
    if (!baseURL) {
      test.fail(true, 'Playwright baseURL is not configured');
      return;
    }

    await page.goto(baseURL);

    const costExplorerLink = page.getByRole('link', { name: /cost explorer/i });
    await expect(costExplorerLink).toBeVisible();

    await costExplorerLink.click();
    await expect(page).toHaveURL(/\/costs$/);
    await expect(page.getByRole('heading', { name: /cost explorer/i })).toBeVisible();
  });
});
