import { test, expect } from '@playwright/test';
import { readFileSync } from 'node:fs';
import AxeBuilder from '@axe-core/playwright';

test.use({ trace: 'off', video: 'off', screenshot: 'off' });
test('teacher day: real read-only overview and explicit HTTP edge states', async ({
  page,
}) => {
  test.skip(
    !process.env.LGG_T15D_PREVIEW,
    'Retained preview; no seed or business writes',
  );
  const { accounts } = JSON.parse(
    readFileSync('.artifacts/t15d-preview.json', 'utf8'),
  );
  let scenario = 'real',
    blocked = 0;
  const errors: string[] = [];
  const observed = new Map<
    string,
    { items: Record<string, unknown>[]; total: number }
  >();
  page.on('pageerror', (e) => errors.push(e.message));
  page.on('response', async (r) => {
    const path = new URL(r.url()).pathname;
    if (
      scenario === 'real' &&
      r.ok() &&
      [
        '/api/lessons',
        '/api/submissions/review-queue',
        '/api/teacher-planning/reminders',
      ].includes(path)
    ) {
      observed.set(path, await r.json());
    }
  });
  await page.route('**/api/**', async (route) => {
    const req = route.request(),
      url = new URL(req.url());
    if (req.method() !== 'GET' && !url.pathname.startsWith('/api/auth/')) {
      blocked++;
      return route.abort();
    }
    const source = observed.get(url.pathname);
    if (scenario !== 'real' && source) {
      if (
        scenario === 'queue-error' &&
        url.pathname === '/api/submissions/review-queue'
      )
        return route.fulfill({
          status: 503,
          json: { detail: 'Explicit HTTP fixture unavailable' },
        });
      if (scenario === 'empty')
        return route.fulfill({ json: { items: [], total: 0 } });
      const data = structuredClone(source);
      const long = 'Александра Константинопольская-Соколова';
      if (url.pathname === '/api/lessons')
        data.items = data.items.slice(0, 1).map((l) => ({
          ...l,
          status: 'scheduled',
          scheduled_at: new Date(Date.now() + 1800000).toISOString(),
          duration_minutes: 60,
          title: 'Подготовка к экзамену: подробный разбор сложной темы',
          student_labels: [{ user_id: 99999, display_name: long }],
        }));
      if (url.pathname === '/api/submissions/review-queue')
        data.items = data.items.slice(0, 1).map((r) => ({
          ...r,
          student_first_name: 'Александра',
          student_last_name: 'Константинопольская-Соколова',
          homework_title:
            'Подробное решение задания с длинным названием и дополнительными условиями',
          course_name: 'Персональный курс подготовки к экзамену',
        }));
      if (url.pathname === '/api/teacher-planning/reminders')
        data.items = data.items.slice(0, 3).map((r, i) => ({
          ...r,
          first_name: 'Александра',
          last_name: 'Константинопольская-Соколова',
          needs_homework: i !== 1,
          needs_lecture: i !== 0,
        }));
      data.total = data.items.length;
      return route.fulfill({ json: data });
    }
    return route.continue();
  });
  await page.setViewportSize({ width: 1340, height: 900 });
  await page.goto('/login');
  await page
    .getByLabel('Логин', { exact: true })
    .fill(accounts.teacher.username);
  await page
    .getByLabel('Пароль', { exact: true })
    .fill(accounts.teacher.password);
  await page.getByRole('button', { name: 'Войти', exact: true }).click();
  await expect(page).toHaveURL(/\/teacher$/);
  const main = page.getByRole('main');
  const review = main
    .locator('section')
    .filter({ has: page.getByRole('heading', { name: /^На проверку/ }) });
  const materials = main.locator('section').filter({
    has: page.getByRole('heading', { name: /^Нужно выдать материалы/ }),
  });
  const next = page.getByRole('region', {
    name: 'Ближайшее занятие',
    exact: true,
  });
  await expect(
    materials.getByRole('link', { name: /^К занятию:/ }).first(),
  ).toBeVisible();
  await expect(
    next.getByRole('link', { name: 'К ученику', exact: true }),
  ).toBeVisible();
  await expect(
    next.getByRole('link', { name: 'К ученику', exact: true }),
  ).toHaveAttribute('href', /^\/teacher\/students\/\d+$/);
  await expect(
    main.getByRole('heading', { name: /^Сегодня/ }),
  ).not.toContainText('МСК');
  await expect(review.getByText('На проверке', { exact: true })).toHaveCount(0);
  await expect(
    review.getByRole('link', { name: /Проверить/ }).first(),
  ).toHaveAttribute('href', /^\/teacher\/review\/\d+\?homework_id=/);
  expect(
    await review.evaluate((el) => getComputedStyle(el).backgroundColor),
  ).toBe('rgb(255, 247, 219)');
  expect(
    await materials.evaluate((el) => getComputedStyle(el).backgroundColor),
  ).toBe('rgb(255, 242, 240)');
  const noOverflow = async () =>
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
  await noOverflow();
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  await page.screenshot({
    path: '.artifacts/teacher-day-real-desktop.png',
    fullPage: true,
  });
  for (const width of [1024, 768, 390, 360]) {
    await page.setViewportSize({ width, height: 844 });
    await noOverflow();
    for (const link of await next.getByRole('link').all())
      expect((await link.boundingBox())!.height).toBeGreaterThanOrEqual(44);
  }
  await page.screenshot({
    path: '.artifacts/teacher-day-real-mobile.png',
    fullPage: true,
  });
  const expand = materials.getByRole('button', { name: /^Показать все/ });
  if (await expand.count()) {
    const before = await materials.getByRole('article').count();
    await expand.click();
    await expect
      .poll(() => materials.getByRole('article').count())
      .toBeGreaterThan(before);
    await materials
      .getByRole('button', { name: 'Свернуть', exact: true })
      .click();
    await expect(materials.getByRole('article')).toHaveCount(3);
    await expect(
      materials.getByRole('button', { name: /^Показать все/ }),
    ).toBeVisible();
  }
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  const badge = materials.getByRole('heading').locator('span');
  expect(
    await badge.evaluate((el) => getComputedStyle(el).backgroundColor),
  ).toBe('rgb(255, 216, 210)');
  const reviewRow = review.getByRole('listitem').first();
  const background = await reviewRow.evaluate(
    (el) => getComputedStyle(el).backgroundColor,
  );
  await reviewRow.getByText('Артём Туров', { exact: true }).hover();
  expect(
    await reviewRow.evaluate((el) => getComputedStyle(el).backgroundColor),
  ).toBe(background);
  const check = review.getByRole('link', { name: /^Проверить:/ }).first();
  expect(await check.evaluate((el) => getComputedStyle(el).borderRadius)).toBe(
    '8px',
  );
  await check.focus();
  await expect(check).toBeFocused();
  expect(observed.size).toBe(3);
  scenario = 'long-http-fixture';
  await page.reload();
  await expect(
    next.getByText('Александра Константинопольская-Соколова', { exact: true }),
  ).toBeVisible();
  await noOverflow();
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  await page.screenshot({
    path: '.artifacts/teacher-day-http-long-mobile.png',
    fullPage: true,
  });
  await page.setViewportSize({ width: 1340, height: 900 });
  await noOverflow();
  for (const width of [1340, 1024, 768, 390, 360]) {
    await page.setViewportSize({ width, height: 900 });
    await noOverflow();
    const fits = await review
      .getByRole('link', { name: /Проверить/ })
      .first()
      .evaluate((link) => {
        const body = link.closest('li')!.querySelector('div')! as HTMLElement;
        return body.scrollWidth <= body.clientWidth + 1;
      });
    expect(fits).toBe(true);
  }
  await page.setViewportSize({ width: 1340, height: 900 });
  await page.screenshot({
    path: '.artifacts/teacher-day-http-long-desktop.png',
    fullPage: true,
  });
  const scheduled = main.locator('[data-status="scheduled"]').first();
  expect(await scheduled.evaluate((el) => getComputedStyle(el).color)).toBe(
    'rgb(7, 86, 128)',
  );
  expect(
    await scheduled.evaluate(
      (el) => getComputedStyle(el, '::before').backgroundColor,
    ),
  ).toBe('rgb(7, 86, 128)');
  expect(
    await scheduled.evaluate(
      (el) => getComputedStyle(el.closest('a')!).backgroundColor,
    ),
  ).toBe('rgb(200, 235, 252)');
  scenario = 'empty';
  await page.reload();
  await expect(
    main.getByText('Сегодня занятий нет.', { exact: true }),
  ).toBeVisible();
  await expect(
    review.getByText('Пока нет работ на проверку.', { exact: true }),
  ).toBeVisible();
  await expect(
    materials.getByText('У закончившихся занятий нет невыданных материалов.', {
      exact: true,
    }),
  ).toBeVisible();
  scenario = 'queue-error';
  await page.reload();
  await expect(review.getByRole('button', { name: /Повторить/ })).toBeVisible();
  await expect(
    materials.getByRole('link', { name: /^К занятию:/ }).first(),
  ).toBeVisible();
  expect(blocked).toBe(0);
  expect(errors).toEqual([]);
  console.log(
    'Teacher day real reads + explicit HTTP fixtures; source business writes0.',
  );
});
