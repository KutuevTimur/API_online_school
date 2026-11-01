import { test, expect, type Page } from '@playwright/test';
import { readFileSync } from 'node:fs';
import AxeBuilder from '@axe-core/playwright';
import type {
  Lesson,
  Lecture,
  Homework,
  Page as ApiPage,
} from '../src/features/courses/queries';
test.use({ trace: 'off', screenshot: 'off', video: 'off' });
async function login(page: Page) {
  const { accounts } = JSON.parse(
    readFileSync('.artifacts/t15d-preview.json', 'utf8'),
  );
  const writes: string[] = [],
    errors: string[] = [];
  page.on('pageerror', (e) => errors.push(e.message));
  await page.route('**/api/**', (route) => {
    const req = route.request();
    if (
      req.method() !== 'GET' &&
      !new URL(req.url()).pathname.startsWith('/api/auth/')
    ) {
      writes.push(req.method() + ' ' + new URL(req.url()).pathname);
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
  return { writes, errors };
}
async function audit(page: Page) {
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth + 1,
    ),
  ).toBe(true);
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
}
test('compact latest real reads: responsive, protected PDF, exact homework and history Back', async ({
  page,
}) => {
  test.skip(!process.env.LGG_T15D_PREVIEW, 'Retained preview, no seed');
  test.setTimeout(60000);
  const { writes, errors } = await login(page);
  await page.goto(
    '/student/materials?history-month=2026-09&history-strip=2026-08',
  );
  const card = page.getByRole('region', {
    name: 'Последнее проведённое занятие',
  });
  const history = page.getByRole('region', { name: 'История занятий' });
  const file = card.getByRole('button', { name: 'Конспект', exact: true });
  await expect(file).toBeVisible();
  await expect(
    card.getByRole('link', { name: 'Д/з', exact: true }),
  ).toBeVisible();
  for (const width of [1340, 768, 360]) {
    await page.setViewportSize({ width, height: 900 });
    expect((await card.boundingBox())!.height).toBeLessThanOrEqual(265);
    expect((await history.boundingBox())!.y).toBeLessThan(480);
    expect(
      await card.evaluate((e) => getComputedStyle(e).backgroundColor),
    ).toBe('rgb(255, 255, 255)');
    await expect(
      card.getByRole('heading', { name: 'Занятие', exact: true }),
    ).toHaveCount(0);
    for (const button of await card.locator('a,button').all()) {
      expect((await button.boundingBox())!.height).toBeGreaterThanOrEqual(44);
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
    const openLesson = card.getByRole('link', {
      name: 'Открыть занятие',
      exact: true,
    });
    await expect(openLesson).toHaveText('Открыть занятие');
    expect(
      await openLesson.evaluate((e) => getComputedStyle(e).backgroundColor),
    ).toBe('rgb(200, 235, 252)');
    if (width === 360)
      expect((await openLesson.boundingBox())!.width).toBeGreaterThan(260);
    if (width === 1340) {
      const bounds = await openLesson.boundingBox();
      await openLesson.hover();
      expect(
        await openLesson.evaluate((e) => getComputedStyle(e).backgroundColor),
      ).toBe('rgb(8, 117, 180)');
      expect(await openLesson.evaluate((e) => getComputedStyle(e).color)).toBe(
        'rgb(255, 255, 255)',
      );
      expect(await openLesson.boundingBox()).toEqual(bounds);
      await audit(page);
      await page.mouse.move(0, 0);
    }

    await audit(page);
    await page.screenshot({
      path: `.artifacts/student-latest-real-${width}.png`,
      fullPage: false,
    });
  }
  const before = page.url();
  await file.press('Enter');
  const dialog = page.getByRole('dialog');
  await expect(dialog).toBeVisible();
  await expect(dialog.getByLabel('Страница 1', { exact: true })).toBeVisible();
  await page.goBack();
  await expect(page).toHaveURL(before);
  await expect(file).toBeFocused();
  await card
    .getByRole('link', { name: 'Открыть занятие', exact: true })
    .press('Enter');
  await expect(page).toHaveURL(/\/student\/lessons\/129$/);
  await page
    .getByRole('link', { name: 'К моим занятиям', exact: true })
    .click();
  await expect(page).toHaveURL(before);
  const homework = card.getByRole('link', { name: 'Д/з', exact: true });
  const target = await homework.getAttribute('href');
  expect(target).toBe('/student/homeworks/63');
  await homework.press('Enter');
  await expect(page).toHaveURL(/\/student\/homeworks\/63$/);
  await page.goBack();
  await expect(page).toHaveURL(before);
  await expect(
    history.getByRole('heading', { name: 'Сентябрь 2026' }),
  ).toBeVisible();
  expect(writes).toEqual([]);
  expect(errors).toEqual([]);
});
test('compact latest explicit HTTP fixtures: multiple, pagination, long, missing, metadata, error, loading, readonly and empty', async ({
  page,
}) => {
  test.skip(
    !process.env.LGG_T15D_PREVIEW,
    'Retained auth; all altered states are HTTP fixtures',
  );
  test.setTimeout(90000);
  const { writes, errors } = await login(page);
  let mode = 'many';
  let base: Lesson | undefined;
  let lectures: ApiPage<Lecture> | undefined;
  let homeworks: Homework[] | undefined;
  let release = () => {};
  let delay = Promise.resolve();
  await page.route('**/api/lessons?*', async (route) => {
    const u = new URL(route.request().url());
    if (
      u.searchParams.get('status') !== 'completed' ||
      u.searchParams.get('limit') !== '1'
    )
      return route.fallback();
    if (!base) base = (await (await route.fetch()).json()).items[0];
    return route.fulfill({
      json: {
        items:
          mode === 'empty'
            ? []
            : [
                {
                  ...base,
                  topic:
                    mode === 'many'
                      ? 'Очень длинная настоящая тема для проверки переносов '.repeat(
                          4,
                        )
                      : null,
                  title: 'Занятие',
                  course_id: mode === 'metadata' ? 999999 : base!.course_id,
                  is_deleted: mode === 'readonly',
                  access_mode: mode === 'readonly' ? 'read_only' : 'active',
                  read_only_reason:
                    mode === 'readonly' ? 'lesson_archived' : null,
                },
              ],
        total: mode === 'empty' ? 0 : 1,
      },
    });
  });
  await page.route('**/api/lectures?*', async (route) => {
    if (!lectures) lectures = await (await route.fetch()).json();
    if (mode === 'loading') await delay;
    if (mode === 'error')
      return route.fulfill({ status: 503, json: { detail: 'HTTP fixture' } });
    const offset = Number(
      new URL(route.request().url()).searchParams.get('offset'),
    );
    return route.fulfill({
      json: {
        items:
          mode === 'missing'
            ? []
            : mode === 'many'
              ? Array.from({ length: offset ? 1 : 20 }, (_, i) => ({
                  ...lectures!.items[0],
                  id: offset + i + 1,
                  file: {
                    ...lectures!.items[0].file,
                    id: (lectures!.items[0].file?.id || 0) + offset + i,
                    display_name: `Конспект ${offset + i + 1} ${'длинное_имя_'.repeat(5)}.pdf`,
                  },
                }))
              : lectures!.items,
        total: mode === 'missing' ? 0 : mode === 'many' ? 21 : lectures!.total,
      },
    });
  });
  await page.route('**/api/homeworks?*', async (route) => {
    if (!homeworks) homeworks = await (await route.fetch()).json();
    if (mode === 'loading') await delay;
    if (mode === 'error')
      return route.fulfill({ status: 503, json: { detail: 'HTTP fixture' } });
    return route.fulfill({
      json:
        mode === 'missing'
          ? []
          : mode === 'many'
            ? [
                homeworks![0],
                {
                  ...homeworks![0],
                  id: 62,
                  placement_id: 99999,
                  title: 'Второе домашнее задание с длинным названием '.repeat(
                    3,
                  ),
                },
              ]
            : homeworks,
    });
  });
  await page.route('**/api/courses/999999', (route) =>
    route.fulfill({ status: 503, json: { detail: 'HTTP fixture metadata' } }),
  );
  await page.goto('/student/materials?history-month=2026-09');
  const card = page.getByRole('region', {
    name: 'Последнее проведённое занятие',
  });
  await page.setViewportSize({ width: 360, height: 900 });
  const lectureToggle = card.getByRole('button', { name: 'Конспекты · 21' });
  await expect(lectureToggle).toBeVisible();
  await expect(
    card.getByRole('button', { name: /^Открыть Конспект/ }),
  ).toHaveCount(0);
  await lectureToggle.click();
  await expect(
    card.getByRole('button', { name: /^Открыть Конспект/ }),
  ).toHaveCount(20);
  await card
    .getByRole('navigation', { name: 'Страницы конспектов занятия' })
    .getByRole('button', { name: 'Далее' })
    .click();
  await expect(
    card.getByRole('button', { name: /^Открыть Конспект 21 / }),
  ).toBeVisible();
  await card.getByRole('button', { name: 'Д/з · 2' }).click();
  await expect(
    card.getByRole('link', { name: /^Второе домашнее задание/ }),
  ).toHaveAttribute('href', '/student/homeworks/62');
  await audit(page);
  await page.goto(
    '/student/materials?history-month=2027-01&history-strip=2026-12',
  );
  await expect(
    card.getByRole('button', { name: 'Конспекты · 21' }),
  ).toBeVisible();
  await expect(
    page.getByRole('button', { name: 'дек 2026 — декабрь 2026', exact: true }),
  ).toBeVisible();
  await audit(page);
  mode = 'missing';
  await page.reload();
  await expect(card.getByText('Конспект пока не добавлен.')).toBeVisible();
  await expect(card.getByText('Д/з пока не выдано.')).toBeVisible();
  await audit(page);
  mode = 'error';
  await page.reload();
  await expect(
    card.getByRole('button', { name: 'Повторить', exact: true }),
  ).toHaveCount(2, { timeout: 15000 });
  await expect(card.getByText('Конспект пока не добавлен.')).toHaveCount(0);
  mode = 'single';
  await card
    .getByRole('region', { name: 'Конспекты занятия' })
    .getByRole('button', { name: 'Повторить', exact: true })
    .click();
  await expect(
    card.getByRole('button', { name: 'Конспект', exact: true }),
  ).toBeVisible();
  await card
    .getByRole('region', { name: 'Домашние задания занятия' })
    .getByRole('button', { name: 'Повторить', exact: true })
    .click();
  await expect(
    card.getByRole('link', { name: 'Д/з', exact: true }),
  ).toBeVisible();
  mode = 'loading';
  delay = new Promise<void>((resolve) => {
    release = resolve;
  });
  await page.reload();
  await expect(card.getByText('Загружаем…', { exact: true })).toHaveCount(2);
  await expect(card.getByText('Конспект пока не добавлен.')).toHaveCount(0);
  release();
  await expect(
    card.getByRole('button', { name: 'Конспект', exact: true }),
  ).toBeVisible();
  mode = 'metadata';
  await page.reload();
  await expect(card.getByText('Имя преподавателя недоступно')).toBeVisible({
    timeout: 15000,
  });
  await expect(
    card.getByRole('link', { name: 'Открыть занятие' }),
  ).toBeVisible();
  await audit(page);
  mode = 'readonly';
  await page.reload();
  await expect(card.getByText(/В архиве/)).toBeVisible();
  await expect(
    card.getByRole('button', { name: 'Конспект', exact: true }),
  ).toBeVisible();
  await audit(page);
  mode = 'empty';
  await page.reload();
  await expect(card.getByText('Проведённых занятий пока нет.')).toBeVisible();
  await expect(card.getByRole('link', { name: 'Открыть занятие' })).toHaveCount(
    0,
  );
  await audit(page);
  expect(writes).toEqual([]);
  expect(errors).toEqual([]);
});
