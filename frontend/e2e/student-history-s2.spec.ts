import { test, expect, type Page } from '@playwright/test';
import { readFileSync } from 'node:fs';
import AxeBuilder from '@axe-core/playwright';

// Retained preview: GET only, except the normal browser login/refresh bridge.
// No seed, reset, notifications, answer edits, upload, or fixture builder.
test.use({ trace: 'off', screenshot: 'off', video: 'off' });
async function login(page: Page) {
  const fixture = JSON.parse(
    readFileSync('.artifacts/t15d-preview.json', 'utf8'),
  );
  const account = fixture.accounts.turov;
  if (!account?.username || !account.password)
    throw new Error('Existing student fixture is missing');
  const blocked: string[] = [];
  await page.route('**/api/**', (route) => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    if (request.method() !== 'GET' && !path.startsWith('/api/auth/')) {
      blocked.push(request.method() + ' ' + path);
      return route.abort();
    }
    return route.continue();
  });
  await page.goto('/login');
  await page.getByLabel('Логин', { exact: true }).fill(account.username);
  await page.getByLabel('Пароль', { exact: true }).fill(account.password);
  await page.getByRole('button', { name: 'Войти', exact: true }).click();
  await expect(page).not.toHaveURL(/\/login/);
  return blocked;
}

async function geometry(page: Page) {
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  for (const section of await page.locator('main > div > section').all()) {
    const box = await section.boundingBox();
    if (box) {
      expect(box.x).toBeGreaterThanOrEqual(0);
      expect(box.x + box.width).toBeLessThanOrEqual(
        (await page.viewportSize())!.width + 1,
      );
    }
  }
  for (const button of await page
    .getByRole('group', { name: 'Месяцы занятий' })
    .getByRole('button')
    .all()) {
    const box = (await button.boundingBox())!;
    expect(box.height).toBeGreaterThanOrEqual(44);
    expect(box.width).toBeGreaterThanOrEqual(43);
  }
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
}

test('S2 real API: history content, lazy files, exact viewer/lesson/homework returns and geometry 1340/768/360', async ({
  page,
}) => {
  test.skip(
    !process.env.LGG_T15D_PREVIEW,
    'Requires retained preview and existing private accounts',
  );
  test.setTimeout(120000);
  const errors: string[] = [];
  page.on('pageerror', (e) => errors.push(e.message));
  const blocked = await login(page);
  const attachments: number[] = [];
  page.on('request', (request) => {
    const url = new URL(request.url());
    if (['/api/lectures', '/api/homeworks'].includes(url.pathname))
      attachments.push(Number(url.searchParams.get('lesson_id')));
  });
  for (const width of [1340, 768, 360]) {
    await page.setViewportSize({ width, height: 900 });
    const latestResponse = page.waitForResponse(
      (r) =>
        new URL(r.url()).pathname === '/api/lessons' &&
        new URL(r.url()).searchParams.get('status') === 'completed',
    );
    await page.goto(
      '/student/materials?history-month=2026-09&history-strip=2026-08',
    );
    const latest = await (await latestResponse).json();
    expect(latest.items[0].status).toBe('completed');
    const latestRegion = page.getByRole('region', {
      name: 'Последнее проведённое занятие',
    });
    await expect(latestRegion.getByRole('heading', { level: 3 })).toHaveText(
      latest.items[0].topic || latest.items[0].title,
    );
    await expect(
      page.getByRole('heading', { name: 'сентябрь 2026', exact: true }),
    ).toBeVisible();
    await expect(
      page
        .getByRole('list', { name: 'Занятия выбранного месяца' })
        .getByRole('button')
        .first(),
    ).toBeVisible();
    expect(attachments.every((id) => id === latest.items[0].id)).toBe(true);
    await geometry(page);
    const row = page
      .getByRole('list', { name: 'Занятия выбранного месяца' })
      .getByRole('button')
      .last();
    await row.focus();
    await row.press('Enter');
    await expect(row).toHaveAttribute('aria-expanded', 'true');
    const body = page.locator('#' + (await row.getAttribute('aria-controls')));
    const open = body.getByRole('button', { name: /^Открыть / }).first();
    await expect(open).toBeVisible();
    await open.scrollIntoViewIfNeeded();
    const historyURL = page.url();
    const scroll = await page.evaluate(() => scrollY);
    await open.click();
    const dialog = page.getByRole('dialog');
    await expect(dialog).toBeVisible();
    const box = (await dialog.boundingBox())!;
    expect(box.x).toBe(0);
    expect(box.y).toBe(0);
    expect(box.width).toBe(width);
    expect(box.height).toBe(900);
    await expect(
      dialog.getByLabel('Страница 1', { exact: true }),
    ).toBeVisible();
    await page.goBack();
    await expect(dialog).not.toBeVisible();
    expect(page.url()).toBe(historyURL);
    await expect(open).toBeFocused();
    await expect
      .poll(() => page.evaluate(() => scrollY))
      .toBeCloseTo(scroll, 0);
    await body
      .getByRole('link', { name: 'Открыть занятие', exact: true })
      .click();
    const returnScroll = await page.evaluate(
      () => history.state.usr.studentHistoryScroll,
    );
    await page.getByRole('link', { name: 'К моим занятиям' }).click();
    expect(page.url()).toBe(historyURL);
    await expect(row).toHaveAttribute('aria-expanded', 'true');
    await expect
      .poll(() => page.evaluate(() => scrollY))
      .toBeCloseTo(returnScroll, 0);
    await body
      .getByRole('link', { name: 'Открыть домашнее задание' })
      .first()
      .click();
    await expect(
      page.getByRole('link', { name: 'К моим занятиям' }),
    ).toBeVisible();
    await page.goBack();
    expect(page.url()).toBe(historyURL);
    await expect(row).toHaveAttribute('aria-expanded', 'true');
    await geometry(page);
    attachments.length = 0;
  }
  expect(blocked).toEqual([]);
  expect(errors).toEqual([]);
});

