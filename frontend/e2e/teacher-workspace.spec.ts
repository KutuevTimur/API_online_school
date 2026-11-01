import { test, expect } from '@playwright/test';
import { readFileSync } from 'node:fs';
import AxeBuilder from '@axe-core/playwright';
test.use({ trace: 'off', screenshot: 'off', video: 'off' });
test('package D: workspace ranges/pages, lesson sections, drafts/files and readonly variants', async ({
  page,
}) => {
  test.skip(
    !process.env.LGG_T15D_PREVIEW,
    'Preserved preview; no seeds or business writes.',
  );
  test.setTimeout(120000);
  page.setDefaultTimeout(10000);
  const fixture = JSON.parse(
    readFileSync('.artifacts/t15d-preview.json', 'utf8'),
  );
  const writes: string[] = [];
  const errors: string[] = [];
  let scenario = 'real';
  let release = () => {};
  let waiting = Promise.resolve();
  const lists: URL[] = [];
  page.on('pageerror', (e) => errors.push(e.message));
  await page.route('**/api/**', async (route) => {
    try {
      const req = route.request();
      const url = new URL(req.url());
      if (req.method() !== 'GET' && !url.pathname.startsWith('/api/auth/')) {
        writes.push(req.method() + ' ' + url.pathname);
        return route.abort();
      }
      if (
        url.pathname === '/api/lessons' &&
        url.searchParams.has('course_id')
      ) {
        lists.push(url);
        if (scenario === 'loading') await waiting;
        if (scenario === 'error')
          return route.fulfill({
            status: 503,
            json: { detail: 'Unavailable' },
          });
        if (scenario === 'empty')
          return route.fulfill({ json: { items: [], total: 0 } });
        if (scenario === 'pages' && url.searchParams.get('limit') !== '1') {
          const response = await route.fetch();
          const body = await response.json();
          const sample = body.items[0] || fixture.lessons['0-3-16'];
          const future = url.searchParams.get('sort_date') === 'asc';
          const all = Array.from({ length: 53 }, (_, index) => ({
            ...sample,
            id: 10000 + index,
            scheduled_at: future
              ? new Date(Date.UTC(2027, 0, index + 1)).toISOString()
              : new Date(Date.UTC(2025, 0, 53 - index)).toISOString(),
            title: `Встреча ${index + 1}`,
            is_deleted: index === 1,
            status: index === 0 ? 'cancelled' : 'scheduled',
          }));
          const offset = Number(url.searchParams.get('offset'));
          return route.fulfill({
            response,
            json: {
              total: all.length,
              items: all.slice(
                offset,
                offset + Number(url.searchParams.get('limit')),
              ),
            },
          });
        }
      }
      if (url.pathname === '/api/lectures' && scenario === 'lecture-error')
        return route.fulfill({ status: 503, json: { detail: 'Unavailable' } });
      if (url.pathname === '/api/lectures' && scenario === 'lecture-loading')
        await waiting;
      if (
        scenario === 'readonly' &&
        /^\/api\/lessons\/\d+$/.test(url.pathname)
      ) {
        const response = await route.fetch();
        return route.fulfill({
          response,
          json: {
            ...(await response.json()),
            can_manage: false,
            is_deleted: true,
            access_mode: 'read_only',
            read_only_reason: 'lesson_archived',
            status: 'cancelled',
          },
        });
      }
      return route.continue();
    } catch {
      if (!page.isClosed()) await route.abort().catch(() => {});
    }
  });
  await page.goto('/login');
  await page
    .getByLabel('Логин', { exact: true })
    .fill(fixture.accounts.teacher.username);
  await page
    .getByLabel('Пароль', { exact: true })
    .fill(fixture.accounts.teacher.password);
  await page.getByRole('button', { name: 'Войти', exact: true }).click();
  await expect(page).toHaveURL(/\/teacher$/);
  const studentId = fixture.accounts.vasilisa.id;
  const workspace = `/teacher/students/${studentId}`;
  await page.goto(workspace);
  await expect(
    page.getByRole('heading', { name: 'Ближайшее занятие' }),
  ).toBeVisible();
  await expect(
    page.getByRole('heading', { name: 'Прошедшие занятия' }),
  ).toBeVisible();
  const past = page.getByRole('list', { name: 'Прошедшие занятия ученика' });
  await expect(past.getByRole('listitem')).not.toHaveCount(0);
  const dates = await past
    .locator('time')
    .evaluateAll((nodes) =>
      nodes.map((node) => Date.parse(node.getAttribute('datetime')!)),
    );
  expect(dates).toEqual([...dates].sort((a, b) => b - a));
  expect(
    lists.some(
      (url) =>
        url.searchParams.get('sort_date') === 'desc' &&
        url.searchParams.has('to_date'),
    ),
  ).toBe(true);
  for (const width of [1340, 768, 360]) {
    await page.setViewportSize({ width, height: 950 });
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
    await page.screenshot({
      path: `.artifacts/t15d-d-workspace-${width}.png`,
      fullPage: true,
    });
  }
  await page.getByText('Следующие занятия', { exact: true }).click();
  const future = page.getByRole('list', { name: 'Следующие занятия ученика' });
  await expect(future.getByRole('listitem')).not.toHaveCount(0);
  const futureDates = await future
    .locator('time')
    .evaluateAll((nodes) =>
      nodes.map((node) => Date.parse(node.getAttribute('datetime')!)),
    );
  expect(futureDates).toEqual([...futureDates].sort((a, b) => a - b));
  // Real checked lesson, PDF and draft preservation. No upload of lecture files (auto mutation).
  const lessonId = fixture.lessons['0-1-18'].id;
  await past
    .locator(`a[href="/teacher/lessons/${lessonId}?student=${studentId}"]`)
    .click();
  await expect(page.getByRole('heading', { level: 1 })).toHaveText(
    'Василиса Немцова · 11 класс',
  );
  await expect(
    page.getByRole('link', { name: 'К ученику', exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole('link', { name: 'Посмотреть проверку' }),
  ).toBeVisible();
  await expect(page.getByLabel('Название задания')).toBeHidden();
  for (const width of [1340, 768, 360]) {
    await page.setViewportSize({ width, height: 950 });
    const lectureTop = await page
      .getByRole('heading', { name: 'Конспекты', exact: true })
      .evaluate((node) => node.getBoundingClientRect().top + scrollY);
    const manageTop = await page
      .getByText('Управление встречей и обучением', { exact: true })
      .evaluate((node) => node.getBoundingClientRect().top + scrollY);
    expect(manageTop).toBeGreaterThan(lectureTop);
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
    await page.screenshot({
      path: `.artifacts/t15d-d-lesson-${width}.png`,
      fullPage: true,
    });
  }
  await page
    .getByRole('button', { name: 'Выдать задание', exact: true })
    .click();
  await page.getByLabel('Название задания').fill('Несохранённое ДЗ D');
  await page
    .getByLabel('Условие', { exact: true })
    .fill('Сохранить https://example.com/ текст');
  await page.getByLabel('Добавить файл').setInputFiles('e2e/fixtures/math.pdf');
  const beforePreview = page.url();
  const pdf = page.getByRole('button', { name: /^Открыть .*\.pdf$/ }).first();
  await pdf.click();
  await expect(
    page.getByRole('dialog').getByLabel('Страница 1', { exact: true }),
  ).toBeVisible();
  await page.keyboard.press('Escape');
  await expect(page).toHaveURL(beforePreview);
  await expect(pdf).toBeFocused();
  await expect(page.getByLabel('Название задания')).toHaveValue(
    'Несохранённое ДЗ D',
  );
  await expect(
    page.locator('#issue-homework p').filter({ hasText: 'math.pdf' }),
  ).toBeVisible();
  await page.getByRole('button', { name: 'Свернуть выдачу задания' }).click();
  const collapse = page.getByRole('dialog', {
    name: 'Свернуть выдачу задания?',
  });
  await expect(collapse).toBeVisible();
  await expect(collapse).toHaveCSS('opacity', '1');
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  await collapse.getByRole('button', { name: 'Отмена', exact: true }).click();
  await expect(page.getByLabel('Название задания')).toHaveValue(
    'Несохранённое ДЗ D',
  );
  await page.getByRole('button', { name: 'Свернуть выдачу задания' }).click();
  await page.getByRole('button', { name: 'Свернуть, сохранив ввод' }).click();
  await expect(page.getByLabel('Название задания')).toBeHidden();
  await expect(
    page.getByRole('button', { name: 'Выдать задание', exact: true }),
  ).toBeFocused();
  await page
    .getByRole('button', { name: 'Выдать задание', exact: true })
    .click();
  await expect(
    page.locator('#issue-homework p').filter({ hasText: 'math.pdf' }),
  ).toBeVisible();
  await page.getByRole('link', { name: 'К ученику', exact: true }).click();
  const leave = page.getByRole('dialog', { name: 'Уйти без сохранения?' });
  await expect(leave).toBeVisible();
  await leave.getByRole('button', { name: 'Отмена', exact: true }).click();
  await expect(page.getByLabel('Название задания')).toHaveValue(
    'Несохранённое ДЗ D',
  );
  // Explicitly discard only local unsaved form, then inspect existing answer variants.
  await page.getByRole('link', { name: 'К ученику', exact: true }).click();
  await leave
    .getByRole('button', { name: 'Уйти без сохранения', exact: true })
    .click();
  for (const [key, text] of [
    ['0-2-20', 'Ответ получен · нужно проверить'],
    ['0-1-20', 'Ответ ещё не отправлен · у ученика черновик'],
    ['0-2-16', 'Ждём ответ ученика'],
  ]) {
    await page.goto(`/teacher/lessons/${fixture.lessons[key].id}`);
    await expect(page.getByText(text, { exact: false }).first()).toBeVisible();
    if (key !== '0-2-20')
      await expect(
        page.getByRole('link', { name: 'Проверить работу' }),
      ).toHaveCount(0);
  }
  await page.goto(`/teacher/lessons/${fixture.lessons['0-2-20'].id}`);
  await page.getByRole('link', { name: 'Проверить работу' }).click();
  const photo = page
    .getByRole('button', { name: /^Открыть .*\.webp$/ })
    .first();
  await photo.click();
  await expect(
    page.getByRole('dialog').getByRole('img', { name: /\.webp$/ }),
  ).toBeVisible();
  await page.keyboard.press('Escape');
  await expect(photo).toBeFocused();
  scenario = 'readonly';
  await page.goto(`/teacher/lessons/${lessonId}`);
  await expect(
    page.getByText(/Только просмотр: занятие в архиве/i),
  ).toBeVisible();
  await expect(
    page.getByRole('button', { name: 'Выдать задание', exact: true }),
  ).toHaveCount(0);
  await expect(
    page.getByRole('button', { name: /^Открыть .*\.pdf$/ }).first(),
  ).toBeVisible();
  scenario = 'real';
  await page.goto(`/teacher/lessons/${fixture.lessons['0-3-17'].id}`);
  await expect(
    page.getByText('Заданий пока нет.', { exact: true }),
  ).toBeVisible();
  for (const state of ['lecture-error', 'lecture-loading']) {
    scenario = state;
    if (state === 'lecture-loading')
      waiting = new Promise<void>((resolve) => {
        release = resolve;
      });
    await page.goto(`/teacher/lessons/${lessonId}`);
    await expect(
      page.getByRole('link', { name: 'Посмотреть проверку' }),
    ).toBeVisible();
    if (state === 'lecture-error') {
      await expect(
        page.getByRole('button', { name: 'Повторить', exact: true }),
      ).toBeVisible();
      scenario = 'real';
      await page
        .getByRole('button', { name: 'Повторить', exact: true })
        .click();
      await expect(
        page.getByRole('button', { name: /^Открыть .*\.pdf$/ }).first(),
      ).toBeVisible();
    } else {
      await expect(page.getByText('Загружаем…', { exact: true })).toBeVisible();
      release();
      await expect(
        page.getByRole('button', { name: /^Открыть .*\.pdf$/ }).first(),
      ).toBeVisible();
    }
  }
  scenario = 'pages';
  await page.goto('/teacher/students?limit=50&sort=recent');
  await page.locator(`a[href="${workspace}"]`).click();
  const pastPages = page.getByRole('navigation', {
    name: 'Страницы прошедших занятий',
  });
  await pastPages.getByRole('button', { name: 'Далее' }).click();
  await expect(page).toHaveURL(/history-offset=20/);
  expect(await page.evaluate(() => history.state.usr?.studentListSearch)).toBe(
    'limit=50&sort=recent',
  );
  await expect(past.getByRole('link').first()).toContainText('Встреча 21');
  await page.getByText('Следующие занятия', { exact: true }).click();
  const nextPages = page.getByRole('navigation', {
    name: 'Страницы следующих занятий',
  });
  await nextPages.getByRole('button', { name: 'Далее' }).click();
  await expect(page).toHaveURL(/next-offset=20/);
  await expect(page).toHaveURL(/history-offset=20/);
  await expect(future.getByRole('link').first()).toContainText('Встреча 21');
  const size = nextPages.getByRole('combobox', { name: 'На странице' });
  await size.focus();
  await page.keyboard.press('ArrowDown');
  await expect(
    page.getByRole('option', { name: '50', exact: true }),
  ).toBeVisible();
  const popupWidth = await page
    .locator('.mantine-Select-dropdown:visible')
    .evaluate((node) => node.getBoundingClientRect().width);
  const inputWidth = await size.evaluate(
    (node) => node.getBoundingClientRect().width,
  );
  expect(Math.abs(popupWidth - inputWidth)).toBeLessThanOrEqual(1);
  await page.screenshot({ path: '.artifacts/t15d-d-select.png' });
  await page.keyboard.press('ArrowDown');
  await page.keyboard.press('Enter');
  await expect(page).toHaveURL(/next-limit=50/);
  await expect(future.getByRole('listitem')).toHaveCount(50);
  await expect(future.getByText('В архиве · Запланировано')).toBeVisible();
  await expect(future.getByText('Отменено', { exact: true })).toBeVisible();
  for (const state of ['empty', 'error', 'loading']) {
    scenario = state;
    if (state === 'loading')
      waiting = new Promise<void>((resolve) => {
        release = resolve;
      });
    await page.goto(workspace);
    if (state === 'empty')
      await expect(
        page.getByRole('link', { name: 'Открыть расписание' }),
      ).toBeVisible();
    if (state === 'error') {
      await expect(
        page.getByRole('button', { name: 'Повторить', exact: true }).first(),
      ).toBeVisible();
      scenario = 'real';
      await page
        .getByRole('button', { name: 'Повторить', exact: true })
        .first()
        .click();
      await expect(
        page
          .getByRole('region', { name: 'Ближайшее занятие' })
          .getByRole('link', { name: 'Открыть занятие' }),
      ).toBeVisible();
    }
    if (state === 'loading') {
      await expect(
        page.getByRole('heading', { name: 'Ближайшее занятие' }),
      ).toBeVisible();
      await expect(
        page
          .getByRole('region', { name: 'Ближайшее занятие' })
          .getByRole('status'),
      ).toBeVisible();
      release();
      await expect(
        page
          .getByRole('region', { name: 'Ближайшее занятие' })
          .getByRole('link', { name: 'Открыть занятие' }),
      ).toBeVisible();
    }
  }
  scenario = 'real';
  await page.goto(`/teacher/students/${fixture.accounts.vagin.id}`);
  await expect(
    page.getByRole('link', { name: 'Открыть расписание' }),
  ).toBeVisible();
  expect(writes).toEqual([]);
  expect(errors).toEqual([]);
});
