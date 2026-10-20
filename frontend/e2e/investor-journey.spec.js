import { test, expect } from '@playwright/test';

const ownerEmail = `phase6-e2e-owner-${Date.now()}@example.test`;
const secondEmail = `phase6-e2e-second-${Date.now()}@example.test`;
const password = 'Browser-Journey-Test-2026';
const apiBase = 'http://127.0.0.1:8000';

test('investor onboarding, advice, portfolio, risk feedback, ownership and mobile workspace', async ({ page, browser }) => {
  const responses = {};
  page.on('response', async (response) => {
    try {
      const url = response.url();
      if (url.includes('/auth/register') || url.includes('/recommendations/') && url.endsWith('/generate') || url.endsWith('/portfolios') || url.includes('/holdings') || url.endsWith('/risk')) {
        responses[url] = await response.json();
      }
    } catch { /* non-JSON or intentionally empty responses */ }
  });
  await page.goto('/');
  await expect(page.getByRole('heading', { name: 'Welcome back' })).toBeVisible();
  await page.getByRole('button', { name: 'Create an account' }).click();
  await page.getByLabel('Full name').fill('Browser Journey Investor');
  await page.getByLabel('Email address').fill(ownerEmail);
  await page.getByLabel('Password').fill('short');
  await expect(page.getByLabel('Password')).toHaveJSProperty('validity.valid', false);
  await page.getByLabel('Password').fill(password);
  await page.getByLabel('PAN SHA-256 hash').fill('a'.repeat(64));
  const registerResponse = page.waitForResponse((response) => response.url().endsWith('/auth/register'));
  await page.getByRole('button', { name: 'Create account' }).click();
  const registered = await (await registerResponse).json();
  const ownerId = registered.user.user_id;
  await expect(page.getByText('Available after reserve')).toBeVisible();

  await page.getByRole('button', { name: 'Cash flow', exact: true }).click();
  await page.getByRole('button', { name: 'Add income' }).first().click();
  await page.getByLabel('Source').fill('Monthly salary');
  await page.getByLabel('Amount (INR)').first().fill('250000');
  const incomeResponse = page.waitForResponse((response) => response.url().includes(`/cashflow/${ownerId}/income`) && response.request().method() === 'POST');
  await page.getByRole('button', { name: 'Add source' }).click();
  const income = await (await incomeResponse).json();
  await expect(page.getByText('Monthly salary')).toBeVisible();
  await page.getByRole('button', { name: 'Add expense' }).first().click();
  await page.getByLabel('Expense').fill('Rent');
  await page.getByLabel('Amount (INR)').last().fill('45000');
  await page.locator('form.expense-entry button.button-primary').click();
  await expect(page.getByText('Rent')).toBeVisible();
  await page.getByRole('button', { name: 'Evaluate cash flow' }).click();
  await expect(page.locator('.metric-card').filter({ hasText: 'Investable buffer' }).locator('.metric-value')).not.toHaveText('—');

  await page.getByRole('button', { name: 'Recommendations', exact: true }).click();
  await page.getByRole('button', { name: 'Generate recommendations' }).first().click();
  await expect(page.locator('tbody tr').first()).toBeVisible();
  await page.getByRole('button', { name: 'Accept' }).first().click();
  await expect(page.getByText('Intent recorded. No brokerage order was sent.')).toBeVisible();
  const declines = page.getByRole('button', { name: 'Decline' });
  let pendingDecisions = await declines.count();
  while (pendingDecisions > 0) {
    await expect(declines.first()).toBeEnabled();
    await declines.first().click();
    await expect(declines).toHaveCount(--pendingDecisions);
  }

  await page.getByRole('button', { name: 'Portfolios', exact: true }).click();
  await page.getByRole('button', { name: 'New portfolio' }).click();
  await page.getByLabel('Portfolio name').fill('Browser test portfolio');
  await page.getByLabel('Opening cash (INR)').fill('50000');
  const portfolioResponse = page.waitForResponse((response) => response.url().endsWith('/portfolios') && response.request().method() === 'POST');
  await page.getByRole('button', { name: 'Create', exact: true }).click();
  const portfolio = await (await portfolioResponse).json();
  const portfolioId = portfolio.portfolio_id;
  await expect(page.getByRole('heading', { name: 'Browser test portfolio' })).toBeVisible();
  await page.getByRole('button', { name: 'Edit details' }).click();
  await page.getByLabel('Portfolio name').last().fill('Browser portfolio updated');
  await page.getByRole('button', { name: 'Save', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Browser portfolio updated' })).toBeVisible();
  await page.getByRole('button', { name: 'Import holding' }).first().click();
  await page.getByLabel('Security').selectOption({ index: 0 });
  await page.getByLabel('Quantity').fill('1');
  const holdingResponse = page.waitForResponse((response) => response.url().includes(`/portfolios/${portfolioId}/holdings`) && response.request().method() === 'POST');
  await page.getByRole('button', { name: 'Add imported position' }).click();
  const holding = await (await holdingResponse).json();
  expect(holding.position_source).toBe('imported');
  await expect(page.locator('.table-panel tbody tr')).toHaveCount(1);

  await page.getByRole('button', { name: 'Risk analytics', exact: true }).click();
  await expect(page.getByText('Conditional Value at Risk (CVaR)')).toBeVisible();
  await expect(page.getByText('Value at Risk · 95%')).toBeVisible();
  await expect(page.getByText('Sector concentration · HHI')).toBeVisible();
  await expect(page.locator('.risk-card').filter({ hasText: 'Conditional Value at Risk (CVaR)' }).locator('strong')).not.toHaveText('—');
  const riskResponse = Object.entries(responses).find(([url]) => url.includes(`/portfolios/${portfolioId}/risk`))?.[1];
  const formattedCvar = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', maximumFractionDigits: 2 }).format(Number(riskResponse.cvar_95));
  await expect(page.locator('.risk-card').filter({ hasText: 'Conditional Value at Risk (CVaR)' }).locator('strong')).toHaveText(formattedCvar);
  await page.getByRole('button', { name: 'Alerts' }).click();
  await expect(page.getByText(/Sector concentration exceeded|VaR threshold breached/).first()).toBeVisible();
  await page.getByRole('button', { name: 'Recommendations', exact: true }).click();
  await page.getByRole('button', { name: 'Generate recommendations' }).first().click();
  await expect(page.getByText(/Capacity multiplier 0\.5/)).toBeVisible();
  await expect(page.getByText(/restricted sectors:/)).toBeVisible();

  // A second authenticated browser session cannot read or mutate the owner’s data.
  const secondContext = await browser.newContext({ viewport: { width: 1280, height: 900 } });
  const other = await secondContext.newPage();
  await other.goto('/');
  await other.getByRole('button', { name: 'Create an account' }).click();
  await other.getByLabel('Full name').fill('Separate Browser Investor');
  await other.getByLabel('Email address').fill(secondEmail);
  await other.getByLabel('Password').fill(password);
  await other.getByLabel('PAN SHA-256 hash').fill('b'.repeat(64));
  const secondRegister = other.waitForResponse((response) => response.url().endsWith('/auth/register'));
  await other.getByRole('button', { name: 'Create account' }).click();
  const secondUser = await (await secondRegister).json();
  const csrf = secondUser.csrf_token;
  const statusCodes = await other.evaluate(async ({ base, owner, portfolio, incomeId, csrfToken }) => {
    const paths = [
      `/users/${owner}`,
      `/cashflow/${owner}/income`,
      `/cashflow/${owner}/expenses`,
      `/cashflow/${owner}/summary`,
      `/recommendations/${owner}`,
      `/portfolios/${portfolio}`,
      `/portfolios/${portfolio}/holdings`,
      `/portfolios/${portfolio}/risk`,
      `/alerts?portfolio_id=${portfolio}`,
    ];
    const reads = await Promise.all(paths.map((path) => fetch(base + path, { credentials: 'include' }).then((response) => response.status)));
    const write = await fetch(`${base}/cashflow/income/${incomeId}`, {
      method: 'DELETE', credentials: 'include', headers: { 'X-CSRF-Token': csrfToken },
    });
    return [...reads, write.status];
  }, { base: apiBase, owner: ownerId, portfolio: portfolioId, incomeId: income.income_id, csrfToken: csrf });
  expect(statusCodes).toEqual(Array(10).fill(404));
  await secondContext.close();

  for (const width of [320, 390, 768, 1280, 1440]) {
    await page.setViewportSize({ width, height: width < 700 ? 844 : 900 });
    const dimensions = await page.evaluate(() => ({ viewport: innerWidth, document: document.documentElement.scrollWidth }));
    expect(dimensions.document, `horizontal overflow at ${width}px`).toBeLessThanOrEqual(dimensions.viewport + 1);
    const tableWrap = page.locator('.table-wrap').first();
    if (await tableWrap.count()) {
      const overflow = await tableWrap.evaluate((element) => getComputedStyle(element).overflowX);
      expect(['auto', 'scroll']).toContain(overflow);
    }
  }
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(page.getByRole('button', { name: 'Open navigation' })).toBeVisible();
  await page.getByRole('button', { name: 'Open navigation' }).click();
  await expect(page.getByRole('navigation', { name: 'Main navigation' })).toBeVisible();
  await page.getByRole('button', { name: 'Alerts' }).click();
  await expect(page.getByRole('heading', { name: 'Alerts', exact: true })).toBeVisible();

  await page.getByRole('button', { name: 'Open navigation' }).click();
  await page.locator('.profile-menu').click();
  await expect(page.getByRole('heading', { name: 'Welcome back' })).toBeVisible();
  await page.getByLabel('Email address').fill(ownerEmail);
  await page.getByLabel('Password').fill(password);
  await page.getByRole('button', { name: 'Sign in' }).click();
  await expect(page.getByRole('button', { name: 'Overview', exact: true })).toBeVisible();
  await expect(page.evaluate(() => localStorage.length)).resolves.toBe(0);
});
