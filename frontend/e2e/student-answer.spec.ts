import {
  test,
  expect,
  type Page,
  type APIRequestContext,
} from '@playwright/test';
import { readFileSync } from 'node:fs';
import AxeBuilder from '@axe-core/playwright';
const credentials = JSON.parse(
  readFileSync('.artifacts/t14e-credentials.json', 'utf8'),
);
const lesson = credentials.student_answer.lessons[0];
let teacherToken: string;
test.use({ trace: 'off', screenshot: 'off', video: 'off', hasTouch: true });
test.beforeAll(async ({ request }) => {
  const login = await request.post('/api/auth/login', {
    form: credentials.teacher,
  });
  expect(login.ok()).toBeTruthy();
  teacherToken = (await login.json()).access_token;
});
async function homework(request: APIRequestContext) {
  const result = await request.post('/api/homeworks', {
    headers: { Authorization: `Bearer ${teacherToken}` },
    multipart: {
      lesson_id: lesson.id,
      student_user_id: lesson.student_user_id,
      title: 'Фото решения · synthetic ' + Date.now(),
      description: 'Решите x² − 5x + 6 = 0. Добавьте фотографии хода решения.',
    },
  });
  expect(result.status()).toBe(201);
  return (await result.json()).id as number;
}
async function login(page: Page) {
  await page.goto('/login');
  await page
    .getByLabel('Логин', { exact: true })
    .fill(credentials.answer_student.username);
  await page
    .getByLabel('Пароль', { exact: true })
    .fill(credentials.answer_student.password);
  await page.getByRole('button', { name: 'Войти', exact: true }).click();
  await expect(
    page.getByRole('heading', { name: 'Мой день', exact: true }),
  ).toBeVisible();
}
const photo = (n: number) => ({
  name: `Решение-${n}.png`,
  mimeType: 'image/png',
  buffer: readFileSync('e2e/fixtures/notebook.png'),
});
const saved = (page: Page) => page.locator('article[aria-label^="Сохранён:"]');
async function save(page: Page, label?: string) {
  if (label)
    await page.getByRole('button', { name: label, exact: true }).click();
  await expect(
    page.getByText(
      /Черновик сохранён|Решение на проверке\. Изменения сохранены/,
    ),
  ).toBeVisible();
}
test('real API desktop/360: draft, 3 photos → append4 → replace/remove → submit/edit → teacher fixture check, immutable result', async ({
  page,
  request,
}) => {
  const id = await homework(request);
  await login(page);
  await page.goto(`/student/homeworks/${id}`);
  await expect(
    page.getByText('Решение ещё не сохранено', { exact: true }),
  ).toBeVisible();
  await page.reload();
  await expect(
    page.getByText('Решение ещё не сохранено', { exact: true }),
  ).toBeVisible();
  await page
    .getByRole('button', { name: 'Отправить решение', exact: true })
    .click();
  await expect(
    page.getByText('Добавьте текст решения или хотя бы один файл.'),
  ).toBeVisible();
  await page
    .getByLabel('Текст решения или вопросы')
    .fill('Корни: 2 и 3. Проверяю подстановкой.');
  await page
    .getByLabel('Добавить файлы', { exact: true })
    .setInputFiles([photo(1), photo(2), photo(3)]);
  await expect(saved(page)).toHaveCount(3);
  await save(page);
  await expect(saved(page)).toHaveCount(3);
  await page.reload();
  await expect(page.getByLabel('Текст решения или вопросы')).toHaveValue(
    'Корни: 2 и 3. Проверяю подстановкой.',
  );
  await expect(saved(page)).toHaveCount(3);
  await page
    .getByLabel('Добавить файлы', { exact: true })
    .setInputFiles(photo(4));
  await save(page);
  await expect(saved(page)).toHaveCount(4);
  await saved(page)
    .first()
    .getByLabel(/Заменить/)
    .setInputFiles(photo(5));
  await save(page);
  await expect(saved(page)).toHaveCount(4);
  await expect(saved(page).filter({ hasText: 'Решение-5' })).toHaveCount(1);
  await saved(page)
    .filter({ hasText: 'Решение-2' })
    .getByRole('button', { name: /Удалить/ })
    .click();
  await page.getByRole('button', { name: 'Удалить файл', exact: true }).click();
  await expect(saved(page)).toHaveCount(3);
  await expect(page.getByRole('dialog')).toHaveCount(0);
  await page.screenshot({
    path: '.artifacts/t15a2-answer-desktop.png',
    fullPage: true,
  });
  await page.setViewportSize({ width: 360, height: 800 });
  await page.screenshot({
    path: '.artifacts/t15a2-answer-mobile.png',
    fullPage: true,
  });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBeTruthy();
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  await page
    .getByRole('button', { name: 'Отправить решение', exact: true })
    .click();
  await expect(page.getByText('На проверке', { exact: true })).toBeVisible();
  await page
    .getByLabel('Текст решения или вопросы')
    .fill('Уточнение: x = 2 или x = 3.');
  await save(page, 'Сохранить изменения');
  const token = (
    await (
      await request.post('/api/auth/login', {
        form: credentials.answer_student,
      })
    ).json()
  ).access_token;
  const headers = { Authorization: `Bearer ${token}` };
  const attempts = await (
    await request.get(`/api/homeworks/${id}/submissions`, { headers })
  ).json();
  expect(attempts.items).toHaveLength(1);
  const answer = attempts.items[0];
  expect(answer.files).toHaveLength(3);
  expect(
    (
      await request.post(
        `/api/submissions/${answer.id}/submit?homework_id=${id}`,
        { headers },
      )
    ).ok(),
  ).toBeTruthy();
  const review = await request.patch(
    `/api/submissions/${answer.id}/teacher?homework_id=${id}`,
    {
      headers: { Authorization: `Bearer ${teacherToken}` },
      data: {
        expected_version: answer.version,
        grade: 0,
        teacher_comment: 'Синтетическая проверка: покажите вычисления.',
      },
    },
  );
  expect(review.ok()).toBeTruthy();
  await page.reload();
  await expect(
    page.getByRole('heading', { name: 'Проверка учителя' }),
  ).toBeVisible();
  await expect(page.getByText('Оценка: 0 из 5')).toBeVisible();
  await expect(page.getByLabel('Текст решения или вопросы')).toHaveAttribute(
    'readonly',
    '',
  );
  await expect(
    page.getByRole('button', { name: /Сохранить|Отправить решение/ }),
  ).toHaveCount(0);
  await page.screenshot({
    path: '.artifacts/t15a2-result-mobile.png',
    fullPage: true,
  });
  const denied = await request.patch(
    `/api/submissions/${answer.id}/student?homework_id=${id}`,
    {
      headers,
      multipart: {
        text_content: 'immutable',
        expected_version: answer.version,
      },
    },
  );
  expect([403, 409]).toContain(denied.status());
  await page.getByText('Исторические попытки', { exact: true }).click();
  await expect(page.getByText(/исторических попыток нет/)).toBeVisible();
  await page.getByText('Сроки и переносы задания', { exact: true }).click();
  await expect(
    page.getByRole('heading', { name: 'Первоначальное задание' }),
  ).toBeVisible();
  await page.goto('/student/homeworks?status=checked&view=all');
  await expect(
    page.getByRole('link', { name: 'Посмотреть результат' }).first(),
  ).toBeVisible();
  await page.screenshot({
    path: '.artifacts/t15a2-list-mobile.png',
    fullPage: true,
  });
});
test('dirty navigation cancellation, offline save, 409 preserves local text and reads server; two sessions', async ({
  page,
  request,
  browser,
}) => {
  const id = await homework(request);
  await login(page);
  await page.goto(`/student/homeworks/${id}`);
  await page.getByLabel('Текст решения или вопросы').fill('Сохранённый текст');
  await page
    .getByLabel('Добавить файлы', { exact: true })
    .setInputFiles(photo(1));
  await expect(saved(page)).toHaveCount(1);
  await save(page);
  await page
    .getByLabel('Текст решения или вопросы')
    .fill('Локальный текст не терять');
  await page
    .getByRole('link', { name: 'Все домашние задания', exact: true })
    .click();
  await expect(page.getByRole('dialog')).toBeVisible();
  await page.getByRole('button', { name: 'Отмена', exact: true }).click();
  await expect(page.getByLabel('Текст решения или вопросы')).toHaveValue(
    'Локальный текст не терять',
  );
  await expect(saved(page)).toHaveCount(1);
  await page.context().setOffline(true);
  await page
    .getByRole('button', { name: 'Отправить решение', exact: true })
    .click();
  await expect(page.getByText(/Нет связи/).first()).toBeVisible();
  await page.context().setOffline(false);
  await page
    .getByRole('button', { name: 'Проверить сохранение файлов', exact: true })
    .click();
  await expect(page.getByText(/Список обновлён/)).toBeVisible();
  const context = await browser.newContext();
  try {
    const other = await context.newPage();
    await login(other);
    await other.goto(`/student/homeworks/${id}`);
    await other
      .getByLabel('Текст решения или вопросы')
      .fill('Текст из второй сессии');
    await save(other, 'Отправить решение');
    await page
      .getByRole('button', { name: 'Отправить решение', exact: true })
      .click();
    await expect(
      page.getByRole('region', { name: 'Сравнение версий' }).first(),
    ).toBeVisible();
    await expect(page.getByLabel('Текст решения или вопросы')).toHaveValue(
      'Локальный текст не терять',
    );
    await page
      .getByRole('button', { name: 'Открыть обновлённый ответ', exact: true })
      .first()
      .click();
    await expect(
      page.getByText('Текст из второй сессии', { exact: true }).first(),
    ).toBeVisible();
    await save(page, 'Сохранить изменения');
  } finally {
    await context.close();
  }
  await page.reload();
  await expect(page.getByLabel('Текст решения или вопросы')).toHaveValue(
    'Локальный текст не терять',
  );
  await expect(saved(page)).toHaveCount(1);
  await expect(page.getByText('На проверке', { exact: true })).toBeVisible();
  await page
    .getByLabel('Текст решения или вопросы')
    .fill('Локальная правка во время проверки');
  const current = (
    await (
      await request.get(`/api/homeworks/${id}/submissions`, {
        headers: { Authorization: `Bearer ${teacherToken}` },
      })
    ).json()
  ).items.find((a: { is_working: boolean }) => a.is_working);
  const review = await request.patch(
    `/api/submissions/${current.id}/teacher?homework_id=${id}`,
    {
      headers: { Authorization: `Bearer ${teacherToken}` },
      data: {
        expected_version: current.version,
        grade: 5,
        teacher_comment: 'Синтетическая проверка в соседней сессии',
      },
    },
  );
  expect(review.ok()).toBeTruthy();
  await page
    .getByRole('button', { name: 'Сохранить изменения', exact: true })
    .click();
  await expect(
    page.getByRole('region', { name: 'Сравнение версий' }).first(),
  ).toBeVisible();
  await expect(
    page.getByText('Локальная правка во время проверки', { exact: true }),
  ).toBeVisible();
  await page
    .getByRole('button', { name: 'Открыть обновлённый ответ', exact: true })
    .first()
    .click();
  await expect(
    page.getByRole('heading', { name: 'Проверка учителя' }),
  ).toBeVisible();
  await expect(page.getByText('Оценка: 5 из 5')).toBeVisible();
  await expect(
    page.getByText('Локальная правка во время проверки', { exact: true }),
  ).toBeVisible();
});
test('413 per file, slow upload lock, session same-user resume, logout clears draft', async ({
  page,
  request,
  context,
}) => {
  const id = await homework(request);
  await login(page);
  await page.goto(`/student/homeworks/${id}`);
  await page.getByLabel('Текст решения или вопросы').fill('Текст остаётся');
  await page.route('**/api/submissions/*/student?*', (route) =>
    route.fulfill({ status: 413, contentType: 'application/json', body: '{}' }),
  );
  await page
    .getByLabel('Добавить файлы', { exact: true })
    .setInputFiles(photo(8));
  await expect(
    page.getByRole('alert').filter({ hasText: /квота/ }),
  ).toBeVisible();
  await expect(saved(page)).toHaveCount(0);
  await expect(page.getByLabel('Текст решения или вопросы')).toHaveValue(
    'Текст остаётся',
  );
  await expect(
    page.getByText('Черновик · ещё не отправлен', { exact: true }),
  ).toBeVisible();
  await page.unroute('**/api/submissions/*/student?*');
  let release!: () => void;
  const paused = new Promise<void>((r) => {
    release = r;
  });
  await page.route('**/api/submissions/*/student?*', async (route) => {
    await paused;
    await route.continue();
  });
  await page
    .getByRole('button', { name: 'Повторить Решение-8.png', exact: true })
    .click();
  await expect(
    page.getByRole('button', { name: 'Отправить решение', exact: true }),
  ).toBeDisabled();
  release();
  await expect(saved(page)).toHaveCount(1);
  await page.unroute('**/api/submissions/*/student?*');
  test.setTimeout(90000);
  await page.getByLabel('Текст решения или вопросы').fill('Текст до тайм-аута');
  let releaseTimeout!: () => void;
  const timed = new Promise<void>((r) => {
    releaseTimeout = r;
  });
  await page.route('**/api/submissions/*/student?*', async (route) => {
    await timed;
    await route.abort().catch(() => {});
  });
  await page
    .getByRole('button', { name: 'Отправить решение', exact: true })
    .click();
  await expect(
    page.getByText('Превышено время ожидания', { exact: true }),
  ).toBeVisible({ timeout: 35000 });
  releaseTimeout();
  await page.unroute('**/api/submissions/*/student?*');
  await expect(page.getByLabel('Текст решения или вопросы')).toHaveValue(
    'Текст до тайм-аута',
  );
  await page
    .getByRole('button', { name: 'Проверить сохранение файлов', exact: true })
    .click();
  await expect(page.getByText(/Список обновлён/)).toBeVisible();
  await page
    .getByLabel('Текст решения или вопросы')
    .fill('Локально до повторного входа');
  await context.clearCookies();
  await page.route('**/api/submissions/*/student?*', (route) =>
    route.fulfill({ status: 401, contentType: 'application/json', body: '{}' }),
  );
  await page
    .getByLabel('Добавить файлы', { exact: true })
    .setInputFiles(photo(9));
  await expect(
    page.getByRole('dialog', { name: 'Войдите снова', exact: true }),
  ).toBeVisible();
  await page
    .getByLabel('Логин', { exact: true })
    .fill(credentials.answer_student.username);
  await page
    .getByLabel('Пароль', { exact: true })
    .fill(credentials.answer_student.password);
  await page.getByRole('button', { name: 'Войти', exact: true }).click();
  await expect(page.getByRole('dialog')).toHaveCount(0);
  await expect(page.getByLabel('Текст решения или вопросы')).toHaveValue(
    'Локально до повторного входа',
  );
  await expect(page.getByText('Решение-9.png', { exact: true })).toBeVisible();
  await page.unroute('**/api/submissions/*/student?*');
  await page
    .getByRole('button', { name: 'Проверить сохранение файлов', exact: true })
    .click();
  await expect(page.getByText(/Список обновлён/)).toBeVisible();
  await save(page, 'Отправить решение');
  await expect(saved(page)).toHaveCount(2);
  await page.getByLabel('Текст решения или вопросы').fill('Удалить при выходе');
  await page.getByRole('button', { name: 'Выйти', exact: true }).click();
  await expect(
    page.getByRole('dialog', { name: 'Выйти из кабинета?' }),
  ).toBeVisible();
  await page
    .getByRole('dialog')
    .getByRole('button', { name: 'Выйти', exact: true })
    .click();
  await expect(page.getByLabel('Логин', { exact: true })).toBeVisible();
});
test('empty list, authored filters keyboard, direct 404 and hidden assignment', async ({
  page,
  request,
}) => {
  const id = await homework(request);
  await page.goto('/login');
  await page
    .getByLabel('Логин', { exact: true })
    .fill(credentials.answer_empty.username);
  await page
    .getByLabel('Пароль', { exact: true })
    .fill(credentials.answer_empty.password);
  await page.getByRole('button', { name: 'Войти', exact: true }).click();
  await expect(
    page.getByRole('heading', { name: 'Мой день', exact: true }),
  ).toBeVisible();
  await page.goto('/student/homeworks');
  await expect(
    page.getByRole('heading', { name: 'Заданий по этим условиям нет' }),
  ).toBeVisible();
  await page
    .getByRole('combobox', { name: 'Статус задания', exact: true })
    .click();
  await expect(page.getByRole('listbox')).toBeVisible();
  await page.keyboard.press('ArrowDown');
  await page.keyboard.press('ArrowDown');
  await page.keyboard.press('Enter');
  await expect(page).toHaveURL(/status=(submitted|checked|all)/);
  await page
    .getByRole('combobox', { name: 'Статус задания', exact: true })
    .click();
  await page.getByRole('option', { name: 'Все статусы', exact: true }).click();
  await expect(page).toHaveURL(/status=all/);
  await page.reload();
  await expect(
    page.getByRole('combobox', { name: 'Статус задания', exact: true }),
  ).toHaveValue('Все статусы');
  await page.setViewportSize({ width: 360, height: 800 });
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBeTruthy();
  await page.goto(`/student/homeworks/${id}`);
  await expect(
    page.getByText(/Нет доступа|Материал больше недоступен/).first(),
  ).toBeVisible();
  await expect(page.getByLabel('Текст решения или вопросы')).toHaveCount(0);
  await page.goto('/student/homeworks/999999999');
  await expect(
    page.getByText('Материал больше недоступен', { exact: true }),
  ).toBeVisible();
});

