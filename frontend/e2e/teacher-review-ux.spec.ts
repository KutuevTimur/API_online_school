import { test, expect } from '@playwright/test';
import { existsSync, readFileSync } from 'node:fs';
import AxeBuilder from '@axe-core/playwright';
test.use({ trace: 'off', screenshot: 'off', video: 'off' });
const storage = '.artifacts/t15d-e-session.json';
test('package E first stage: preserved queue/review, files, targets, readonly and async states', async ({
  browser,
}) => {
  test.skip(
    !process.env.LGG_T15D_PREVIEW,
    'Preserved preview; no seed or business writes.',
  );
  test.setTimeout(90000);
  const fixture = JSON.parse(
    readFileSync('.artifacts/t15d-preview.json', 'utf8'),
  );
  const context = await browser.newContext({
    baseURL: 'http://127.0.0.1:5173',
    ...(existsSync(storage) ? { storageState: storage } : {}),
  });
  const page = await context.newPage();
  page.setDefaultTimeout(10000);
  const writes: string[] = [],
    errors: string[] = [],
    queueRequests: URL[] = [];
  let mode = 'real';
  let queueSample: Record<string, unknown>;
  let release = () => {};
  let waiting = Promise.resolve();
  page.on('pageerror', (e) => errors.push(e.message));
  await page.route('**/api/**', async (route) => {
    const req = route.request(),
      url = new URL(req.url());
    if (req.method() !== 'GET' && !url.pathname.startsWith('/api/auth/')) {
      writes.push(req.method() + ' ' + url.pathname);
      return route.abort();
    }
    if (url.pathname === '/api/submissions/review-queue') {
      queueRequests.push(url);
      if (mode === 'loading') await waiting;
      if (mode === 'error')
        return route.fulfill({ status: 503, json: { detail: 'Unavailable' } });
      if (mode === 'empty')
        return route.fulfill({ json: { items: [], total: 0 } });
      if (mode === 'pages') {
        const offset = Number(url.searchParams.get('offset')),
          limit = Number(url.searchParams.get('limit'));
        const rows = Array.from({ length: 53 }, (_, i) => ({
          ...queueSample,
          id: 20000 + i,
          homework_title: `Работа ${i + 1}`,
        }));
        return route.fulfill({
          json: { items: rows.slice(offset, offset + limit), total: 53 },
        });
      }
    }
    if (/^\/api\/homeworks\/\d+$/.test(url.pathname) && mode === 'long') {
      const response = await route.fetch(),
        data = await response.json();
      return route.fulfill({
        response,
        json: {
          ...data,
          description: 'Длинное условие https://example.com/task\n'.repeat(30),
        },
      });
    }
    if (/^\/api\/submissions\/\d+$/.test(url.pathname) && mode === 'text') {
      const response = await route.fetch(),
        data = await response.json();
      return route.fulfill({
        response,
        json: {
          ...data,
          text_content: 'Полноценный текстовый ответ без файла',
          files: [],
        },
      });
    }
    return route.continue();
  });
  try {
    await page.goto('/teacher/review');
    await expect
      .poll(
        async () =>
          new URL(page.url()).pathname === '/login' ||
          (await page
            .getByRole('list', { name: 'Работы на проверку' })
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
      await page.goto('/teacher/review');
    }
    await expect(
      page.getByRole('list', { name: 'Работы на проверку' }),
    ).toBeVisible();
    await context.storageState({ path: storage });
    // Read via the same authorized browser context, no extra login.
    const realQueue = await page.evaluate(async () => {
      const { request } = await import('/src/shared/api/client.ts');
      return request<{ items: Record<string, unknown>[] }>(
        '/submissions/review-queue',
        { params: { limit: 20, offset: 0 } },
      );
    });
    queueSample = realQueue.items[0];
    expect(queueSample).toBeTruthy();
    const course = page
      .locator('details')
      .filter({ has: page.locator('summary').filter({ hasText: /^Курс:/ }) });
    await expect(course).not.toHaveAttribute('open');
    await course.locator('summary').press('Enter');
    const courseSelect = page.getByRole('combobox', {
      name: 'Курс',
      exact: true,
    });
    await courseSelect.click();
    await expect(page.getByRole('listbox')).toBeVisible();
    const popup = page.locator('.mantine-Select-dropdown:visible');
    expect(
      Math.abs(
        (await popup.boundingBox())!.width -
          (await courseSelect.boundingBox())!.width,
      ),
    ).toBeLessThanOrEqual(1);
    await page.keyboard.press('ArrowDown');
    await page.keyboard.press('Enter');
    await expect(page).toHaveURL(/course_id=\d+/);
    await course.locator('summary').click();
    await expect(course.locator('summary')).not.toHaveText('Курс: все курсы');
    await page.getByRole('button', { name: 'Сбросить фильтры' }).click();
    await page.goto(
      `/teacher/review?student_user_id=${queueSample.student_user_id}&course_id=${queueSample.course_id}&limit=50`,
    );
    const work = page
      .getByRole('list', { name: 'Работы на проверку' })
      .getByRole('link')
      .first();
    await work.click();
    const reviewURL = page.url();
    const h1 = page.getByRole('heading', { level: 1 });
    await expect(h1).toContainText(String(queueSample.student_first_name));
    await expect(page.getByRole('link', { name: 'К занятию' })).toBeVisible();
    const condition = page.locator('details').filter({
      has: page.locator('summary').filter({ hasText: 'Условие задания' }),
    });
    await expect(condition).toHaveAttribute('open', '');
    const radios = page.getByRole('radio');
    await expect(radios).toHaveCount(6);
    for (const radio of await radios.all())
      await expect(radio).not.toBeChecked();
    await page
      .getByRole('button', { name: 'Завершить проверку', exact: true })
      .click();
    await expect(
      page.getByRole('radio', { name: '0', exact: true }),
    ).toBeFocused();
    await page.keyboard.press('Space');
    await page.getByRole('radio', { name: '1', exact: true }).check();
    await page.getByRole('radio', { name: '0', exact: true }).check();
    await page
      .getByLabel('Комментарий ученику', { exact: true })
      .fill('Черновик E сохраняется');
    await page
      .getByLabel('Добавить файлы к проверке', { exact: true })
      .setInputFiles('e2e/fixtures/math.pdf');
    for (const width of [1340, 768, 360]) {
      await page.setViewportSize({ width, height: 950 });
      const solution = page
        .getByRole('heading', { name: 'Решение ученика' })
        .locator('..');
      const grading = page
        .getByRole('heading', { name: 'Проверка', exact: true })
        .locator('..');
      const left = (await solution.boundingBox())!,
        right = (await grading.boundingBox())!;
      if (width === 1340) {
        expect(left.width / right.width).toBeGreaterThan(1.8);
        expect(Math.abs(left.y - right.y)).toBeLessThan(1);
      } else expect(right.y).toBeGreaterThan(left.y + left.height);
      for (const radio of await radios.all()) {
        const target = await radio.evaluate((el) =>
          el.closest('.mantine-Radio-body')!.getBoundingClientRect().toJSON(),
        );
        expect(target.width).toBeGreaterThanOrEqual(44);
        expect(target.height).toBeGreaterThanOrEqual(44);
      }
      // Clicking the full label target selects, including 0.
      await page.locator('label').filter({ hasText: /^0$/ }).click();
      await expect(
        page.getByRole('radio', { name: '0', exact: true }),
      ).toBeChecked();
      expect(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= innerWidth,
        ),
      ).toBe(true);
      expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
      await page.mouse.click(5, 150);
      await page.screenshot({
        path: `.artifacts/t15d-e-review-${width}.png`,
        fullPage: true,
      });
    }
    for (const ext of ['webp', 'pdf']) {
      const opener = page
        .getByRole('button', { name: new RegExp(`^Открыть .*\\.${ext}$`) })
        .first();
      await opener.focus();
      await page.keyboard.press('Enter');
      const viewer = page.getByRole('dialog');
      if (ext === 'pdf')
        await expect(
          viewer.getByLabel('Страница 1', { exact: true }),
        ).toBeVisible();
      else
        await expect(
          viewer.getByRole('img', { name: /\.webp$/ }),
        ).toBeVisible();
      await page.keyboard.press('Escape');
      await expect(viewer).not.toBeAttached();
      await expect(opener).toBeFocused();
      await expect(page).toHaveURL(reviewURL);
      await expect(
        page.getByLabel('Комментарий ученику', { exact: true }),
      ).toHaveValue('Черновик E сохраняется');
      await expect(
        page.getByRole('radio', { name: '0', exact: true }),
      ).toBeChecked();
      await expect(page.getByText('math.pdf', { exact: true })).toBeVisible();
    }
    await page
      .getByRole('button', { name: 'Завершить проверку', exact: true })
      .click();
    const confirm = page.getByRole('dialog', { name: 'Завершить проверку?' });
    await expect(confirm.getByText('Оценка: 0 из 5.')).toBeVisible();
    await expect(confirm).toHaveCSS('opacity', '1');
    expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
    await page.keyboard.press('Escape');
    await expect(confirm).not.toBeAttached();
    await page.getByRole('link', { name: 'К очереди', exact: true }).click();
    let leave = page.getByRole('dialog', { name: 'Уйти без сохранения?' });
    await leave.getByRole('button', { name: 'Отмена', exact: true }).click();
    await expect(page.getByText('math.pdf', { exact: true })).toBeVisible();
    await page.getByRole('link', { name: 'К очереди', exact: true }).click();
    leave = page.getByRole('dialog', { name: 'Уйти без сохранения?' });
    await leave
      .getByRole('button', { name: 'Уйти без сохранения', exact: true })
      .click();
    await expect(page).toHaveURL(/student_user_id=.*course_id=.*limit=50/);
    // GET-only variants: long condition, text-only and checked from existing data.
    mode = 'long';
    await page.goto(reviewURL);
    await expect(condition).toHaveAttribute('open', '');
    await condition.locator('summary').click();
    await expect(condition).not.toHaveAttribute('open');
    await expect(h1).toBeVisible();
    await expect(page.getByRole('link', { name: 'К занятию' })).toBeVisible();
    await condition.locator('summary').press('Enter');
    await expect(condition.getByRole('link').first()).toBeVisible();
    mode = 'text';
    await page.reload();
    await expect(
      page.getByText('Полноценный текстовый ответ без файла'),
    ).toBeVisible();
    await expect(
      page.getByLabel('Комментарий ученику', { exact: true }),
    ).toBeEnabled();
    mode = 'real';
    const checked = fixture.answers['0-1-18'];
    await page.goto(
      `/teacher/review/${checked.id}?homework_id=${checked.homework_id}`,
    );
    await expect(page.getByText(/Проверено · Оценка:/)).toBeVisible();
    await expect(page.getByRole('radio')).toHaveCount(0);
    await expect(
      page.getByLabel('Комментарий ученику', { exact: true }),
    ).toHaveCount(0);
    await page.screenshot({
      path: '.artifacts/t15d-e-checked-360.png',
      fullPage: true,
    });
    mode = 'pages';
    await page.goto('/teacher/review?student_user_id=42&course_id=7');
    await page
      .getByRole('navigation', { name: 'Страницы очереди проверки' })
      .getByRole('button', { name: 'Далее' })
      .click();
    await expect(page.getByRole('link', { name: /Работа 21/ })).toBeVisible();
    expect(queueRequests.at(-1)!.searchParams.get('offset')).toBe('20');
    expect(queueRequests.at(-1)!.searchParams.get('student_user_id')).toBe(
      '42',
    );
    expect(queueRequests.at(-1)!.searchParams.get('course_id')).toBe('7');
    await page.screenshot({
      path: '.artifacts/t15d-e-queue-360.png',
      fullPage: true,
    });
    await page.setViewportSize({ width: 1340, height: 950 });
    await page.screenshot({
      path: '.artifacts/t15d-e-queue-1340.png',
      fullPage: true,
    });
    mode = 'empty';
    await page.goto('/teacher/review');
    await expect(page.getByText(/Пока нет работ на проверку/)).toBeVisible();
    mode = 'error';
    await page.reload();
    await expect(
      page.getByRole('button', { name: 'Повторить', exact: true }),
    ).toBeVisible();
    mode = 'real';
    await page.getByRole('button', { name: 'Повторить', exact: true }).click();
    await expect(
      page.getByRole('list', { name: 'Работы на проверку' }),
    ).toBeVisible();
    mode = 'loading';
    waiting = new Promise<void>((r) => (release = r));
    await page.reload();
    await expect(
      page.getByRole('status').filter({ hasText: /^Загружаем…$/ }),
    ).toBeVisible();
    mode = 'real';
    release();
    await expect(
      page.getByRole('list', { name: 'Работы на проверку' }),
    ).toBeVisible();
    await context.storageState({ path: storage });
    expect(writes).toEqual([]);
    expect(errors).toEqual([]);
  } finally {
    release();
    await context.storageState({ path: storage });
    await context.close();
  }
});
