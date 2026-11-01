import { test, expect, type Page } from '@playwright/test';
import { readFileSync } from 'node:fs';
import AxeBuilder from '@axe-core/playwright';
test.use({ trace: 'off', screenshot: 'off', video: 'off' });
async function audit(page: Page) {
  expect(
    await page.evaluate(() => {
      if (document.documentElement.scrollWidth <= innerWidth + 1) return [];
      return [...document.querySelectorAll('main *, header *, nav *')]
        .filter((e) => {
          const r = e.getBoundingClientRect();
          return r.width > 0 && (r.right > innerWidth + 1 || r.left < -1);
        })
        .slice(0, 12)
        .map((e) => ({
          tag: e.tagName,
          cls: e.className,
          text: e.textContent?.slice(0, 60),
          right: e.getBoundingClientRect().right,
        }));
    }),
  ).toEqual([]);
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
}
test('approved student blue shell, consistent CTA geometry, hover, keyboard and read states', async ({
  page,
}) => {
  test.skip(!process.env.LGG_T15D_PREVIEW, 'Retained preview only');
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
  await page.goto('/login');
  await page.getByLabel('Логин', { exact: true }).fill(accounts.turov.username);
  await page
    .getByLabel('Пароль', { exact: true })
    .fill(accounts.turov.password);
  await page.getByRole('button', { name: 'Войти', exact: true }).click();
  await expect(page).toHaveURL(/\/student$/);
  const recent = page.getByRole('region', { name: 'Мои занятия', exact: true });
  await expect(
    recent.getByRole('link', { name: 'Открыть занятия', exact: true }),
  ).toBeVisible();
  for (const width of [1340, 1024, 768, 360]) {
    await page.setViewportSize({ width, height: 950 });
    await audit(page);
    expect(
      await page
        .locator('[data-role=student]')
        .evaluate((e) => getComputedStyle(e).backgroundColor),
    ).toBe('rgb(237, 246, 250)');
    for (const button of await page
      .locator('main a.mantine-Button-root:visible')
      .all()) {
      const offset = await button.evaluate((e) => {
        const a = e.getBoundingClientRect(),
          b = e.querySelector('.mantine-Button-label')!.getBoundingClientRect();
        return Math.abs(a.y + a.height / 2 - b.y - b.height / 2);
      });
      expect(offset).toBeLessThanOrEqual(1);
      if ((await button.textContent())?.includes('Присоединиться')) {
        expect(await button.locator('svg.lucide-video').count()).toBe(1);
      } else
        expect(await button.locator('svg.lucide-arrow-right').count()).toBe(1);
    }
    if (width >= 1024) {
      const nav = page.getByRole('navigation', { name: 'Основные разделы' });
      expect(await nav.getByRole('link').allTextContents()).toEqual([
        'Мой день',
        'Расписание',
        'Занятия',
        'Д/з',
        'Курсы',
      ]);
      const active = nav.getByRole('link', { name: 'Мой день', exact: true });
      await active.hover();
      expect(
        await active.evaluate((e) => getComputedStyle(e).backgroundColor),
      ).toBe('rgb(200, 235, 252)');
      expect(
        await nav
          .getByRole('link', { name: 'Занятия', exact: true })
          .locator('svg')
          .count(),
      ).toBe(1);
    } else {
      const nav = page.getByRole('navigation', { name: 'Разделы на телефоне' });
      await expect(
        nav.getByRole('link', { name: 'Занятия', exact: true }),
      ).toBeVisible();
      await nav.getByRole('button', { name: 'Ещё', exact: true }).click();
      await expect(
        page.getByRole('menuitem', { name: 'Д/з', exact: true }),
      ).toBeVisible();
      await page.keyboard.press('Escape');
      await expect(page.locator('[role=menu]')).toHaveCount(0);
      await expect(
        nav.getByRole('button', { name: 'Ещё', exact: true }),
      ).toBeFocused();
    }
    await page.screenshot({
      path: `.artifacts/student-blue-${width}.png`,
      fullPage: true,
    });
  }
  await page.setViewportSize({ width: 1340, height: 950 });
  const button = recent.getByRole('link', {
    name: 'Открыть занятия',
    exact: true,
  });
  await page.mouse.move(0, 0);
  expect(
    await button.evaluate((e) => getComputedStyle(e).backgroundColor),
  ).toBe('rgb(255, 255, 255)');
  const before = await button.boundingBox();
  await button.hover();
  expect(
    await button.evaluate((e) => getComputedStyle(e).backgroundColor),
  ).toBe('rgb(217, 238, 249)');
  expect(await button.evaluate((e) => getComputedStyle(e).borderTopColor)).toBe(
    'rgb(8, 117, 180)',
  );
  expect(await button.boundingBox()).toEqual(before);
  await button.focus();
  await page.keyboard.press('Enter');
  await expect(page).toHaveURL(/\/student\/materials$/);
  await page.goBack();
  await expect(button).toBeVisible();
  // Explicitly empty overview fixtures: keep recovery/links and shell stable.
  await page.route('**/api/lessons?*', (route) =>
    route.fulfill({ json: { items: [], total: 0 } }),
  );
  await page.route('**/api/homeworks/my/page?*', (route) =>
    route.fulfill({ json: { items: [], total: 0 } }),
  );
  await page.reload();
  await expect(page.getByText(/Пока нет предстоящих/)).toBeVisible();
  await expect(
    page.getByRole('heading', { name: 'На проверке', exact: true }),
  ).toBeVisible();
  await expect(button).toBeVisible();
  await audit(page);
  expect(writes).toEqual([]);
  expect(errors).toEqual([]);
});
test('teacher real shell and admin preview keep original navigation and surfaces', async ({
  page,
}) => {
  test.skip(!process.env.LGG_T15D_PREVIEW, 'Retained preview only');
  const { accounts } = JSON.parse(
    readFileSync('.artifacts/t15d-preview.json', 'utf8'),
  );
  const writes: string[] = [];
  await page.route('**/api/**', (route) => {
    const req = route.request(),
      path = new URL(req.url()).pathname;
    if (req.method() !== 'GET' && !path.startsWith('/api/auth/')) {
      writes.push(path);
      return route.abort();
    }
    return route.continue();
  });
  await page.goto('/login');
  await page
    .getByLabel('Логин', { exact: true })
    .fill(accounts.teacher.username);
  await page
    .getByLabel('Пароль', { exact: true })
    .fill(accounts.teacher.password);
  await page.getByRole('button', { name: 'Войти', exact: true }).click();
  await expect(page).toHaveURL(/\/teacher$/);
  for (const width of [1340, 360]) {
    await page.setViewportSize({ width, height: 950 });
    await audit(page);
    expect(
      await page
        .getByRole('banner')
        .evaluate((e) => getComputedStyle(e).backgroundColor),
    ).toBe('rgb(255, 255, 255)');
    await expect(page.locator('[data-role=teacher]')).not.toHaveClass(
      /studentShell/,
    );
  }
  await page.setViewportSize({ width: 1340, height: 950 });
  expect(
    await page
      .getByRole('navigation', { name: 'Основные разделы' })
      .getByRole('link')
      .allTextContents(),
  ).toEqual(['Мой день', 'Ученики', 'Расписание', 'На проверку']);
  // Admin shell is the existing dev gallery, not a real admin account/API PASS.
  await page.goto('/__ui?role=admin');
  await expect(page.locator('[data-role=admin]')).toBeVisible();
  expect(
    await page
      .getByRole('banner')
      .evaluate((e) => getComputedStyle(e).backgroundColor),
  ).toBe('rgb(255, 255, 255)');
  expect(
    (await new AxeBuilder({ page }).include('header nav').analyze()).violations,
  ).toEqual([]);
  expect(writes).toEqual([]);
});
