import { test, expect, type Page } from '@playwright/test';
import { readFileSync, writeFileSync } from 'node:fs';
import AxeBuilder from '@axe-core/playwright';
const enabled = process.env.LGG_F014_UI_REVIEW === '1';
test.skip(!enabled, 'Only the dedicated F01.4 UI-review target');
const fixture = enabled
  ? JSON.parse(readFileSync('.artifacts/f014-ux-preview.json', 'utf8'))
  : {};
const week = '/teacher/schedule?week=2030-01-14&day=1';
const cell = (page: Page, date: string, hour: number) =>
  page.locator(
    `button[data-start="${date}T${String(hour).padStart(2, '0')}:00:00+03:00"]`,
  );
async function login(page: Page) {
  await page.goto('/login');
  await page
    .getByLabel('Логин', { exact: true })
    .fill(fixture.accounts.teacher.username);
  await page
    .getByLabel('Пароль', { exact: true })
    .fill(fixture.accounts.teacher.password);
  const response = page.waitForResponse(
    (r) =>
      r.url().endsWith('/api/auth/browser/login') &&
      r.request().method() === 'POST',
  );
  await page.getByRole('button', { name: 'Войти', exact: true }).click();
  expect((await response).status()).toBe(200);
  await expect(
    page.getByRole('link', { name: 'Расписание', exact: true }).first(),
  ).toBeVisible();
}
test('bulk paint twenty actual windows, keyboard, mobile and occupied lessons', async ({
  page,
}) => {
  test.setTimeout(90000);
  const errors: string[] = [];
  page.on('pageerror', (e) => errors.push(e.message));
  await login(page);
  await page.setViewportSize({ width: 1280, height: 1000 });
  await page.goto(week);
  await expect(
    page.getByRole('button', { name: 'Открыть время для записи' }),
  ).toBeEnabled();
  await expect(
    page.getByRole('heading', { name: 'Запись и брони' }),
  ).toHaveCount(0);
  const writes: { body: { items: unknown[] }; status: number }[] = [];
  page.on('response', async (r) => {
    if (
      r.url().endsWith('/api/teacher-planning/booking-windows') &&
      r.request().method() === 'POST'
    )
      writes.push({ body: r.request().postDataJSON(), status: r.status() });
  });
  await page.getByRole('button', { name: 'Открыть время для записи' }).click();
  const existing = await page
    .getByLabel('15 января, 08:00 МСК · открыто для записи')
    .count();
  if (!existing) {
    // One held mouse gesture, then independent cells; keyboard is an equivalent path.
    const a = cell(page, '2030-01-15', 8),
      b = cell(page, '2030-01-15', 9),
      c = cell(page, '2030-01-15', 10);
    await a.scrollIntoViewIfNeeded();
    const first = await a.boundingBox();
    expect(first).toBeTruthy();
    await page.mouse.move(
      first!.x + first!.width / 2,
      first!.y + first!.height / 2,
    );
    await page.mouse.down();
    await b.hover();
    await c.hover();
    await page.mouse.up();
    for (let hour = 11; hour < 18; hour++)
      await cell(page, '2030-01-15', hour).click();
    for (let hour = 8; hour < 17; hour++)
      await cell(page, '2030-01-16', hour).click();
    await cell(page, '2030-01-16', 17).focus();
    await page.keyboard.press('Space');
    await expect(
      page.getByRole('button', { name: 'Открыть выбранные (20)', exact: true }),
    ).toBeEnabled();
    await page
      .getByRole('button', { name: 'Открыть выбранные (20)', exact: true })
      .click();
    await page
      .getByRole('dialog')
      .getByRole('button', { name: 'Открыть окна (20)', exact: true })
      .click();
    await expect(
      page.getByText('Время обновлено. Открытые окна отмечены в календаре.'),
    ).toBeVisible();
    expect(writes).toHaveLength(1);
    expect(writes[0].body.items).toHaveLength(20);
    expect(writes[0].status).toBe(200);
    await expect(
      page.getByLabel('15 января, 08:00 МСК · открыто для записи'),
    ).toBeVisible();
  } else {
    await expect(
      page.locator('span[aria-label$="· открыто для записи"]'),
    ).toHaveCount(20);
  }
  await page.getByRole('button', { name: 'Отмена', exact: true }).click();
  await page.reload();
  await expect(
    page.getByLabel('15 января, 08:00 МСК · открыто для записи'),
  ).toBeVisible();
  await page.screenshot({
    path: '.artifacts/f014-ux-desktop.png',
    fullPage: true,
  });
  const closes: { items: unknown[] }[] = [];
  page.on('request', (r) => {
    if (
      r.method() === 'POST' &&
      r.url().endsWith('/api/teacher-planning/booking-windows/close')
    )
      closes.push(r.postDataJSON());
  });
  await page
    .getByRole('button', { name: 'Убрать время для записи', exact: true })
    .click();
  for (const date of ['2030-01-15', '2030-01-16'])
    for (let hour = 8; hour < 18; hour++) await cell(page, date, hour).click();
  await expect(
    page.getByRole('button', { name: 'Убрать выбранные (20)', exact: true }),
  ).toBeEnabled();
  await page.screenshot({
    path: '.artifacts/f014-ux-remove-desktop.png',
    fullPage: true,
  });
  await page
    .getByRole('button', { name: 'Убрать выбранные (20)', exact: true })
    .click();
  await page
    .getByRole('dialog')
    .getByRole('button', { name: 'Закрыть окна (20)', exact: true })
    .click();
  await expect(
    page.getByText('Время обновлено. Открытые окна отмечены в календаре.'),
  ).toBeVisible();
  expect(closes).toHaveLength(1);
  expect(closes[0].items).toHaveLength(20);
  await page.getByRole('button', { name: 'Отмена', exact: true }).click();
  await page.reload();
  await expect(
    page.getByRole('button', { name: 'Открыть время для записи', exact: true }),
  ).toBeEnabled();
  await expect(
    page.locator('span[aria-label$="· открыто для записи"]'),
  ).toHaveCount(0);
  // Clear white hours stay unpublished and existing bookings still occupy their cells.
  await page.goto('/teacher/schedule?week=2030-01-07&day=1');
  await page.getByRole('button', { name: 'Открыть время для записи' }).click();
  await cell(page, '2030-01-08', 20).click();
  await page
    .getByRole('button', { name: 'Предыдущая неделя', exact: true })
    .click();
  await expect(page.getByRole('dialog')).toBeVisible();
  await page
    .getByRole('dialog')
    .getByRole('button', { name: 'Отмена', exact: true })
    .click();
  await expect(
    page.getByRole('button', { name: 'Открыть выбранные (1)', exact: true }),
  ).toBeEnabled();
  await page
    .getByRole('button', { name: 'Снять выделение', exact: true })
    .click();
  await page.setViewportSize({ width: 390, height: 900 });
  await page.getByRole('button', { name: /пн 7.*занятий:/i }).click();
  await expect(cell(page, '2030-01-07', 15)).toHaveCount(0);
  await expect(
    page.locator('[data-calendar-booking-id]').first(),
  ).toBeVisible();
  await cell(page, '2030-01-07', 18).click();
  await page.getByRole('button', { name: /вт 8.*занятий:/i }).click();
  await cell(page, '2030-01-08', 20).click();
  await expect(
    page.getByRole('button', { name: 'Открыть выбранные (2)', exact: true }),
  ).toBeEnabled();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await page.screenshot({
    path: '.artifacts/f014-ux-mobile.png',
    fullPage: true,
  });
  await page
    .getByRole('button', { name: 'Снять выделение', exact: true })
    .click();
  await page.getByRole('button', { name: 'Отмена', exact: true }).click();
  await page
    .getByRole('button', { name: 'Убрать время для записи', exact: true })
    .click();
  await cell(page, '2030-01-08', 8).click();
  await cell(page, '2030-01-08', 9).click();
  await expect(
    page.getByRole('button', { name: 'Убрать выбранные (2)', exact: true }),
  ).toBeEnabled();
  await page.screenshot({
    path: '.artifacts/f014-ux-remove-mobile.png',
    fullPage: true,
  });
  const axe = await new AxeBuilder({ page }).analyze();
  writeFileSync('.artifacts/f014-ux-axe.json', JSON.stringify(axe.violations));
  expect(axe.violations.map((v) => v.id)).toEqual([]);
  expect(errors).toEqual([]);
  writeFileSync(
    '.artifacts/f014-ux-bulk-result.json',
    JSON.stringify({
      windows: 20,
      posts: writes.length,
      closed: closes[0].items.length,
      axe: axe.violations.length,
    }),
  );
});
test('booking opens in context; active student has no redundant account command', async ({
  page,
  browser,
}) => {
  test.setTimeout(90000);
  await login(page);
  await page.goto('/teacher/schedule?week=2030-01-07&day=0');
  await page
    .getByRole('button', { name: 'Открыть время для записи' })
    .waitFor({ state: 'visible' });
  const button = page.locator(
    `[data-booking-id="${fixture.bookings[0].booking_id}"] button`,
  );
  await expect(
    page.locator('[data-calendar-booking-id]').first(),
  ).toBeVisible();
  if (await button.count()) {
    await button.click();
    const detail = page.getByRole('dialog', { name: 'Запись на занятие' });
    await expect(detail).toContainText('Приёмка');
    await detail
      .getByRole('button', { name: 'Пригласить ученика', exact: true })
      .click();
    const confirm = page.getByRole('dialog', { name: 'Пригласить ученика' });
    await confirm.getByLabel('Проверил адресата и область доступа').check();
    await confirm
      .getByRole('button', { name: 'Создать приглашение', exact: true })
      .click();
    const invitation = page.getByLabel('Ссылка приглашения');
    await expect(invitation).toBeVisible();
    const username = await page
      .getByLabel('Логин ученика', { exact: true })
      .inputValue();
    const url = await invitation.inputValue();
    await page
      .getByRole('dialog', { name: 'Приглашение ученика' })
      .getByRole('button', { name: 'Готово', exact: true })
      .click();
    await page
      .getByRole('dialog', { name: 'Запись на занятие' })
      .getByRole('button', { name: 'Закрыть', exact: true })
      .click();
    const studentContext = await browser.newContext({
      baseURL: 'http://127.0.0.1:5175',
    });
    const s = await studentContext.newPage();
    await s.goto(url);
    await s
      .getByLabel('Новый пароль', { exact: true })
      .fill('F014-ui-review-only-123');
    await s
      .getByLabel('Повторите пароль', { exact: true })
      .fill('F014-ui-review-only-123');
    await s
      .getByRole('button', { name: 'Сохранить пароль', exact: true })
      .click();
    await expect(
      s.getByText('Пароль сохранён. Теперь войдите в кабинет.'),
    ).toBeVisible();
    await page.reload();
    const lesson = page.locator('a[aria-label*="Приёмка"]');
    await expect(lesson).toBeVisible();
    expect(username).toBeTruthy();
    await studentContext.close();
  }
  await page.goto('/teacher/students');
  await page.getByText('Приёмка Synthetic', { exact: true }).click();
  await page
    .getByText('Запись через VK и родители', {
      selector: 'summary',
      exact: true,
    })
    .click();
  await expect(
    page.getByRole('button', { name: 'Доступ в кабинет', exact: true }),
  ).toHaveCount(0);
  await expect(
    page.getByRole('button', { name: 'Выдать доступ', exact: true }),
  ).toHaveCount(0);
  await expect(
    page.getByRole('button', { name: 'Пригласить ученика', exact: true }),
  ).toHaveCount(0);
});