test('S2 HTTP fixtures: 0/1/23 lessons, page 2, planned/cancelled/archive, course teachers and errors', async ({
  page,
}) => {
  test.skip(
    !process.env.LGG_T15D_PREVIEW,
    'HTTP state fixtures still require real retained authentication',
  );
  test.setTimeout(90000);
  const blocked = await login(page);
  let mode: 'many' | 'empty' | 'one' | 'error' = 'many';
  const template = {
    id: 90001,
    course_id: 18,
    teacher_user_id: 1,
    title: 'HTTP fixture · повторение',
    topic: 'Граница года',
    scheduled_at: '2026-12-31T21:00:00Z',
    status: 'scheduled',
    access_mode: 'active',
    is_deleted: false,
  };
  const fixtureCourses = [
    { id: 18, name: 'Математика', teacher_name: 'Анна Иванова' },
    { id: 19, name: 'Русский', teacher_name: 'Борис Петров' },
  ];
  await page.route('**/api/courses?**', (route) =>
    route.fulfill({ json: { items: fixtureCourses, total: 2 } }),
  );
  await page.route('**/api/courses/19', (route) =>
    route.fulfill({ json: fixtureCourses[1] }),
  );
  await page.route('**/api/lessons?**', (route) => {
    const p = new URL(route.request().url()).searchParams;
    if (p.has('status'))
      return route.fulfill({ json: { items: [], total: 0 } });
    if (mode === 'error')
      return route.fulfill({ status: 503, json: { detail: 'Unavailable' } });
    const total = mode === 'empty' ? 0 : mode === 'one' ? 1 : 23;
    const offset = Number(p.get('offset') || 0),
      limit = Number(p.get('limit') || 20);
    return route.fulfill({
      json: {
        total,
        items: Array.from(
          { length: Math.max(0, Math.min(limit, total - offset)) },
          (_, i) => ({
            ...template,
            id: 90001 + offset + i,
            topic: `Тема ${offset + i + 1}`,
            status: i === 1 ? 'cancelled' : i === 2 ? 'completed' : 'scheduled',
            is_deleted: i === 2,
            access_mode: i === 2 ? 'read_only' : 'active',
          }),
        ),
      },
    });
  });
  await page.goto(
    '/student/materials?history-month=2027-01&history-strip=2026-12',
  );
  const course = page.getByRole('combobox', { name: 'Курс', exact: true });
  await course.click();
  const option = page.getByRole('option', { name: 'Русский · Борис Петров' });
  await expect(option).toBeVisible();
  const popup = (await page
    .getByRole('region', { name: 'Варианты: Курс' })
    .boundingBox())!;
  const trigger = (await course.boundingBox())!;
  expect(Math.abs(popup.x - trigger.x)).toBeLessThanOrEqual(1);
  expect(Math.abs(popup.width - trigger.width)).toBeLessThanOrEqual(1);
  await course.press('ArrowDown');
  await course.press('ArrowDown');
  await course.press('Enter');
  expect(new URL(page.url()).searchParams.get('course_id')).toBe('19');
  await expect(page.getByText('В архиве · Завершено')).toBeVisible();
  await expect(page.getByText('Отменено', { exact: true })).toBeVisible();
  const paging = page.getByRole('navigation', {
    name: 'Страницы истории занятий',
  });
  await paging.getByRole('button', { name: 'Далее', exact: true }).click();
  await expect(
    page
      .getByRole('list', { name: 'Занятия выбранного месяца' })
      .getByRole('button'),
  ).toHaveCount(3);
  expect(new URL(page.url()).searchParams.get('history-offset')).toBe('20');
  await page.getByRole('button', { name: 'Следующие месяцы' }).click();
  expect(new URL(page.url()).searchParams.get('history-month')).toBe('2027-01');
  await page.goBack();
  mode = 'empty';
  await page.reload();
  await expect(
    page.getByRole('button', { name: 'На первую страницу' }),
  ).toBeVisible();
  await page.getByRole('button', { name: 'На первую страницу' }).click();
  await expect(page.getByText(/Занятий в этом месяце пока нет/)).toBeVisible();
  mode = 'one';
  await page.reload();
  await expect(
    page
      .getByRole('list', { name: 'Занятия выбранного месяца' })
      .getByRole('button'),
  ).toHaveCount(1);
  mode = 'error';
  await page.reload();
  await expect(page.getByRole('alert')).toBeVisible();
  await expect(
    page.getByText(/Занятий в этом месяце пока нет/),
  ).not.toBeVisible();
  mode = 'one';
  await page.getByRole('button', { name: 'Повторить', exact: true }).click();
  await expect(
    page
      .getByRole('list', { name: 'Занятия выбранного месяца' })
      .getByRole('button'),
  ).toHaveCount(1);
  expect(blocked).toEqual([]);
});
