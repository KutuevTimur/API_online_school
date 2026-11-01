import { test, expect, type Page } from '@playwright/test';
import { readFileSync } from 'node:fs';
import AxeBuilder from '@axe-core/playwright';
test.use({ trace: 'off', screenshot: 'off', video: 'off' });
async function audit(page: Page, shellOnly = false) {
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth + 1,
    ),
  ).toBe(true);
  const axe = new AxeBuilder({ page });
  if (shellOnly)
    axe
      .include('[data-role=student] > header')
      .include('nav[aria-label="Разделы на телефоне"]');
  expect((await axe.analyze()).violations).toEqual([]);
}
test('compact student mobile shell: real routes, keyboard, Back and files', async ({
  page,
}) => {
  test.skip(!process.env.LGG_T15D_PREVIEW, 'Retained preview, no seed');
  test.setTimeout(90000);
  const { accounts } = JSON.parse(
    readFileSync('.artifacts/t15d-preview.json', 'utf8'),
  );
  const writes: string[] = [],
    errors: string[] = [];
  page.on('pageerror', (e) => errors.push(e.message));
  await page.route('**/api/**', (route) => {
    const req = route.request(),
      path = new URL(req.url()).pathname;
    if (req.method() !== 'GET' && !path.startsWith('/api/auth/')) {
      writes.push(req.method() + ' ' + path);
      return route.abort();
    }
    return route.continue();
  });
  await page.setViewportSize({ width: 360, height: 800 });
  await page.goto('/login');
  await page.getByLabel('Логин', { exact: true }).fill(accounts.turov.username);
  await page
    .getByLabel('Пароль', { exact: true })
    .fill(accounts.turov.password);
  await page.getByRole('button', { name: 'Войти', exact: true }).click();
  await expect(page).toHaveURL(/\/student$/);
  await expect(page.getByText('Загружаем…', { exact: true })).toHaveCount(0);
  const banner = page.getByRole('banner'),
    bottom = page.getByRole('navigation', { name: 'Разделы на телефоне' });
  const bell = banner.getByRole('link', { name: /Уведомления/ });
  for (const width of [360, 388, 768]) {
    await page.setViewportSize({ width, height: 800 });
    expect((await banner.boundingBox())!.height).toBe(48);
    expect(
      await banner.evaluate((e) => getComputedStyle(e).backgroundColor),
    ).toBe('rgb(255, 255, 255)');
    const bellSize = (await bell.boundingBox())!;
    expect(bellSize.width).toBeGreaterThanOrEqual(44);
    expect(bellSize.height).toBeGreaterThanOrEqual(44);
    expect(bellSize.y).toBeGreaterThanOrEqual(0);
    expect((await bottom.boundingBox())!.height).toBe(49);
    expect(await bottom.getByRole('link').allTextContents()).toEqual([
      'Мой день',
      'Занятия',
      'Расписание',
    ]);
    await expect(bell).toBeVisible();
    await expect(banner.getByRole('link', { name: 'Профиль' })).toBeHidden();
    for (const control of await bottom.locator('a, button').all()) {
      const r = (await control.boundingBox())!;
      expect(r.height).toBeGreaterThanOrEqual(44);
      expect(r.width).toBeGreaterThanOrEqual(44);
      const offset = await control.evaluate((e) => {
        const r = e.getBoundingClientRect();
        const inner = e.querySelector('.mantine-Button-label') || e;
        const nodes = [...inner.childNodes].filter(
          (n) => n.nodeType === Node.TEXT_NODE && n.textContent?.trim(),
        );
        if (!nodes.length) return 0;
        const range = document.createRange();
        range.selectNodeContents(nodes[0]);
        return range.getBoundingClientRect().bottom - r.bottom;
      });
      expect(offset).toBeLessThanOrEqual(0);
    }
    await audit(page);
    await page.screenshot({
      path: `.artifacts/student-mobile-day-${width}.png`,
      fullPage: false,
    });
  }
  await page.setViewportSize({ width: 360, height: 800 });
  await bottom
    .getByRole('link', { name: 'Расписание', exact: true })
    .press('Enter');
  await expect(page).toHaveURL(/\/student\/schedule/);
  await expect(
    bottom.getByRole('link', { name: 'Расписание' }),
  ).toHaveAttribute('aria-current', 'page');
  await page.goBack();
  const more = bottom.getByRole('button', { name: 'Ещё', exact: true });
  await more.click();
  await expect(
    page.getByRole('menuitem', { name: 'Д/з', exact: true }),
  ).toBeVisible();
  await expect(page.getByRole('menu')).toHaveCSS('opacity', '1');
  await audit(page);
  await page.screenshot({ path: '.artifacts/student-mobile-more-360.png' });
  await page.keyboard.press('Escape');
  await expect(page.locator('[role=menu]')).toHaveCount(0);
  await expect(more).toBeFocused();
  await more.press('Enter');
  await page.getByRole('menuitem', { name: 'Д/з', exact: true }).click();
  await expect(page).toHaveURL(/\/student\/homeworks$/);
  await expect(more).toHaveAttribute('data-active', 'true');
  await page.goBack();
  await bell.press('Enter');
  await expect(page).toHaveURL(/\/notifications$/);
  await page.goBack();
  // Owner's current lesson/homework: GET-only, no answer/mark-read actions.
  for (const path of ['/student/lessons/129', '/student/homeworks/63']) {
    await page.goto(path);
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
    await expect(bell).toBeVisible();
    // Lesson content has an existing unrelated condition-link contrast finding.
    await audit(page, true);
    if (path.includes('lessons')) {
      const open = page
        .getByRole('button', { name: /^Открыть .*\.pdf$/ })
        .first();
      await open.click();
      const dialog = page.getByRole('dialog');
      await expect(dialog).toBeVisible();
      expect(
        await page.evaluate(() => {
          const nav = document.querySelector(
            'nav[aria-label="Разделы на телефоне"]',
          )!;
          const r = nav.getBoundingClientRect();
          return !nav.contains(
            document.elementFromPoint(innerWidth / 2, r.top + 20),
          );
        }),
      ).toBe(true);
      await page.keyboard.press('Escape');
      await expect(dialog).toHaveCount(0);
      await expect(open).toBeFocused();
    }
    await page.screenshot({
      path: `.artifacts/student-mobile-${path.includes('lessons') ? 'lesson' : 'homework'}-360.png`,
      fullPage: false,
    });
  }
  expect(writes).toEqual([]);
  expect(errors).toEqual([]);
});

