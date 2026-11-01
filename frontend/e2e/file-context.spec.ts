import { test, expect, type Page } from '@playwright/test';
import { existsSync, readFileSync } from 'node:fs';
import AxeBuilder from '@axe-core/playwright';

const teacherStorage = '.artifacts/t15d-e-session.json';
const studentStorage = '.artifacts/t15d-e2-student-session.json';
test.use({
  trace: 'off',
  screenshot: 'off',
  video: 'off',
  storageState:
    process.env.LGG_T15D_PREVIEW && existsSync(teacherStorage)
      ? teacherStorage
      : undefined,
});
test('package B: read-only real API files, context, safe links and dirty review', async ({
  page,
  browser,
}) => {
  test.skip(
    !process.env.LGG_T15D_PREVIEW,
    'Uses preserved preview, never seeds.',
  );
  test.setTimeout(90000);
  page.setDefaultTimeout(10000);
  const fixture = JSON.parse(
    readFileSync('.artifacts/t15d-preview.json', 'utf8'),
  );
  const writes: string[] = [];
  const submitted = fixture.answers['0-2-20'];
  const errors: string[] = [];
  let descriptions = false;
  let fileError = false;
  let slowFile = false;
  let releaseFile = () => {};
  let waiting = Promise.resolve();
  const text =
    '<b>Условие</b>\nhttps://example.com/a_(b), http://example.org/test.\njavascript:alert(1) data:text/html,test file:///tmp/a //example.org\nhttps://example.net/' +
    'long'.repeat(80);
  async function protect(target: Page) {
    target.on('pageerror', (error) => errors.push(error.message));
    await target.route('**/api/**', async (route) => {
      const request = route.request();
      const path = new URL(request.url()).pathname;
      if (request.method() !== 'GET' && !path.startsWith('/api/auth/')) {
        writes.push(request.method() + ' ' + path);
        return route.abort();
      }
      // Stable historical GET fixture: the owner can finish every real review.
      if (path === `/api/submissions/${submitted.id}`)
        return route.fulfill({ json: submitted });
      if (path === `/api/homeworks/${submitted.homework_id}`) {
        const response = await route.fetch();
        return route.fulfill({
          response,
          json: { ...(await response.json()), can_review: true },
        });
      }
      if (/\/(file|files\/\d+)$/.test(path)) {
        if (fileError)
          return route.fulfill({
            status: 503,
            json: { detail: 'Unavailable' },
          });
        if (slowFile) await waiting;
      }
      if (descriptions && /^\/api\/homeworks(?:\/\d+)?$/.test(path)) {
        const response = await route.fetch();
        const body = await response.json();
        if (Array.isArray(body)) body.forEach((hw) => (hw.description = text));
        else body.description = text;
        return route.fulfill({ response, json: body });
      }
      return route.continue();
    });
  }
  async function login(
    target: Page,
    account: { username: string; password: string },
    home = '/teacher',
  ) {
    await protect(target);
    await target.goto(home);
    await expect
      .poll(
        async () =>
          new URL(target.url()).pathname === '/login' ||
          (await target.getByRole('heading', { level: 1 }).isVisible()),
      )
      .toBe(true);
    if (new URL(target.url()).pathname === '/login') {
      await target.getByLabel('Логин', { exact: true }).fill(account.username);
      await target.getByLabel('Пароль', { exact: true }).fill(account.password);
      await target.getByRole('button', { name: 'Войти', exact: true }).click();
      await expect(target).not.toHaveURL(/\/login/);
    }
  }
  async function pdf(
    target: Page,
    width: number,
    close: 'button' | 'back' | 'escape',
  ) {
    await target.setViewportSize({ width, height: 950 });
    const before = target.url();
    const state = await target.evaluate(() => history.state.usr ?? null);
    const trigger = target
      .getByRole('button', { name: /^Открыть .*\.pdf$/ })
      .first();
    await trigger.focus();
    await trigger.press('Enter');
    const dialog = target.getByRole('dialog');
    await expect(dialog).toBeVisible();
    await expect(
      dialog.getByLabel('Страница 1', { exact: true }),
    ).toBeVisible();
    expect(await target.evaluate(() => history.state.usr ?? null)).toEqual(
      state,
    );
    await target.screenshot({ path: `.artifacts/t15d-b-pdf-${width}.png` });
    if (close === 'back') await target.goBack();
    else if (close === 'escape') await target.keyboard.press('Escape');
    else await dialog.getByRole('button', { name: 'Закрыть просмотр' }).click();
    await expect(dialog).toBeHidden();
    await expect(target).toHaveURL(before);
    await expect(trigger).toBeFocused();
    expect(await target.evaluate(() => history.state.usr ?? null)).toEqual(
      state,
    );
  }

  await login(page, fixture.accounts.teacher);
  const schedule = '/teacher/schedule?week=2026-10-19&view=all&day=1';
  await page.goto(schedule);
  const lessonId = fixture.lessons['0-1-17'].id;
  await page.locator(`a[href="/teacher/lessons/${lessonId}"]`).first().click();
  for (const [width, close] of [
    [1340, 'button'],
    [768, 'back'],
    [360, 'escape'],
  ] as const)
    await pdf(page, width, close);
  await page.getByRole('link', { name: 'К расписанию' }).click();
  await expect(page).toHaveURL(schedule);

  // GET substitution only: exercise untrusted/long content without editing records.
  descriptions = true;
  await page.goto(
    `/teacher/lessons/${lessonId}?student=${fixture.accounts.schegletov.id}`,
  );
  for (const width of [1340, 768, 360]) {
    await page.setViewportSize({ width, height: 950 });
    const link = page.getByRole('link', {
      name: 'https://example.com/a_(b) (откроется в новой вкладке)',
      exact: true,
    });
    await expect(link).toBeVisible();
    await expect(link).toHaveAttribute('rel', 'noopener noreferrer');
    await expect(link).toHaveAttribute('target', '_blank');
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
    if (width !== 768)
      await page.screenshot({
        path: `.artifacts/t15d-b-links-${width}.png`,
        fullPage: true,
      });
  }
  await page.route('https://example.com/**', (route) =>
    route.fulfill({ body: 'Synthetic destination' }),
  );
  const opened = page.waitForEvent('popup');
  await page
    .getByRole('link', {
      name: 'https://example.com/a_(b) (откроется в новой вкладке)',
      exact: true,
    })
    .click();
  const popup = await opened;
  await expect(popup).toHaveURL('https://example.com/a_(b)');
  expect(await popup.evaluate(() => window.opener === null)).toBe(true);
  await popup.close();

  const studentsUrl = '/teacher/students?limit=50&sort=recent';
  const studentId = fixture.accounts.schegletov.id;
  await page.goto(studentsUrl);
  await page.locator(`a[href="/teacher/students/${studentId}"]`).click();
  let workspaceUrl = page.url();
  const historyItem = page
    .getByRole('list', { name: 'Занятия выбранного месяца' })
    .getByRole('listitem')
    .filter({
      has: page.locator(`button[aria-controls="history-lesson-${lessonId}"]`),
    });
  await historyItem
    .locator(`button[aria-controls="history-lesson-${lessonId}"]`)
    .click();
  workspaceUrl = page.url();
  await expect(
    historyItem.getByRole('link', { name: /https:\/\/example.com/ }),
  ).toBeVisible();
  await pdf(page, 360, 'button');
  await historyItem
    .locator(`a[href="/teacher/lessons/${lessonId}?student=${studentId}"]`)
    .click();
  expect(await page.evaluate(() => history.state.usr.studentListSearch)).toBe(
    'limit=50&sort=recent',
  );
  await expect(page).toHaveURL(
    new RegExp(`/teacher/lessons/${lessonId}\\?student=${studentId}$`),
  );
  await expect(page.getByRole('heading', { level: 1 })).toContainText(
    'Артём Щеглетов',
  );
  await pdf(page, 360, 'escape');
  await page.getByRole('link', { name: 'К ученику', exact: true }).click();
  await expect(page).toHaveURL(workspaceUrl);
  await page.getByRole('link', { name: 'Свои ученики', exact: true }).click();
  await expect(page).toHaveURL(/\/teacher\/students\?sort=recent&limit=50$/);

  await page.goto(
    `/teacher/review/${submitted.id}?homework_id=${submitted.homework_id}&limit=50&view=all`,
  );
  const reviewUrl = page.url();
  await page
    .getByLabel('Комментарий ученику', { exact: true })
    .fill('Несохранённая проверка B');
  await page.getByRole('radio', { name: '0', exact: true }).check();
  await page
    .getByLabel('Добавить файлы к проверке', { exact: true })
    .setInputFiles('e2e/fixtures/math.pdf');
  const photo = page
    .getByRole('button', { name: /^Открыть .*\.webp$/ })
    .first();
  await photo.click();
  await expect(
    page.getByRole('dialog').getByRole('img', { name: /\.webp$/ }),
  ).toBeVisible();
  await expect(page.getByRole('dialog')).toHaveCSS('opacity', '1');
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  await page.screenshot({ path: '.artifacts/t15d-b-review-photo.png' });
  await page.keyboard.press('Escape');
  await expect(page).toHaveURL(reviewUrl);
  await expect(photo).toBeFocused();
  await expect(
    page.getByLabel('Комментарий ученику', { exact: true }),
  ).toHaveValue('Несохранённая проверка B');
  await expect(
    page.getByRole('radio', { name: '0', exact: true }),
  ).toBeChecked();
  await expect(page.getByText('math.pdf', { exact: true })).toBeVisible();
  await expect(
    page.locator('details').filter({
      has: page.locator('summary').filter({ hasText: 'Условие задания' }),
    }),
  ).toHaveAttribute('open', '');
  await pdf(page, 360, 'back');
  await page.getByRole('link', { name: 'К очереди', exact: true }).click();
  const leave = page.getByRole('dialog', { name: 'Уйти без сохранения?' });
  await expect(leave).toBeVisible();
  await leave.getByRole('button', { name: 'Отмена', exact: true }).click();
  await expect(leave).not.toBeAttached();
  await expect(
    page.getByLabel('Комментарий ученику', { exact: true }),
  ).toHaveValue('Несохранённая проверка B');
  await page.screenshot({
    path: '.artifacts/t15d-b-review-dirty.png',
    fullPage: true,
  });

  const context = await browser.newContext({
    baseURL: 'http://127.0.0.1:5173',
    ...(existsSync(studentStorage) ? { storageState: studentStorage } : {}),
  });
  const student = await context.newPage();
  try {
    await login(student, fixture.accounts.schegletov, '/student');
    await student.goto(`/student/lessons/${lessonId}?week=2026-10-19&view=all`);
    await pdf(student, 360, 'button');
    fileError = true;
    await student
      .getByRole('button', { name: /^Открыть .*\.pdf$/ })
      .first()
      .click();
    await expect(student.getByRole('dialog').getByRole('alert')).toBeVisible();
    fileError = false;
    await student.getByRole('button', { name: 'Повторить просмотр' }).click();
    await expect(
      student.getByLabel('Страница 1', { exact: true }),
    ).toBeVisible();
    await student.keyboard.press('Escape');
    slowFile = true;
    waiting = new Promise<void>((resolve) => (releaseFile = resolve));
    await student
      .getByRole('button', { name: /^Открыть .*\.pdf$/ })
      .first()
      .click();
    await expect(
      student.getByText('Загружаем файл…', { exact: true }),
    ).toBeVisible();
    await student.keyboard.press('Escape');
    slowFile = false;
    releaseFile();
    await expect(student.getByRole('dialog')).toBeHidden();
    expect(
      (await new AxeBuilder({ page: student }).analyze()).violations,
    ).toEqual([]);
  } finally {
    await context.storageState({ path: studentStorage });
    await context.close();
  }
  await page.context().storageState({ path: '.artifacts/t15d-e-session.json' });
  expect(writes).toEqual([]);
  expect(errors).toEqual([]);
});
