import { test, expect } from '@playwright/test';
import { readFileSync, mkdirSync } from 'node:fs';
import AxeBuilder from '@axe-core/playwright';
import type { Lesson, Page } from '../src/features/courses/queries';
test.use({ trace: 'off', screenshot: 'off', video: 'off' });

test('real read-only calendar, then isolated HTTP fixture changes', async ({
  page,
}) => {
  test.skip(
    !process.env.LGG_T15D_PREVIEW,
    'Retained preview, no seeds or business writes.',
  );
  test.setTimeout(120000);
  const { accounts } = JSON.parse(
    readFileSync('.artifacts/t15d-preview.json', 'utf8'),
  );
  let fixture = false,
    fail = false,
    blocked = 0,
    revision = 0;
  let readScenario = 'normal';
  let releaseLoading = () => {};
  let loading = Promise.resolve();
  let source: Lesson | undefined;
  let items: Lesson[] = [];
  const writes: Record<string, unknown>[] = [],
    errors: string[] = [];
  page.on('pageerror', (e) => errors.push(e.message));
  page.on('response', async (response) => {
    if (
      !fixture &&
      new URL(response.url()).pathname === '/api/lessons' &&
      response.ok()
    ) {
      const data = (await response
        .json()
        .catch(() => ({ items: [] }))) as Page<Lesson>;
      source =
        data.items?.find((l) => l.can_manage && l.status === 'scheduled') ||
        source;
    }
  });
  await page.route('**/api/**', async (route) => {
    const req = route.request(),
      url = new URL(req.url());
    if (fixture && /^\/api\/lessons(?:\/\d+)?$/.test(url.pathname)) {
      const id = Number(url.pathname.split('/').at(-1));
      if (req.method() === 'PATCH') {
        const body = req.postDataJSON(),
          item = items.find((l) => l.id === id);
        writes.push(body);
        if (!item || fail || body.expected_updated_at !== item.updated_at)
          return route.fulfill({
            status: 409,
            json: { detail: 'Object changed; reload before saving' },
          });
        Object.assign(item, body, {
          updated_at: new Date(
            Date.UTC(2026, 10, 1, 0, 0, ++revision),
          ).toISOString(),
        });
        return route.fulfill({ json: item });
      }
      if (req.method() === 'GET') {
        if (id) return route.fulfill({ json: items.find((l) => l.id === id) });
        if (readScenario === 'loading') await loading;
        if (readScenario === 'error')
          return route.fulfill({
            status: 503,
            json: { detail: 'HTTP fixture unavailable' },
          });
        if (readScenario === 'empty')
          return route.fulfill({ json: { items: [], total: 0 } });
        const from = url.searchParams.get('from_date'),
          to = url.searchParams.get('to_date');
        const list = items.filter(
          (l) =>
            (!from || new Date(l.scheduled_at) >= new Date(from)) &&
            (!to || new Date(l.scheduled_at) <= new Date(to)),
        );
        return route.fulfill({ json: { items: list, total: list.length } });
      }
    }
    if (fixture && /\/api\/lessons\/9000[123]\/students$/.test(url.pathname))
      return route.fulfill({ json: { items: [], total: 0 } });
    if (req.method() !== 'GET' && !url.pathname.startsWith('/api/auth/')) {
      blocked++;
      return route.abort();
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
  await page.setViewportSize({ width: 1340, height: 900 });
  await page.goto('/teacher/schedule?week=2026-10-26&day=2');
  const calendar = page.getByLabel('Календарь недели', { exact: true });
  await expect(calendar.locator('article').first()).toBeVisible();
  await expect
    .poll(() =>
      calendar.evaluate((e) =>
        e
          .getAnimations({ subtree: true })
          .some((a) => a.playState === 'running'),
      ),
    )
    .toBe(false);
  const measured = await calendar.evaluate((e) => ({
    width: e.clientWidth,
    height: e.clientHeight,
    scroll: e.scrollHeight,
    top: e.getBoundingClientRect().top,
    cards: [...e.querySelectorAll('article')].map(
      (n) => n.getBoundingClientRect().height,
    ),
  }));
  expect(measured.scroll).toBeLessThan(1400);
  expect(Math.max(...measured.cards)).toBeLessThan(90);
  expect(measured.top).toBeLessThan(330);
  expect(measured.width).toBeGreaterThan(1200);
  expect(measured.height).toBeGreaterThan(650);
  mkdirSync('.artifacts', { recursive: true });
  await page.screenshot({
    path: '.artifacts/teacher-schedule-real-desktop.png',
  });
  await page.setViewportSize({ width: 360, height: 800 });
  expect(
    await page
      .getByRole('heading', { level: 2 })
      .first()
      .evaluate((e) => e.getBoundingClientRect().height),
  ).toBeLessThan(52);
  await expect(
    page.getByRole('button', { name: /ср 28 .*октября, занятий:/ }),
  ).toHaveAttribute('aria-pressed', 'true');
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await page.screenshot({
    path: '.artifacts/teacher-schedule-real-mobile.png',
  });
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  await expect.poll(() => !!source).toBe(true);
  // Everything below is an explicitly labelled in-memory HTTP fixture.
  if (!source) throw new Error('No authorized lesson snapshot');
  items = [
    {
      ...source,
      id: 90001,
      title: 'HTTP fixture',
      topic: null,
      regular_series_id: null,
      scheduled_at: '2026-11-02T15:00:00+03:00',
      duration_minutes: 55,
      status: 'scheduled',
      updated_at: '2026-11-01T00:00:00Z',
      student_labels: [
        { user_id: 90001, display_name: 'HTTP fixture · Первый ученик' },
      ],
    },
    {
      ...source,
      id: 90002,
      title: 'HTTP fixture',
      topic: null,
      regular_series_id: null,
      scheduled_at: '2026-11-02T17:00:00+03:00',
      duration_minutes: 55,
      status: 'scheduled',
      updated_at: '2026-11-01T00:00:00Z',
      student_labels: [
        {
          user_id: 90002,
          display_name:
            'HTTP fixture · Очень длинное имя ученика для проверки границ карточки',
        },
      ],
    },
  ];
  fixture = true;
  await page.setViewportSize({ width: 1340, height: 900 });
  await page.goto('/teacher/schedule?week=2026-11-02&day=0');
  const first = calendar
    .locator('article')
    .filter({ has: page.locator('a[href="/teacher/lessons/90001"]') });
  await expect(first).toHaveCount(1);
  const morning = calendar
    .locator('section')
    .first()
    .locator('[data-hour="8"]');
  await expect(morning).toHaveCSS('height', '44px');
  await expect(calendar.locator('[data-time-label="8"]')).toHaveCSS(
    'height',
    '44px',
  );
  await expect(
    calendar.locator('section').first().locator('[data-hour="12"]'),
  ).toHaveCSS('height', '88px');
  items[0].scheduled_at = '2026-11-02T08:00:00+03:00';
  await page.reload();
  await expect(calendar.locator('[data-hour="8"]')).toHaveCount(7);
  for (const row of await calendar.locator('[data-hour="8"]').all())
    await expect(row).toHaveCSS('height', '88px');
  await expect(calendar.locator('[data-time-label="8"]')).toHaveCSS(
    'height',
    '88px',
  );
  items[0].scheduled_at = '2026-11-02T15:00:00+03:00';
  await page.reload();
  const link = first.getByRole('link');
  await link.hover();
  const beforeColor = await first.evaluate(
    (e) => getComputedStyle(e).backgroundColor,
  );
  const beforeLinkColor = await link.evaluate(
    (e) => getComputedStyle(e).backgroundColor,
  );
  await page.mouse.down();
  expect(await link.evaluate((e) => e.matches(':active'))).toBe(true);
  expect(await first.evaluate((e) => getComputedStyle(e).backgroundColor)).toBe(
    beforeColor,
  );
  expect(await link.evaluate((e) => getComputedStyle(e).backgroundColor)).toBe(
    beforeLinkColor,
  );
  await page.mouse.up();
  await expect(page).toHaveURL(/\/teacher\/lessons\/90001$/);
  await expect(page.locator('main')).toHaveCSS('max-width', '1192px');
  await page.getByRole('link', { name: 'К расписанию', exact: true }).click();
  await first.getByRole('button', { name: /Управление занятием/ }).click();
  await page.getByRole('menuitem', { name: 'Перенести', exact: true }).click();
  await expect(
    page.getByRole('combobox', { name: 'Время начала, МСК' }),
  ).toBeVisible();
  await page.getByRole('button', { name: 'Отмена', exact: true }).click();
  await expect(page.getByRole('dialog')).toHaveCount(0);
  await expect(page.getByRole('menu')).toHaveCount(0);
  expect(writes).toHaveLength(0);
  await calendar.evaluate((e) => {
    e.scrollTop = 0;
  });
  await first.dragTo(morning);
  await expect(
    page.getByRole('dialog', { name: 'Перенести занятие', exact: true }),
  ).toBeVisible();
  await expect(page.getByText(/станет:.*2 ноября, 08:00/)).toBeVisible();
  expect(writes).toHaveLength(0);
  await page.getByRole('button', { name: 'Отмена', exact: true }).click();
  await expect(page.getByRole('dialog')).toHaveCount(0);
  // Keep both hours inside the stable middle of the scroll panel. Otherwise
  // native drag auto-scroll can move the destination while Playwright drops.
  await calendar.evaluate((panel) => {
    const card = panel
      .querySelector('a[href="/teacher/lessons/90001"]')!
      .closest('article')!;
    const box = card.getBoundingClientRect();
    panel.scrollTop +=
      box.top +
      box.height / 2 -
      panel.getBoundingClientRect().top -
      panel.clientHeight / 2;
  });
  const nextHour = calendar
    .locator('section')
    .nth(1)
    .locator('[data-hour="16"]');
  await expect
    .poll(async () => {
      const sourceBox = (await first.boundingBox())!;
      const targetBox = (await nextHour.boundingBox())!;
      const panelBox = (await calendar.boundingBox())!;
      return (
        Math.min(sourceBox.y, targetBox.y) > panelBox.y + 96 &&
        Math.max(
          sourceBox.y + sourceBox.height,
          targetBox.y + targetBox.height,
        ) <
          panelBox.y + panelBox.height - 56
      );
    })
    .toBe(true);
  await first.dragTo(nextHour);
  await expect(
    page.getByRole('dialog', { name: 'Перенести занятие', exact: true }),
  ).toBeVisible();
  await expect(page.getByText(/станет:.*3 ноября, 16:00/)).toBeVisible();
  expect(writes).toHaveLength(0);
  await page
    .getByRole('button', { name: 'Подтвердить перенос', exact: true })
    .click();
  await expect(page.getByRole('dialog')).toHaveCount(0);
  expect(writes).toHaveLength(1);
  expect(writes[0].scheduled_at).toBe('2026-11-03T13:00:00.000Z');
  await page.getByRole('button', { name: 'Вернуть', exact: true }).click();
  await expect
    .poll(() => items[0].scheduled_at)
    .toBe('2026-11-02T15:00:00+03:00');
  expect(writes[1].expected_updated_at).toBe('2026-11-01T00:00:01.000Z');
  await first.getByRole('button', { name: /Управление занятием/ }).click();
  await page
    .getByRole('menuitem', { name: 'Отменить занятие', exact: true })
    .click();
  expect(items[0].status).toBe('scheduled');
  await page
    .getByRole('button', { name: 'Отменить занятие', exact: true })
    .click();
  await expect(first).toHaveCount(0);
  await page.getByRole('button', { name: 'Вернуть', exact: true }).click();
  await expect(first).toHaveCount(1);
  expect(items[0].status).toBe('scheduled');
  fail = true;
  await first.getByRole('button', { name: /Управление занятием/ }).click();
  await page
    .getByRole('menuitem', { name: 'Отменить занятие', exact: true })
    .click();
  await page
    .getByRole('button', { name: 'Отменить занятие', exact: true })
    .click();
  await expect(
    page.getByRole('button', {
      name: 'Загрузить актуальное занятие',
      exact: true,
    }),
  ).toBeVisible();
  await expect(
    page.getByRole('button', { name: 'Отменить занятие', exact: true }),
  ).toBeDisabled();
  expect(items[0].status).toBe('scheduled');
  await page.getByRole('button', { name: 'Отмена', exact: true }).click();
  fail = false;
  await first.getByRole('button', { name: /Управление занятием/ }).click();
  await page
    .getByRole('menuitem', { name: 'Отменить занятие', exact: true })
    .click();
  await page
    .getByRole('button', { name: 'Отменить занятие', exact: true })
    .click();
  await expect(first).toHaveCount(0);
  await page.getByText('История и отменённые', { exact: true }).click();
  await page
    .getByRole('checkbox', { name: 'Показать отменённые', exact: true })
    .click();
  await expect(
    page.getByRole('checkbox', { name: 'Показать отменённые', exact: true }),
  ).toBeChecked();
  await expect(first).toHaveCount(1);
  await first.getByRole('button', { name: /Управление занятием/ }).click();
  await page
    .getByRole('menuitem', { name: 'Восстановить занятие', exact: true })
    .click();
  await page
    .getByRole('button', { name: 'Восстановить занятие', exact: true })
    .click();
  await expect.poll(() => items[0].status).toBe('scheduled');
  await page.getByText('История и отменённые', { exact: true }).click();
  for (const width of [1024, 768, 360]) {
    await page.setViewportSize({ width, height: 900 });
    // Mantine's exit portal fades for 150ms: assert settled geometry without sleeps.
    await expect
      .poll(() =>
        page.evaluate(() => document.documentElement.scrollWidth - innerWidth),
      )
      .toBeLessThanOrEqual(0);
    const geometry = await page.evaluate(() => ({
      width: innerWidth,
      scroll: document.documentElement.scrollWidth,
      over: [...document.querySelectorAll('body *')]
        .filter((e) => e.getBoundingClientRect().right > innerWidth + 1)
        .slice(0, 8)
        .map((e) => ({
          tag: e.tagName,
          cl: e.className,
          width: e.getBoundingClientRect().width,
        })),
    }));
    expect(geometry.scroll, JSON.stringify(geometry)).toBeLessThanOrEqual(
      geometry.width,
    );
    await expect(
      calendar.getByRole('link', {
        name: /Открыть занятие:.*HTTP fixture · Первый/,
      }),
    ).toBeVisible();
  }
  await page.screenshot({
    path: '.artifacts/teacher-schedule-http-mobile.png',
  });
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  readScenario = 'empty';
  await page.reload();
  await expect(
    calendar
      .getByText('Нет занятий', { exact: true })
      .filter({ visible: true }),
  ).toHaveCount(1);
  readScenario = 'error';
  await page.reload();
  await expect(
    page.getByText('Не удалось загрузить данные', { exact: true }),
  ).toBeVisible();
  readScenario = 'normal';
  await page.getByRole('button', { name: 'Повторить', exact: true }).click();
  await expect(first).toHaveCount(1);
  readScenario = 'loading';
  loading = new Promise<void>((resolve) => {
    releaseLoading = resolve;
  });
  await page.reload();
  await expect(
    page.getByText('Загружаем…', { exact: true }).first(),
  ).toBeVisible();
  readScenario = 'normal';
  releaseLoading();
  await expect(first).toHaveCount(1);
  const menuButton = first.getByRole('button', { name: /Управление занятием/ });
  await menuButton.focus();
  await page.keyboard.press('Enter');
  await expect(page.getByRole('menu')).toBeVisible();
  await expect(page.getByRole('menu')).toHaveCSS('opacity', '1');
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  await page.keyboard.press('Escape');
  await expect(menuButton).toBeFocused();
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await expect(first).toHaveCSS('animation-name', 'none');
  expect(blocked).toBe(0);
  expect(errors).toEqual([]);
  console.log(
    'real read-only + HTTP fixture mutations; preview business writes = 0',
    measured,
  );
});