test('unread badge HTTP fixtures: loading, failure, focus refresh, zero and many', async ({
  page,
}) => {
  test.skip(
    !process.env.LGG_T15D_PREVIEW,
    'Retained auth, fixture unread only',
  );
  test.setTimeout(45000);
  const { accounts } = JSON.parse(
    readFileSync('.artifacts/t15d-preview.json', 'utf8'),
  );
  let count: number | null = null;
  let release!: () => void;
  const pending = new Promise<void>((resolve) => {
    release = resolve;
  });
  await page.route('**/api/notifications/unread', async (route) => {
    await pending;
    return count === null
      ? route.fulfill({ status: 503, json: { detail: 'HTTP fixture' } })
      : route.fulfill({ json: { unread: count } });
  });
  const writes: string[] = [];
  await page.route('**/api/**', (route) => {
    const req = route.request();
    if (
      req.method() !== 'GET' &&
      !new URL(req.url()).pathname.startsWith('/api/auth/')
    ) {
      writes.push(req.method());
      return route.abort();
    }
    return route.fallback();
  });
  await page.setViewportSize({ width: 360, height: 800 });
  await page.goto('/login');
  await page.getByLabel('Логин', { exact: true }).fill(accounts.turov.username);
  await page
    .getByLabel('Пароль', { exact: true })
    .fill(accounts.turov.password);
  await page.getByRole('button', { name: 'Войти', exact: true }).click();
  await expect(page).toHaveURL(/\/student$/);
  const banner = page.getByRole('banner');
  const bell = banner.getByRole('link', { name: /Уведомления/ });
  await expect(bell).toBeVisible();
  await expect(bell.locator('span[aria-label]')).toHaveCount(0);
  const size = await bell.boundingBox();
  release();
  await expect(bell.getByText('Число непрочитанных недоступно')).toBeAttached({
    timeout: 15000,
  });
  await audit(page);
  for (const value of [0, 1, 3, 120]) {
    count = value;
    const response = page.waitForResponse(
      (r) => new URL(r.url()).pathname === '/api/notifications/unread',
      { timeout: 10000 },
    );
    await page.evaluate(() => window.dispatchEvent(new Event('focus')));
    await response;
    if (value)
      await expect(bell.getByLabel(`Непрочитанных: ${value}`)).toHaveText(
        value > 99 ? '99+' : String(value),
      );
    else await expect(bell.locator('span[aria-label]')).toHaveCount(0);
    expect(await bell.boundingBox()).toEqual(size);
    await audit(page);
  }
  expect(writes).toEqual([]);
});
