import { test, expect } from '@playwright/test';
import { readFileSync } from 'node:fs';
import AxeBuilder from '@axe-core/playwright';
test.use({ trace: 'off', screenshot: 'off', video: 'off' });
test('package C: calendar weeks, day view, aligned hours and protected meeting form', async ({
  page,
}) => {
  test.skip(
    !process.env.LGG_T15D_PREVIEW,
    'Preserved preview only; no seeds or business writes.',
  );
  test.setTimeout(120000);
  const { accounts } = JSON.parse(
    readFileSync('.artifacts/t15d-preview.json', 'utf8'),
  );
  const writes: string[] = [];
  const errors: string[] = [];
  let scenario = 'real';
  let expectedCount = 0;
  let release = () => {};
  let loading = Promise.resolve();
  page.on('pageerror', (error) => errors.push(error.message));
  await page.route('**/api/**', async (route) => {
    const req = route.request();
    const url = new URL(req.url());
    if (req.method() !== 'GET' && !url.pathname.startsWith('/api/auth/')) {
      writes.push(req.method() + ' ' + url.pathname);
      return route.abort();
    }
    if (
      url.pathname === '/api/lessons' &&
      url.searchParams.get('limit') === '1000'
    ) {
      if (scenario === 'loading') await loading;
      if (scenario === 'error')
        return route.fulfill({ status: 503, json: { detail: 'Unavailable' } });
      if (scenario === 'empty')
        return route.fulfill({ json: { items: [], total: 0 } });
      if (
        scenario === 'real' &&
        url.searchParams.get('from_date')?.startsWith('2026-10-18')
      ) {
        const response = await route.fetch();
        const body = await response.json();
        expectedCount = body.items.filter(
          (l: { status: string }) => l.status !== 'cancelled',
        ).length;
        return route.fulfill({ response, json: body });
      }
      if (scenario === 'long') {
        const response = await route.fetch();
        const body = await response.json();
        body.items[0].scheduled_at = body.items[0].scheduled_at.replace(
          ':00:00',
          ':15:00',
        );
        body.items[0].title = 'Тригонометрические уравнения';
        body.items[0].topic = 'Разбор самостоятельной работы';
        body.items[0].student_labels[0].display_name =
          'Александра-Екатерина Константинопольская-Долгорукова';
        body.items = [body.items[0]];
        body.total = 1;
        return route.fulfill({ response, json: body });
      }
    }
    return route.continue();
  });
  await page.goto('/login');
  await page
    .getByLabel('Логин', { exact: true })
    .fill(accounts.teacher.username);
  await page
    .getByLabel('Пароль', { exact: true })
    .fill(accounts.teacher.password);
  await page.getByRole('button', { name: 'Войти', exact: true }).click();
  await expect(page).toHaveURL(/\/teacher$/);
  const url = '/teacher/schedule?week=2026-10-19&day=1&view=active';
  await page.goto(url);
  const calendar = page.getByLabel('Календарь недели');
  const days = calendar.locator(':scope > section');
  const add = page.getByRole('button', {
    name: 'Добавить занятие',
    exact: true,
  });
  await expect.poll(() => expectedCount).toBeGreaterThan(0);
  for (const width of [1340, 1024, 1023, 768, 360]) {
    await page.setViewportSize({ width, height: 900 });
    await expect(calendar.locator('article')).toHaveCount(expectedCount);
    const visible = await days.evaluateAll(
      (nodes) =>
        nodes.filter((node) => getComputedStyle(node).display !== 'none')
          .length,
    );
    expect(visible).toBe(width > 1023 ? 7 : 1);
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    if (width > 1023) {
      expect(await days.first().locator('[data-hour]').count()).toBe(14);
      for (let hour = 8; hour < 22; hour++) {
        const tops = await calendar
          .locator(`[data-hour="${hour}"]`)
          .evaluateAll((nodes) =>
            nodes.map((node) => node.getBoundingClientRect().top),
          );
        expect(Math.max(...tops) - Math.min(...tops)).toBeLessThan(1);
      }
      const sizes = await calendar
        .locator('article a, [data-hour] > button')
        .evaluateAll((nodes) =>
          nodes.map((node) => node.getBoundingClientRect().height),
        );
      expect(Math.min(...sizes)).toBeGreaterThanOrEqual(44);
    } else {
      const chooser = page.getByLabel('День недели', { exact: true });
      let total = 0;
      for (let day = 0; day < 7; day++) {
        await chooser.getByRole('button').nth(day).click();
        await expect(chooser.getByRole('button').nth(day)).toHaveAttribute(
          'aria-pressed',
          'true',
        );
        total += await calendar
          .locator('section[data-selected="true"] article')
          .count();
      }
      expect(total).toBe(expectedCount);
      await chooser.getByRole('button').nth(1).click();
      await expect(calendar.locator('article:visible a').first()).toContainText(
        '17:00',
      );
    }
    await page.screenshot({
      path: `.artifacts/t15d-schedule-regression-${width}.png`,
      fullPage: true,
    });
  }
  await page.setViewportSize({ width: 1340, height: 900 });
  await page
    .getByRole('button', { name: 'Следующая неделя', exact: true })
    .click();
  await expect(page).toHaveURL(/week=2026-10-26/);
  await expect(calendar.locator('article').first()).toBeVisible();
  await page
    .getByRole('button', { name: 'Предыдущая неделя', exact: true })
    .click();
  await expect(page).toHaveURL(/week=2026-10-19/);
  // Real details may contain preserved homework: only inspect links here.
  // The new HTTP-fixture scenario covers lesson navigation and returnTo.
  const event = calendar.locator('article:visible').first();
  await expect(event.locator('a').first()).toHaveAttribute(
    'href',
    /\/teacher\/lessons\/\d+$/,
  );
  await event.getByRole('button', { name: /Управление занятием/ }).click();
  await expect(
    page.getByRole('menuitem', { name: /^К ученику:/ }).first(),
  ).toHaveAttribute('href', /\/teacher\/students\/\d+$/);
  await page.keyboard.press('Escape');
  await add.click();
  let dialog = page.getByRole('dialog');
  await expect(dialog).toBeVisible();
  await dialog.getByText('Дополнительно', { exact: true }).click();
  await page.keyboard.press('Escape');
  await expect(dialog).toHaveCount(0);
  await expect(add).toBeFocused();
  await add.click();
  dialog = page.getByRole('dialog');
  const select = dialog.getByRole('combobox', { name: 'Ученик', exact: true });
  await select.click();
  await expect(page.getByRole('option').first()).toBeVisible();
  await page.screenshot({
    path: '.artifacts/t15d-schedule-regression-select.png',
    fullPage: true,
  });
  await page.keyboard.press('ArrowDown');
  await page.keyboard.press('Enter');
  await expect(select).not.toHaveValue('');
  await page.keyboard.press('Escape');
  await expect(dialog).toHaveAccessibleName('Закрыть форму занятия?');
  await dialog.getByRole('button', { name: 'Отмена', exact: true }).click();
  await expect(select).not.toHaveValue('');
  await dialog
    .getByLabel('Название занятия', { exact: true })
    .fill('Сохранить введённое');
  await page.keyboard.press('Escape');
  await dialog.getByRole('button', { name: 'Отмена', exact: true }).click();
  await expect(
    dialog.getByLabel('Название занятия', { exact: true }),
  ).toHaveValue('Сохранить введённое');
  await page.setViewportSize({ width: 360, height: 800 });
  await expect(dialog).toHaveCSS('opacity', '1');
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  await page.screenshot({
    path: '.artifacts/t15d-schedule-regression-dirty.png',
    fullPage: true,
  });
  await page.keyboard.press('Escape');
  await dialog
    .getByRole('button', { name: 'Закрыть форму', exact: true })
    .click();
  await expect(dialog).toHaveCount(0);
  for (const mode of ['long', 'empty', 'error']) {
    scenario = mode;
    await page.goto(url);
    if (mode === 'error') {
      await expect(
        page.getByRole('button', { name: 'Повторить', exact: true }).first(),
      ).toBeVisible();
      scenario = 'real';
      await page
        .getByRole('button', { name: 'Повторить', exact: true })
        .first()
        .click();
      await expect(calendar.locator('article')).toHaveCount(expectedCount);
    } else if (mode === 'empty') {
      await expect(calendar.locator('article')).toHaveCount(0);
      await expect(
        calendar.getByText('Нет занятий').filter({ visible: true }),
      ).toHaveCount(1);
    } else {
      await page.setViewportSize({ width: 1340, height: 900 });
      await expect(calendar.locator('article').first()).toContainText('17:15');
      await calendar
        .locator('article')
        .first()
        .getByRole('button', { name: /Управление занятием/ })
        .click();
      await expect(page.getByRole('menu')).toContainText(
        'Разбор самостоятельной работы',
      );
      await page.keyboard.press('Escape');
      await expect(page.getByRole('menu')).toHaveCount(0);
      expect(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= innerWidth,
        ),
      ).toBe(true);
      expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
      await page.screenshot({
        path: '.artifacts/t15d-schedule-regression-long.png',
        fullPage: true,
      });
      await page.setViewportSize({ width: 360, height: 800 });
    }
  }
  scenario = 'loading';
  loading = new Promise<void>((resolve) => {
    release = resolve;
  });
  await page.goto(url);
  await expect(
    page.locator('[aria-busy="true"]:visible').first(),
  ).toBeVisible();
  await expect(add).toBeVisible();
  release();
  scenario = 'real';
  await expect(calendar.locator('article')).toHaveCount(expectedCount);
  // Keyboard traversal scrolls focus into view above the narrow shell navigation.
  await page.setViewportSize({ width: 360, height: 800 });
  const lessonLink = calendar.locator('article:visible a').first();
  await lessonLink.focus();
  await page.keyboard.press('Tab');
  const focus = await page.evaluate(() => {
    const node = document.activeElement as HTMLElement;
    const rect = node.getBoundingClientRect();
    return {
      height: rect.height,
      top: rect.top,
      bottom: rect.bottom,
      outline: getComputedStyle(node).outlineStyle,
    };
  });
  expect(focus.height).toBeGreaterThanOrEqual(44);
  expect(focus.top).toBeGreaterThanOrEqual(0);
  expect(focus.bottom).toBeLessThanOrEqual(740);
  expect(focus.outline).not.toBe('none');
  expect(writes).toEqual([]);
  expect(errors).toEqual([]);
});
