import { test, expect } from '@playwright/test';
import { readFileSync } from 'node:fs';
import AxeBuilder from '@axe-core/playwright';
const credentials = JSON.parse(
  readFileSync('.artifacts/t14e-credentials.json', 'utf8'),
);
test.use({ trace: 'off', screenshot: 'off', video: 'off' });
async function login(page: import('@playwright/test').Page, role = 'student') {
  await page.goto('/login');
  await page
    .getByLabel('Логин', { exact: true })
    .fill(credentials[role].username);
  await page
    .getByLabel('Пароль', { exact: true })
    .fill(credentials[role].password);
  await page.getByRole('button', { name: 'Войти', exact: true }).click();
  await expect(
    page.getByRole('heading', {
      name:
        role === 'student'
          ? 'Мой день'
          : role === 'teacher'
            ? 'Мой день'
            : 'Вход выполнен',
    }),
  ).toBeVisible();
}
test('three roles, reload, guard, cookie flags, logout', async ({
  page,
  context,
}) => {
  for (const role of ['student', 'teacher', 'admin']) {
    await login(page, role);
    expect(new URL(page.url()).pathname).toBe(
      role === 'teacher'
        ? '/teacher'
        : role === 'admin'
          ? '/admin/users'
          : '/student',
    );
    const cookie = (await context.cookies()).find(
      (c) => c.name === 'lgg_refresh',
    )!;
    expect(cookie.httpOnly).toBe(true);
    expect(cookie.path).toBe('/api/auth/browser');
    expect(cookie.sameSite).toBe('Lax');
    await page.reload();
    await expect(
      page.getByRole('heading', {
        name:
          role === 'student'
            ? 'Мой день'
            : role === 'teacher'
              ? 'Мой день'
              : 'Вход выполнен',
      }),
    ).toBeVisible();
    await page.goto(role === 'student' ? '/admin/users' : '/student');
    await expect(
      page.getByRole('heading', { name: 'Нет доступа' }),
    ).toBeVisible();
    await page.goto('/' + role);
    await page.getByRole('button', { name: 'Выйти', exact: true }).click();
    await expect(
      page.getByRole('button', { name: 'Войти', exact: true }),
    ).toBeVisible();
    expect(
      (await context.cookies()).some((c) => c.name === 'lgg_refresh'),
    ).toBe(false);
  }
});
test('two tabs simultaneous reload, logout broadcast and race', async ({
  page,
  context,
}) => {
  await login(page);
  const second = await context.newPage();
  await second.goto('/student');
  await expect(second.getByRole('heading', { name: 'Мой день' })).toBeVisible();
  await Promise.all([page.reload(), second.reload()]);
  for (const tab of [page, second])
    await expect(tab.getByRole('heading', { name: 'Мой день' })).toBeVisible();
  await Promise.all([
    page.getByRole('button', { name: 'Выйти', exact: true }).click(),
    second.reload(),
  ]);
  for (const tab of [page, second])
    await expect(
      tab.getByRole('button', { name: 'Войти', exact: true }),
    ).toBeVisible();
});
test('mobile keyboard, invalid credentials, offline, reduced motion, axe', async ({
  page,
  context,
}) => {
  await page.setViewportSize({ width: 360, height: 800 });
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await page.goto('/login');
  await page.getByRole('button', { name: 'Войти', exact: true }).click();
  await expect(page.getByLabel('Логин', { exact: true })).toBeFocused();
  const reveal = page.getByRole('button', {
    name: 'Показать пароль',
    exact: true,
  });
  const target = await reveal.boundingBox();
  expect(target!.width).toBeGreaterThanOrEqual(44);
  expect(target!.height).toBeGreaterThanOrEqual(44);
  await reveal.focus();
  await page.keyboard.press('Enter');
  await expect(
    page.getByRole('button', { name: 'Скрыть пароль', exact: true }),
  ).toBeFocused();
  await page.keyboard.press('Enter');
  await page
    .getByLabel('Логин', { exact: true })
    .fill('nonexistent-synthetic-' + Date.now());
  await page.keyboard.press('Tab');
  await page.keyboard.type('WrongSynthetic-123');
  await page.getByRole('button', { name: 'Войти', exact: true }).click();
  await expect(page.getByRole('alert')).toContainText('Неверный');
  await context.setOffline(true);
  await page.getByLabel('Пароль', { exact: true }).fill('WrongSynthetic-123');
  await page.getByRole('button', { name: 'Войти', exact: true }).click();
  await expect(page.getByRole('alert')).toBeVisible();
  await context.setOffline(false);
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
});
test('activation and reset fragment scrub, validation, consume and login', async ({
  page,
}) => {
  for (const purpose of ['invite', 'reset']) {
    await page.goto(credentials[purpose].url);
    expect(new URL(page.url()).hash).toBe('');
    await page.getByLabel('Новый пароль', { exact: true }).fill('Short');
    await page
      .getByLabel('Повторите пароль', { exact: true })
      .fill('different');
    await page.getByRole('button', { name: 'Сохранить пароль' }).click();
    await expect(page.getByRole('alert')).toContainText('8 символов');
    await page
      .getByLabel('Новый пароль', { exact: true })
      .fill('Synthetic-New-123');
    await page
      .getByLabel('Повторите пароль', { exact: true })
      .fill('Synthetic-New-123');
    await page.getByRole('button', { name: 'Сохранить пароль' }).click();
    await expect(
      page.getByRole('status').filter({ hasText: 'Пароль сохранён' }),
    ).toContainText('Пароль сохранён');
    await page.getByRole('link', { name: 'Перейти ко входу' }).click();
    await page
      .getByLabel('Логин', { exact: true })
      .fill(credentials[purpose].username);
    await page.getByLabel('Пароль', { exact: true }).fill('Synthetic-New-123');
    await page.getByRole('button', { name: 'Войти', exact: true }).click();
    await expect(page.getByRole('heading', { name: 'Мой день' })).toBeVisible();
    await page.getByRole('button', { name: 'Выйти', exact: true }).click();
    await expect(
      page.getByRole('button', { name: 'Войти', exact: true }),
    ).toBeVisible();
  }
});

