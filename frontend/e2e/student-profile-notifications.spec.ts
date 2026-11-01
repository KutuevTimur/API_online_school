import { test, expect, type Page } from '@playwright/test';
import { readFileSync } from 'node:fs';
import AxeBuilder from '@axe-core/playwright';
const credentials = JSON.parse(
  readFileSync('.artifacts/t14e-credentials.json', 'utf8'),
);
test.use({ trace: 'off', screenshot: 'off', video: 'off' });
async function login(page: Page, key = 'profile_student', path = '/student') {
  await page.goto('/login?returnTo=' + encodeURIComponent(path));
  await page
    .getByLabel('Логин', { exact: true })
    .fill(credentials[key].username);
  await page
    .getByLabel('Пароль', { exact: true })
    .fill(credentials[key].password);
  await page.getByRole('button', { name: 'Войти', exact: true }).click();
  await expect(page).toHaveURL(path);
}
test('history entry, lesson materials and archive remain available, desktop/mobile keyboard', async ({
  page,
}) => {
  await login(page, 'profile_student', '/student/materials');
  await expect(
    page.getByRole('heading', { name: 'Мои занятия', exact: true }),
  ).toBeVisible();
  const fixture = credentials.student_profile;
  const lesson = fixture.lessons[0];
  await page.getByRole('combobox', { name: 'Курс', exact: true }).click();
  await page
    .getByRole('option', { name: /^Алгебра · учебный курс · / })
    .click();
  await expect(page).toHaveURL(/course_id=/);
  await page.reload();
  await expect(
    page.getByRole('heading', { name: 'История занятий', exact: true }),
  ).toBeVisible();
  await page.goto('/student/lessons/' + lesson.id);
  const open = page.getByRole('button', {
    name: 'Открыть Учебный пример.pdf',
    exact: true,
  });
  await open.click();
  await expect(
    page.getByRole('dialog').getByLabel('Страница 1', { exact: true }),
  ).toBeVisible();
  await page.keyboard.press('Escape');
  await expect(open).toBeFocused();
  const archived = fixture.lessons.find(
    (l: { archive: boolean; teacher_user_id: number }) =>
      l.archive && l.teacher_user_id === lesson.teacher_user_id,
  );
  await page.goto('/student/lessons/' + archived.id);
  await expect(page.getByText(/Только просмотр: Курс в архиве/)).toBeVisible();
  await page.setViewportSize({ width: 360, height: 800 });
  await expect(
    page.getByRole('button', {
      name: 'Открыть Учебный пример.pdf',
      exact: true,
    }),
  ).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  await page.goto('/student/materials?history-month=2099-01');
  await expect(page.getByText(/Занятий в этом месяце пока нет/)).toBeVisible();
  await page.goto('/student/materials/2147483647');
  await expect(
    page.getByText('Материал больше недоступен', { exact: true }),
  ).toBeVisible();
});
test('notifications explicit mark-read, unavailable target recovery, direct homework target and unread state', async ({
  page,
}) => {
  await login(page, 'profile_student', '/notifications');
  await expect(
    page.getByRole('heading', { name: 'Уведомления', exact: true }),
  ).toBeVisible();
  await expect(page.getByRole('article')).toHaveCount(2);
  const unavailable = page.getByRole('article').filter({
    has: page.getByRole('heading', { name: 'Занятие отменено', exact: true }),
  });
  await unavailable
    .getByRole('button', { name: 'Открыть уведомление' })
    .click();
  await expect(
    page.getByText(/Материал больше недоступен. Уведомление прочитано/),
  ).toBeVisible();
  await page
    .getByRole('article')
    .filter({
      has: page.getByRole('heading', {
        name: 'Назначено домашнее задание',
        exact: true,
      }),
    })
    .getByRole('button', { name: 'Открыть уведомление' })
    .click();
  await expect(page).toHaveURL(/\/student\/homeworks\/\d+/);
  await expect(page.getByRole('heading', { name: /Задание ·/ })).toBeVisible();
  await page.goto('/notifications?unread=1');
  await expect(
    page.getByText('Непрочитанных уведомлений нет.', { exact: true }),
  ).toBeVisible();
  // URL navigation commits in a React transition. uncheck() checks the DOM
  // synchronously, before the controlled value settles; assert the result instead.
  const unreadFilter = page.getByLabel('Только непрочитанные', { exact: true });
  await unreadFilter.click();
  await expect(page).toHaveURL(/unread=0/);
  await expect(unreadFilter).not.toBeChecked();
  await expect(
    page.getByRole('article').filter({ hasText: / · Прочитано/ }),
  ).toHaveCount(2);
  await page.screenshot({
    path: '.artifacts/checkup-notifications-desktop.png',
    fullPage: true,
  });
  await page.setViewportSize({ width: 360, height: 800 });
  await unreadFilter.focus();
  await page.keyboard.press('Space');
  await expect(page).toHaveURL(/unread=1/);
  await expect(unreadFilter).toBeChecked();
  await expect(
    page.getByText('Непрочитанных уведомлений нет.', { exact: true }),
  ).toBeVisible();
  await page.reload();
  await expect(unreadFilter).toBeChecked();
  await unreadFilter.click();
  await expect(page).toHaveURL(/unread=0/);
  await expect(unreadFilter).not.toBeChecked();
  await expect(page.getByRole('article')).toHaveCount(2);
  await page.screenshot({
    path: '.artifacts/t15a3-notifications-mobile.png',
    fullPage: true,
  });
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
});
test('profile real save, conflict preserves form, dirty navigation, avatar failure/replacement/delete404 and mobile', async ({
  page,
}) => {
  await login(page, 'profile_student', '/profile');
  const name = 'Synthetic ' + Date.now();
  await expect(page.getByLabel('Имя', { exact: true })).toBeVisible();
  await page.getByLabel('Имя', { exact: true }).fill(name);
  await page
    .getByRole('link', { name: 'Мой день', exact: true })
    .first()
    .click();
  await expect(
    page.getByRole('dialog', { name: 'Уйти без сохранения?' }),
  ).toBeVisible();
  await page.getByRole('button', { name: 'Отмена', exact: true }).click();
  await expect(page.getByLabel('Имя', { exact: true })).toHaveValue(name);
  await page
    .getByRole('button', { name: 'Сохранить профиль', exact: true })
    .click();
  await expect(
    page.getByRole('button', { name: 'Сохранить профиль', exact: true }),
  ).toBeDisabled();
  await page.reload();
  await expect(page.getByLabel('Имя', { exact: true })).toHaveValue(name);
  await page
    .getByLabel('Логин', { exact: true })
    .fill(credentials.read_student.username);
  await page
    .getByRole('button', { name: 'Сохранить профиль', exact: true })
    .click();
  await expect(
    page.getByText(/Логин или почта уже используются/).last(),
  ).toBeVisible();
  await expect(page.getByLabel('Логин', { exact: true })).toHaveValue(
    credentials.read_student.username,
  );
  await page
    .getByLabel('Логин', { exact: true })
    .fill(credentials.profile_student.username);
  await page
    .getByLabel('Новый аватар', { exact: true })
    .setInputFiles('e2e/fixtures/notebook.png');
  await expect(
    page.getByText('Аватар обновлён', { exact: true }),
  ).toBeVisible();
  const avatar = page.getByRole('img', { name: 'Ваш аватар' });
  await expect(avatar).toBeVisible();
  const oldSrc = await avatar.getAttribute('src');
  await page.route(/\/api\/users\/\d+$/, (route) =>
    route.fulfill({ status: 503, json: {} }),
  );
  await page.route('**/api/users/*/avatar', (route) =>
    route.request().method() === 'PATCH'
      ? route.fulfill({ status: 500, json: {} })
      : route.continue(),
  );
  await page
    .getByLabel('Новый аватар', { exact: true })
    .setInputFiles('e2e/fixtures/notebook.png');
  await expect(
    page.getByText(
      'Результат изменения неизвестен. Сначала проверьте аватар.',
      { exact: true },
    ),
  ).toBeVisible();
  await expect(avatar).toBeVisible();
  expect(oldSrc).toBeTruthy();
  await expect(page.getByLabel('Новый аватар', { exact: true })).toBeDisabled();
  await page.unroute(/\/api\/users\/\d+$/);
  await page.unroute('**/api/users/*/avatar');
  await page
    .getByRole('button', { name: 'Проверить аватар', exact: true })
    .click();
  await expect(page.getByLabel('Новый аватар', { exact: true })).toBeEnabled();
  await page.setViewportSize({ width: 360, height: 800 });
  await page.screenshot({
    path: '.artifacts/t15a3-profile-mobile.png',
    fullPage: true,
  });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  // A repeated delete has an unknown response; commit the real delete then return404.
  await page.route('**/api/users/*/avatar', async (route) => {
    if (route.request().method() === 'DELETE') {
      await route.fetch();
      await route.fulfill({ status: 404, json: {} });
    } else await route.continue();
  });
  await page
    .getByRole('button', { name: 'Удалить аватар', exact: true })
    .click();
  await page
    .getByRole('dialog')
    .getByRole('button', { name: 'Удалить аватар', exact: true })
    .click();
  await expect(
    page.getByText('Аватар уже удалён. Данные обновлены.', { exact: true }),
  ).toBeVisible();
  await expect(avatar).toHaveCount(0);
});
test('password wrong current preserves session, masked input, revoke and same-user reauth', async ({
  page,
  request,
}) => {
  await login(page, 'password_student', '/profile');
  const old = credentials.password_student.password;
  const next = 'Synthetic-T15a3-' + Date.now();
  await page
    .getByLabel('Текущий пароль', { exact: true })
    .fill('wrong-synthetic-password');
  await page.getByLabel('Новый пароль', { exact: true }).fill(next);
  await page.getByLabel('Повторите новый пароль', { exact: true }).fill(next);
  await expect(
    page.getByLabel('Новый пароль', { exact: true }),
  ).toHaveAttribute('type', 'password');
  await page
    .getByRole('button', { name: 'Изменить пароль', exact: true })
    .click();
  await expect(
    page.getByText('Текущий пароль неверен. Проверьте его.').last(),
  ).toBeVisible();
  await expect(page.getByRole('dialog', { name: 'Войдите снова' })).toHaveCount(
    0,
  );
  await page.getByLabel('Текущий пароль', { exact: true }).fill(old);
  await page
    .getByRole('button', { name: 'Изменить пароль', exact: true })
    .click();
  const modal = page.getByRole('dialog', { name: 'Войдите снова' });
  await expect(modal).toBeVisible();
  await modal
    .getByLabel('Логин', { exact: true })
    .fill(credentials.password_student.username);
  await modal.getByLabel('Пароль', { exact: true }).fill(next);
  await modal.getByRole('button', { name: 'Войти', exact: true }).click();
  await expect(modal).toHaveCount(0);
  await expect(page.getByLabel('Новый пароль', { exact: true })).toHaveValue(
    '',
  );
  // Restore this isolated synthetic account so the saved credentials remain current.
  const response = await request.post('/api/auth/login', {
    form: { username: credentials.password_student.username, password: next },
  });
  expect(response.status()).toBe(200);
  const token = (await response.json()).access_token;
  const me = await request.get('/api/users/me', {
    headers: { Authorization: 'Bearer ' + token },
  });
  expect(me.status()).toBe(200);
  const restored = await request.post(
    '/api/auth/change_password/' + (await me.json()).id,
    {
      headers: { Authorization: 'Bearer ' + token },
      data: { current_password: next, new_password: old },
    },
  );
  expect(restored.status()).toBe(200);
});
test('history courses and notification errors retry, slow loading, unavailable target404, admin avatar excluded', async ({
  page,
}) => {
  await login(page, 'read_empty', '/student/materials');
  await expect(
    page.getByRole('heading', { name: 'Курсов пока нет' }),
  ).toBeVisible();
  let fail = true;
  await page.route('**/api/courses?**', (route) =>
    fail ? route.fulfill({ status: 503, json: {} }) : route.continue(),
  );
  await page.reload();
  await expect(
    page.getByRole('button', { name: 'Повторить', exact: true }),
  ).toBeVisible();
  fail = false;
  await page.getByRole('button', { name: 'Повторить', exact: true }).click();
  await expect(
    page.getByRole('heading', { name: 'Курсов пока нет' }),
  ).toBeVisible();
  await page.route('**/api/notifications?**', async (route) => {
    await new Promise((resolve) => setTimeout(resolve, 500));
    await route.continue();
  });
  await page.goto('/notifications');
  await expect(page.getByText('Загружаем…', { exact: true })).toBeVisible();
  await expect(
    page.getByText('Уведомлений пока нет.', { exact: true }),
  ).toBeVisible();
  await page.getByRole('button', { name: 'Выйти', exact: true }).click();
  await login(page, 'admin', '/profile');
  await expect(
    page.getByRole('heading', { name: 'Учётная запись', exact: true }),
  ).toBeVisible();
  await expect(page).toHaveTitle('Профиль — LGG');
  await expect(page.getByLabel('Новый аватар', { exact: true })).toHaveCount(0);
});