test('bulk error keeps selection, reads unknown receipt and never resends; nested Escape restores focus', async ({
  page,
}) => {
  test.setTimeout(90000);
  await login(page);
  await page.goto('/teacher/schedule?week=2031-01-06&day=0');
  await page.getByRole('button', { name: 'Открыть время для записи' }).click();
  await cell(page, '2031-01-06', 10).click();
  let posts = 0;
  await page.route('**/api/teacher-planning/booking-windows', (r) => {
    if (r.request().method() !== 'POST') return r.continue();
    posts++;
    return r.fulfill({ status: 409, json: { code: 'SLOT_UNAVAILABLE' } });
  });
  await page
    .getByRole('button', { name: 'Открыть выбранные (1)', exact: true })
    .click();
  let dialog = page.getByRole('dialog');
  await dialog
    .getByRole('button', { name: 'Открыть окна (1)', exact: true })
    .click();
  await expect(dialog).toContainText('Данные изменились');
  await dialog
    .getByRole('button', { name: 'Обновить данные, сохранив введённое' })
    .click();
  await expect(dialog).toContainText('Данные обновлены');
  await page.keyboard.press('Escape');
  await expect(
    page.getByRole('button', { name: 'Открыть выбранные (1)', exact: true }),
  ).toBeEnabled();
  expect(posts).toBe(1);
  await page.unroute('**/api/teacher-planning/booking-windows');
  await page.route('**/api/teacher-planning/booking-windows', (r) => {
    posts++;
    return r.abort();
  });
  await page.route('**/api/users/me/integrations/vk/operations/*', (r) =>
    r.fulfill({ status: 404, json: { code: 'NOT_FOUND' } }),
  );
  await page
    .getByRole('button', { name: 'Открыть выбранные (1)', exact: true })
    .click();
  dialog = page.getByRole('dialog');
  await dialog
    .getByRole('button', { name: 'Открыть окна (1)', exact: true })
    .click();
  await dialog.getByRole('button', { name: 'Проверить результат' }).click();
  await expect(dialog).toContainText('Результат пока неизвестен');
  expect(posts).toBe(2);
  await page.keyboard.press('Escape');
  await page
    .getByRole('button', { name: 'Открыть выбранные (1)', exact: true })
    .click();
  await expect(
    page.getByRole('button', { name: 'Проверить результат' }),
  ).toBeVisible();
  expect(posts).toBe(2);
  await page.keyboard.press('Escape');
  await page
    .getByRole('button', { name: 'Снять выделение', exact: true })
    .click();
  await page.getByRole('button', { name: 'Отмена', exact: true }).click();
  await page.goto('/teacher/schedule?week=2030-01-07&day=0');
  const opener = page.locator(
    `[data-booking-id="${fixture.bookings[1].booking_id}"] button`,
  );
  await opener.click();
  const parent = page.getByRole('dialog', { name: 'Запись на занятие' });
  const invite = parent.getByRole('button', {
    name: 'Пригласить ученика',
    exact: true,
  });
  await invite.click();
  await expect(
    page.getByRole('dialog', { name: 'Пригласить ученика' }),
  ).toBeVisible();
  await page.keyboard.press('Escape');
  await expect(invite).toBeFocused();
  await page.keyboard.press('Escape');
  await expect(opener).toBeFocused();
});
