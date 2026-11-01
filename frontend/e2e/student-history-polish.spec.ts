import { test, expect, type Page } from '@playwright/test';
import { readFileSync } from 'node:fs';
import AxeBuilder from '@axe-core/playwright';
import type { Lesson } from '../src/features/courses/queries';
test.use({ trace: 'off', screenshot: 'off', video: 'off' });
async function login(page: Page) {
  const { accounts } = JSON.parse(
    readFileSync('.artifacts/t15d-preview.json', 'utf8'),
  );
  const writes: string[] = [],
    errors: string[] = [],
    attachments: number[] = [];
  page.on('pageerror', (e) => errors.push(e.message));
  page.on('request', (r) => {
    const u = new URL(r.url());
    if (['/api/lectures', '/api/homeworks'].includes(u.pathname))
      attachments.push(Number(u.searchParams.get('lesson_id')));
  });
  await page.route('**/api/**', (route) => {
    const r = route.request(),
      p = new URL(r.url()).pathname;
    if (r.method() !== 'GET' && !p.startsWith('/api/auth/')) {
      writes.push(r.method() + ' ' + p);
      return route.abort();
    }
    return route.fallback();
  });
  await page.goto('/login');
  await page.getByLabel('Логин', { exact: true }).fill(accounts.turov.username);
  await page
    .getByLabel('Пароль', { exact: true })
    .fill(accounts.turov.password);
  await page.getByRole('button', { name: 'Войти', exact: true }).click();
  await expect(page).toHaveURL(/\/student$/);
  return { writes, errors, attachments };
}
async function audit(page: Page) {
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth + 1,
    ),
  ).toBe(true);
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
}
test('history real reads: aligned controls, responsive rows, year/month, popup, materials and Back', async ({
  page,
}) => {
  test.skip(!process.env.LGG_T15D_PREVIEW, 'Retained preview only, no seed');
  test.setTimeout(90000);
  const { writes, errors, attachments } = await login(page);
  const pastResponse = page.waitForResponse((r) => {
    const u = new URL(r.url());
    return (
      u.pathname === '/api/lessons' &&
      u.searchParams.get('limit') === '20' &&
      u.searchParams.get('sort_date') === 'desc'
    );
  });
  const futureResponse = page.waitForResponse((r) => {
    const u = new URL(r.url());
    return (
      u.pathname === '/api/lessons' &&
      u.searchParams.get('limit') === '20' &&
      u.searchParams.get('sort_date') === 'asc'
    );
  });
  await page.goto('/student/materials');
  const past = await (await pastResponse).json(),
    future = await (await futureResponse).json();
  const history = page.getByRole('region', { name: 'История занятий' });
  const latest = page.getByRole('region', {
    name: 'Последнее проведённое занятие',
  });
  await expect(
    latest.getByRole('button', { name: 'Конспект', exact: true }),
  ).toBeVisible();
  await expect(
    history.getByRole('heading', {
      name: `Прошедшие · ${past.total}`,
      exact: true,
    }),
  ).toBeVisible();
  await expect(
    history.getByRole('heading', {
      name: `Предстоящие · ${future.total}`,
      exact: true,
    }),
  ).toBeVisible();
  const year = history.getByRole('combobox', { name: 'Год', exact: true });
  const current = history.getByRole('button', {
    name: 'Текущий месяц',
    exact: true,
  });
  const months = history.getByRole('group', { name: 'Месяцы занятий' });
  const yearValue = await year.inputValue();
  for (const width of [1340, 768, 360]) {
    await page.setViewportSize({ width, height: 900 });
    const a = (await year.boundingBox())!,
      b = (await current.boundingBox())!;
    expect(Math.abs(a.y + a.height - b.y - b.height)).toBeLessThanOrEqual(1);
    expect(
      Math.abs(a.y + a.height / 2 - b.y - b.height / 2),
    ).toBeLessThanOrEqual(1);
    expect(b.x).toBeGreaterThan(a.x + a.width);
    expect(a.height).toBeGreaterThanOrEqual(44);
    expect(b.height).toBeGreaterThanOrEqual(44);
    expect((await latest.boundingBox())!.height).toBeLessThanOrEqual(265);
    for (const button of await months.getByRole('button').all()) {
      expect((await button.boundingBox())!.height).toBeGreaterThanOrEqual(44);
      if ((await button.getAttribute('aria-pressed')) === 'false')
        await expect(button).toHaveAttribute('data-variant', 'default');
    }
    for (const button of [
      current,
      ...(await months.getByRole('button').all()),
    ]) {
      expect(
        await button.evaluate((e) => {
          const a = e.getBoundingClientRect(),
            b = e
              .querySelector('.mantine-Button-label')!
              .getBoundingClientRect();
          return Math.abs(a.y + a.height / 2 - b.y - b.height / 2);
        }),
      ).toBeLessThanOrEqual(1);
    }
    if (past.total <= past.items.length && future.total <= future.items.length)
      await expect(history.getByText(/^Показано/)).toHaveCount(0);
    await audit(page);
    await history.evaluate((e) => e.scrollIntoView({ block: 'start' }));
    await page.screenshot({
      path: `.artifacts/history-polish-real-${width}.png`,
      fullPage: false,
    });
  }
  await year.press('ArrowDown');
  const popup = page.getByRole('region', { name: 'Варианты: Год' });
  await expect(popup).toBeVisible();
  const y = (await year.boundingBox())!,
    p = (await popup.boundingBox())!;
  expect(Math.abs(y.x - p.x)).toBeLessThanOrEqual(1);
  expect(Math.abs(y.width - p.width)).toBeLessThanOrEqual(1);
  await audit(page);
  await page.keyboard.press('Escape');
  await expect(year).toBeFocused();
  await year.press('ArrowDown');
  await page
    .getByRole('option', { name: String(Number(yearValue) - 1), exact: true })
    .click();
  await expect(page).toHaveURL(
    new RegExp(`history-month=${Number(yearValue) - 1}-`),
  );
  await current.press('Enter');
  const currentURL = page.url();
  const selectedMonth = new URL(currentURL).searchParams.get('history-month');
  await months.getByRole('button', { name: 'Предыдущие месяцы' }).click();
  expect(new URL(page.url()).searchParams.get('history-month')).toBe(
    selectedMonth,
  );
  await page.goBack();
  await expect(page).toHaveURL(currentURL);
  // Open only the owner's known current lesson129 (HW63), never homework58.
  const toggle = history.locator('button[aria-controls="student-history-129"]');
  await expect(toggle).toHaveCount(1);
  await expect(toggle).toContainText('Материалы');
  await toggle.press('Enter');
  await expect(toggle).toHaveAttribute('aria-expanded', 'true');
  const row = history.locator('#student-history-129');
  const file = row.getByRole('button', { name: /^Открыть .*\.pdf$/ }).first();
  await expect(file).toBeVisible();
  await audit(page);
  const expandedURL = page.url();
  await file.press('Enter');
  await expect(page.getByRole('dialog')).toBeVisible();
  await expect(
    page.getByRole('dialog').getByLabel('Страница 1', { exact: true }),
  ).toBeVisible();
  await page.keyboard.press('Escape');
  await expect(file).toBeFocused();
  await row
    .getByRole('link', { name: 'Открыть занятие', exact: true })
    .press('Enter');
  await expect(page).toHaveURL(/\/student\/lessons\/129$/);
  await page
    .getByRole('link', { name: 'К моим занятиям', exact: true })
    .click();
  await expect(page).toHaveURL(expandedURL);
  await expect(toggle).toHaveAttribute('aria-expanded', 'true');
  await toggle.press('Enter');
  await expect(toggle).toHaveAttribute('aria-expanded', 'false');
  expect(attachments.every((id) => id === 129)).toBe(true);
  expect(writes).toEqual([]);
  expect(errors).toEqual([]);
});
test('history HTTP fixtures: truthful group counts, pagination, long readonly, loading/error/empty', async ({
  page,
}) => {
  test.skip(
    !process.env.LGG_T15D_PREVIEW,
    'Retained auth, browser-only state fixtures',
  );
  test.setTimeout(90000);
  const { writes, errors } = await login(page);
  let mode = 'many';
  let base: Lesson | undefined;
  let release = () => {};
  let delay = Promise.resolve();
  await page.route('**/api/lessons?*', async (route) => {
    const u = new URL(route.request().url());
    if (u.searchParams.get('limit') === '1') return route.fallback();
    if (!base) {
      const data = await (await route.fetch()).json();
      base = data.items[0];
    }
    if (mode === 'loading') await delay;
    if (mode === 'error')
      return route.fulfill({ status: 503, json: { detail: 'HTTP fixture' } });
    const upcoming = u.searchParams.get('sort_date') === 'asc',
      offset = Number(u.searchParams.get('offset'));
    let items: Lesson[] = [];
    let total = 0;
    if (mode === 'many' || mode === 'loading') {
      total = upcoming ? 1 : 21;
      items = Array.from({ length: upcoming || offset ? 1 : 20 }, (_, i) => ({
        ...base!,
        id: 99000 + offset + i + (upcoming ? 100 : 0),
        title: 'Занятие',
        topic: upcoming ? 'Предстоящая тема' : `Тема ${offset + i + 1}`,
        status: upcoming ? 'scheduled' : 'completed',
      }));
    } else if (mode === 'long') {
      total = 1;
      items = [
        {
          ...base!,
          id: 99001,
          title: 'Занятие',
          topic: 'Очень длинная тема занятия без обрезания '.repeat(6),
          is_deleted: true,
          access_mode: 'read_only',
          read_only_reason: 'lesson_archived',
          status: 'completed',
        },
      ];
    }
    return route.fulfill({ json: { items, total } });
  });
  await page.setViewportSize({ width: 360, height: 900 });
  await page.goto('/student/materials');
  const history = page.getByRole('region', { name: 'История занятий' });
  const latest = page.getByRole('region', {
    name: 'Последнее проведённое занятие',
  });
  await expect(
    history.getByRole('heading', { name: 'Прошедшие · 21', exact: true }),
  ).toBeVisible();
  await expect(
    history.getByRole('heading', { name: 'Предстоящие · 1', exact: true }),
  ).toBeVisible();
  await expect(
    history.getByText('Показано 1–20', { exact: true }),
  ).toBeVisible();
  await history
    .getByRole('navigation', { name: 'Страницы истории занятий' })
    .getByRole('button', { name: 'Далее' })
    .click();
  await expect(
    history.getByText('Показано 21–21', { exact: true }),
  ).toBeVisible();
  await audit(page);
  mode = 'long';
  await page.goto('/student/materials');
  await expect(
    history.getByRole('button', { name: /Очень длинная тема/ }),
  ).toHaveCount(2);
  await expect(history.getByText('Занятие', { exact: true })).toHaveCount(0);
  await expect(history.getByText('В архиве · Завершено')).toHaveCount(2);
  await audit(page);
  mode = 'loading';
  delay = new Promise<void>((resolve) => {
    release = resolve;
  });
  await page.reload();
  await expect(history.getByText('Загружаем…', { exact: true })).toHaveCount(2);
  await expect(history.getByText(/Занятий в этом месяце пока нет/)).toHaveCount(
    0,
  );
  await expect(
    latest.getByRole('link', { name: 'Открыть занятие', exact: true }),
  ).toBeVisible();
  release();
  await expect(
    history.getByRole('heading', { name: 'Прошедшие · 21', exact: true }),
  ).toBeVisible();
  mode = 'error';
  await page.reload();
  await expect(
    history.getByRole('button', { name: 'Повторить', exact: true }),
  ).toHaveCount(2, { timeout: 15000 });
  await expect(history.getByText(/Занятий в этом месяце пока нет/)).toHaveCount(
    0,
  );
  mode = 'many';
  await history
    .getByRole('button', { name: 'Повторить', exact: true })
    .first()
    .click();
  await expect(
    history.getByRole('heading', { name: 'Прошедшие · 21', exact: true }),
  ).toBeVisible();
  await history
    .getByRole('button', { name: 'Повторить', exact: true })
    .first()
    .click();
  await expect(
    history.getByRole('heading', { name: 'Предстоящие · 1', exact: true }),
  ).toBeVisible();
  mode = 'empty';
  await page.reload();
  await expect(
    history.getByRole('heading', { name: 'Прошедшие · 0', exact: true }),
  ).toBeVisible();
  await expect(
    history.getByRole('heading', { name: 'Предстоящие · 0', exact: true }),
  ).toBeVisible();
  await expect(history.getByText(/^Показано/)).toHaveCount(0);
  await expect(
    latest.getByRole('link', { name: 'Открыть занятие', exact: true }),
  ).toBeVisible();
  await audit(page);
  expect(writes).toEqual([]);
  expect(errors).toEqual([]);
});
