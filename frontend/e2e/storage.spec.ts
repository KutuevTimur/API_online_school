import { test, expect, type APIRequestContext } from '@playwright/test';
import { readFileSync } from 'node:fs';
import AxeBuilder from '@axe-core/playwright';
const credentials = JSON.parse(
  readFileSync('.artifacts/storage-credentials.json', 'utf8'),
);
test.use({ trace: 'off', screenshot: 'off', video: 'off' });
let admin: Record<string, string>,
  teacher: Record<string, string>,
  student: Record<string, string>,
  other: Record<string, string>;
let courseId: number;
async function api(
  request: APIRequestContext,
  path: string,
  headers = admin,
  method = 'GET',
  data?: unknown,
) {
  const response = await request.fetch('/api' + path, {
    headers,
    method,
    data,
  });
  expect(response.ok(), `${method} ${path}: ${response.status()}`).toBe(true);
  return response.status() === 204 ? undefined : response.json();
}
test.beforeAll(async ({ request }) => {
  for (const key of ['admin', 'teacher', 'student', 'other']) {
    const response = await request.post('/api/auth/login', {
      form: {
        username: credentials[key].username,
        password: credentials[key].password,
      },
    });
    expect(response.ok()).toBe(true);
    const headers = {
      Authorization: 'Bearer ' + (await response.json()).access_token,
    };
    if (key === 'admin') admin = headers;
    if (key === 'teacher') teacher = headers;
    if (key === 'student') student = headers;
    if (key === 'other') other = headers;
  }
  for (const [index, headers] of [teacher, other].entries()) {
    const id = index ? credentials.other.id : credentials.teacher.id;
    await api(request, '/teacher_students', admin, 'POST', {
      teacher_user_id: id,
      student_user_id: credentials.student.id,
    });
    const course = await api(request, '/courses', headers, 'POST', {
      name: `Synthetic storage ${index}`,
      slug: 'storage-' + index + Date.now(),
    });
    if (!index) courseId = course.id;
    await api(request, `/courses/${course.id}/students`, headers, 'POST', {
      student_user_id: credentials.student.id,
    });
    const lesson = await api(request, '/lessons', headers, 'POST', {
      course_id: course.id,
      student_user_id: credentials.student.id,
      title: 'Synthetic storage lesson',
      scheduled_at: `2031-01-0${index + 1}T09:00:00Z`,
    });
    const uploaded = await request.post('/api/lectures', {
      headers,
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
    expect(uploaded.ok()).toBe(true);
    if (!index) await api(request, `/courses/${course.id}`, headers, 'DELETE');
  }
});
test('teacher course usage and pupil decimal quota: real API, read-only report, empty/error/mobile/keyboard', async ({
  page,
  request,
}) => {
  const report = await api(
    request,
    `/admin/users/${credentials.teacher.id}/course-storage`,
  );
  const second = await api(
    request,
    `/admin/users/${credentials.other.id}/course-storage`,
  );
  const pupil = await api(request, `/users/${credentials.student.id}/storage`);
  expect(report.used_bytes).toBeGreaterThan(0);
  expect(report.courses.map((c: { course_id: number }) => c.course_id)).toEqual(
    [courseId],
  );
  expect(pupil.used_bytes).toBe(report.used_bytes + second.used_bytes);
  expect(report).not.toHaveProperty('limit_bytes');
  for (const headers of [teacher, student, other])
    expect(
      (
        await request.get(
          `/api/admin/users/${credentials.teacher.id}/course-storage`,
          { headers },
        )
      ).status(),
    ).toBe(403);
  await page.goto('/login');
  await page
    .getByLabel('Логин', { exact: true })
    .fill(credentials.admin.username);
  await page
    .getByLabel('Пароль', { exact: true })
    .fill(credentials.admin.password);
  await page.getByRole('button', { name: 'Войти', exact: true }).click();
  await expect(page).toHaveURL('/admin/users');
  await page.goto(`/admin/users/${credentials.teacher.id}`);
  await expect(
    page.getByRole('heading', {
      name: 'Файлы в курсах преподавателя',
      exact: true,
    }),
  ).toBeVisible();
  await expect(page.getByText(/Всего занято:/)).not.toHaveText(
    'Всего занято: 0 Б.',
  );
  await expect(
    page.getByText('Изменить лимит места', { exact: true }),
  ).toHaveCount(0);
  await page.getByText('Посмотреть по курсам', { exact: true }).click();
  await expect(
    page.locator(`a[href="/admin/courses/${courseId}"]`),
  ).toBeVisible();
  await page.screenshot({ path: '.artifacts/storage-teacher-1280.png' });
  const path = `**/api/admin/users/${credentials.teacher.id}/course-storage`;
  await page.route(path, (route) => route.fulfill({ status: 503, json: {} }));
  await page.reload();
  const block = page.locator('section').filter({
    has: page.getByRole('heading', {
      name: 'Файлы в курсах преподавателя',
      exact: true,
    }),
  });
  await expect(
    block.getByRole('button', { name: 'Повторить', exact: true }),
  ).toBeVisible();
  await page.unroute(path);
  await block.getByRole('button', { name: 'Повторить', exact: true }).click();
  await expect(block.getByText(/Всего занято:/)).toBeVisible();
  await page.goto(`/admin/users/${credentials.empty.id}`);
  await expect(
    page.getByText('Всего занято: 0 Б.', { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText('В курсах пока нет учебных файлов.', { exact: true }),
  ).toBeVisible();
  await page.goto(`/admin/users/${credentials.student.id}`);
  await expect(
    page.getByRole('heading', {
      name: 'Место для файлов ученика',
      exact: true,
    }),
  ).toBeVisible();
  await expect(page.getByText(/Это не лимит одного файла/)).toBeVisible();
  await page.getByText('Изменить лимит места', { exact: true }).click();
  await page.getByLabel('Новый лимит', { exact: true }).fill('0.001');
  await expect(
    page.getByRole('button', { name: 'Проверить новый лимит', exact: true }),
  ).toBeDisabled();
  await page.getByLabel('Новый лимит', { exact: true }).fill('0.05');
  await page
    .getByRole('button', { name: 'Проверить новый лимит', exact: true })
    .click();
  await expect(page.getByRole('dialog')).toContainText('50 МБ');
  await page
    .getByRole('dialog')
    .getByRole('button', { name: 'Изменить лимит места', exact: true })
    .click();
  await expect(page.getByText('Лимит изменён', { exact: true })).toBeVisible();
  expect(
    (await api(request, `/users/${credentials.student.id}/storage`))
      .limit_bytes,
  ).toBe(50_000_000);
  await page.setViewportSize({ width: 360, height: 850 });
  await page.emulateMedia({ reducedMotion: 'reduce' });
  const select = page.getByRole('combobox', {
    name: 'Единица измерения',
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
  await page.screenshot({ path: '.artifacts/storage-student-360.png' });
  await page.getByLabel('Новый лимит', { exact: true }).fill('0.06');
  await page
    .getByRole('button', { name: 'Проверить новый лимит', exact: true })
    .click();
  await page.route(
    `**/api/admin/users/${credentials.student.id}/storage-quota`,
    (route) => route.fulfill({ status: 409, json: {} }),
  );
  await page
    .getByRole('dialog')
    .getByRole('button', { name: 'Изменить лимит места', exact: true })
    .click();
  await expect(page.getByRole('dialog').getByRole('alert')).toBeVisible();
  await page
    .getByRole('dialog')
    .getByRole('button', { name: 'Отмена', exact: true })
    .click();
  await expect(page.getByLabel('Новый лимит', { exact: true })).toHaveValue(
    '0.06',
  );
});
