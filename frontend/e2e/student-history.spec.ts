import { test, expect } from '@playwright/test';
import { existsSync, readFileSync } from 'node:fs';
import AxeBuilder from '@axe-core/playwright';

const storage = '.artifacts/t15d-e-session.json';
test.use({
  trace: 'off',
  screenshot: 'off',
  video: 'off',
  storageState:
    process.env.LGG_T15D_PREVIEW && existsSync(storage) ? storage : undefined,
});
test('student card: month history, real files, return context, settings and readonly', async ({
  page,
}) => {
  test.skip(
    !process.env.LGG_T15D_PREVIEW,
    'Preserved preview: no seeds or business writes.',
  );
  test.setTimeout(90000);
  const fixture = JSON.parse(
    readFileSync('.artifacts/t15d-preview.json', 'utf8'),
  );
  const id = fixture.accounts.vasilisa.id;
  const writes: string[] = [],
    errors: string[] = [],
    requests: URL[] = [];
  let mode = 'real',
    release = () => {};
  let waiting = Promise.resolve();
  page.on('pageerror', (e) => errors.push(e.message));
  await page.route('**/api/**', async (route) => {
    const req = route.request(),
      url = new URL(req.url()),
      path = url.pathname;
    if (req.method() !== 'GET' && !path.startsWith('/api/auth/')) {
      writes.push(req.method() + ' ' + path);
      return route.abort();
    }
    if (path === '/api/lessons' && url.searchParams.get('course_id')) {
      requests.push(url);
      if (
        url.searchParams.get('limit') !== '1' &&
        url.searchParams.get('sort_date') === 'desc'
      ) {
        if (mode === 'loading') await waiting;
        if (mode === 'error')
          return route.fulfill({
            status: 503,
            json: { detail: 'Unavailable' },
          });
        if (mode === 'empty')
          return route.fulfill({ json: { items: [], total: 0 } });
        if (mode === 'pages') {
          const base = fixture.lessons['0-1-18'];
          const all = Array.from({ length: 53 }, (_, i) => ({
            ...base,
            id: 10000 + i,
            title: `Проверка страницы ${i + 1}`,
            scheduled_at: new Date(
              Date.UTC(2026, 8, 30, 18) - i * 3600000,
            ).toISOString(),
            is_deleted: i === 0,
            access_mode: i === 0 ? 'read_only' : 'active',
            status: i === 0 ? 'cancelled' : 'completed',
          }));
          const offset = Number(url.searchParams.get('offset')),
            limit = Number(url.searchParams.get('limit'));
          return route.fulfill({
            json: { items: all.slice(offset, offset + limit), total: 53 },
          });
        }
      }
    }
    return route.continue();
  });
  const workspace = `/teacher/students/${id}?history-month=2026-10`;
  await page.goto(workspace);
  await expect
    .poll(
      async () =>
        new URL(page.url()).pathname === '/login' ||
        (await page
          .getByRole('heading', { name: 'История занятий', exact: true })
          .isVisible()),
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
    await expect(page).not.toHaveURL(/\/login/);
    await page.goto(workspace);
  }
  await expect(
    page.getByRole('heading', { name: 'История занятий', exact: true }),
  ).toBeVisible();
  const last = page.getByRole('region', {
    name: 'Последнее проведённое занятие',
    exact: true,
  });
  const rows = page.getByRole('list', { name: 'Занятия выбранного месяца' });
  const lastFile = last
    .getByRole('button', { name: /^Открыть .*\.pdf$/ })
    .first();
  await expect(lastFile).toBeVisible();
  await lastFile.click();
  await expect(page.getByRole('dialog')).toHaveCount(1);
  await expect(
    page.getByRole('dialog').getByLabel('Страница 1', { exact: true }),
  ).toBeVisible();
  await page.keyboard.press('Escape');
  await expect(lastFile).toBeFocused();
  await rows.getByRole('button', { name: /22 октября/ }).click();
  const row = rows.getByRole('listitem').first();
  const file = row.getByRole('button', { name: /^Открыть .*\.pdf$/ }).first();
  await expect(file).toBeVisible();
  const before = page.url();
  for (const width of [1340, 768, 360]) {
    await page.setViewportSize({ width, height: 1000 });
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
    await page.screenshot({
      path: `.artifacts/t15d-student-history-${width}.png`,
      fullPage: true,
    });
  }
  await file.focus();
  await page.keyboard.press('Enter');
  await expect(page.getByRole('dialog')).toHaveCount(1);
  await expect(
    page.getByRole('dialog').getByLabel('Страница 1', { exact: true }),
  ).toBeVisible();
  await page.goBack();
  await expect(page).toHaveURL(before);
  await expect(file).toBeFocused();
  await row.getByRole('link', { name: 'Открыть занятие', exact: true }).click();
  await expect(
    page.getByRole('heading', { name: 'Конспекты', exact: true }),
  ).toBeVisible();
  await page.getByRole('link', { name: 'К ученику', exact: true }).click();
  await expect(page).toHaveURL(before);
  await expect(
    rows.getByRole('button', { name: /22 октября/ }),
  ).toHaveAttribute('aria-expanded', 'true');
  await page
    .getByRole('button', { name: 'Настройки ученика', exact: true })
    .click();
  await expect(
    page.getByRole('heading', { name: 'Цена занятия', exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole('button', { name: 'Изменить цену занятия' }),
  ).toBeVisible();
  await expect(
    page.getByRole('button', { name: 'Изменить недельную норму' }),
  ).toBeVisible();
  await page.getByRole('button', { name: 'Изменить цену занятия' }).click();
  await page.getByLabel('Цена занятия, ₽').fill('1234,50');
  await page.getByRole('link', { name: 'Свои ученики', exact: true }).click();
  await expect(
    page.getByRole('dialog', { name: 'Уйти без сохранения?' }),
  ).toBeVisible();
  await page.getByRole('button', { name: 'Отмена', exact: true }).click();
  await expect(page.getByLabel('Цена занятия, ₽')).toHaveValue('1234,50');
  await page
    .getByRole('button', { name: 'Отменить изменение цены', exact: true })
    .click();
  await page.getByText('Приглашение и доступ', { exact: true }).click();
  await expect(
    page.getByRole('button', { name: 'Выдать новое приглашение до активации' }),
  ).toBeVisible();
  await expect(
    page.getByRole('button', { name: 'Выдать новое приглашение до активации' }),
  ).toBeEnabled();
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  mode = 'pages';
  await page.goto(`/teacher/students/${id}?history-month=2026-09`);
  await expect(
    page.getByText('В архиве · Отменено', { exact: true }),
  ).toBeVisible();
  const pagination = page.getByRole('navigation', {
    name: 'Страницы занятий месяца',
  });
  await pagination.getByRole('button', { name: 'Далее', exact: true }).click();
  await expect(page).toHaveURL(/history-offset=20/);
  await expect(rows.getByRole('button').first()).toContainText(
    'Проверка страницы 21',
  );
  expect(
    requests.some(
      (u) =>
        u.searchParams.get('from_date') === '2026-08-31T21:00:00.000Z' &&
        u.searchParams.get('to_date') === '2026-09-30T20:59:59.999999Z',
    ),
  ).toBe(true);
  await page.getByRole('button', { name: /август 2026$/ }).click();
  await expect(page).toHaveURL(/history-offset=0/);
  await expect(page).toHaveURL(/history-month=2026-08/);
  for (const state of ['empty', 'error', 'loading']) {
    mode = state;
    if (state === 'loading')
      waiting = new Promise<void>((resolve) => {
        release = resolve;
      });
    await page.goto(workspace);
    if (state === 'empty')
      await expect(
        page.getByText('Прошедших занятий в этом месяце нет.'),
      ).toBeVisible();
    if (state === 'error') {
      const retry = page
        .getByRole('region', { name: 'История занятий', exact: true })
        .getByRole('button', { name: 'Повторить', exact: true });
      await expect(retry).toBeVisible();
      mode = 'real';
      await retry.click();
      await expect(rows.getByRole('listitem').first()).toBeVisible();
    }
    if (state === 'loading') {
      await expect(
        page
          .getByRole('region', { name: 'История занятий', exact: true })
          .getByRole('status'),
      ).toBeVisible();
      release();
      await expect(rows.getByRole('listitem').first()).toBeVisible();
    }
  }
  mode = 'real';
  await page.goto(workspace);
  await page.context().storageState({ path: storage });
  expect(writes).toEqual([]);
  expect(errors).toEqual([]);
});