test('first automatic save: delayed refetch preserves pending navigation, text and selected file', async ({
  page,
  request,
}) => {
  const id = await homework(request);
  await login(page);
  await page.goto(`/student/homeworks/${id}`);
  await page
    .getByLabel('Текст решения или вопросы')
    .fill('Первый сохранённый текст');
  let releaseRead!: () => void;
  let releaseWrite!: () => void;
  const readGate = new Promise<void>((resolve) => {
    releaseRead = resolve;
  });
  const writeGate = new Promise<void>((resolve) => {
    releaseWrite = resolve;
  });
  await page.route(`**/api/homeworks/${id}`, async (route) => {
    if (route.request().method() === 'GET') await readGate;
    await route.continue();
  });
  try {
    await page
      .getByLabel('Добавить файлы', { exact: true })
      .setInputFiles(photo(21));
    await expect(saved(page)).toHaveCount(1);
    await page
      .getByLabel('Текст решения или вопросы')
      .fill('Правка при первом обновлении');
    await page.route('**/api/submissions/*/student?*', async (route) => {
      await writeGate;
      await route.continue();
    });
    await page
      .getByLabel('Добавить файлы', { exact: true })
      .setInputFiles(photo(22));
    await page
      .getByRole('link', { name: 'Все домашние задания', exact: true })
      .click();
    await expect(page.getByRole('dialog')).toBeVisible();
    const refreshed = page.waitForResponse(
      (response) => new URL(response.url()).pathname === `/api/homeworks/${id}`,
    );
    releaseRead();
    await refreshed;
    await expect(page.getByRole('dialog')).toBeVisible();
    await page.getByRole('button', { name: 'Отмена', exact: true }).click();
    await expect(page.getByLabel('Текст решения или вопросы')).toHaveValue(
      'Правка при первом обновлении',
    );
    await expect(
      page.getByRole('article', { name: 'Решение-22.png', exact: true }),
    ).toBeVisible();
    releaseWrite();
    await expect(saved(page)).toHaveCount(2);
    await save(page);
    await page.reload();
    await expect(page.getByLabel('Текст решения или вопросы')).toHaveValue(
      'Правка при первом обновлении',
    );
    await expect(saved(page)).toHaveCount(2);
    await expect(
      page.getByText('Черновик · ещё не отправлен', { exact: true }),
    ).toBeVisible();
  } finally {
    releaseRead();
    releaseWrite();
  }
});
