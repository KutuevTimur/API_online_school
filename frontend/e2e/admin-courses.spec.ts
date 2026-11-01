import {
  test,
  expect,
  type Page,
  type APIRequestContext,
} from '@playwright/test';
import { readFileSync, existsSync, chmodSync } from 'node:fs';
import type { components } from '../src/shared/api/schema';
import AxeBuilder from '@axe-core/playwright';
const credentials = JSON.parse(
  readFileSync('.artifacts/t15c2-credentials.json', 'utf8'),
);
test.use({ trace: 'off', screenshot: 'off', video: 'off' });
let admin: Record<string, string>,
  teacher: Record<string, string>,
  student: Record<string, string>,
  other: Record<string, string>;
let course: components['schemas']['CoursesResponseDTO'],
  lesson: components['schemas']['LessonResponseDTO'],
  archived: components['schemas']['LessonResponseDTO'],
  file: components['schemas']['FileDescriptorDTO'];
async function api(
  request: APIRequestContext,
  path: string,
  headers = admin,
  method = 'GET',
  data?: unknown,
) {
  const r = await request.fetch('/api' + path, { method, headers, data });
  expect(r.ok(), `${method} ${path}: ${r.status()}`).toBe(true);
  return r.status() === 204 ? undefined : r.json();
}
test.afterEach(async ({ page }) => {
  if (new URL(page.url()).pathname.startsWith('/admin/')) {
    await page
      .context()
      .storageState({ path: '.artifacts/t15c2-admin-state.json' });
    chmodSync('.artifacts/t15c2-admin-state.json', 0o600);
  }
});
async function login(page: Page) {
  if (existsSync('.artifacts/t15c2-admin-state.json')) {
    const state = JSON.parse(
      readFileSync('.artifacts/t15c2-admin-state.json', 'utf8'),
    );
    await page.context().addCookies(state.cookies);
    const refreshed = page.waitForResponse((r) =>
      r.url().endsWith('/auth/browser/refresh'),
    );
    await page.goto('/admin/users');
    if ((await refreshed).ok()) {
      await expect(page).toHaveURL('/admin/users');
      return;
    }
    await page.context().clearCookies();
  }
  await page.goto('/login');
  await page
    .getByLabel('Логин', { exact: true })
    .fill(credentials.admin.username);
  await page
    .getByLabel('Пароль', { exact: true })
    .fill(credentials.admin.password);
  await page.getByRole('button', { name: 'Войти', exact: true }).click();
  await expect(page).toHaveURL('/admin/users');
}
async function disposable(request: APIRequestContext, suffix: string) {
  const target = await api(request, '/courses', teacher, 'POST', {
    name: `Одноразовый synthetic ${suffix} ${Date.now()}`,
    slug: 't15c2-' + suffix + Date.now(),
  });
  if (suffix === 'purge') {
    await api(request, `/courses/${target.id}/students`, teacher, 'POST', {
      student_user_id: credentials.student.id,
    });
    const item = await api(request, '/lessons', teacher, 'POST', {
      course_id: target.id,
      student_user_id: credentials.student.id,
      title: 'Disposable file lesson',
      scheduled_at: new Date(Date.UTC(2030, 0, target.id, 9)).toISOString(),
    });
    const r = await request.post('/api/lectures', {
      headers: teacher,
      multipart: {
        lesson_id: item.id,
        student_user_id: credentials.student.id,
        file: {
          name: 'disposable.pdf',
          mimeType: 'application/pdf',
          buffer: readFileSync('e2e/fixtures/math.pdf'),
        },
      },
    });
    expect(r.ok()).toBe(true);
    target.file = (await r.json()).file;
  }
  return target;
}
test.beforeAll(async ({ request }) => {
  for (const key of ['admin', 'teacher', 'student', 'other']) {
    const r = await request.post('/api/auth/login', {
      form: {
        username: credentials[key].username,
        password: credentials[key].password,
      },
    });
    expect(r.ok()).toBe(true);
    const headers = {
      Authorization: 'Bearer ' + (await r.json()).access_token,
    };
    if (key === 'admin') admin = headers;
    if (key === 'teacher') teacher = headers;
    if (key === 'student') student = headers;
    if (key === 'other') other = headers;
  }
  await api(request, '/teacher_students', admin, 'POST', {
    teacher_user_id: credentials.teacher.id,
    student_user_id: credentials.student.id,
  });
  course = await disposable(request, 'архив');
  await api(request, `/courses/${course.id}/students`, teacher, 'POST', {
    student_user_id: credentials.student.id,
  });
  lesson = await api(request, '/lessons', teacher, 'POST', {
    course_id: course.id,
    student_user_id: credentials.student.id,
    title: 'Материалы synthetic',
    scheduled_at: '2026-10-19T09:00:00Z',
  });
  archived = await api(request, '/lessons', teacher, 'POST', {
    course_id: course.id,
    student_user_id: credentials.student.id,
    title: 'Отдельный архив synthetic',
    scheduled_at: '2026-10-20T09:00:00Z',
  });
  const upload = await request.post('/api/lectures', {
    headers: teacher,
    multipart: {
      lesson_id: lesson.id,
      student_user_id: credentials.student.id,
      file: {
        name: 'synthetic.pdf',
        mimeType: 'application/pdf',
        buffer: readFileSync('e2e/fixtures/math.pdf'),
      },
    },
  });
  expect(upload.ok()).toBe(true);
  file = (await upload.json()).file;
  const hwResponse = await request.post('/api/homeworks', {
    headers: teacher,
    multipart: {
      lesson_id: lesson.id,
      student_user_id: credentials.student.id,
      title: 'Synthetic задание',
      description: 'Условие synthetic',
    },
  });
  expect(hwResponse.ok()).toBe(true);
  const hw = await hwResponse.json();
  const answer = await request.post(`/api/homeworks/${hw.id}/submissions`, {
    headers: student,
    multipart: { text_content: 'Synthetic ответ ученика' },
  });
  expect(answer.ok()).toBe(true);
  await api(request, `/lessons/${archived.id}`, teacher, 'DELETE');
  await api(request, `/courses/${course.id}`, teacher, 'DELETE');
});
test('archive read/download, restore course and lesson, explicit recipient, history and audit real API', async ({
  page,
  request,
}) => {
  await login(page);
  await page.goto(
    `/admin/courses?teacher=${credentials.teacher.id}&student=${credentials.student.id}&view=archive`,
  );
  await expect(
    page.locator(`a[href="/admin/courses/${course.id}"]`),
  ).toBeVisible();
  await page.locator(`a[href="/admin/courses/${course.id}"]`).click();
  await page.getByRole('link', { name: lesson.title }).click();
  await expect(page.getByText('Synthetic ответ ученика')).toHaveCount(0);
  await page.getByRole('combobox', { name: 'Получатель материалов' }).click();
  await page.getByRole('option').first().click();
  await expect(page.getByText('Synthetic ответ ученика')).toBeVisible();
  await page.getByRole('button', { name: 'Открыть synthetic.pdf' }).click();
  const download = page.waitForEvent('download');
  await page.getByRole('button', { name: /Скачать/ }).click();
  expect((await download).suggestedFilename()).toContain('.pdf');
  await page.keyboard.press('Escape');
  expect(
    (await request.get('/api' + file.download_url, { headers: student })).ok(),
  ).toBe(true);
  await page.goto(`/admin/courses/${course.id}`);
  await page
    .getByRole('button', { name: 'Восстановить курс', exact: true })
    .click();
  await expect(
    page
      .getByRole('dialog')
      .getByRole('button', { name: 'Отмена', exact: true }),
  ).toBeFocused();
  await page
    .getByRole('dialog')
    .getByRole('button', { name: 'Восстановить курс', exact: true })
    .click();
  await expect(page.getByRole('dialog')).toHaveCount(0);
  expect((await api(request, `/lessons/${archived.id}`)).is_deleted).toBe(true);
  await page.getByText('Ученики и доступ к истории', { exact: true }).click();
  await page
    .getByRole('button', { name: 'Отозвать доступ к истории', exact: true })
    .click();
  await expect(page.getByRole('dialog')).toContainText(
    String(credentials.student.id),
  );
  await page
    .getByRole('dialog')
    .getByRole('button', { name: 'Отозвать доступ', exact: true })
    .click();
  await expect(
    page.getByText('Доступ к истории отозван', { exact: true }),
  ).toBeVisible();
  expect(
    (
      await request.get('/api' + file.download_url, { headers: student })
    ).status(),
  ).toBe(404);
  await page
    .getByRole('button', { name: 'Вернуть доступ к истории', exact: true })
    .click();
  await page
    .getByRole('dialog')
    .getByRole('button', { name: 'Вернуть доступ', exact: true })
    .click();
  await expect(
    page.getByText('Доступ к истории разрешён', { exact: true }),
  ).toBeVisible();
  await page.goto(`/admin/lessons/${archived.id}`);
  await page
    .getByRole('button', { name: 'Восстановить занятие', exact: true })
    .click();
  await page
    .getByRole('dialog')
    .getByRole('button', { name: 'Восстановить занятие', exact: true })
    .click();
  await expect(page.getByText(/Занятие не архивировано/)).toBeVisible();
  await page.goto(`/admin/audit?actor=${credentials.admin.id}&action=restore`);
  await expect(page.getByRole('main')).toContainText(
    'Восстановление из архива',
  );
  const audit = await api(
    request,
    `/audit-events?actor_user_id=${credentials.admin.id}&action=restore`,
  );
  expect(audit.items.length).toBeGreaterThanOrEqual(2);
  expect(
    audit.items.every(
      (e: components['schemas']['AuditEventResponseDTO']) =>
        e.actor_user_id === credentials.admin.id && e.action === 'restore',
    ),
  ).toBe(true);
  expect(JSON.stringify(audit)).not.toMatch(
    /access_token|hashed_password|text_content|activation_link/,
  );
  await page.screenshot({ path: '.artifacts/t15c2-audit-1280.png' });
});
test('purge exact confirmation, 400/409 preserved, cleanup failed and retry, negative roles', async ({
  page,
  request,
}) => {
  const target = await disposable(request, 'purge');
  await login(page);
  await page.goto(`/admin/courses/${target.id}`);
  await page.getByRole('button', { name: 'Удалить курс безвозвратно' }).click();
  const dialog = page.getByRole('dialog');
  const submit = dialog.getByRole('button', {
    name: 'Удалить безвозвратно',
    exact: true,
  });
  await expect(
    dialog.getByRole('button', { name: 'Отмена', exact: true }),
  ).toBeFocused();
  await expect(submit).toBeDisabled();
  await page
    .getByLabel('Точное название курса', { exact: true })
    .fill(target.name + ' ');
  await page.getByLabel('Номер курса', { exact: true }).fill(String(target.id));
  await expect(submit).toBeDisabled();
  await page
    .getByLabel('Точное название курса', { exact: true })
    .fill(target.name);
  for (const status of [400, 409]) {
    await page.route(`**/api/courses/${target.id}/purge`, (r) =>
      r.fulfill({ status, json: { detail: 'injected' } }),
    );
    await submit.click();
    await expect(dialog.getByRole('alert')).toBeVisible();
    await expect(
      page.getByLabel('Точное название курса', { exact: true }),
    ).toHaveValue(target.name);
    await page.unroute(`**/api/courses/${target.id}/purge`);
  }
  for (const headers of [teacher, student, other]) {
    for (const [path, method, data] of [
      [
        `/courses/${target.id}/purge`,
        'POST',
        { confirm_course_id: target.id, confirm_name: target.name },
      ],
      [`/courses/${course.id}/restore`, 'POST', {}],
      [
        `/courses/${course.id}/students/${credentials.student.id}/history-access`,
        'PATCH',
        { revoked: true },
      ],
      ['/admin/file-deletions/retry', 'POST', {}],
      ['/audit-events', 'GET', undefined],
    ] as const) {
      expect(
        (
          await request.fetch('/api' + path, { headers, method, data })
        ).status(),
      ).toBe(403);
    }
  }
  const invalid = await request.post(`/api/courses/${target.id}/purge`, {
    headers: admin,
    data: { confirm_course_id: target.id, confirm_name: target.name + 'wrong' },
  });
  expect(invalid.status()).toBe(400);
  await page.route(`**/api/courses/${target.id}/purge`, async (route) => {
    const r = await route.fetch();
    expect(r.ok()).toBe(true);
    const body = await r.json();
    await route.fulfill({
      response: r,
      json: { ...body, cleanup: { completed: 0, failed: 1 } },
    });
  });
  await submit.click();
  await expect(
    page.getByRole('heading', { name: 'Курс удалён безвозвратно' }),
  ).toBeVisible();
  await expect(
    page.getByText('Остались файлы, ожидающие очистки.', { exact: false }),
  ).toBeVisible();
  expect(
    (
      await request.get(`/api/courses/${target.id}`, { headers: admin })
    ).status(),
  ).toBe(404);
  expect(
    (
      await request.get('/api' + target.file.download_url, { headers: admin })
    ).status(),
  ).toBe(404);
  await page
    .getByRole('button', { name: 'Повторить очистку файлов', exact: true })
    .click();
  await expect(
    page.getByText('Очищено файлов: 0. Ожидают очистки: 0.'),
  ).toBeVisible();
});
test('unknown purge checks server state, loading/empty/error, mobile keyboard axe and filter search', async ({
  page,
  request,
}) => {
  const target = await disposable(request, 'unknown');
  await login(page);
  await page.goto(`/admin/courses/${target.id}`);
  await page.getByRole('button', { name: 'Удалить курс безвозвратно' }).click();
  await page
    .getByLabel('Точное название курса', { exact: true })
    .fill(target.name);
  await page.getByLabel('Номер курса', { exact: true }).fill(String(target.id));
  let count = 0;
  await page.route(`**/api/courses/${target.id}/purge`, async (route) => {
    count++;
    const r = await route.fetch();
    expect(r.ok()).toBe(true);
    await route.abort('failed');
  });
  await page
    .getByRole('button', { name: 'Удалить безвозвратно', exact: true })
    .click();
  await expect(
    page.getByRole('button', { name: 'Удалить безвозвратно', exact: true }),
  ).toBeDisabled();
  await page
    .getByRole('dialog')
    .getByRole('button', { name: 'Отмена', exact: true })
    .click();
  await page.getByRole('button', { name: 'Удалить курс безвозвратно' }).click();
  await expect(
    page.getByRole('button', { name: 'Удалить безвозвратно', exact: true }),
  ).toBeDisabled();
  await page.getByRole('button', { name: 'Проверить состояние' }).click();
  await expect(
    page.getByRole('heading', { name: 'Курс удалён безвозвратно' }),
  ).toBeVisible();
  expect(count).toBe(1);
  let release!: () => void;
  const delayed = new Promise<void>((resolve) => {
    release = resolve;
  });
  await page.route('**/api/courses?*', async (route) => {
    await delayed;
    await route.continue();
  });
  await page.goto('/admin/courses');
  await expect(
    page.getByRole('status').filter({ hasText: 'Загружаем…' }).first(),
  ).toBeVisible();
  release();
  await expect(
    page.locator(`a[href="/admin/courses/${course.id}"]`),
  ).toBeVisible();
  await page.unroute('**/api/courses?*');
  await page.route('**/api/courses?*', (r) =>
    r.fulfill({ status: 503, json: {} }),
  );
  await page.goto('/admin/courses');
  await expect(
    page.getByRole('button', { name: 'Повторить', exact: true }),
  ).toBeVisible();
  await page.unroute('**/api/courses?*');
  await page.getByRole('button', { name: 'Повторить', exact: true }).click();
  await expect(
    page.locator(`a[href="/admin/courses/${course.id}"]`),
  ).toBeVisible();
  await page.setViewportSize({ width: 360, height: 800 });
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await page
    .getByText('Поиск по преподавателю и ученику', { exact: true })
    .click();
  await page
    .getByLabel('Поиск: преподаватель', { exact: true })
    .fill('nonexistent_synthetic');
  await expect(page.getByText('Найдено: 0')).toBeVisible();
  await page
    .getByRole('button', {
      name: 'Очистить: Поиск: преподаватель',
      exact: true,
    })
    .click();
  const select = page.getByRole('combobox', {
    name: 'Преподаватель',
    exact: true,
  });
  await select.focus();
  await page.keyboard.press('ArrowDown');
  await expect(page.getByRole('listbox')).toBeVisible();
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  await page.keyboard.press('Escape');
  await expect(select).toBeFocused();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await page.screenshot({ path: '.artifacts/t15c2-courses-360.png' });
  await page.goto('/admin/courses?student=99999999');
  await expect(
    page.getByText('Курсы не найдены. Измените фильтры.'),
  ).toBeVisible();
  await page.goto(`/admin/courses/${course.id}`);
  await page.getByRole('button', { name: 'Удалить курс безвозвратно' }).click();
  await expect(
    page
      .getByRole('dialog')
      .getByRole('button', { name: 'Отмена', exact: true }),
  ).toBeFocused();
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  await page
    .getByRole('dialog')
    .getByRole('button', { name: 'Отмена', exact: true })
    .click();
  await expect(
    page.getByRole('button', { name: 'Удалить курс безвозвратно' }),
  ).toBeFocused();
  expect((await api(request, `/courses/${course.id}`)).id).toBe(course.id);
  await page.goto('/admin/audit');
  await expect(
    page.getByRole('heading', { name: 'Журнал действий', exact: true }),
  ).toBeVisible();
  await expect(page.getByText(/Всего записей:/)).toBeVisible();
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  if (
    await page.getByRole('button', { name: 'Далее', exact: true }).isVisible()
  ) {
    await page.getByRole('button', { name: 'Далее', exact: true }).click();
    await expect(page).toHaveURL(/offset=20/);
  }
  await page.goto('/admin/audit?action=nonexistent');
  await expect(
    page.getByText('Записи не найдены. Измените фильтры.'),
  ).toBeVisible();
});
