import { test, expect, type Page } from '@playwright/test';
import { readFileSync } from 'node:fs';
import AxeBuilder from '@axe-core/playwright';
import type {
  Answer,
  Homework,
  Lecture,
  Page as ApiPage,
} from '../src/features/courses/queries';
test.use({ trace: 'off', screenshot: 'off', video: 'off' });
async function audit(page: Page) {
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth + 1,
    ),
  ).toBe(true);
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  const measurements = await page
    .locator('main .mantine-Button-root:visible')
    .evaluateAll((elements) =>
      elements.map((e) => {
        const label = e.querySelector('.mantine-Button-label');
        const a = e.getBoundingClientRect(),
          b = label?.getBoundingClientRect();
        return {
          name: e.textContent,
          offset: b ? Math.abs(a.y + a.height / 2 - b.y - b.height / 2) : 0,
          clipped: e.scrollHeight > e.clientHeight + 1,
        };
      }),
    );
  expect(measurements.filter((e) => e.offset > 1 || e.clipped)).toEqual([]);
}
test('student study: real protected documents and explicit isolated HTTP state/write fixtures', async ({
  page,
}) => {
  test.skip(!process.env.LGG_T15D_PREVIEW, 'Retained preview; no seed');
  test.setTimeout(180000);
  const { accounts } = JSON.parse(
    readFileSync('.artifacts/t15d-preview.json', 'utf8'),
  );
  let capturedAnswer: Answer | undefined;
  page.on('response', async (r) => {
    const u = new URL(r.url());
    if (
      /^\/api\/submissions\/\d+$/.test(u.pathname) &&
      u.searchParams.get('homework_id') === '61' &&
      r.ok() &&
      !capturedAnswer
    ) {
      try {
        capturedAnswer = await r.json();
      } catch {
        /* An aborted navigation response is not the captured answer. */
      }
    }
  });
  const writes: string[] = [],
    mockWrites: string[] = [],
    errors: string[] = [];
  page.on('pageerror', (e) => errors.push(e.message));
  await page.route('**/api/**', (route) => {
    const req = route.request(),
      path = new URL(req.url()).pathname;
    if (req.method() !== 'GET' && !path.startsWith('/api/auth/')) {
      writes.push(req.method() + ' ' + path);
      return route.abort();
    }
    return route.continue();
  });
  await page.goto('/login');
  await page.getByLabel('Логин', { exact: true }).fill(accounts.turov.username);
  await page
    .getByLabel('Пароль', { exact: true })
    .fill(accounts.turov.password);
  await page.getByRole('button', { name: 'Войти', exact: true }).click();
  await expect(page).toHaveURL(/\/student$/);
  const hwResponse = page.waitForResponse(
    (r) => new URL(r.url()).pathname === '/api/homeworks/61',
  );
  const lectureResponse = page.waitForResponse(
    (r) =>
      new URL(r.url()).pathname === '/api/lectures' &&
      new URL(r.url()).searchParams.get('lesson_id') === '127',
  );
  await page.goto('/student/homeworks/61');
  const hw: Homework = await (await hwResponse).json();
  const lectures: ApiPage<Lecture> = await (await lectureResponse).json();
  expect(hw.id).toBe(61);
  expect(hw.file).toBeTruthy();
  expect(lectures.items.length).toBeGreaterThan(0);
  await expect.poll(() => capturedAnswer).toBeTruthy();
  const realAnswer = capturedAnswer!;
  const material = page.getByRole('region', { name: 'Просмотр: конспект' });
  const condition = page.getByRole('region', {
    name: 'Просмотр: файл задания',
  });
  for (const width of [1340, 1024, 768, 360]) {
    await page.setViewportSize({ width, height: 950 });
    await page.goto('/student/homeworks/61');
    await expect(
      page.getByRole('region', { name: 'Ваше решение', exact: true }),
    ).toBeVisible();
    await expect(
      page.getByRole('link', {
        name: /https:\/\/bank-zadach.ru\/test\/K87TPV/,
      }),
    ).toBeVisible();
    if (width >= 1024) {
      await expect(page.locator('[data-file-viewer="embedded"]')).toHaveCount(
        1,
      );
      await expect(
        page.getByRole('button', { name: 'Развернуть конспект', exact: true }),
      ).toHaveAttribute('aria-expanded', 'false');
      await expect(material).toHaveCount(0);
      await expect(
        condition.getByLabel('Страница 1', { exact: true }),
      ).toBeVisible();
      const doc = await condition.boundingBox(),
        answer = await page
          .getByRole('region', { name: 'Ваше решение', exact: true })
          .boundingBox();
      expect(answer!.x).toBeGreaterThan(doc!.x + doc!.width);
      await page
        .getByRole('button', { name: 'Развернуть конспект', exact: true })
        .click();
      await expect(
        material.getByLabel('Страница 1', { exact: true }),
      ).toBeVisible();
      await page
        .getByRole('button', { name: 'Свернуть конспект', exact: true })
        .click();
    } else {
      await expect(page.locator('[data-file-viewer="embedded"]')).toHaveCount(
        0,
      );
      await page
        .getByRole('button', { name: 'Развернуть файл задания', exact: true })
        .click();
      await expect(
        condition.getByLabel('Страница 1', { exact: true }),
      ).toBeVisible();
      await page
        .getByRole('button', { name: 'Свернуть файл задания', exact: true })
        .click();
    }
    await audit(page);
    await page.screenshot({
      path: `.artifacts/student-study-real-${width}.png`,
      fullPage: true,
    });
  }
  await page.setViewportSize({ width: 1340, height: 950 });
  await page.goto('/student/homeworks/61');
  await expect(
    condition.getByLabel('Страница 1', { exact: true }),
  ).toBeVisible();
  await condition
    .getByRole('button', { name: 'Увеличить', exact: true })
    .click();
  await expect(
    condition.getByRole('status').filter({ hasText: 'Масштаб 125%' }),
  ).toBeAttached();
  await page
    .getByRole('button', { name: 'Свернуть файл задания', exact: true })
    .click();
  await page
    .getByRole('button', { name: 'Развернуть файл задания', exact: true })
    .click();
  await expect(
    condition.getByRole('status').filter({ hasText: 'Масштаб 125%' }),
  ).toBeAttached();
  const opener = condition.getByRole('button', {
    name: 'Открыть крупно',
    exact: true,
  });
  await opener.focus();
  await opener.press('Enter');
  const dialog = page.getByRole('dialog');
  await expect(dialog).toBeVisible();
  await expect(page.locator('[data-file-viewer]')).toHaveCount(1);
  await dialog.getByRole('button', { name: 'Уменьшить', exact: true }).click();
  const download = page.waitForEvent('download');
  await dialog
    .getByRole('button', { name: 'Скачать файл', exact: true })
    .click();
  expect((await download).suggestedFilename()).toBe(hw.file!.display_name);
  await page.keyboard.press('Escape');
  await expect(dialog).toHaveCount(0);
  await expect(opener).toBeFocused();
  await expect(page.locator('[data-file-viewer="embedded"]')).toHaveCount(1);
  await page.goto('/student/lessons/127');
  await expect(
    page.getByRole('link', { name: /https:\/\/bank-zadach.ru\/test\/K87TPV/ }),
  ).toBeVisible();
  expect(writes).toEqual([]);
  // Everything below uses explicit browser-only state and write fixtures.
  let mode = 'empty',
    working: Answer | null = null;
  const fixtureHw = {
    ...hw,
    id: 99001,
    lesson_id: 99010,
    working_submission_id: null,
    title: 'Условие с длинным названием и ссылкой',
    description:
      'Решите вариант: https://example.com/variant\nПояснение к каждому шагу.',
    file: hw.file,
  };
  const makeAnswer = (status: 'draft' | 'submitted' | 'checked'): Answer => ({
    ...realAnswer,
    id: 99002,
    homework_id: 99001,
    version: 1,
    status,
    text_content:
      status === 'draft' ? 'Серверный черновик' : 'Отправленное решение',
    files: [],
    review_files: [],
    grade: status === 'checked' ? 0 : null,
    teacher_comment: null,
  });
  await page.route('**/api/**', async (route) => {
    const req = route.request(),
      url = new URL(req.url()),
      path = url.pathname;
    if (path === '/api/homeworks/99001')
      return route.fulfill({
        json: {
          ...fixtureHw,
          working_submission_id: working?.id ?? null,
          access_mode: mode === 'readonly' ? 'read_only' : 'active',
          read_only_reason: mode === 'readonly' ? 'course_archived' : null,
          file: mode === 'noFiles' ? null : fixtureHw.file,
        },
      });
    if (
      path === '/api/lectures' &&
      url.searchParams.get('lesson_id') === '99010'
    ) {
      if (mode === 'metadataError')
        return route.fulfill({ status: 503, json: { detail: 'fixture' } });
      return route.fulfill({
        json: mode === 'noFiles' ? { items: [], total: 0 } : lectures,
      });
    }
    if (path === '/api/submissions/99002' && req.method() === 'GET')
      return route.fulfill({ json: working });
    if (
      path === '/api/homeworks/99001/submissions' &&
      req.method() === 'POST'
    ) {
      mockWrites.push(req.method() + ' ' + path);
      working = {
        ...makeAnswer('draft'),
        text_content: 'Локальный ответ без реальной отправки',
      };
      return route.fulfill({ json: working });
    }
    if (path === '/api/submissions/99002/student' && req.method() === 'PATCH') {
      mockWrites.push(req.method() + ' ' + path);
      working = { ...working!, version: working!.version + 1 };
      if (req.postData()?.includes('filename='))
        working.files = [
          {
            id: 99005,
            file: { ...hw.file!, id: 99005, display_name: 'fixture.pdf' },
          },
        ] as Answer['files'];
      else working.text_content = 'Изменение после отправки';
      return route.fulfill({ json: working });
    }
    if (path === '/api/submissions/99002/submit' && req.method() === 'POST') {
      mockWrites.push(req.method() + ' ' + path);
      working = {
        ...working!,
        status: 'submitted',
        version: working!.version + 1,
      };
      return route.fulfill({ json: working });
    }
    return route.fallback();
  });
  await page.goto('/student/homeworks/99001');
  const text = page.getByLabel('Текст решения или вопросы');
  await text.fill('Локальный ответ без реальной отправки');
  await condition
    .getByRole('button', { name: 'Открыть крупно', exact: true })
    .click();
  await expect(dialog).toBeVisible();
  await page.goBack();
  await expect(dialog).toHaveCount(0);
  await expect(text).toHaveValue('Локальный ответ без реальной отправки');
  await page
    .getByRole('button', { name: 'Развернуть конспект', exact: true })
    .click();
  await page
    .getByRole('button', { name: 'Свернуть конспект', exact: true })
    .click();
  await page
    .getByRole('button', { name: 'Развернуть конспект', exact: true })
    .click();
  await expect(text).toHaveValue('Локальный ответ без реальной отправки');
  await page
    .getByRole('link', { name: 'Все домашние задания', exact: true })
    .click();
  const guard = page.getByRole('dialog', { name: 'Уйти без сохранения?' });
  await expect(guard).toBeVisible();
  await guard.getByRole('button', { name: 'Отмена', exact: true }).click();
  await expect(text).toHaveValue('Локальный ответ без реальной отправки');
  await page
    .getByLabel('Добавить файлы', { exact: true })
    .setInputFiles('e2e/fixtures/math.pdf');
  await expect(
    page.getByText('fixture.pdf', { exact: true }).first(),
  ).toBeVisible();
  await page
    .getByRole('button', { name: 'Отправить решение', exact: true })
    .click();
  await expect(
    page.getByRole('button', { name: 'Сохранить изменения', exact: true }),
  ).toBeVisible();
  await text.fill('Изменение после отправки');
  await page
    .getByRole('button', { name: 'Сохранить изменения', exact: true })
    .click();
  await expect(text).toHaveValue('Изменение после отправки');
  await expect(page.getByText(/Изменения сохранены/)).toBeVisible();
  expect(
    mockWrites.some((p) => p === 'POST /api/submissions/99002/submit'),
  ).toBe(true);
  for (mode of [
    'draft',
    'submitted',
    'checked',
    'readonly',
    'noFiles',
    'metadataError',
  ]) {
    working = makeAnswer(
      mode === 'checked'
        ? 'checked'
        : mode === 'submitted'
          ? 'submitted'
          : 'draft',
    );
    await page.goto('/student/homeworks/99001');
    await expect(text).toBeVisible();
    if (mode === 'checked') {
      await expect(page.getByText('Оценка: 0 из 5')).toBeVisible();
      await expect(text).not.toBeEditable();
    }
    if (mode === 'readonly') {
      await expect(
        page.getByRole('button', { name: 'Отправить решение', exact: true }),
      ).toHaveCount(0);
      await expect(text).not.toBeEditable();
    }
    if (mode === 'noFiles') {
      await expect(
        page.getByText('Материалы пока не добавлены.'),
      ).toBeVisible();
      await expect(
        page.getByRole('button', { name: /Свернуть конспект/ }),
      ).toHaveCount(0);
    }
    if (mode === 'metadataError') {
      await expect(
        page.getByRole('button', { name: 'Повторить', exact: true }),
      ).toBeVisible();
      mode = 'draft';
      await page
        .getByRole('button', { name: 'Повторить', exact: true })
        .click();
      await expect(
        page.getByRole('button', { name: 'Развернуть конспект', exact: true }),
      ).toHaveAttribute('aria-expanded', 'false');
      await page
        .getByRole('button', { name: 'Развернуть конспект', exact: true })
        .click();
      await expect(material).toBeVisible();
    }
    await audit(page);
  }
  expect(writes).toEqual([]);
  expect(errors).toEqual([]);
});

