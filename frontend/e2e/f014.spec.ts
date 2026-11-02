import { test, expect, type Page } from '@playwright/test';
import { readFileSync, writeFileSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import AxeBuilder from '@axe-core/playwright';
const note = JSON.parse(readFileSync('.artifacts/f014-preview.json', 'utf8'));
const schedule = '/teacher/schedule?week=2030-01-07&day=0';
const row = (page: Page, n = 0) =>
  page.locator(`li[data-booking-id="${note.bookings[n].booking_id}"]`);
async function login(page: Page, account = note.accounts.teacher) {
  await page.goto('/login');
  await page.getByLabel('Логин', { exact: true }).fill(account.username);
  await page.getByLabel('Пароль', { exact: true }).fill(account.password);
  const response = page.waitForResponse(
    (r) =>
      r.url().endsWith('/api/auth/browser/login') &&
      r.request().method() === 'POST',
  );
  await page.getByRole('button', { name: 'Войти', exact: true }).click();
  const authenticated = await response;
  expect(authenticated.status()).toBe(200);
  const token = (await authenticated.json()).access_token;
  await expect(page).toHaveURL(/\/(teacher|student)/);
  return token;
}
test.beforeEach(async ({ context }) => {
  await context.route('**/*', (r) => {
    const u = new URL(r.request().url());
    return u.hostname === '127.0.0.1' && u.port === '5174'
      ? r.continue()
      : r.abort();
  });
});
test('F01.4 real two-role booking, invitation, activation and same Lesson', async ({
  page,
  browser,
}) => {
  test.setTimeout(120000);
  await page.context().addCookies([
    {
      name: 'lgg_refresh',
      value: 'retained-placeholder',
      domain: '127.0.0.1',
      path: '/api/auth/browser',
    },
  ]);
  console.log('F014 flow: login');
  const token = await login(page);
  expect(
    (await page.context().cookies()).find((c) => c.name === 'lgg_refresh')
      ?.value,
  ).toBe('retained-placeholder');
  expect(
    (await page.context().cookies()).some((c) => c.name === 'lgg_f014_refresh'),
  ).toBe(true);
  console.log('F014 flow: schedule');
  await page.goto(schedule);
  console.log('F014 flow: schedule loaded');
  await expect(row(page, 1)).toContainText('Кабинет не подключён');
  // Parent permission has its own confirmation, independent of the booking.
  await row(page, 1)
    .getByRole('button', { name: 'Подтвердить связь', exact: true })
    .click();
  let dialog = page.getByRole('dialog');
  await expect(dialog).toContainText('Родитель · …00');
  await expect(dialog).toContainText('решениям и оценкам не предоставляется');
  await dialog
    .getByRole('button', { name: 'Подтвердить связь', exact: true })
    .click();
  await expect(row(page, 1)).toContainText('Связь подтверждена');
  await row(page, 1)
    .getByRole('button', { name: 'Отозвать связь', exact: true })
    .click();
  await page
    .getByRole('dialog')
    .getByRole('button', { name: 'Отозвать связь', exact: true })
    .click();
  await expect(row(page, 1)).toContainText('Связь отозвана');
  // Explicit dated window publication, then close that exact window.
  console.log('F014 flow: publish');
  await page.getByRole('button', { name: 'Открыть время для записи' }).click();
  await page.getByLabel('Время начала, МСК').fill('19:00');
  await page.getByRole('button', { name: 'Открыть окно', exact: true }).click();
  await page
    .getByRole('dialog')
    .getByRole('button', { name: 'Открыть окно', exact: true })
    .click();
  await page.getByText('Окна выбранной недели', { exact: true }).click();
  const windowRow = page
    .locator('li')
    .filter({ hasText: '19:00' })
    .filter({
      has: page.getByRole('button', { name: 'Закрыть окно', exact: true }),
    });
  await windowRow
    .getByRole('button', { name: 'Закрыть окно', exact: true })
    .click();
  await page
    .getByRole('dialog')
    .getByRole('button', { name: 'Закрыть окно', exact: true })
    .click();
  await expect(windowRow).toHaveCount(0);
  await row(page, 1)
    .getByRole('button', { name: 'Подключить кабинет' })
    .click();
  dialog = page.getByRole('dialog');
  await dialog.getByLabel('Проверил адресата и область доступа').check();
  const resolveResponse = page.waitForResponse(
    (r) =>
      r
        .url()
        .includes(`/bookings/${note.bookings[1].booking_id}/resolve-invite`) &&
      r.request().method() === 'POST',
  );
  await dialog
    .getByRole('button', { name: 'Выдать доступ', exact: true })
    .click();
  expect((await resolveResponse).status()).toBe(200);
  const invitation = await page.getByLabel('Ссылка приглашения').inputValue();
  const studentUsername = await page
    .getByLabel('Логин ученика', { exact: true })
    .inputValue();
  expect(studentUsername).toBeTruthy();
  await page
    .getByRole('dialog')
    .getByRole('button', { name: 'Готово' })
    .click();
  await expect(row(page, 1)).toContainText('Ожидает активации');
  const detail = await page.request.get(
    `/api/teacher-planning/bookings/${note.bookings[1].booking_id}`,
    { headers: { Authorization: `Bearer ${token}` } },
  );
  const booking = await detail.json();
  expect(booking.booking_id).toBe(note.bookings[1].booking_id);
  expect(booking.lesson_id).toBeTruthy();
  const profileResponse = await page.request.get(
    `/api/users/${booking.recipient.linked_student_user_id}`,
    { headers: { Authorization: `Bearer ${token}` } },
  );
  const profile = await profileResponse.json();
  const studentContext = await browser.newContext({
    baseURL: 'http://127.0.0.1:5174',
  });
  const studentPage = await studentContext.newPage();
  console.log('F014 flow: activate');
  await studentPage.goto(invitation);
  await studentPage
    .getByLabel('Новый пароль', { exact: true })
    .fill('F014-student-only-123');
  await studentPage
    .getByLabel('Повторите пароль', { exact: true })
    .fill('F014-student-only-123');
  await studentPage.getByRole('button', { name: 'Сохранить пароль' }).click();
  await expect(
    studentPage.getByText('Пароль сохранён. Теперь войдите в кабинет.'),
  ).toBeVisible();
  await login(studentPage, {
    username: studentUsername,
    password: 'F014-student-only-123',
  });
  await studentPage.goto('/student/schedule?week=2030-01-07');
  const lessonLink = studentPage
    .locator(`a[href="/student/lessons/${booking.lesson_id}"]`)
    .first();
  await expect(lessonLink).toBeVisible();
  await lessonLink.click();
  await expect(studentPage).toHaveURL(
    new RegExp(`/student/lessons/${booking.lesson_id}`),
  );
  await page.getByRole('button', { name: 'Обновить запись и брони' }).click();
  await expect(row(page, 1)).toContainText('Кабинет подключён');
  await expect(
    page.locator(`[data-booking-id="${booking.booking_id}"]`),
  ).toHaveCount(1);
  await expect(row(page, 0)).toContainText('Кабинет не подключён');
  writeFileSync(
    '.artifacts/f014-browser-result.json',
    JSON.stringify({
      lesson_id: booking.lesson_id,
      student_username: profile.username,
      booking_id: booking.booking_id,
    }),
  );
  await studentContext.close();
});
test('F01.4 viewport, keyboard, popup, focus and accessibility matrix', async ({
  page,
}) => {
  test.setTimeout(120000);
  await login(page);
  await page.goto(schedule);
  for (const width of [360, 390, 768, 1280]) {
    await page.setViewportSize({ width, height: 900 });
    await expect(row(page)).toContainText('Бронь подтверждена');
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    await row(page).getByRole('button', { name: 'Подключить кабинет' }).click();
    const dialog = page.getByRole('dialog');
    await expect(dialog).toBeVisible();
    await page.keyboard.press('Tab');
    expect(
      await page.evaluate(
        () => !!document.activeElement?.closest('[role="dialog"]'),
      ),
    ).toBe(true);
    await page.keyboard.press('Escape');
    await expect(dialog).toHaveCount(0);
    await expect(
      row(page).getByRole('button', { name: 'Подключить кабинет' }),
    ).toBeFocused();
    await page.screenshot({
      path: `.artifacts/f014-${width}.png`,
      fullPage: true,
    });
  }
  await page.getByRole('button', { name: 'Открыть время для записи' }).click();
  await page.getByLabel('Дата занятия', { exact: true }).click();
  await expect(
    page.getByRole('button', { name: 'Следующий месяц', exact: true }),
  ).toBeVisible();
  await page.keyboard.press('Escape');
  await page.getByRole('button', { name: 'Открыть время для записи' }).click();
  await page.evaluate(() => (document.documentElement.style.zoom = '2'));
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await row(page).getByRole('button', { name: 'Подключить кабинет' }).click();
  await expect(page.getByRole('dialog')).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await page.keyboard.press('Escape');
  await page.evaluate(() => (document.documentElement.style.zoom = '1'));
  const results = await new AxeBuilder({ page })
    .include('[aria-label="Запись и брони"]')
    .analyze();
  expect(results.violations.map((v) => v.id)).toEqual([]);
});
test('F01.4 active User self-link uses the same account, no activation invitation', async ({
  page,
}) => {
  test.setTimeout(90000);
  await login(page, note.accounts.student);
  await page.goto('/profile');
  await page.getByText('Связь с записью', { exact: true }).click();
  await page
    .getByLabel('Текущий пароль для подтверждения связи')
    .fill(note.accounts.student.password);
  // Select exactly the fixture source, not another additive test source.
  await page
    .getByRole('combobox', { name: 'Источник записи', exact: true })
    .click();
  const option = page.getByRole('option').filter({ hasText: 'f014-' });
  await option.click();
  await page.getByRole('button', { name: 'Получить код связи' }).click();
  await page
    .getByRole('dialog')
    .getByRole('button', { name: 'Подтвердить', exact: true })
    .click();
  const secret = await page.getByLabel('Одноразовый код связи').inputValue();
  expect(secret.length).toBeGreaterThan(31);
  const claimed = spawnSync(
    '.venv/bin/python',
    ['scripts/f014_preview.py', 'claim'],
    {
      cwd: '..',
      input: JSON.stringify({ secret }),
      env: { ...process.env, PYTHONPATH: '.' },
      encoding: 'utf8',
    },
  );
  expect(claimed.status, claimed.stderr).toBe(0);
  await page.getByRole('button', { name: 'Обновить состояние связи' }).click();
  await page
    .getByLabel('Текущий пароль для подтверждения связи')
    .fill(note.accounts.student.password);
  await page.getByRole('button', { name: 'Подтвердить свою связь' }).click();
  await page
    .getByRole('dialog')
    .getByRole('button', { name: 'Подтвердить', exact: true })
    .click();
  await expect(
    page.getByText('Связь подтверждена.', { exact: true }),
  ).toBeVisible();
});

test('F01.4 existing User materialization and own student context across dates', async ({
  page,
  browser,
}) => {
  test.setTimeout(90000);
  const token = await login(page);
  await page.goto(schedule);
  await expect(row(page, 2)).toContainText('Кабинет подключён');
  await row(page, 2)
    .getByRole('button', { name: 'Подключить кабинет' })
    .click();
  const dialog = page.getByRole('dialog');
  await expect(dialog).toContainText('Аккаунт уже активирован');
  await dialog.getByLabel('Проверил адресата и область доступа').check();
  await dialog
    .getByRole('button', { name: 'Выдать доступ', exact: true })
    .click();
  await expect(
    row(page, 2).getByRole('link', { name: 'Открыть занятие' }),
  ).toBeVisible();
  await expect(page.getByLabel('Ссылка приглашения')).toHaveCount(0);
  const own = await page.request.get(
    `/api/teacher-planning/linked-bookings?connection_id=${note.connection}&student_user_id=${note.ids.student}`,
    { headers: { Authorization: `Bearer ${token}` } },
  );
  expect(own.status()).toBe(200);
  const body = await own.json();
  expect(body.items[0].booking_id).toBe(note.bookings[2].booking_id);
  expect(body.items[0].recipient.linked_student_user_id).toBe(note.ids.student);
  await row(page, 2)
    .getByRole('link', { name: 'К ученику', exact: true })
    .click();
  await expect(
    page.getByRole('heading', { name: 'Связь с записью' }),
  ).toBeVisible();
  await expect(row(page, 2)).toContainText('Бронь подтверждена');
  const foreignContext = await browser.newContext({
    baseURL: 'http://127.0.0.1:5174',
  });
  const foreignPage = await foreignContext.newPage();
  const foreignToken = await login(foreignPage, note.accounts.teacher2);
  const foreign = await foreignPage.request.get(
    `/api/teacher-planning/linked-bookings?connection_id=${note.connection}&student_user_id=${note.ids.student}`,
    { headers: { Authorization: `Bearer ${foreignToken}` } },
  );
  expect(foreign.status()).toBe(200);
  expect((await foreign.json()).items).toEqual([]);
  await foreignContext.close();
});

test('F01.4 loading empty long error offline stale denied and unknown receipt', async ({
  page,
  context,
}) => {
  test.setTimeout(120000);
  await login(page);
  let state = 'long';
  let posts = 0;
  let release = () => {};
  const hold = new Promise<void>((r) => {
    release = r;
  });
  await page.route('**/api/teacher-planning/bookings?*', async (route) => {
    if (state === 'loading') await hold;
    if (state === 'error') return route.fulfill({ status: 503, json: {} });
    if (state === 'empty')
      return route.fulfill({ json: { items: [], next_cursor: null } });
    const response = await route.fetch();
    const body = await response.json();
    if (state === 'long')
      for (const b of body.items) {
        b.recipient.first_name = 'Александра-Екатерина';
        b.recipient.last_name = 'Константинопольская-Долгорукова';
      }
    return route.fulfill({ response, json: body });
  });
  await page.goto(schedule);
  await page.setViewportSize({ width: 360, height: 850 });
  await expect(row(page)).toContainText('Константинопольская-Долгорукова');
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  state = 'empty';
  await page.reload();
  await expect(page.getByText('Броней на эту неделю пока нет.')).toBeVisible();
  state = 'loading';
  await page.reload();
  await expect(
    page.locator('[aria-label="Запись и брони"] [aria-busy="true"]').first(),
  ).toBeVisible();
  release();
  state = 'error';
  await page.reload();
  await expect(page.locator('[aria-label="Запись и брони"]')).toContainText(
    'Попробуйте ещё раз',
    { timeout: 15000 },
  );
  state = 'real';
  await page.reload();
  await expect(row(page)).toContainText('Приёмка');
  await page.route(
    '**/api/teacher-planning/bookings/*/resolve-invite',
    async (route) => {
      posts++;
      return route.fulfill({ status: 409, json: { code: 'STALE_REVISION' } });
    },
  );
  await row(page).getByRole('button', { name: 'Подключить кабинет' }).click();
  let dialog = page.getByRole('dialog');
  await dialog
    .getByLabel(
      'Проверил прошедшие брони этого ребёнка; разрешаю добавить их в историю',
    )
    .check();
  await dialog.getByLabel('Проверил адресата и область доступа').check();
  await dialog
    .getByRole('button', { name: 'Выдать доступ', exact: true })
    .click();
  await expect(dialog).toContainText('Данные изменились');
  await expect(
    dialog.getByLabel('Проверил адресата и область доступа'),
  ).toBeChecked();
  expect(posts).toBe(1);
  await dialog
    .getByRole('button', { name: 'Обновить данные, сохранив введённое' })
    .click();
  await expect(dialog).toContainText('Данные обновлены');
  expect(posts).toBe(1);
  await page.keyboard.press('Escape');
  await row(page).getByRole('button', { name: 'Подключить кабинет' }).click();
  dialog = page.getByRole('dialog');
  await dialog.getByLabel('Проверил адресата и область доступа').check();
  await context.setOffline(true);
  await dialog
    .getByRole('button', { name: 'Выдать доступ', exact: true })
    .click();
  await expect(dialog).toContainText('Нет связи');
  expect(posts).toBe(1);
  await context.setOffline(false);
  await page.keyboard.press('Escape');
  await page.unroute('**/api/teacher-planning/bookings/*/resolve-invite');
  await page.route(
    '**/api/teacher-planning/bookings/*/resolve-invite',
    (route) => {
      posts++;
      return route.abort();
    },
  );
  await page.route('**/api/users/me/integrations/vk/operations/*', (route) =>
    route.fulfill({ status: 404, json: { code: 'NOT_FOUND' } }),
  );
  await row(page).getByRole('button', { name: 'Подключить кабинет' }).click();
  dialog = page.getByRole('dialog');
  await dialog.getByLabel('Проверил адресата и область доступа').check();
  await dialog
    .getByRole('button', { name: 'Выдать доступ', exact: true })
    .click();
  await dialog.getByRole('button', { name: 'Проверить результат' }).click();
  await expect(dialog).toContainText('Результат пока неизвестен');
  expect(posts).toBe(2);
  await page.keyboard.press('Escape');
  await row(page).getByRole('button', { name: 'Подключить кабинет' }).click();
  await expect(
    page.getByRole('button', { name: 'Проверить результат' }),
  ).toBeVisible();
  expect(posts).toBe(2);
  await page.keyboard.press('Escape');
  // Capability permission changes affect controls, while confirmed calendar rows remain.
  await page.route('**/api/teacher-planning/booking-capabilities', (route) =>
    route.fulfill({ status: 403, json: {} }),
  );
  await page.reload();
  await expect(
    page.getByText('Нет доступа к этому материалу').first(),
  ).toBeVisible();
});

test('F01.4 archive, same-User reauth draft and expired invitation states', async ({
  page,
  browser,
}) => {
  test.setTimeout(90000);
  await login(page);
  let posts = 0;
  await page.route('**/api/teacher-planning/bookings?*', async (route) => {
    const response = await route.fetch();
    const body = await response.json();
    for (const b of body.items)
      if (b.booking_id === note.bookings[0].booking_id)
        b.access_state = 'blocked';
    return route.fulfill({ response, json: body });
  });
  await page.goto(schedule);
  await expect(row(page)).toContainText('Доступ закрыт или курс в архиве');
  await expect(
    row(page).getByRole('button', { name: 'Подключить кабинет' }),
  ).toHaveCount(0);
  await page.unroute('**/api/teacher-planning/bookings?*');
  await page.reload();
  await row(page).getByRole('button', { name: 'Подключить кабинет' }).click();
  let dialog = page.getByRole('dialog');
  await dialog.getByLabel('Проверил адресата и область доступа').check();
  await page.route('**/api/teacher-planning/bookings/*/resolve-invite', (r) => {
    posts++;
    return r.fulfill({ status: 401, json: {} });
  });
  await page.route('**/api/auth/browser/refresh', (r) =>
    r.fulfill({ status: 401, json: {} }),
  );
  await dialog
    .getByRole('button', { name: 'Выдать доступ', exact: true })
    .click();
  const reauth = page.getByRole('dialog', { name: 'Войдите снова' });
  await expect(reauth).toBeVisible();
  await reauth
    .getByLabel('Логин', { exact: true })
    .fill(note.accounts.teacher.username);
  await reauth
    .getByLabel('Пароль', { exact: true })
    .fill(note.accounts.teacher.password);
  await reauth.getByRole('button', { name: 'Войти', exact: true }).click();
  await expect(reauth).toHaveCount(0);
  dialog = page.getByRole('dialog');
  await expect(
    dialog.getByLabel('Проверил адресата и область доступа'),
  ).toBeChecked();
  await expect(
    dialog.getByRole('button', { name: 'Проверить результат' }),
  ).toBeVisible();
  expect(posts).toBe(1);
  const expiredContext = await browser.newContext({
    baseURL: 'http://127.0.0.1:5174',
  });
  const expiredPage = await expiredContext.newPage();
  await expiredPage.route('**/api/account_invitations/consume', (r) =>
    r.fulfill({ status: 410, json: {} }),
  );
  await expiredPage.goto('/activate#token=f014-expired-synthetic-only');
  await expiredPage
    .getByLabel('Новый пароль', { exact: true })
    .fill('F014-expired-only-123');
  await expiredPage
    .getByLabel('Повторите пароль', { exact: true })
    .fill('F014-expired-only-123');
  await expiredPage
    .getByRole('button', { name: 'Сохранить пароль', exact: true })
    .click();
  await expect(expiredPage.getByRole('alert')).toContainText(
    'Ссылка недействительна или уже использована',
  );
  await expiredContext.close();
});
