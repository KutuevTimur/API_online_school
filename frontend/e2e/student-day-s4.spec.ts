import { test, expect, type Page } from '@playwright/test';
import { readFileSync } from 'node:fs';
import AxeBuilder from '@axe-core/playwright';
import type { Lesson, Homework } from '../src/features/courses/queries';
test.use({ trace: 'off', screenshot: 'off', video: 'off' });
async function geometry(page: Page) {
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth + 1,
    ),
  ).toBe(true);
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  for (const button of await page
    .locator('a.mantine-Button-root:visible')
    .all()) {
    expect(
      await button.evaluate((e) => e.scrollHeight <= e.clientHeight + 1),
    ).toBe(true);
  }
}
test('S4 student real reads and explicit HTTP fixtures', async ({ page }) => {
  test.skip(!process.env.LGG_T15D_PREVIEW, 'Retained preview only; no seed');
  test.setTimeout(180000);
  const { accounts } = JSON.parse(
    readFileSync('.artifacts/t15d-preview.json', 'utf8'),
  );
  const writes: string[] = [],
    errors: string[] = [];
  const snapshots: Record<string, { items: (Lesson & Homework)[] }> = {};
  page.on('pageerror', (e) => errors.push(e.message));
  page.on('response', async (response) => {
    const url = new URL(response.url());
    if (
      response.request().method() === 'GET' &&
      response.ok() &&
      url.pathname.startsWith('/api/')
    ) {
      try {
        snapshots[url.pathname + (url.searchParams.get('status') || '')] =
          await response.json();
      } catch {
        /* no binary reads here */
      }
    }
  });
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
  const nearest = page.getByRole('region', { name: 'Ближайшее занятие' });
  const result = page.getByRole('region', { name: 'Последний результат' });
  await expect(
    nearest.getByRole('link', { name: 'Открыть занятие' }),
  ).toBeVisible();
  await expect(nearest.getByText(/^Преподаватель:/)).toBeVisible();
  await expect(
    result.getByRole('link', { name: 'Посмотреть результат' }),
  ).toBeVisible();
  const baseLesson = snapshots['/api/lessonsscheduled'].items[0];
  const checked = snapshots['/api/homeworks/my/pagechecked'].items[0];
  expect(checked.id).not.toBe(58);
  for (const width of [1340, 768, 360]) {
    await page.setViewportSize({ width, height: 900 });
    await geometry(page);
    await page.screenshot({
      path: `.artifacts/s4-real-day-${width}.png`,
      fullPage: true,
    });
  }
  await result.getByRole('link', { name: 'Посмотреть результат' }).click();
  await expect(
    page.getByRole('region', { name: 'Результат проверки', exact: true }),
  ).toBeFocused();
  await expect(
    page.getByRole('region', { name: 'Результат проверки', exact: true }),
  ).toBeInViewport();
  await page.goBack();
  await expect(
    result.getByRole('link', { name: 'Посмотреть результат' }),
  ).toBeVisible();
  const submitted = page.locator('section').filter({
    has: page.getByRole('heading', {
      name: 'На проверке',
      exact: true,
    }),
  });
  // Skip the owner practice homework even if it moved into submitted.
  const safeLink = submitted
    .locator(
      'a[href^="/student/homeworks/"]:not([href="/student/homeworks/58"])',
    )
    .first();
  if (await safeLink.count()) {
    await safeLink.click();
    await expect(
      page.getByText(/Решение отправлено. До проверки/),
    ).toBeVisible();
    await page.goBack();
  }
  for (const width of [1340, 768, 360]) {
    await page.setViewportSize({ width, height: 900 });
    await page.goto('/student/schedule?week=2026-10-26&day=1');
    await expect(
      page.getByText('Запланировано', { exact: true }).first(),
    ).toBeVisible();
    await expect(
      page
        .locator('span:visible')
        .filter({ hasText: /^Преподаватель:/ })
        .first(),
    ).toBeVisible();
    expect(await page.getByText(/55 мин/).count()).toBe(0);
    await geometry(page);
    await page.screenshot({
      path: `.artifacts/s4-real-schedule-${width}.png`,
      fullPage: true,
    });
  }
  const initialURL = page.url();
  await page
    .getByRole('button', { name: 'Следующая неделя', exact: true })
    .click();
  await expect(page).not.toHaveURL(initialURL);
  await page.goBack();
  await expect(page).toHaveURL(initialURL);
  const lessonLink = page
    .getByRole('link', { name: /Открыть занятие:/ })
    .first();
  await lessonLink.click();
  await expect(page).toHaveURL(/\/student\/lessons\//);
  await page.goBack();
  await expect(page).toHaveURL(initialURL);
  expect(writes).toEqual([]);
  // Explicit HTTP fixtures from here: no claim of real API state coverage.
  let mode = 'many',
    metadataError = false,
    call: string | null = 'https://example.com/meeting';
  let release = () => {};
  let delayed = Promise.resolve();
  const title =
    'Длинная тема: параметры и графики квадратных уравнений '.repeat(4);
  const fakeLesson = {
    ...baseLesson,
    id: 9901,
    course_id: 9900,
    course_name: 'Курс из занятия',
    topic: title,
    effective_call_url: call,
  };
  const hw = {
    ...checked,
    id: 9902,
    title: 'Тема результата',
    working_submission_id: 9903,
    lesson_id: 9901,
    access_mode: 'read_only',
  };
  await page.route('**/api/**', async (route) => {
    const url = new URL(route.request().url()),
      path = url.pathname;
    if (route.request().method() !== 'GET') return route.fallback();
    if (path === '/api/courses/9900')
      return metadataError
        ? route.fulfill({ status: 503, json: { detail: 'fixture metadata' } })
        : route.fulfill({
            json: {
              id: 9900,
              name:
                mode === 'compact'
                  ? 'Курс вне первой страницы'
                  : 'Курс вне первой страницы ' + title,
              teacher_name:
                'Александра-Екатерина Константинопольская-Долгорукова',
            },
          });
    if (path === '/api/lessons') {
      if (mode === 'loading') await delayed;
      if (mode === 'error')
        return route.fulfill({
          status: 503,
          json: { detail: 'fixture lessons' },
        });
      return route.fulfill({
        json: {
          items:
            mode === 'empty'
              ? []
              : [
                  {
                    ...fakeLesson,
                    effective_call_url: call,
                    access_mode: mode === 'readonly' ? 'read_only' : 'active',
                  },
                ],
          total: mode === 'empty' ? 0 : 1,
        },
      });
    }
    if (path === '/api/courses')
      return route.fulfill({ json: { items: [], total: 8 } });
    if (path === '/api/homeworks/my/page') {
      const status = url.searchParams.get('status');
      const count =
        mode === 'empty' ? 0 : status === 'checked' || mode === 'one' ? 1 : 2;
      return route.fulfill({
        json: {
          items: Array.from({ length: count }, (_, i) => ({
            ...hw,
            id: 9902 + i,
          })),
          total: count,
        },
      });
    }
    if (path === '/api/homeworks/9902')
      return route.fulfill({
        json: {
          ...hw,
          working_submission_id: 9904,
          file: null,
          access_mode: 'active',
        },
      });
    if (path === '/api/submissions/9904')
      return route.fulfill({
        json: {
          id: 9904,
          homework_id: 9902,
          version: 1,
          attempt_number: 1,
          is_working: true,
          status: 'submitted',
          text_content: 'Отправленное решение fixture',
          files: [],
          review_files: [],
          grade: null,
        },
      });
    if (path === '/api/lectures')
      return route.fulfill({ json: { items: [], total: 0 } });
    if (path === '/api/submissions/9903')
      return route.fulfill({ json: { id: 9903, status: 'checked', grade: 0 } });
    return route.fallback();
  });
  for (const width of [1340, 768, 360]) {
    await page.setViewportSize({ width, height: 900 });
    await page.goto('/student');
    await expect(nearest.getByText(/^Преподаватель:/)).toBeVisible();
    await expect(result.getByText('Проверено · 0 из 5')).toBeVisible();
    expect(
      await page.getByRole('heading', { level: 2 }).allTextContents(),
    ).toEqual([
      'Ближайшее занятие',
      'К выполнению',
      'На проверке',
      'Последний результат',
      'Мои занятия',
      'Мои курсы',
    ]);
    const rows = submitted.locator('li');
    expect(await rows.count()).toBe(2);
    expect(
      await rows.evaluateAll((es) =>
        es.map((e) => getComputedStyle(e).backgroundColor),
      ),
    ).toEqual(['rgb(230, 244, 236)', 'rgb(230, 244, 236)']);
    await geometry(page);
    if (width === 360) {
      const join = nearest.getByRole('link', { name: 'Присоединиться' });
      await join.focus();
      await page.keyboard.press('Tab');
      await expect(
        nearest.getByRole('link', { name: 'Открыть занятие' }),
      ).toBeFocused();
      await page.keyboard.press('Tab');
      await expect(
        page.getByRole('link', { name: 'Открыть задание' }).first(),
      ).toBeFocused();
      await page.keyboard.press('Tab');
      await expect(
        page.getByRole('link', { name: 'Открыть задание' }).nth(1),
      ).toBeFocused();
      await page.keyboard.press('Tab');
      await expect(
        submitted.getByRole('link', { name: 'Открыть решение' }).first(),
      ).toBeFocused();
      await page.keyboard.press('Tab');
      await page.keyboard.press('Tab');
      await expect(
        result.getByRole('link', { name: 'Посмотреть результат' }),
      ).toBeFocused();
    }
    await page.screenshot({
      path: `.artifacts/s4-fixture-long-${width}.png`,
      fullPage: true,
    });
  }
  for (const value of [null, 'javascript:alert(1)']) {
    call = value;
    mode = 'one';
    await page.reload();
    await expect(
      nearest.getByText('Ссылка на встречу ещё не добавлена'),
    ).toBeVisible();
    await expect(
      nearest.getByRole('link', { name: 'Присоединиться' }),
    ).toHaveCount(0);
    expect(await submitted.locator('li').count()).toBe(1);
  }
  metadataError = true;
  await page.reload();
  await expect(nearest.getByRole('alert')).toContainText(
    'Не удалось загрузить',
  );
  await expect(nearest.getByText('Курс: Курс из занятия')).toBeVisible();
  metadataError = false;
  await nearest.getByRole('button', { name: 'Повторить', exact: true }).click();
  await expect(nearest.getByText(/^Преподаватель:/)).toBeVisible();
  mode = 'empty';
  await page.reload();
  await expect(nearest.getByText(/Пока нет предстоящих/)).toBeVisible();
  await expect(page.getByText('Заданий к выполнению пока нет.')).toBeVisible();
  await expect(
    page.getByText('Здесь появятся отправленные решения.'),
  ).toBeVisible();
  mode = 'loading';
  delayed = new Promise<void>((r) => (release = r));
  await page.reload();
  await expect(nearest.getByRole('status')).toBeVisible();
  release();
  await expect(
    nearest.getByRole('link', { name: 'Открыть занятие' }),
  ).toBeVisible();
  mode = 'error';
  await page.reload();
  await expect(
    nearest.getByRole('button', { name: 'Повторить', exact: true }),
  ).toBeVisible();
  mode = 'readonly';
  await nearest.getByRole('button', { name: 'Повторить', exact: true }).click();
  await expect(nearest.getByText('Только просмотр')).toBeVisible();
  await geometry(page);
  // Additional bounded coverage: ordinary mobile density, exact solution and day navigation.
  mode = 'compact';
  call = 'https://example.com/meeting';
  fakeLesson.topic = 'Квадратные уравнения';
  await page.goto('/student');
  const todoHeading = page.getByRole('heading', {
    name: 'К выполнению',
    exact: true,
  });
  await expect(todoHeading).toBeVisible();
  expect((await todoHeading.boundingBox())!.y).toBeLessThan(725);
  await submitted
    .getByRole('link', { name: 'Открыть решение' })
    .first()
    .click();
  await expect(page).toHaveURL(/\/student\/homeworks\/9902$/);
  await expect(
    page.getByRole('textbox', { name: 'Текст решения' }),
  ).toHaveValue('Отправленное решение fixture');
  await expect(page.getByText(/Решение отправлено. До проверки/)).toBeVisible();
  await page.goBack();
  await expect(todoHeading).toBeVisible();
  await page.goto('/student/schedule?week=2026-10-26&day=1');
  await expect(
    page.getByText(
      'Преподаватель: Александра-Екатерина Константинопольская-Долгорукова',
    ),
  ).toBeVisible();
  await geometry(page);
  await page.getByRole('button', { name: /ср 28 октября/ }).click();
  await expect(page).toHaveURL(/day=2/);
  await expect(
    page
      .locator('section[data-selected="true"]')
      .getByText('В этот день занятий нет.'),
  ).toBeVisible();
  await page.goBack();
  await expect(page).toHaveURL(/day=1/);
  metadataError = true;
  await page.reload();
  await expect(page.getByRole('alert')).toContainText('Не удалось загрузить');
  await expect(
    page.getByRole('link', { name: 'Открыть занятие: Квадратные уравнения' }),
  ).toBeVisible();
  metadataError = false;
  await page.getByRole('button', { name: 'Повторить', exact: true }).click();
  await expect(page.getByText(/^Преподаватель:/)).toBeVisible();
  expect(writes).toEqual([]);
  expect(errors).toEqual([]);
});

test('S4 teacher shared CallLink regression', async ({ page }) => {
  test.skip(!process.env.LGG_T15D_PREVIEW, 'Retained preview only; no seed');
  const { accounts } = JSON.parse(
    readFileSync('.artifacts/t15d-preview.json', 'utf8'),
  );
  const writes: string[] = [];
  const errors: string[] = [];
  page.on('pageerror', (e) => errors.push(e.message));
  const teacher = page;
  await teacher.route('**/api/**', (route) => {
    const req = route.request(),
      path = new URL(req.url()).pathname;
    if (req.method() !== 'GET' && !path.startsWith('/api/auth/')) {
      writes.push(req.method() + ' ' + path);
      return route.abort();
    }
    return route.continue();
  });
  await teacher.goto('/login');
  await teacher
    .getByLabel('Логин', { exact: true })
    .fill(accounts.teacher.username);
  await teacher
    .getByLabel('Пароль', { exact: true })
    .fill(accounts.teacher.password);
  await teacher.getByRole('button', { name: 'Войти', exact: true }).click();
  await expect(teacher).toHaveURL(/\/teacher$/);
  await teacher.goto('/teacher/lessons/124');
  for (const width of [1340, 768, 360]) {
    await teacher.setViewportSize({ width, height: 900 });
    await expect(
      teacher.getByRole('link', { name: 'Открыть встречу', exact: true }),
    ).toBeVisible();
    await expect(
      teacher.getByRole('link', { name: 'Присоединиться', exact: true }),
    ).toHaveCount(0);
    await geometry(teacher);
  }
  expect(writes).toEqual([]);
  expect(errors).toEqual([]);
});
