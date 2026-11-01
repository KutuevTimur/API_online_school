import { test, expect, type Page } from '@playwright/test';
import { readFileSync } from 'node:fs';
import AxeBuilder from '@axe-core/playwright';
const credentials = JSON.parse(
  readFileSync('.artifacts/t14e-credentials.json', 'utf8'),
);
const lesson = credentials.planning_read.lessons.find(
  (l: { archive: boolean }) => !l.archive,
);
test.use({ trace: 'off', screenshot: 'off', video: 'off', hasTouch: true });
async function login(
  page: Page,
  account: { username: string; password: string },
  path: string,
) {
  await page.goto('/login?returnTo=' + encodeURIComponent(path));
  await page.getByLabel('Логин', { exact: true }).fill(account.username);
  await page.getByLabel('Пароль', { exact: true }).fill(account.password);
  await page.getByRole('button', { name: 'Войти', exact: true }).click();
  await expect(page).toHaveURL(path);
}
async function confirm(page: Page) {
  await page
    .getByRole('button', { name: 'Завершить проверку', exact: true })
    .click();
  const dialog = page.getByRole('dialog', {
    name: 'Завершить проверку?',
    exact: true,
  });
  await expect(
    dialog.getByText(
      'Оценку и комментарий изменить нельзя. Ученик увидит результат.',
    ),
  ).toBeVisible();
  await dialog
    .getByRole('button', { name: 'Завершить проверку', exact: true })
    .click();
  await expect(dialog).toBeHidden();
}
for (const grade of [0, 5])
  test(`both roles: assign → 3 photos/PDF → review ${grade}, conflict/unknown, mobile keyboard and result`, async ({
    page,
    browser,
    request,
  }) => {
    const title = `Synthetic review ${grade} ${Date.now()}`;
    await login(
      page,
      credentials.planning_teacher,
      `/teacher/lessons/${lesson.id}`,
    );
    await page.getByLabel('Название задания', { exact: true }).fill(title);
    await page
      .getByLabel('Условие', { exact: true })
      .fill('Решите уравнение. Покажите ход решения.');
    const issued = page.waitForResponse(
      (r) =>
        r.url().endsWith('/api/homeworks') && r.request().method() === 'POST',
    );
    await page
      .getByRole('button', { name: 'Выдать задание', exact: true })
      .click();
    const response = await issued;
    expect(response.status()).toBe(201);
    const hw = await response.json();
    const context = await browser.newContext({
      baseURL: 'http://127.0.0.1:5173',
    });
    const student = await context.newPage();
    try {
      await login(
        student,
        credentials.planning_student,
        `/student/homeworks/${hw.id}`,
      );
      await student
        .getByLabel('Текст решения или вопросы', { exact: true })
        .fill('Первый ответ\nВторая строка');
      await student
        .getByLabel('Добавить файлы', { exact: true })
        .setInputFiles([
          ...[1, 2, 3].map((i) => ({
            name: `review-photo-${i}.png`,
            mimeType: 'image/png',
            buffer: readFileSync('e2e/fixtures/notebook.png'),
          })),
          {
            name: 'review.pdf',
            mimeType: 'application/pdf',
            buffer: readFileSync('e2e/fixtures/math.pdf'),
          },
        ]);
      await expect(
        student.locator('article[aria-label^="Сохранён:"]'),
      ).toHaveCount(4);
      const sent = student.waitForResponse(
        (r) => r.url().includes('/submit?') && r.request().method() === 'POST',
      );
      await student
        .getByRole('button', { name: 'Отправить решение', exact: true })
        .click();
      const submitted = await sent;
      expect(submitted.status()).toBe(200);
      const sentAnswer = await submitted.json();
      expect(sentAnswer.files).toHaveLength(4);
      await expect(
        student.getByText('На проверке', { exact: true }),
      ).toBeVisible();
      await student.reload();
      await expect(student.getByLabel('Текст решения или вопросы')).toHaveValue(
        'Первый ответ\nВторая строка',
      );
      await expect(
        student.locator('article[aria-label^="Сохранён:"]'),
      ).toHaveCount(4);
      await page.goto(
        `/teacher/review?student_user_id=${lesson.student_user_id}&course_id=${lesson.course_id}`,
      );
      await page.getByRole('link').filter({ hasText: title }).click();
      const reviewURL = page.url();
      await expect(
        page.getByText('Первый ответ\nВторая строка', { exact: true }),
      ).toBeVisible();
      await page.screenshot({
        path: `.artifacts/t15b3-review-${grade}-desktop.png`,
        fullPage: true,
      });
      await page
        .getByRole('button', { name: 'Завершить проверку', exact: true })
        .click();
      await expect(
        page.getByText('Выберите оценку от 0 до 5', { exact: true }),
      ).toBeVisible();
      await expect(
        page.getByRole('radio', { name: '0', exact: true }),
      ).toBeFocused();
      await page
        .getByRole('radio', { name: String(grade), exact: true })
        .press('Space');
      if (grade === 0)
        await page
          .getByLabel('Комментарий ученику')
          .fill('Проверь знаки.\nРезультат — ноль.');
      // Preview navigation must preserve the teacher draft and must not open a dirty dialog.
      for (const name of [
        'review-photo-1.webp',
        'review-photo-2.webp',
        'review-photo-3.webp',
        'review.pdf',
      ]) {
        await page
          .getByRole('button', { name: `Открыть ${name}`, exact: true })
          .click();
        const viewer = page.getByRole('dialog');
        await expect(
          viewer.getByRole('button', { name: 'Скачать файл' }),
        ).toBeEnabled();
        if (name.endsWith('.pdf'))
          await expect(viewer.getByLabel('Страница 1')).toBeVisible();
        else await expect(viewer.getByRole('img', { name })).toBeVisible();
        await viewer
          .getByRole('button', { name: 'Увеличить', exact: true })
          .click();
        await page
          .getByRole('button', { name: 'Закрыть просмотр', exact: true })
          .click();
      }
      await page.getByRole('link', { name: 'К очереди', exact: true }).click();
      await expect(
        page.getByRole('dialog', { name: 'Уйти без сохранения?' }),
      ).toBeVisible();
      await page.getByRole('button', { name: 'Отмена', exact: true }).click();
      await expect(
        page.getByRole('dialog', { name: 'Уйти без сохранения?' }),
      ).toBeHidden();
      const mutation = '**/api/submissions/*/teacher?*';
      if (grade === 0) {
        await student
          .getByLabel('Текст решения или вопросы')
          .fill('Обновлённый ответ ученика');
        await student
          .getByRole('button', { name: 'Сохранить изменения', exact: true })
          .click();
        await expect(student.getByText(/Изменения сохранены/)).toBeVisible();
        await confirm(page);
        await page
          .getByRole('button', { name: 'Проверить результат на сервере' })
          .click();
        await page
          .getByRole('button', {
            name: 'Открыть обновлённый ответ',
            exact: true,
          })
          .click();
        await expect(
          page.getByText('Обновлённый ответ ученика', { exact: true }),
        ).toBeVisible();
        await expect(
          page.getByRole('radio', { name: '0', exact: true }),
        ).toBeChecked();
        await expect(page.getByLabel('Комментарий ученику')).toHaveValue(
          'Проверь знаки.\nРезультат — ноль.',
        );
        // No commit: unknown outcome must be reconciled before a deliberate retry.
        await page.route(mutation, (route) => route.abort('failed'), {
          times: 1,
        });
        await confirm(page);
        await expect(
          page.getByRole('button', { name: 'Завершить проверку', exact: true }),
        ).toBeDisabled();
        await page
          .getByRole('button', { name: 'Проверить результат на сервере' })
          .click();
        await expect(
          page.getByRole('button', { name: 'Завершить проверку', exact: true }),
        ).toBeEnabled();
      } else {
        // Commit then lose the acknowledgement: a read must recover 5 without another PATCH.
        await page.route(
          mutation,
          async (route) => {
            const result = await route.fetch();
            expect(result.status()).toBe(200);
            await route.abort('failed');
          },
          { times: 1 },
        );
      }
      await page.setViewportSize({ width: 360, height: 800 });
      await page
        .getByRole('button', {
          name: 'Открыть review-photo-1.webp',
          exact: true,
        })
        .press('Enter');
      await expect(
        page
          .getByRole('dialog')
          .getByRole('img', { name: 'review-photo-1.webp', exact: true }),
      ).toBeVisible();
      await page
        .getByRole('button', { name: 'Увеличить', exact: true })
        .click();
      await page.keyboard.press('Escape');
      await expect(page.getByRole('dialog')).toBeHidden();
      expect(
        await page.evaluate(
          () => document.documentElement.scrollWidth <= innerWidth,
        ),
      ).toBeTruthy();
      expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
      await page.screenshot({
        path: `.artifacts/t15b3-review-${grade}-mobile.png`,
        fullPage: true,
      });
      await confirm(page);
      // Automatic safe refetch may already have recovered the commit.
      const reconcile = page.getByRole('button', {
        name: 'Проверить результат на сервере',
      });
      if (await reconcile.isVisible()) await reconcile.click();
      await expect(
        page.getByText(`Проверено · Оценка: ${grade} из 5`, { exact: true }),
      ).toBeVisible();
      await page.reload();
      await expect(
        page.getByText(`Проверено · Оценка: ${grade} из 5`, { exact: true }),
      ).toBeVisible();
      await student.reload();
      await expect(
        student.getByText(`Оценка: ${grade} из 5`, { exact: true }),
      ).toBeVisible();
      await expect(
        student.getByLabel('Текст решения или вопросы'),
      ).toHaveAttribute('readonly', '');
      if (grade === 0)
        await expect(
          student.getByText('Проверь знаки.\nРезультат — ноль.', {
            exact: true,
          }),
        ).toBeVisible();
      await page.getByRole('link', { name: 'К очереди', exact: true }).click();
      await expect(page).toHaveURL(
        new RegExp(
          `student_user_id=${lesson.student_user_id}.*course_id=${lesson.course_id}`,
        ),
      );
      await expect(
        page.getByRole('link').filter({ hasText: title }),
      ).toHaveCount(0);
      await page.goto('/teacher');
      await expect(
        page.getByRole('heading', { name: 'Мой день', exact: true }),
      ).toBeVisible();
      // A different teacher cannot open this answer or its direct file ids.
      const loginResponse = await request.post('/api/auth/login', {
        form: credentials.teacher,
      });
      expect(loginResponse.ok()).toBeTruthy();
      const headers = {
        Authorization: `Bearer ${(await loginResponse.json()).access_token}`,
      };
      const submissionId = new URL(reviewURL).pathname.split('/').pop();
      expect(
        (
          await request.get(
            `/api/submissions/${submissionId}?homework_id=${hw.id}`,
            { headers },
          )
        ).status(),
      ).toBe(404);
      for (const file of sentAnswer.files) {
        expect(
          (
            await request.get(
              `/api/submissions/${submissionId}/files/${file.id}?homework_id=${hw.id}`,
              { headers },
            )
          ).status(),
        ).toBe(404);
      }
      await page
        .getByRole('link', { name: 'На проверку', exact: true })
        .first()
        .click();
      await expect(
        page.getByRole('heading', { name: 'На проверку', exact: true }),
      ).toBeVisible();
    } finally {
      await context.close();
    }
  });