test('profile uncertain save read-before-retry, same-user reauth preserves fields, logout clears profile', async ({
  page,
}) => {
  await login(page, 'profile_student', '/profile');
  const name = 'Synthetic recovery ' + Date.now();
  await page.getByLabel('Имя', { exact: true }).fill(name);
  await page.route('**/api/users/*', (route) =>
    route.request().method() === 'PATCH'
      ? route.fulfill({ status: 503, json: {} })
      : route.continue(),
  );
  await page
    .getByRole('button', { name: 'Сохранить профиль', exact: true })
    .click();
  await expect(
    page.getByRole('button', { name: 'Проверить сохранение', exact: true }),
  ).toBeVisible();
  await expect(page.getByLabel('Имя', { exact: true })).toHaveValue(name);
  await expect(
    page.getByRole('button', { name: 'Сохранить профиль', exact: true }),
  ).toBeDisabled();
  await page.unroute('**/api/users/*');
  await page
    .getByRole('button', { name: 'Проверить сохранение', exact: true })
    .click();
  await expect(
    page.getByRole('button', { name: 'Сохранить профиль', exact: true }),
  ).toBeEnabled();
  await page.route('**/api/users/*', (route) =>
    route.request().method() === 'PATCH'
      ? route.fulfill({ status: 401, json: {} })
      : route.continue(),
  );
  await page.route('**/api/auth/browser/refresh', (route) =>
    route.fulfill({ status: 401, json: {} }),
  );
  await page
    .getByRole('button', { name: 'Сохранить профиль', exact: true })
    .click();
  const modal = page.getByRole('dialog', { name: 'Войдите снова' });
  await expect(modal).toBeVisible();
  await page.unroute('**/api/users/*');
  await page.unroute('**/api/auth/browser/refresh');
  await modal
    .getByLabel('Логин', { exact: true })
    .fill(credentials.profile_student.username);
  await modal
    .getByLabel('Пароль', { exact: true })
    .fill(credentials.profile_student.password);
  await modal.getByRole('button', { name: 'Войти', exact: true }).click();
  await expect(modal).toHaveCount(0);
  await expect(page.getByLabel('Имя', { exact: true })).toHaveValue(name);
  await page
    .getByRole('button', { name: 'Проверить сохранение', exact: true })
    .click();
  await page
    .getByRole('button', { name: 'Сохранить профиль', exact: true })
    .click();
  await expect(
    page.getByRole('button', { name: 'Сохранить профиль', exact: true }),
  ).toBeDisabled();
  await page.screenshot({
    path: '.artifacts/t15a3-profile-desktop.png',
    fullPage: true,
  });
  await page.getByLabel('Имя', { exact: true }).fill('Unsaved synthetic');
  await page.getByRole('button', { name: 'Выйти', exact: true }).click();
  const logout = page.getByRole('dialog', { name: 'Выйти из кабинета?' });
  await expect(logout).toBeVisible();
  await logout.getByRole('button', { name: 'Выйти', exact: true }).click();
  await expect(
    page.getByRole('heading', { name: 'Вход в кабинет', exact: true }),
  ).toBeVisible();
  await login(page, 'read_empty', '/profile');
  await expect(page.getByLabel('Имя', { exact: true })).not.toHaveValue(
    'Unsaved synthetic',
  );
});
