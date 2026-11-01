import { test, expect } from '@playwright/test';
import { existsSync, readFileSync } from 'node:fs';
import AxeBuilder from '@axe-core/playwright';
test.use({ trace: 'off', screenshot: 'off', video: 'off' });
test('teacher overview soft accents: real read and filled/empty/loading/error states', async ({
  browser,
}) => {
  test.skip(
    !process.env.LGG_T15D_PREVIEW,
    'Preserved preview, no seeds or business writes.',
  );
  const storage = '.artifacts/t15d-e-session.json';
  const fixture = JSON.parse(
    readFileSync('.artifacts/t15d-preview.json', 'utf8'),
  );
  const context = await browser.newContext({
    baseURL: 'http://127.0.0.1:5173',
    ...(existsSync(storage) ? { storageState: storage } : {}),
  });
  const page = await context.newPage();
  const writes: string[] = [],
    errors: string[] = [];
  let mode = 'real',
    release = () => {},
    waiting = Promise.resolve();
  page.on('pageerror', (e) => errors.push(e.message));
  await page.route('**/api/**', async (route) => {
    const req = route.request(),
      path = new URL(req.url()).pathname;
    if (req.method() !== 'GET' && !path.startsWith('/api/auth/')) {
      writes.push(path);
      return route.abort();
    }
    if (
      mode !== 'real' &&
      [
        '/api/submissions/review-queue',
        '/api/teacher-planning/reminders',
      ].includes(path)
    ) {
      if (mode === 'loading') await waiting;
      if (mode === 'error')
        return route.fulfill({ status: 503, json: { detail: 'Unavailable' } });
      if (mode === 'empty')
        return route.fulfill({ json: { items: [], total: 0 } });
      if (mode === 'filled' && path === '/api/submissions/review-queue')
        return route.fulfill({
          json: {
            items: [
              {
                id: 15,
                homework_id: 17,
                student_user_id: 21,
                student_first_name: 'Пример',
                student_last_name: 'Ученика',
                student_username: 'synthetic',
                homework_title: 'Практика',
                course_name: 'Пример Ученика',
                submitted_at: '2026-10-22T12:00:00Z',
              },
            ],
            total: 1,
          },
        });
    }
    return route.continue();
  });
  const queue = page.locator('section').filter({
    has: page.getByRole('heading', { name: 'На проверку', exact: true }),
  });
  const materials = page.locator('section').filter({
    has: page.getByRole('heading', {
      name: 'Нужно выдать материалы',
      exact: true,
    }),
  });
  async function inspect() {
    await expect(queue).toHaveCSS('background-color', 'rgb(255, 247, 219)');
    await expect(materials).toHaveCSS('background-color', 'rgb(255, 255, 255)');
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  }
  try {
    await page.goto('/teacher');
    await expect
      .poll(
        async () =>
          new URL(page.url()).pathname === '/login' ||
          (await queue.isVisible()),
      )
      .toBe(true);
    if (new URL(page.url()).pathname === '/login') {
      await page
        .getByLabel('Логин', { exact: true })
        .fill(fixture.accounts.teacher.username);
      await page
        .getByLabel('Пароль', { exact: true })
        .fill(fixture.accounts.teacher.password);
      await page.getByRole('button', { name: 'Войти', exact: true }).click();
    }
    await expect(queue).toBeVisible();
    await expect(
      materials.getByRole('status').filter({ hasText: 'Загружаем' }),
    ).toHaveCount(0);
    for (const width of [1340, 768, 360]) {
      await page.setViewportSize({ width, height: 1000 });
      await inspect();
      await page.screenshot({
        path: `.artifacts/t15d-day-colors-${width}.png`,
        fullPage: true,
      });
    }
    await page.setViewportSize({ width: 1340, height: 1000 });
    for (const state of ['filled', 'empty', 'error', 'loading']) {
      mode = state;
      if (state === 'loading')
        waiting = new Promise<void>((resolve) => {
          release = resolve;
        });
      await page.reload();
      if (state === 'filled')
        await expect(
          queue.getByRole('link', { name: /Пример Ученика/ }),
        ).toBeVisible();
      if (state === 'empty')
        await expect(
          queue.getByText('Пока нет работ на проверку.'),
        ).toBeVisible();
      if (state === 'error')
        await expect(
          queue.getByRole('button', { name: 'Повторить', exact: true }),
        ).toBeVisible();
      if (state === 'loading')
        await expect(
          queue.getByRole('status').filter({ hasText: 'Загружаем' }),
        ).toBeVisible();
      await inspect();
      if (state === 'loading') {
        mode = 'real';
        release();
      }
    }
    mode = 'real';
    release();
    await page.reload();
    const link = queue.getByRole('link', { name: 'Вся очередь', exact: true });
    await link.focus();
    await page.keyboard.press('Enter');
    await expect(page).toHaveURL(/\/teacher\/review$/);
    await page.goBack();
    await expect(queue).toBeVisible();
    expect(writes).toEqual([]);
    expect(errors).toEqual([]);
  } finally {
    release();
    await context.storageState({ path: storage });
    await context.close();
  }
});
