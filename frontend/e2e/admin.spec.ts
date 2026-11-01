import { test, expect, type Page } from '@playwright/test';
import { readFileSync, existsSync, chmodSync } from 'node:fs';
import AxeBuilder from '@axe-core/playwright';
const credentials = JSON.parse(
  readFileSync('.artifacts/t15c1-credentials.json', 'utf8'),
);
test.use({ trace: 'off', screenshot: 'off', video: 'off' });
const adminPages = new WeakSet<Page>();
test.afterEach(async ({ page }) => {
  if (
    adminPages.has(page) &&
    new URL(page.url()).pathname.startsWith('/admin/')
  ) {
    await page
      .context()
      .storageState({ path: '.artifacts/t15c1-admin-state.json' });
    chmodSync('.artifacts/t15c1-admin-state.json', 0o600);
  }
});
async function login(page: Page, key = 'admin') {
  if (key === 'admin') adminPages.add(page);
  else adminPages.delete(page);
  if (key === 'admin' && existsSync('.artifacts/t15c1-admin-state.json')) {
    const state = JSON.parse(
      readFileSync('.artifacts/t15c1-admin-state.json', 'utf8'),
    );
    await page.context().addCookies(state.cookies);
    const refresh = page.waitForResponse((r) =>
      r.url().endsWith('/auth/browser/refresh'),
    );
    await page.goto('/admin/users');
    const response = await refresh;
    if (response.ok()) {
      const token = (await response.json()).access_token;
      const me = await page.request.get('/api/users/me', {
        headers: { Authorization: `Bearer ${token}` },
      });
      if (me.ok() && (await me.json()).id === credentials.admin.id) {
        await expect(page).toHaveURL('/admin/users');
        return { Authorization: `Bearer ${token}` };
      }
    }
    await page.context().clearCookies();
  }
  await page.goto('/login');
  await page
    .getByLabel('Логин', { exact: true })
    .fill(credentials[key].username);
  await page
    .getByLabel('Пароль', { exact: true })
    .fill(credentials[key].password);
  const result = page.waitForResponse(
    (r) =>
      r.url().endsWith('/auth/browser/login') &&
      r.request().method() === 'POST',
  );
  await page.getByRole('button', { name: 'Войти', exact: true }).click();
  const token = (await (await result).json()).access_token;
  await expect(page).toHaveURL(
    key === 'admin'
      ? '/admin/users'
      : key === 'student'
        ? '/student'
        : '/teacher',
  );
  return { Authorization: `Bearer ${token}` };
}
async function issue(page: Page, name: string) {
  await page.getByRole('button', { name, exact: true }).click();
  await page
    .getByRole('dialog')
    .getByRole('button', { name: 'Выдать ссылку', exact: true })
    .click();
}
test('real API create, activation/reset, shared links, account status, quota and audit', async ({
  page,
}) => {
  test.setTimeout(90000);
  const headers = await login(page);
  const api = async (path: string, method = 'GET', data?: unknown) => {
    const response = await page.request.fetch('/api' + path, {
      method,
      headers,
      data,
    });
    expect(response.ok(), `API ${method} ${path}`).toBe(true);
    return response.status() === 204 ? undefined : response.json();
  };
  const unique = 't15c1_ui_' + Date.now();
  for (const role of ['teacher', 'student']) {
    await page.goto('/admin/users/new');
    await page
      .getByRole('combobox', { name: 'Роль нового пользователя', exact: true })
      .click();
    await page
      .getByRole('option', {
        name: role === 'teacher' ? 'Преподаватель' : 'Ученик',
        exact: true,
      })
      .click();
    await page.getByLabel('Логин', { exact: true }).fill(unique + role);
    await page.getByLabel('Имя', { exact: true }).fill('Синтетический');
    await page.getByLabel('Фамилия', { exact: true }).fill('Пользователь');
    const response = page.waitForResponse(
      (r) =>
        r.url().endsWith('/auth/register_by_admin') &&
        r.request().method() === 'POST',
    );
    await page
      .getByRole('button', { name: 'Создать пользователя', exact: true })
      .click();
    const created = await (await response).json();
    await expect(page.getByRole('dialog')).toContainText('Действует до');
    await expect(page.getByLabel('Ссылка приглашения')).toBeVisible();
    const raw = created.activation_link.split('#token=')[1];
    const consume = await page.request.post(
      '/api/account_invitations/consume',
      {
        data: {
          token: raw,
          purpose: 'invite',
          new_password: credentials.student.password,
        },
      },
    );
    expect(consume.ok()).toBe(true);
    await page
      .getByRole('dialog')
      .getByRole('button', { name: 'Готово', exact: true })
      .click();
    const user = await api(`/admin/users/${created.id}`);
    expect(user.is_activated).toBe(true);
    await page.goto(`/admin/users/${created.id}`);
    await expect(
      page.getByRole('button', {
        name: 'Выдать ссылку сброса пароля',
        exact: true,
      }),
    ).toBeEnabled();
  }
  const { teacher, other, student } = credentials;
  await api('/teacher_students', 'POST', {
    teacher_user_id: teacher.id,
    student_user_id: student.id,
  });
  await page.goto(`/admin/users/${student.id}`);
  await page
    .getByText('Подключить существующего ученика', { exact: true })
    .click();
  await page
    .getByLabel('Поиск: преподаватель', { exact: true })
    .fill(other.username);
  await expect(page.getByText('Найдено: 1.', { exact: true })).toBeVisible();
  await page
    .getByRole('combobox', { name: 'Преподаватель', exact: true })
    .click();
  await page.getByRole('option', { name: new RegExp(other.username) }).click();
  await page
    .getByRole('button', { name: 'Проверить и подключить', exact: true })
    .click();
  await expect(page.getByRole('dialog')).toContainText(other.username);
  await page
    .getByRole('dialog')
    .getByRole('button', { name: 'Подключить ученика', exact: true })
    .click();
  await expect(
    page.getByRole('button', {
      name: `Завершить связь с ${other.username}`,
      exact: true,
    }),
  ).toBeVisible();
  await api('/teacher_students', 'POST', {
    teacher_user_id: other.id,
    student_user_id: student.id,
  });
  expect(
    (await api(`/teacher_students?student_user_id=${student.id}&active=true`))
      .total,
  ).toBe(2);
  await page
    .getByRole('button', {
      name: `Завершить связь с ${teacher.username}`,
      exact: true,
    })
    .click();
  await expect(page.getByRole('dialog')).toContainText(
    'другого преподавателя продолжат работать',
  );
  await page
    .getByRole('dialog')
    .getByRole('button', { name: 'Отмена', exact: true })
    .press('Enter');
  await expect(
    page.getByRole('button', {
      name: `Завершить связь с ${teacher.username}`,
      exact: true,
    }),
  ).toBeFocused();
  await page
    .getByRole('button', {
      name: `Завершить связь с ${teacher.username}`,
      exact: true,
    })
    .click();
  await page
    .getByRole('dialog')
    .getByRole('button', { name: 'Завершить связь', exact: true })
    .click();
  await expect(
    page.getByRole('button', {
      name: `Завершить связь с ${teacher.username}`,
      exact: true,
    }),
  ).toHaveCount(0);
  expect(
    (await api(`/teacher_students?student_user_id=${student.id}&active=true`))
      .items[0].teacher_user_id,
  ).toBe(other.id);
  expect((await api(`/admin/users/${student.id}`)).is_active).toBe(true);
  await issue(page, 'Выдать ссылку сброса пароля');
  await expect(page.getByLabel('Ссылка сброса пароля')).toBeVisible();
  await page.evaluate(() => {
    Object.defineProperty(navigator, 'clipboard', {
      configurable: true,
      value: { writeText: () => Promise.reject(new Error('denied')) },
    });
  });
  await page
    .getByRole('button', { name: 'Скопировать ссылку', exact: true })
    .click();
  await expect(page.getByRole('dialog')).toContainText('скопируйте её вручную');
  const resetLink = await page.getByLabel('Ссылка сброса пароля').inputValue();
  const reset = await page.request.post('/api/account_invitations/consume', {
    data: {
      token: resetLink.split('#token=')[1],
      purpose: 'reset',
      new_password: student.password,
    },
  });
  expect(reset.ok()).toBe(true);
  await page
    .getByRole('dialog')
    .getByRole('button', { name: 'Готово', exact: true })
    .click();
  await page.getByText('Редактировать профиль', { exact: true }).click();
  await page.getByLabel('Имя', { exact: true }).fill('Обновлённый');
  const patch = page.waitForRequest(
    (r) => r.method() === 'PATCH' && r.url().endsWith(`/users/${student.id}`),
  );
  await page
    .getByRole('button', { name: 'Сохранить профиль', exact: true })
    .click();
  expect((await patch).postDataJSON()).not.toHaveProperty('role');
  await expect(page.getByRole('heading', { level: 1 })).toContainText(
    'Обновлённый',
  );
  await page
    .getByRole('button', { name: 'Заблокировать общий аккаунт', exact: true })
    .click();
  await expect(page.getByRole('dialog')).toContainText('Все сессии');
  await page
    .getByRole('dialog')
    .getByRole('button', { name: 'Заблокировать аккаунт', exact: true })
    .click();
  await expect(
    page.getByRole('button', {
      name: 'Выдать ссылку сброса пароля',
      exact: true,
    }),
  ).toBeDisabled();
  expect((await api(`/admin/users/${student.id}`)).is_active).toBe(false);
  await page
    .getByRole('button', { name: 'Включить общий аккаунт', exact: true })
    .click();
  await page
    .getByRole('dialog')
    .getByRole('button', { name: 'Включить аккаунт', exact: true })
    .click();
  await expect(
    page.getByRole('button', {
      name: 'Заблокировать общий аккаунт',
      exact: true,
    }),
  ).toBeVisible();
  await page.getByText('Изменить лимит места', { exact: true }).click();
  await page
    .getByRole('combobox', { name: 'Единица измерения', exact: true })
    .click();
  await page.getByRole('option', { name: 'МБ', exact: true }).click();
  await page.getByLabel('Новый лимит', { exact: true }).fill('19');
  await expect(
    page.getByRole('button', { name: 'Проверить новый лимит', exact: true }),
  ).toBeDisabled();
  await page.getByLabel('Новый лимит', { exact: true }).fill('32');
  await page
    .getByRole('button', { name: 'Проверить новый лимит', exact: true })
    .click();
  await page
    .getByRole('dialog')
    .getByRole('button', { name: 'Изменить лимит места', exact: true })
    .click();
  await expect(page.getByText('Лимит изменён', { exact: true })).toBeVisible();
  expect((await api(`/users/${student.id}/storage`)).limit_bytes).toBe(
    32_000_000,
  );
  const audits = (
    await api(`/audit-events?actor_user_id=${credentials.admin.id}&limit=100`)
  ).items;
  for (const action of [
    'account_create',
    'profile_update',
    'teacher_student_link',
    'teacher_student_end',
    'account_status',
    'file_quota',
    'reset_issued',
    'reset_consumed',
  ]) {
    if (action === 'reset_consumed') continue; // consume is audited as target actor, separately from issuer
    expect(
      audits.some((a: { action: string }) => a.action === action),
      action,
    ).toBe(true);
  }
  expect(JSON.stringify(audits)).not.toContain('activation_link');
  for (const width of [1280, 360]) {
    await page.setViewportSize({ width, height: 900 });
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
    await page.screenshot({
      path: `.artifacts/t15c1-user-${width}.png`,
      fullPage: true,
    });
  }
});
test('read resilience, no results, URL filters, null invitation, mobile select and permission403', async ({
  page,
}) => {
  test.setTimeout(60000);
  const headers = await login(page);
  let fail = true;
  await page.route('**/api/admin/users?*', (route) =>
    fail
      ? route.fulfill({ status: 503, json: { detail: 'synthetic' } })
      : route.continue(),
  );
  await page.goto('/admin/users?role=student&is_active=true');
  await expect(
    page.getByRole('button', { name: 'Повторить', exact: true }),
  ).toBeVisible();
  fail = false;
  await page.getByRole('button', { name: 'Повторить', exact: true }).click();
  await expect(
    page.getByRole('list', { name: 'Пользователи', exact: true }),
  ).toBeVisible();
  await page.getByLabel('Поиск по имени или логину').fill('no_such_t15c1_user');
  await expect(
    page.getByText('Ничего не найдено. Очистите поиск или измените фильтры.'),
  ).toBeVisible();
  expect(page.url()).not.toContain('no_such');
  await page
    .getByRole('button', {
      name: 'Очистить: Поиск по имени или логину',
      exact: true,
    })
    .click();
  await expect(page.getByLabel('Поиск по имени или логину')).toBeFocused();
  await page.setViewportSize({ width: 360, height: 900 });
  await page.getByRole('combobox', { name: 'Роль', exact: true }).click();
  await expect(page.getByRole('listbox')).toBeVisible();
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  await page.keyboard.press('Escape');
  await page.goto(`/admin/users/${credentials.student.id}`);
  await page.route('**/api/account_invitations/issue', (route) =>
    route.fulfill({
      status: 200,
      json: { activation_link: null, expires_at: null },
    }),
  );
  await issue(page, 'Выдать ссылку сброса пароля');
  await expect(page.getByRole('dialog')).toContainText(
    'Приглашение недоступно',
  );
  await expect(page.getByLabel('Ссылка сброса пароля')).toHaveCount(0);
  await page
    .getByRole('dialog')
    .getByRole('button', { name: 'Готово', exact: true })
    .click();
  await page.getByText('Редактировать профиль', { exact: true }).click();
  const nameInput = page.getByLabel('Имя', { exact: true });
  const originalName = await nameInput.inputValue();
  await nameInput.fill('Черновик администратора');
  await page.route(`**/api/users/${credentials.student.id}`, (route) =>
    route.request().method() === 'PATCH'
      ? route.fulfill({ status: 409, json: { detail: 'Conflict' } })
      : route.continue(),
  );
  await page
    .getByRole('button', { name: 'Сохранить профиль', exact: true })
    .click();
  await expect(page.getByLabel('Логин', { exact: true })).toBeFocused();
  await expect(nameInput).toHaveValue('Черновик администратора');
  await page.unroute(`**/api/users/${credentials.student.id}`);

  await page.route(`**/api/users/${credentials.student.id}`, (route) =>
    route.request().method() === 'PATCH'
      ? route.fulfill({
          status: 422,
          json: {
            detail: [
              {
                loc: ['body', 'first_name'],
                msg: 'invalid',
                type: 'value_error',
              },
            ],
          },
        })
      : route.continue(),
  );
  await page
    .getByRole('button', { name: 'Сохранить профиль', exact: true })
    .click();
  await expect(nameInput).toBeFocused();
  await expect(nameInput).toHaveValue('Черновик администратора');
  await page.unroute(`**/api/users/${credentials.student.id}`);
  await page.route(`**/api/users/${credentials.student.id}`, (route) =>
    route.request().method() === 'PATCH'
      ? route.abort('failed')
      : route.continue(),
  );
  await page
    .getByRole('button', { name: 'Сохранить профиль', exact: true })
    .click();
  await expect(
    page.getByRole('button', { name: 'Сохранить профиль', exact: true }),
  ).toBeDisabled();
  await expect(nameInput).toHaveValue('Черновик администратора');
  await page.unroute(`**/api/users/${credentials.student.id}`);
  await page
    .getByRole('button', {
      name: 'Перечитать данные перед повтором',
      exact: true,
    })
    .click();
  await expect(
    page.getByRole('button', { name: 'Сохранить профиль', exact: true }),
  ).toBeEnabled();
  await page
    .getByRole('main')
    .getByRole('link', { name: 'Пользователи', exact: true })
    .click();
  await expect(
    page.getByRole('dialog', { name: 'Уйти без сохранения?', exact: true }),
  ).toBeVisible();
  await page
    .getByRole('dialog')
    .getByRole('button', { name: 'Отмена', exact: true })
    .click();
  await expect(nameInput).toHaveValue('Черновик администратора');
  await nameInput.fill(originalName);
  await page.route(
    `**/api/users/${credentials.student.id}/account-status`,
    (route) => route.fulfill({ status: 403, json: { detail: 'Forbidden' } }),
  );
  await page
    .getByRole('button', { name: 'Заблокировать общий аккаунт', exact: true })
    .click();
  await page
    .getByRole('dialog')
    .getByRole('button', { name: 'Заблокировать аккаунт', exact: true })
    .click();
  await expect(page.getByRole('dialog').getByRole('alert')).toBeVisible();
  await page
    .getByRole('dialog')
    .getByRole('button', { name: 'Отмена', exact: true })
    .click();
  await page.unroute(`**/api/users/${credentials.student.id}/account-status`);
  const bad = await page.request.patch(`/api/users/${credentials.student.id}`, {
    headers,
    data: { role: 'admin' },
  });
  expect(bad.status()).toBe(422);
  await page.getByRole('button', { name: 'Выйти', exact: true }).click();
  const logoutDialog = page.getByRole('dialog', {
    name: 'Выйти из кабинета?',
    exact: true,
  });
  if (await logoutDialog.isVisible())
    await logoutDialog
      .getByRole('button', { name: 'Выйти', exact: true })
      .click();
  await expect(page).toHaveURL(/\/login(?:\?|$)/);
  const studentHeaders = await login(page, 'student');
  for (const path of ['/admin/users', '/teacher_students', '/audit-events']) {
    const denied = await page.request.get('/api' + path, {
      headers: studentHeaders,
    });
    expect(denied.status()).toBe(403);
  }
  await page.goto('/admin/users');
  await expect(
    page.getByRole('heading', { name: 'Нет доступа', exact: true }),
  ).toBeVisible();
});
test('loading and teacher isolation after ending one shared link', async ({
  page,
}) => {
  const headers = await login(page);
  const path = `/admin/users/${credentials.student.id}`;
  let release: (() => void) | undefined;
  const held = new Promise<void>((resolve) => {
    release = resolve;
  });
  await page.route('**/api' + path, async (route) => {
    await held;
    await route.continue();
  });
  await page.goto(path);
  await expect(page.getByText('Загружаем…', { exact: true })).toBeVisible();
  release?.();
  await expect(page.getByRole('heading', { level: 1 })).toContainText(
    'Обновлённый',
  );
  await page.unroute('**/api' + path);
  const source = await page.request.get('/api/audit-events', {
    headers,
    params: { actor_user_id: credentials.student.id, action: 'reset_consumed' },
  });
  expect(source.ok()).toBe(true);
  expect((await source.json()).items.length).toBeGreaterThan(0);
  for (const key of ['teacher', 'other']) {
    const account = credentials[key];
    const response = await page.request.post('/api/auth/login', {
      form: { username: account.username, password: account.password },
    });
    expect(response.ok()).toBe(true);
    const tokens = await response.json();
    const auth = { Authorization: `Bearer ${tokens.access_token}` };
    const students = await page.request.get('/api/users/students', {
      headers: auth,
    });
    expect(students.ok()).toBe(true);
    const pupils = (await students.json()).items;
    expect(
      pupils.some(
        (u: { user_id: number }) => u.user_id === credentials.student.id,
      ),
    ).toBe(key === 'other');
    for (const [target, method, data] of [
      ['/admin/users', 'GET', undefined],
      [
        '/teacher_students',
        'POST',
        {
          teacher_user_id: account.id,
          student_user_id: credentials.student.id,
        },
      ],
      [
        `/admin/users/${credentials.student.id}/storage-quota`,
        'PATCH',
        { limit_bytes: 32 * 1024 ** 2 },
      ],
      [
        '/account_invitations/issue',
        'POST',
        { user_id: credentials.student.id, purpose: 'reset' },
      ],
    ] as const) {
      const denied = await page.request.fetch('/api' + target, {
        method,
        headers: auth,
        data,
      });
      expect(denied.status()).toBe(403);
    }
  }
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await page.setViewportSize({ width: 360, height: 900 });
  await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
});