test('concurrent 401 single-flight, repeated 401 reauth and same-user login', async ({
  page,
}) => {
  await login(page);
  let rotations = 0;
  page.on('request', (request) => {
    if (request.url().endsWith('/auth/browser/refresh')) rotations++;
  });
  let failures = 2;
  await page.route('**/api/users/me', async (route) => {
    if (failures-- > 0)
      await route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: '{}',
      });
    else await route.continue();
  });
  await page.evaluate(async () => {
    const modulePath = '/src/shared/api/client.ts';
    const { request } = await import(modulePath);
    await Promise.all([request('/users/me'), request('/users/me')]);
  });
  expect(rotations).toBe(1);
  await page.unroute('**/api/users/me');
  await page.route('**/api/users/me', (route) =>
    route.fulfill({ status: 401, contentType: 'application/json', body: '{}' }),
  );
  await page.evaluate(async () => {
    const modulePath = '/src/shared/api/client.ts';
    const { request } = await import(modulePath);
    await request('/users/me').catch(() => {});
  });
  await page.unroute('**/api/users/me');

  await expect(
    page.getByRole('heading', { name: 'Войдите снова' }),
  ).toBeVisible();
  await expect(page.getByLabel('Логин', { exact: true })).toBeFocused();
  await expect(page.locator('.mantine-Modal-content')).toHaveCSS(
    'opacity',
    '1',
  );
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  await page
    .getByLabel('Логин', { exact: true })
    .fill(credentials.student.username);
  await page
    .getByLabel('Пароль', { exact: true })
    .fill(credentials.student.password);
  await page.getByRole('button', { name: 'Войти', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Мой день' })).toBeVisible();
});

test('lost rotated cookie requires new login, no seamless recovery claim', async ({
  page,
  context,
}) => {
  await login(page);
  const old = (await context.cookies()).find((c) => c.name === 'lgg_refresh')!;
  await page.evaluate(async () => {
    const modulePath = '/src/features/auth/session.ts';
    const { session } = await import(modulePath);
    await session.refresh();
  });
  // Model the old cookie retained when Set-Cookie was lost after server commit.
  await context.addCookies([old]);
  await page.reload();
  await expect(
    page.getByRole('button', { name: 'Войти', exact: true }),
  ).toBeVisible();
});

test('no Web Locks fails closed', async ({ page }) => {
  await page.addInitScript(() =>
    Object.defineProperty(navigator, 'locks', { value: undefined }),
  );
  await page.goto('/student');
  await expect(page.getByRole('alert')).toContainText('современном браузере');
});

test('pending login blocks duplicate submit and preserves geometry', async ({
  page,
}) => {
  await page.goto('/login');
  let count = 0;
  let release!: () => void;
  const gate = new Promise<void>((resolve) => {
    release = resolve;
  });
  await page.route('**/api/auth/browser/login', async (route) => {
    count++;
    await gate;
    await route.continue();
  });
  await page
    .getByLabel('Логин', { exact: true })
    .fill(credentials.student.username);
  await page
    .getByLabel('Пароль', { exact: true })
    .fill(credentials.student.password);
  const submit = page.getByRole('button', { name: 'Войти', exact: true });
  const before = await submit.boundingBox();
  await submit.click();
  await expect(submit).toBeDisabled();
  expect((await submit.boundingBox())?.width).toBe(before?.width);
  await expect.poll(() => count).toBe(1);
  release();
  await expect(page.getByRole('heading', { name: 'Мой день' })).toBeVisible();
});

test('two tabs recover concurrent 401 without replaying shared cookie', async ({
  page,
  context,
}) => {
  await login(page);
  const second = await context.newPage();
  await second.goto('/student');
  await expect(second.getByRole('heading', { name: 'Мой день' })).toBeVisible();
  const failed = new Set();
  await context.route('**/api/users/me', async (route) => {
    const tab = route.request().frame().page();
    if (!failed.has(tab)) {
      failed.add(tab);
      await route.fulfill({
        status: 401,
        contentType: 'application/json',
        body: '{}',
      });
    } else await route.continue();
  });
  await Promise.all(
    [page, second].map((tab) =>
      tab.evaluate(async () => {
        const modulePath = '/src/shared/api/client.ts';
        const { request } = await import(modulePath);
        await request('/users/me');
      }),
    ),
  );
  await context.unroute('**/api/users/me');
  await Promise.all([page.reload(), second.reload()]);
  for (const tab of [page, second])
    await expect(tab.getByRole('heading', { name: 'Мой день' })).toBeVisible();
});

test('external returnTo stays at role destination', async ({ page }) => {
  await page.goto('/login?returnTo=https%3A%2F%2Fforeign.example%2F');
  await page
    .getByLabel('Логин', { exact: true })
    .fill(credentials.student.username);
  await page
    .getByLabel('Пароль', { exact: true })
    .fill(credentials.student.password);
  await page.getByRole('button', { name: 'Войти', exact: true }).click();
  await expect(page).toHaveURL('http://127.0.0.1:5173/student');
});
