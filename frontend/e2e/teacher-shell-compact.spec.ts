import { test, expect } from '@playwright/test';
import { readFileSync, mkdirSync } from 'node:fs';
import AxeBuilder from '@axe-core/playwright';
test.use({ trace: 'off', screenshot: 'off', video: 'off' });
test('teacher compact navigation: real reads, role routing and HTTP unread states', async ({
  page,
}) => {
  test.skip(
    !process.env.LGG_T15D_PREVIEW,
    'Retained preview; no seed or business writes',
  );
  test.setTimeout(90000);
  const { accounts } = JSON.parse(
    readFileSync('.artifacts/t15d-preview.json', 'utf8'),
  );
  let scenario = 'real',
    blocked = 0;
  let release = () => {};
  let loading = Promise.resolve();
  const errors: string[] = [];
  page.on('pageerror', (e) => errors.push(e.message));
  await page.route('**/api/**', async (route) => {
    const req = route.request(),
      url = new URL(req.url());
    if (req.method() !== 'GET' && !url.pathname.startsWith('/api/auth/')) {
      blocked++;
      return route.abort();
    }
    if (url.pathname === '/api/notifications/unread' && scenario !== 'real') {
      if (scenario === 'loading') await loading;
      if (scenario === 'error')
        return route.fulfill({
          status: 503,
          json: { detail: 'HTTP fixture unavailable' },
        });
      return route.fulfill({ json: { unread: scenario === 'many' ? 145 : 0 } });
    }
    return route.continue();
  });
  await page.setViewportSize({ width: 360, height: 800 });
  await page.goto('/login');
  await page
    .getByLabel('Логин', { exact: true })
    .fill(accounts.teacher.username);
  await page
    .getByLabel('Пароль', { exact: true })
    .fill(accounts.teacher.password);
  const realCount = page.waitForResponse(
    (r) => new URL(r.url()).pathname === '/api/notifications/unread' && r.ok(),
  );
  await page.getByRole('button', { name: 'Войти', exact: true }).click();
  await expect(page).toHaveURL(/\/teacher$/);
  const unread = (await (await realCount).json()).unread as number;
  const header = page.getByRole('banner');
  const nav = page.getByRole('navigation', { name: 'Разделы на телефоне' });
  const bell = header.getByRole('link', { name: /^Уведомления/ });
  const more = nav.getByRole('button', { name: 'Ещё', exact: true });
  await expect(bell).toBeVisible();
  await expect(
    header.getByRole('link', { name: 'Профиль', exact: true }),
  ).toBeHidden();
  await expect(
    nav.getByRole('link', { name: 'Проверка', exact: true }),
  ).toHaveAttribute('href', '/teacher/review');
  expect(
    await nav
      .getByRole('link')
      .evaluateAll((nodes) => nodes.map((n) => n.getAttribute('href'))),
  ).toEqual(['/teacher', '/teacher/schedule', '/teacher/review']);
  expect(await page.locator('a[href^="/student"]').count()).toBe(0);
  if (unread > 0)
    await expect(
      bell.locator('[aria-label^="Непрочитанных:"]'),
    ).toHaveAttribute('aria-label', `Непрочитанных: ${unread}`);
  for (const width of [360, 388, 768]) {
    await page.setViewportSize({ width, height: 800 });
    await expect
      .poll(() => header.evaluate((e) => e.getBoundingClientRect().height))
      .toBe(48);
    await expect
      .poll(() => nav.evaluate((e) => e.getBoundingClientRect().height))
      .toBe(49);
    expect(
      await bell.evaluate((e) => e.getBoundingClientRect().width),
    ).toBeGreaterThanOrEqual(44);
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
  }
  await page.setViewportSize({ width: 360, height: 800 });
  mkdirSync('.artifacts', { recursive: true });
  await page.screenshot({ path: '.artifacts/teacher-shell-real-mobile.png' });
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  await more.focus();
  await page.keyboard.press('Enter');
  const menu = page.getByRole('menu');
  await expect(menu).toHaveCSS('opacity', '1');
  await expect(
    menu.getByRole('menuitem', { name: 'Ученики', exact: true }),
  ).toBeVisible();
  await expect(
    menu.getByRole('menuitem', { name: 'Профиль', exact: true }),
  ).toBeVisible();
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  await page.keyboard.press('Escape');
  await expect(more).toBeFocused();
  await more.click();
  await menu.getByRole('menuitem', { name: 'Ученики', exact: true }).click();
  await expect(page).toHaveURL(/\/teacher\/students/);
  await expect(more).toHaveAttribute('data-active', 'true');
  await page.goBack();
  await expect(
    nav.getByRole('link', { name: 'Мой день', exact: true }),
  ).toHaveAttribute('aria-current', 'page');
  await bell.click();
  await expect(page).toHaveURL(/\/notifications/);
  await expect(more).toHaveAttribute('data-active', 'true');
  await page.goBack();
  await page.setViewportSize({ width: 1340, height: 900 });
  await expect(nav).toBeHidden();
  await expect(
    header
      .getByRole('navigation', { name: 'Основные разделы' })
      .getByRole('link', { name: 'На проверку', exact: true }),
  ).toBeVisible();
  await expect(
    header.getByRole('link', { name: 'Профиль', exact: true }),
  ).toBeVisible();
  await page.screenshot({ path: '.artifacts/teacher-shell-real-desktop.png' });
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  // Explicit HTTP fixtures below: only the unread-count response is replaced.
  await page.setViewportSize({ width: 360, height: 800 });
  scenario = 'many';
  await page.reload();
  await expect(bell.getByText('99+', { exact: true })).toBeVisible();
  await expect(bell.locator('[aria-label^="Непрочитанных:"]')).toHaveAttribute(
    'aria-label',
    'Непрочитанных: 145',
  );
  expect(
    (
      await new AxeBuilder({ page })
        .include('[data-role="teacher"] > header')
        .include('nav[aria-label="Разделы на телефоне"]')
        .analyze()
    ).violations,
  ).toEqual([]);
  await page.screenshot({ path: '.artifacts/teacher-shell-http-badge.png' });
  scenario = 'zero';
  await page.reload();
  await expect(bell).toBeVisible();
  await expect(bell.locator('[aria-label^="Непрочитанных:"]')).toHaveCount(0);
  scenario = 'error';
  await page.reload();
  await expect(bell).toContainText('Число непрочитанных недоступно');
  await expect(bell.locator('[aria-label^="Непрочитанных:"]')).toHaveCount(0);
  scenario = 'loading';
  loading = new Promise<void>((r) => {
    release = r;
  });
  await page.reload();
  await expect(bell).toBeVisible();
  await expect(header).toHaveCSS('height', '48px');
  scenario = 'zero';
  release();
  await expect(bell.locator('[aria-label^="Непрочитанных:"]')).toHaveCount(0);
  // Sibling appearance regression in the existing dev showcase, not real-role acceptance.
  for (const role of ['student', 'admin']) {
    await page.goto(`/__ui?role=${role}`);
    if (role === 'student') {
      await expect(header).toHaveCSS('height', '48px');
      await expect(nav).toHaveCSS('height', '49px');
      await expect(
        nav.getByRole('link', { name: 'Занятия', exact: true }),
      ).toBeVisible();
      expect(await page.locator('a[href^="/teacher"]').count()).toBe(0);
    } else {
      await expect(nav).toHaveCount(0);
      expect(
        await header.evaluate((e) => e.getBoundingClientRect().height),
      ).toBeGreaterThan(60);
    }
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
  }
  expect(blocked).toBe(0);
  expect(errors).toEqual([]);
  console.log(
    'teacher real reads / unread HTTP fixtures / student-admin dev showcase; preview business writes=0',
  );
});