test('day overview: real API, Moscow midnight, independent errors and queue filters', async ({
  page,
}) => {
  await page.clock.setFixedTime(new Date('2026-10-20T20:59:00Z'));
  await login(page, credentials.planning_teacher, '/teacher');
  await expect(
    page.getByText('Сегодня · 20 октября · МСК', { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole('heading', { name: 'Нужно выдать материалы' }),
  ).toBeVisible();
  await expect(page.getByRole('link', { name: 'Вся очередь' })).toBeVisible();
  const nextDay = page.waitForResponse((r) => {
    const url = new URL(r.url());
    return (
      url.pathname === '/api/lessons' &&
      url.searchParams.get('from_date') === '2026-10-20T21:00:00.000Z' &&
      url.searchParams.has('to_date')
    );
  });
  await page.clock.setFixedTime(new Date('2026-10-20T21:01:00Z'));
  await page.reload();
  expect((await nextDay).ok()).toBeTruthy();
  await expect(
    page.getByText('Сегодня · 21 октября · МСК', { exact: true }),
  ).toBeVisible();
  await page.route('**/api/submissions/review-queue?*', (route) =>
    route.abort('failed'),
  );
  await page.reload();
  await expect(
    page.getByRole('button', { name: 'Повторить', exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText('Сегодня · 21 октября · МСК', { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole('heading', { name: 'Нужно выдать материалы' }),
  ).toBeVisible();
  await page.unroute('**/api/submissions/review-queue?*');
  await page.getByRole('button', { name: 'Повторить', exact: true }).click();
  await expect(page.getByRole('link', { name: 'Вся очередь' })).toBeVisible();
  await page.goto(
    `/teacher/review?student_user_id=${lesson.student_user_id}&course_id=${lesson.course_id}`,
  );
  await page.getByRole('button', { name: 'Сбросить фильтры' }).click();
  await expect(page).not.toHaveURL(/student_user_id=\d/);
  await page.goto('/teacher/review?student_user_id=2147483647');
  await expect(
    page.getByText('По этим фильтрам нет работ на проверку.', { exact: true }),
  ).toBeVisible();
  await page.getByRole('button', { name: 'Сбросить фильтры' }).click();
  await page.setViewportSize({ width: 360, height: 800 });
  await page
    .locator('summary')
    .filter({ hasText: /^Курс:/ })
    .click();
  await page.getByRole('combobox', { name: 'Курс', exact: true }).click();
  await expect(page.getByRole('listbox')).toBeVisible();
  await page.keyboard.press('Escape');
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
});
