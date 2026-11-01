import { test, expect } from '@playwright/test';
import { readFileSync } from 'node:fs';
import AxeBuilder from '@axe-core/playwright';
import type { Lesson } from '../src/features/courses/queries';
test.use({ trace: 'off', screenshot: 'off', video: 'off' });
test('day recent lesson: real reads, navigation, responsive order and explicit HTTP fixtures', async ({
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
  await page.goto('/login');
  await page.getByLabel('Логин', { exact: true }).fill(accounts.turov.username);
  await page
    .getByLabel('Пароль', { exact: true })
    .fill(accounts.turov.password);
  const latestResponse = page
    .waitForResponse((r) => {
      const u = new URL(r.url());
      return (
        u.pathname === '/api/lessons' &&
        u.searchParams.get('status') === 'completed' &&
        u.searchParams.get('limit') === '1'
      );
    })
    .then((r) => r.json());
  await page.getByRole('button', { name: 'Войти', exact: true }).click();
  await expect(page).toHaveURL(/\/student$/);
  const latest: Lesson = (await latestResponse).items[0];
  expect(latest.status).toBe('completed');
  const block = page.getByRole('region', { name: 'Мои занятия', exact: true });
  for (const width of [1340, 768, 360]) {
    await page.setViewportSize({ width, height: 900 });
    await expect(block.getByRole('heading', { level: 3 })).toHaveCount(0);
    await expect(block.getByText(/^Курс:/)).toHaveCount(0);
    await expect(
      block.getByText(
        'Последнее занятие · ' +
          new Intl.DateTimeFormat('ru-RU', {
            timeZone: 'Europe/Moscow',
            day: 'numeric',
            month: 'long',
          }).format(new Date(latest.scheduled_at)) +
          ', ' +
          new Intl.DateTimeFormat('ru-RU', {
            timeZone: 'Europe/Moscow',
            hour: '2-digit',
            minute: '2-digit',
          }).format(new Date(latest.scheduled_at)) +
          ' МСК',
        { exact: true },
      ),
    ).toBeVisible();
    await expect(block.getByText(/^Преподаватель:/)).toBeVisible();
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth + 1,
      ),
    ).toBe(true);
    expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
    const b = await block.boundingBox(),
      result = await page
        .getByRole('region', { name: 'Последний результат' })
        .boundingBox();
    if (width === 360) expect(b!.y).toBeGreaterThan(result!.y + result!.height);
    for (const button of await block.locator('.mantine-Button-root').all()) {
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
    await page.screenshot({
      path: `.artifacts/day-history-real-${width}.png`,
      fullPage: true,
    });
  }
  await block
    .getByRole('link', { name: 'Открыть занятия', exact: true })
    .press('Enter');
  await expect(page).toHaveURL(/\/student\/materials$/);
  await expect(
    page.getByRole('heading', { level: 1, name: 'Мои занятия' }),
  ).toBeVisible();
  await page.goBack();
  await expect(block).toBeVisible();
  // Explicit HTTP fixtures cover absent/error/loading/metadata/long/read-only, never source writes.
  let mode = 'long',
    release = () => {};
  let delay = Promise.resolve();
  await page.route('**/api/lessons?*', async (route) => {
    if (
      new URL(route.request().url()).searchParams.get('status') !== 'completed'
    )
      return route.fallback();
    if (mode === 'loading') await delay;
    if (mode === 'error')
      return route.fulfill({ status: 503, json: { detail: 'fixture' } });
    return route.fulfill({
      json: {
        items:
          mode === 'empty'
            ? []
            : [
                {
                  ...latest,
                  topic:
                    'Очень длинная тема занятия: уравнения и графики '.repeat(
                      5,
                    ),
                  course_id: 99000,
                  course_name: 'Название из занятия',
                  access_mode: 'read_only',
                },
              ],
        total: mode === 'empty' ? 0 : 1,
      },
    });
  });
  await page.route('**/api/courses/99000', (route) =>
    mode === 'metadataError'
      ? route.fulfill({ status: 503, json: { detail: 'fixture' } })
      : route.fulfill({
          json: {
            id: 99000,
            name: 'Курс вне первой страницы с длинным названием '.repeat(3),
            teacher_name:
              'Александра-Екатерина Константинопольская-Долгорукова',
          },
        }),
  );
  for (const width of [1340, 768, 360]) {
    await page.setViewportSize({ width, height: 900 });
    await page.reload();
    await expect(
      block.getByText('Только просмотр', { exact: true }),
    ).toHaveCount(0);
    await expect(block.getByText(/^Преподаватель:/)).toBeVisible();
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth + 1,
      ),
    ).toBe(true);
    expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  }
  mode = 'metadataError';
  await page.reload();
  await expect(block.getByRole('alert')).toContainText('Не удалось загрузить');
  await expect(
    block.getByRole('link', { name: 'Открыть занятия', exact: true }),
  ).toBeVisible();
  mode = 'long';
  await block.getByRole('button', { name: 'Повторить', exact: true }).click();
  await expect(block.getByText(/^Преподаватель:/)).toBeVisible();
  mode = 'empty';
  await page.reload();
  await expect(
    block.getByText('Здесь появится последнее проведённое занятие.'),
  ).toBeVisible();
  await expect(
    block.getByRole('link', { name: 'Открыть занятия', exact: true }),
  ).toBeVisible();
  mode = 'loading';
  delay = new Promise<void>((r) => (release = r));
  await page.reload();
  await expect(block.getByRole('status')).toBeVisible();
  await expect(
    block.getByRole('link', { name: 'Открыть занятия', exact: true }),
  ).toBeVisible();
  release();
  await expect(
    block.getByRole('link', { name: 'Открыть занятия', exact: true }),
  ).toBeVisible();
  mode = 'error';
  await page.reload();
  await expect(
    block.getByRole('button', { name: 'Повторить', exact: true }),
  ).toBeVisible();
  mode = 'long';
  await block.getByRole('button', { name: 'Повторить', exact: true }).click();
  await expect(
    block.getByRole('link', { name: 'Открыть занятия', exact: true }),
  ).toBeVisible();
  expect(writes).toEqual([]);
  expect(errors).toEqual([]);
});
