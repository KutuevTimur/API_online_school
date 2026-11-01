import { test, expect } from '@playwright/test';
import { readFileSync } from 'node:fs';
import AxeBuilder from '@axe-core/playwright';

test.use({ trace: 'off', screenshot: 'off', video: 'off' });

test('package A: preserved preview, responsive day and independent read states', async ({
  page,
}) => {
  test.skip(
    !process.env.LGG_T15D_PREVIEW,
    'Requires the preserved Timur preview; never seeds data.',
  );
  test.setTimeout(90000);
  const { accounts } = JSON.parse(
    readFileSync('.artifacts/t15d-preview.json', 'utf8'),
  );
  const errors: string[] = [];
  const writes: string[] = [];
  page.on('pageerror', (error) => errors.push(error.message));
  let scenario = 'real';
  let releaseLoading = () => {};
  let loading = Promise.resolve();
  const longName = 'Александра-Екатерина Константинопольская-Долгорукова';
  await page.route('**/api/**', async (route) => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    if (request.method() !== 'GET' && !path.startsWith('/api/auth/')) {
      writes.push(request.method() + ' ' + path);
      await route.abort();
      return;
    }
    const target = [
      '/api/lessons',
      '/api/submissions/review-queue',
      '/api/teacher-planning/reminders',
    ].includes(path);
    if (!target || scenario === 'real') return route.continue();
    if (scenario === 'loading') {
      await loading;
      return route.continue();
    }
    if (scenario === 'empty')
      return route.fulfill({ json: { items: [], total: 0 } });
    if (
      scenario === 'noToday' &&
      path === '/api/lessons' &&
      !new URL(request.url()).searchParams.has('status')
    )
      return route.fulfill({ json: { items: [], total: 0 } });
    if (scenario === path)
      return route.fulfill({ status: 503, json: { detail: 'Unavailable' } });
    if (scenario !== 'long') return route.continue();
    const response = await route.fetch();
    const body = await response.json();
    for (const item of body.items) {
      if (path === '/api/lessons') {
        item.student_labels = item.student_labels.map(
          (student: { user_id: number }) => ({
            ...student,
            display_name: longName,
          }),
        );
        item.effective_call_url = 'https://example.com/meeting';
      } else if (path === '/api/submissions/review-queue') {
        item.student_first_name = 'Александра-Екатерина';
        item.student_last_name = 'Константинопольская-Долгорукова';
      } else {
        item.first_name = 'Александра-Екатерина';
        item.last_name = 'Константинопольская-Долгорукова';
      }
    }
    await route.fulfill({ response, json: body });
  });
  await page.goto('/login');
  await page
    .getByLabel('Логин', { exact: true })
    .fill(accounts.teacher.username);
  await page
    .getByLabel('Пароль', { exact: true })
    .fill(accounts.teacher.password);
  const queueResponse = page.waitForResponse(
    (response) =>
      new URL(response.url()).pathname === '/api/submissions/review-queue',
  );
  await page.getByRole('button', { name: 'Войти', exact: true }).click();
  const queueCount = (await (await queueResponse).json()).items.length;
  expect(queueCount).toBeGreaterThan(0);
  await expect(page).toHaveURL(/\/teacher$/);
  const today = page.getByRole('region', { name: 'Сегодняшние занятия' });
  const next = page.getByRole('region', { name: 'Ближайшее занятие' });
  const queue = page.locator('section').filter({
    has: page.getByRole('heading', { name: 'На проверку', exact: true }),
  });
  const reminders = page.locator('section').filter({
    has: page.getByRole('heading', {
      name: 'Нужно выдать материалы',
      exact: true,
    }),
  });
  await expect(today.getByRole('listitem')).toHaveCount(5);
  await expect(queue.getByRole('listitem')).toHaveCount(queueCount);
  await expect(
    reminders.getByText('ДЗ не выдано', { exact: false }).first(),
  ).toBeVisible();
  const noOverflow = async () =>
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
  for (const width of [1340, 768, 360]) {
    await page.setViewportSize({ width, height: 1000 });
    await page.mouse.move(0, 0);
    await expect(today.getByRole('listitem')).toHaveCount(5);
    await noOverflow();
    const position = await Promise.all(
      [next, today, queue, reminders].map((item) => item.boundingBox()),
    );
    expect(position.every(Boolean)).toBe(true);
    if (width === 1340) {
      expect(position[2]!.x).toBeGreaterThan(
        position[0]!.x + position[0]!.width,
      );
      expect(position[3]!.x).toBe(position[2]!.x);
      expect(position[1]!.y).toBeGreaterThan(position[0]!.y);
    } else {
      expect(position[1]!.y).toBeGreaterThan(position[0]!.y);
      expect(position[2]!.y).toBeGreaterThan(position[1]!.y);
      expect(position[3]!.y).toBeGreaterThan(position[2]!.y);
    }
    expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
    await next
      .getByRole('link', { name: 'Открыть занятие', exact: true })
      .focus();
    for (let step = 0; step < 10; step++) {
      await page.keyboard.press('Tab');
      const focus = page.locator(':focus');
      if (await focus.evaluate((element) => !!element.closest('main'))) {
        expect(
          await focus.evaluate((element) => {
            const box = element.getBoundingClientRect();
            const hit = document.elementFromPoint(
              box.x + box.width / 2,
              box.y + box.height / 2,
            );
            return !!hit && (element.contains(hit) || hit.contains(element));
          }),
        ).toBe(true);
      }
    }
    await page.evaluate(() => {
      if (document.activeElement instanceof HTMLElement)
        document.activeElement.blur();
      window.scrollTo(0, 0);
    });
    await page.screenshot({
      path: `.artifacts/t15d-a-${width}.png`,
      fullPage: true,
    });
  }
  await page.setViewportSize({ width: 1340, height: 1000 });
  const primary = next.getByRole('link', {
    name: 'Открыть занятие',
    exact: true,
  });
  await primary.focus();
  await page.keyboard.press('Tab');
  await expect(
    next.getByRole('link', { name: 'К ученику', exact: true }),
  ).toBeFocused();
  expect(
    await page
      .locator(':focus')
      .evaluate((element) => getComputedStyle(element).outlineStyle),
  ).not.toBe('none');
  await page.keyboard.press('Enter');
  await expect(page).toHaveURL(/\/teacher\/students\/\d+$/);
  await page.goBack();
  await today.getByRole('link').first().click();
  await expect(page).toHaveURL(/\/teacher\/lessons\/\d+$/);
  await page.goBack();
  await queue.getByRole('listitem').first().getByRole('link').click();
  await expect(page).toHaveURL(/\/teacher\/review\//);
  await page.goBack();
  await reminders.getByRole('link').first().click();
  await expect(page).toHaveURL(/\/teacher\/lessons\/\d+\?student=\d+/);
  await page.goBack();
  await page
    .getByRole('link', { name: 'Открыть расписание', exact: true })
    .click();
  await expect(page).toHaveURL(/\/teacher\/schedule/);
  await page.goBack();
  for (const path of [
    '/api/submissions/review-queue',
    '/api/teacher-planning/reminders',
    '/api/lessons',
  ]) {
    scenario = path;
    await page.reload();
    const failed = path.includes('review-queue')
      ? queue
      : path.includes('reminders')
        ? reminders
        : page.locator('main');
    await expect(
      failed.getByText('Не удалось загрузить данные', { exact: true }).first(),
    ).toBeVisible();
    if (path !== '/api/lessons')
      await expect(today.getByRole('listitem')).toHaveCount(5);
    else await expect(queue.getByRole('listitem')).toHaveCount(queueCount);
    scenario = 'real';
    await failed
      .getByRole('button', { name: 'Повторить', exact: true })
      .first()
      .click();
    await expect(today.getByRole('listitem')).toHaveCount(5);
    await expect(queue.getByRole('listitem')).toHaveCount(queueCount);
    await expect(reminders.getByRole('link').first()).toBeVisible();
  }
  scenario = 'loading';
  loading = new Promise<void>((resolve) => {
    releaseLoading = resolve;
  });
  await page.reload({ waitUntil: 'domcontentloaded' });
  await expect(page.getByText('Загружаем…', { exact: true })).toHaveCount(4);
  await expect(page.locator('[aria-busy="true"]').first()).toBeVisible();
  await expect(
    page.getByRole('link', { name: 'Открыть расписание', exact: true }),
  ).toBeVisible();
  await page.screenshot({
    path: '.artifacts/t15d-a-loading.png',
    fullPage: true,
  });
  scenario = 'real';
  releaseLoading();
  await expect(today.getByRole('listitem')).toHaveCount(5);
  scenario = 'empty';
  await page.reload();
  await expect(
    page.getByText('Сегодня занятий нет.', { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText('Пока нет работ на проверку.', { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText('У закончившихся занятий нет невыданных материалов.', {
      exact: true,
    }),
  ).toBeVisible();
  await expect(page.getByText(/Будущих встреч пока нет/)).toBeVisible();
  await page.setViewportSize({ width: 360, height: 850 });
  await noOverflow();
  await page.screenshot({
    path: '.artifacts/t15d-a-empty.png',
    fullPage: true,
  });
  scenario = 'noToday';
  await page.reload();
  await expect(
    page.getByText('Сегодня занятий нет.', { exact: true }),
  ).toBeVisible();
  await expect(
    next.getByRole('link', { name: 'Открыть занятие', exact: true }),
  ).toBeVisible();
  await expect(queue.getByRole('listitem')).toHaveCount(queueCount);
  scenario = 'long';
  await page.reload();
  await expect(
    next.getByRole('heading', { level: 3, name: longName }),
  ).toBeVisible();
  await expect(
    next.getByRole('link', { name: 'Открыть встречу', exact: true }),
  ).toHaveAttribute('target', '_blank');
  for (const width of [360, 768, 1340]) {
    await page.setViewportSize({ width, height: 1000 });
    await noOverflow();
    expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  }
  expect(writes).toEqual([]);
  expect(errors).toEqual([]);
});
