import { test, expect } from '@playwright/test';
import { existsSync, readFileSync } from 'node:fs';
import AxeBuilder from '@axe-core/playwright';
test.use({ trace: 'off', screenshot: 'off', video: 'off' });
test('lesson material states and visible actions: neutral pending, confirmed success and not-needed', async ({
  browser,
}) => {
  test.skip(
    !process.env.LGG_T15D_PREVIEW,
    'Preserved preview: all mutations below are browser mocks.',
  );
  test.setTimeout(90000);
  const fixture = JSON.parse(
    readFileSync('.artifacts/t15d-preview.json', 'utf8'),
  );
  const storage = '.artifacts/t15d-e-session.json';
  const context = await browser.newContext({
    baseURL: 'http://127.0.0.1:5173',
    ...(existsSync(storage) ? { storageState: storage } : {}),
  });
  const page = await context.newPage();
  const lesson = fixture.lessons['0-2-17'].id,
    student = fixture.accounts.stepan.id;
  const writes: string[] = [],
    errors: string[] = [];
  let hasLecture = false,
    hasHomework = false,
    lectureNotNeeded = false,
    homeworkNotNeeded = false;
  let mode = 'normal',
    release = () => {},
    waiting = Promise.resolve();
  const file = fixture.materials['0-1-17'].lecture.file;
  page.on('pageerror', (e) => errors.push(e.message));
  await page.route('**/api/**', async (route) => {
    const req = route.request(),
      url = new URL(req.url()),
      path = url.pathname;
    const selected =
      url.searchParams.get('lesson_id') === String(lesson) &&
      url.searchParams.get('student_user_id') === String(student);
    if (
      req.method() === 'GET' &&
      path === `/api/lessons/${lesson}` &&
      mode === 'readonly'
    ) {
      const response = await route.fetch();
      return route.fulfill({
        response,
        json: {
          ...(await response.json()),
          access_mode: 'read_only',
          read_only_reason: 'course_archived',
          can_manage: false,
        },
      });
    }
    if (
      req.method() === 'PATCH' &&
      path === `/api/teacher-planning/lessons/${lesson}/students/${student}`
    ) {
      const body = req.postDataJSON();
      if ('lecture_not_needed' in body)
        lectureNotNeeded = body.lecture_not_needed;
      if ('homework_not_needed' in body)
        homeworkNotNeeded = body.homework_not_needed;
      return route.fulfill({ json: {} });
    }
    if (req.method() === 'POST' && path === '/api/lectures') {
      if (mode === 'uploading') await waiting;
      if (mode === 'upload-error')
        return route.fulfill({ status: 503, json: { detail: 'Unavailable' } });
      hasLecture = true;
      return route.fulfill({ json: {} });
    }
    if (req.method() === 'POST' && path === '/api/homeworks') {
      if (mode === 'issuing') await waiting;
      hasHomework = true;
      return route.fulfill({ json: {} });
    }
    if (req.method() !== 'GET' && !path.startsWith('/api/auth/')) {
      writes.push(path);
      return route.abort();
    }
    if (selected && path === '/api/teacher-planning/reminders') {
      if (mode === 'get-error')
        return route.fulfill({ status: 503, json: { detail: 'Unavailable' } });
      if (mode === 'get-loading') await waiting;
      return route.fulfill({
        json: {
          items: [
            {
              has_lecture: hasLecture,
              has_homework: hasHomework,
              lecture_not_needed: lectureNotNeeded,
              homework_not_needed: homeworkNotNeeded,
            },
          ],
          total: 1,
        },
      });
    }
    if (selected && path === '/api/lectures')
      return route.fulfill({
        json: {
          items: hasLecture ? [{ id: 99021, file }] : [],
          total: hasLecture ? 1 : 0,
        },
      });
    if (selected && path === '/api/homeworks')
      return route.fulfill({
        json: hasHomework
          ? [
              {
                id: 99022,
                title: 'Задание для проверки интерфейса',
                description: 'Условие',
                deadline: null,
                file: null,
              },
            ]
          : [],
      });
    return route.continue();
  });
  const notes = page.getByRole('region', { name: 'Конспекты', exact: true }),
    homework = page.getByRole('region', {
      name: 'Домашние задания',
      exact: true,
    });
  async function audit() {
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  }
  async function tone(panel: typeof notes, state?: string) {
    if (state)
      await expect(panel).toHaveAttribute('data-material-state', state);
    else await expect(panel).not.toHaveAttribute('data-material-state');
  }
  try {
    await page.goto(`/teacher/lessons/${lesson}?student=${student}`);
    await expect
      .poll(
        async () =>
          new URL(page.url()).pathname === '/login' ||
          (await notes.isVisible()),
      )
      .toBe(true);
    if (new URL(page.url()).pathname === '/login') {
      await page
        .getByLabel('Логин', { exact: true })
        .fill(fixture.accounts.teacher.username);
      await page
        .getByLabel('Пароль', { exact: true })
        .fill(fixture.accounts.teacher.password);
      await page.getByRole('button', { name: 'Войти', exact: true }).click();
    }
    for (const width of [1340, 768, 360]) {
      await page.setViewportSize({ width, height: 1000 });
      await tone(notes, 'missing');
      await tone(homework, 'missing');
      await expect(
        notes.getByRole('button', { name: 'Не добавлять конспект' }),
      ).toBeVisible();
      await expect(
        homework.getByRole('button', { name: 'Не задавать ДЗ' }),
      ).toBeVisible();
      const picker = notes.getByLabel('Добавить конспект', { exact: true });
      await expect(picker).toBeVisible();
      const title = notes.getByRole('heading', {
        name: 'Конспекты',
        exact: true,
      });
      if (width === 1340) {
        const a = (await title.boundingBox())!,
          b = (await picker.boundingBox())!;
        expect(b.x).toBeGreaterThan(a.x + a.width);
        expect(Math.abs(a.y - b.y)).toBeLessThan(20);
      }
      await audit();
      await page.screenshot({
        path: `.artifacts/t15d-materials-missing-${width}.png`,
        fullPage: true,
      });
    }
    await notes.getByRole('button', { name: 'Не добавлять конспект' }).click();
    await tone(notes);
    await expect(
      notes.getByText('Конспект не требуется', { exact: true }),
    ).toBeVisible();
    await homework.getByRole('button', { name: 'Не задавать ДЗ' }).click();
    await tone(homework);
    await expect(
      homework.getByText('ДЗ не требуется', { exact: true }),
    ).toBeVisible();
    await audit();
    await notes
      .getByRole('button', { name: 'Снова напоминать о конспекте' })
      .click();
    await homework
      .getByRole('button', { name: 'Снова напоминать о ДЗ' })
      .click();
    await tone(notes, 'missing');
    await tone(homework, 'missing');
    mode = 'uploading';
    waiting = new Promise<void>((resolve) => {
      release = resolve;
    });
    await notes
      .getByLabel('Добавить конспект', { exact: true })
      .setInputFiles('e2e/fixtures/math.pdf');
    await expect(
      notes.getByRole('status').filter({ hasText: /Загружаем|Обрабатываем/ }),
    ).toBeVisible();
    await tone(notes);
    await audit();
    mode = 'normal';
    release();
    await tone(notes, 'ready');
    await expect(
      notes.getByText('Загружен · доступен ученику', { exact: true }).first(),
    ).toBeVisible();
    await expect(
      notes.getByRole('button', { name: 'Не добавлять конспект' }),
    ).toBeVisible();
    await homework
      .getByRole('button', { name: 'Выдать задание', exact: true })
      .click();
    await homework
      .getByLabel('Название задания', { exact: true })
      .fill('Проверка формы');
    await homework
      .getByLabel('Условие', { exact: true })
      .fill('Несохранённое условие');
    await homework
      .getByLabel('Добавить файл')
      .setInputFiles('e2e/fixtures/math.pdf');
    const open = notes.getByRole('button', {
      name: 'Открыть ' + file.display_name,
      exact: true,
    });
    await open.click();
    await expect(
      page.getByRole('dialog').getByLabel('Страница 1', { exact: true }),
    ).toBeVisible();
    await page.keyboard.press('Escape');
    await expect(page.getByRole('dialog')).not.toBeAttached();
    await expect(open).toBeFocused();
    await expect(
      homework.getByLabel('Название задания', { exact: true }),
    ).toHaveValue('Проверка формы');
    await expect(
      homework
        .getByRole('button', { name: 'Убрать файл условия' })
        .locator('..'),
    ).toContainText('math.pdf');
    mode = 'issuing';
    waiting = new Promise<void>((resolve) => {
      release = resolve;
    });
    await homework
      .getByRole('button', { name: 'Выдать задание', exact: true })
      .click();
    await tone(homework);
    mode = 'normal';
    release();
    await tone(homework, 'ready');
    for (const width of [1340, 768, 360]) {
      await page.setViewportSize({ width, height: 1000 });
      await audit();
      await page.screenshot({
        path: `.artifacts/t15d-materials-ready-${width}.png`,
        fullPage: true,
      });
    }
    mode = 'readonly';
    await page.reload();
    await tone(notes);
    await tone(homework);
    await expect(
      notes.getByLabel('Добавить конспект', { exact: true }),
    ).toHaveCount(0);
    await expect(
      page.getByRole('button', {
        name: /Не добавлять конспект|Не задавать ДЗ|Выдать задание/,
      }),
    ).toHaveCount(0);
    await expect(
      notes.getByRole('button', {
        name: 'Открыть ' + file.display_name,
        exact: true,
      }),
    ).toBeVisible();
    await audit();
    hasLecture = false;
    hasHomework = false;
    mode = 'get-loading';
    waiting = new Promise<void>((resolve) => {
      release = resolve;
    });
    await page.reload();
    await expect(
      notes.getByRole('status').filter({ hasText: 'Загружаем' }).first(),
    ).toBeVisible();
    await tone(notes);
    await audit();
    mode = 'normal';
    release();
    await tone(notes, 'missing');
    mode = 'get-error';
    await page.reload();
    await expect(
      notes.getByRole('button', { name: 'Повторить', exact: true }),
    ).toBeVisible();
    await tone(notes);
    mode = 'normal';
    await notes.getByRole('button', { name: 'Повторить', exact: true }).click();
    await tone(notes, 'missing');
    mode = 'upload-error';
    await notes
      .getByLabel('Добавить конспект', { exact: true })
      .setInputFiles('e2e/fixtures/math.pdf');
    await expect(notes.getByRole('alert')).toBeVisible();
    await tone(notes);
    await audit();
    expect(writes).toEqual([]);
    expect(errors).toEqual([]);
  } finally {
    release();
    await context.storageState({ path: storage });
    await context.close();
  }
});