test('teacher compatibility uses current real work and isolated local grading fixture', async ({
  page,
}) => {
  test.skip(!process.env.LGG_T15D_PREVIEW, 'Retained preview only');
  test.setTimeout(60000);
  const { accounts } = JSON.parse(
    readFileSync('.artifacts/t15d-preview.json', 'utf8'),
  );
  const writes: string[] = [],
    errors: string[] = [];
  page.on('pageerror', (e) => errors.push(e.message));
  await page.route('**/api/**', (route) => {
    const req = route.request(),
      path = new URL(req.url()).pathname;
    if (req.method() !== 'GET' && !path.startsWith('/api/auth/')) {
      writes.push(req.method() + ' ' + path);
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
  await page.goto('/teacher/lessons/127');
  const link = page
    .getByRole('link', { name: /^(Посмотреть проверку|Проверить работу)$/ })
    .first();
  await expect(link).toBeVisible();
  const target = await link.getAttribute('href');
  expect(target).toBeTruthy();
  const parsed = new URL(target!, 'http://127.0.0.1:5173'),
    hwId = parsed.searchParams.get('homework_id'),
    answerId = parsed.pathname.split('/').at(-1);
  const response = page
    .waitForResponse(
      (r) => new URL(r.url()).pathname === `/api/submissions/${answerId}`,
    )
    .then((r) => r.json());
  await link.click();
  const current: Answer = await response;
  const embedded = page.getByRole('region', { name: 'Просмотр файла решения' });
  for (const width of [1340, 768, 360]) {
    await page.setViewportSize({ width, height: 950 });
    if (width >= 1024) {
      await expect(embedded.getByRole('img')).toBeVisible();
    } else {
      await expect(embedded).toHaveCount(0);
      await page.getByRole('button', { name: /^Открыть Снимок/ }).click();
      await expect(page.getByRole('dialog').getByRole('img')).toBeVisible();
      await page.keyboard.press('Escape');
    }
    await audit(page);
  }
  // Explicit submitted fixture allows local grading controls on an already checked real work.
  await page.route(`**/api/submissions/${answerId}?*`, (route) =>
    route.fulfill({
      json: {
        ...current,
        status: 'submitted',
        grade: null,
        teacher_comment: null,
      },
    }),
  );
  await page.route(`**/api/homeworks/${hwId}`, async (route) => {
    const res = await route.fetch();
    return route.fulfill({
      response: res,
      json: { ...(await res.json()), can_review: true },
    });
  });
  await page.setViewportSize({ width: 1340, height: 950 });
  await page.reload();
  await page.getByRole('radio', { name: '0', exact: true }).check();
  await page
    .getByLabel('Комментарий ученику', { exact: true })
    .fill('Локальный комментарий без сохранения');
  await page
    .getByLabel('Добавить файлы к проверке', { exact: true })
    .setInputFiles('e2e/fixtures/math.pdf');
  await expect(embedded.getByRole('img')).toBeVisible();
  await embedded
    .getByRole('button', { name: 'Увеличить', exact: true })
    .click();
  const opener = embedded.getByRole('button', {
    name: 'Открыть крупно',
    exact: true,
  });
  await opener.click();
  await expect(page.locator('[data-file-viewer]')).toHaveCount(1);
  await page.goBack();
  await expect(opener).toBeFocused();
  await expect(
    page.getByRole('radio', { name: '0', exact: true }),
  ).toBeChecked();
  await expect(
    page.getByLabel('Комментарий ученику', { exact: true }),
  ).toHaveValue('Локальный комментарий без сохранения');
  await expect(page.getByText('math.pdf', { exact: true })).toBeVisible();
  expect(writes).toEqual([]);
  expect(errors).toEqual([]);
});
