import { test, expect, type Page } from '@playwright/test';
import { readFileSync } from 'node:fs';
import AxeBuilder from '@axe-core/playwright';
const c = JSON.parse(readFileSync('.artifacts/ui21-credentials.json', 'utf8'));
test.use({ trace: 'off', video: 'off', screenshot: 'off', hasTouch: true });
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
  await dialog
    .getByRole('button', { name: 'Завершить проверку', exact: true })
    .click();
  await expect(dialog).toBeHidden();
}
const pdf = (name: string) => ({
  name,
  mimeType: 'application/pdf',
  buffer: readFileSync('e2e/fixtures/math.pdf'),
});
const photo = {
  name: 'Решение.png',
  mimeType: 'image/png',
  buffer: readFileSync('e2e/fixtures/notebook.png'),
};
for (const grade of [0, 5])
  test(`UX21 both roles grade${grade}: materials, automatic upload, review files, unknown/conflict, lesson thread`, async ({
    page,
    browser,
    request,
  }) => {
    await login(page, c.teacher, `/teacher/lessons/${c.lesson_id}`);
    if (grade === 0) {
      const lectureUpload = page.waitForResponse(
        (r) =>
          r.url().endsWith('/api/lectures') && r.request().method() === 'POST',
      );

      await page
        .getByLabel('Добавить файлы материалов', { exact: true })
        .setInputFiles(pdf('Конспект.pdf'));
      expect((await lectureUpload).status()).toBe(201);
      await expect(
        page.getByText('Загружен · доступен ученику', { exact: true }).first(),
      ).toBeVisible();
      await expect(
        page.getByText('Убрать из очереди', { exact: true }),
      ).toHaveCount(0);
      await expect(
        page.getByRole('navigation', { name: 'Страницы конспектов занятия' }),
      ).toHaveCount(0);
    }
    const title = `Задание UX21 ${grade} ${Date.now()}`;
    await page.getByLabel('Название задания', { exact: true }).fill(title);
    await page
      .getByLabel('Условие', { exact: true })
      .fill('Условие учителя\n' + 'Покажите ход решения. '.repeat(25));
    const issued = page.waitForResponse(
      (r) =>
        r.url().endsWith('/api/homeworks') && r.request().method() === 'POST',
    );
    await page
      .getByRole('button', { name: 'Выдать задание', exact: true })
      .click();
    const issuedResponse = await issued;
    expect(issuedResponse.status()).toBe(201);
    const hw = await issuedResponse.json();
    const studentContext = await browser.newContext({
      baseURL: 'http://127.0.0.1:5173',
      viewport: { width: 360, height: 800 },
      hasTouch: true,
    });
    const student = await studentContext.newPage();
    try {
      await login(student, c.student, `/student/homeworks/${hw.id}`);
      await student
        .getByLabel('Текст решения или вопросы', { exact: true })
        .fill('Вопрос ученика\nКак выбрать способ решения?');
      await expect(
        student.getByRole('button', { name: 'Проверить сохранение файлов' }),
      ).toHaveCount(0);
      await expect(
        student.getByRole('button', {
          name: 'Сохранить черновик',
          exact: true,
        }),
      ).toHaveCount(0);
      await student
        .getByLabel('Добавить файлы', { exact: true })
        .setInputFiles([photo, pdf('Моё решение.pdf')]);
      await expect(
        student.locator('article[aria-label^="Сохранён:"]'),
      ).toHaveCount(2);
      await student
        .getByLabel('Заменить Моё решение.pdf', { exact: true })
        .setInputFiles(pdf('Исправленное решение.pdf'));
      await expect(
        student.locator(
          'article[aria-label="Сохранён: Исправленное решение.pdf"]',
        ),
      ).toBeVisible();
      await expect(
        student.getByRole('button', { name: 'Отправить решение', exact: true }),
      ).toBeEnabled();
      const sent = student.waitForResponse(
        (r) => r.url().includes('/submit?') && r.request().method() === 'POST',
      );
      await student
        .getByRole('button', { name: 'Отправить решение', exact: true })
        .click();
      const sentAnswer = await (await sent).json();
      await student.goto('/student');
      await expect(
        student.getByRole('heading', { name: 'На проверке у учителя' }),
      ).toBeVisible();
      await expect(
        student.getByRole('heading', { name: title, exact: true }),
      ).toBeVisible();
      await page.goto('/teacher');
      await expect(
        page.getByRole('heading', { name: 'Нужно выдать материалы' }),
      ).toBeVisible();
      await expect(
        page.getByText('Прошедшее занятие без материалов', { exact: false }),
      ).toBeVisible();
      await page.screenshot({
        path: `.artifacts/ui21-teacher-day-${grade}.png`,
        fullPage: true,
      });
      await page.goto('/teacher/review');
      await page.getByRole('link').filter({ hasText: title }).click();
      await page
        .getByRole('radio', { name: String(grade), exact: true })
        .press('Space');
      await page
        .getByLabel('Комментарий ученику')
        .fill('Комментарий учителя\nПроверь знаки.');
      await page
        .getByLabel('Добавить файлы к проверке', { exact: true })
        .setInputFiles([pdf('Разбор.pdf'), photo]);
      await expect(
        page.getByText('Отправится вместе с проверкой', { exact: true }),
      ).toHaveCount(2);
      const feedbackName =
        grade === 5 ? 'Исправленный разбор.pdf' : 'Разбор.pdf';
      if (grade === 5) {
        await page
          .getByLabel('Заменить файл проверки Разбор.pdf', { exact: true })
          .setInputFiles(pdf(feedbackName));
        await page
          .getByLabel('Добавить файлы к проверке', { exact: true })
          .setInputFiles(pdf('Лишний.pdf'));
        await page
          .locator('article')
          .filter({ has: page.getByText('Лишний.pdf', { exact: true }) })
          .getByRole('button', { name: 'Удалить файл', exact: true })
          .click();
        await expect(
          page.getByText('Отправится вместе с проверкой', { exact: true }),
        ).toHaveCount(2);
      }
      if (grade === 0) {
        await student.goto(`/student/homeworks/${hw.id}`);
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
          page.getByText('Отправится вместе с проверкой', { exact: true }),
        ).toHaveCount(2);
      } else {
        await page.route(
          '**/api/submissions/*/review?*',
          async (route) => {
            const r = await route.fetch();
            expect(r.status()).toBe(200);
            await route.abort('failed');
          },
          { times: 1 },
        );
      }
      await page.screenshot({
        path: `.artifacts/ui21-review-${grade}-desktop.png`,
        fullPage: true,
      });
      await page.setViewportSize({ width: 360, height: 800 });
      await confirm(page);
      const recovery = page.getByRole('button', {
        name: 'Проверить результат на сервере',
      });
      if (await recovery.isVisible()) await recovery.click();
      await expect(
        page.getByText(`Проверено · Оценка: ${grade} из 5`, { exact: true }),
      ).toBeVisible();
      await expect(
        page.getByRole('button', {
          name: `Открыть ${feedbackName}`,
          exact: true,
        }),
      ).toBeVisible();
      await student.goto(`/student/lessons/${c.lesson_id}`);
      const thread = student.locator('article').filter({
        has: student.getByRole('heading', { name: title, exact: true }),
      });
      await expect(
        thread.getByRole('heading', { name: 'Задание учителя', exact: true }),
      ).toBeVisible();
      await expect(
        thread.getByRole('heading', { name: 'Ваше решение', exact: true }),
      ).toBeVisible();
      await expect(
        thread.getByText(`Оценка: ${grade} из 5`, { exact: true }),
      ).toBeVisible();
      await thread
        .getByRole('button', { name: `Открыть ${feedbackName}`, exact: true })
        .click();
      await expect(
        student.getByRole('dialog').getByLabel('Страница 1'),
      ).toBeVisible();
      await student
        .getByRole('button', { name: 'Увеличить', exact: true })
        .click();
      await student.keyboard.press('Escape');
      await expect(student.getByRole('dialog')).toBeHidden();
      await student.screenshot({
        path: `.artifacts/ui21-student-thread-${grade}-360.png`,
        fullPage: true,
      });
      expect(
        await student.evaluate(
          () => document.documentElement.scrollWidth <= innerWidth,
        ),
      ).toBeTruthy();
      expect(
        (await new AxeBuilder({ page: student }).analyze()).violations,
      ).toEqual([]);
      const foreign = await request.post('/api/auth/login', {
        form: {
          username: c.foreign_teacher.username,
          password: c.foreign_teacher.password,
        },
      });
      const headers = {
        Authorization: `Bearer ${(await foreign.json()).access_token}`,
      };
      expect(
        (
          await request.get(
            `/api/submissions/${sentAnswer.id}?homework_id=${hw.id}`,
            { headers },
          )
        ).status(),
      ).toBe(404);
    } finally {
      await studentContext.close();
    }
  });

test('UX21 student week/day signals and compact notifications', async ({
  page,
}) => {
  await login(page, c.student, '/student/schedule');
  await expect(
    page.getByRole('button', { name: 'Текущая неделя', exact: true }),
  ).toHaveAttribute('aria-pressed', 'true');
  await page
    .getByRole('button', { name: 'Предыдущая неделя', exact: true })
    .click();
  await expect(
    page.getByRole('button', { name: 'Предыдущая неделя', exact: true }),
  ).toHaveAttribute('aria-pressed', 'true');
  await page
    .getByRole('button', { name: 'Текущая неделя', exact: true })
    .click();
  await page.setViewportSize({ width: 360, height: 800 });
  await expect(
    page.getByRole('button', { name: /есть занятия/ }).first(),
  ).toBeVisible();
  await page.screenshot({
    path: '.artifacts/ui21-student-schedule-360.png',
    fullPage: true,
  });
  await page.goto('/notifications');
  await expect(
    page.getByText('Новое · не прочитано', { exact: true }).first(),
  ).toBeVisible();
  await page
    .getByRole('button', { name: 'Открыть уведомление', exact: true })
    .first()
    .click();
  await expect(page).not.toHaveURL('/notifications');
  await page.goto('/notifications');
  await expect(
    page.getByText('Прочитано', { exact: true }).first(),
  ).toBeVisible();
  await expect(
    page.getByText('Новое · не прочитано', { exact: true }).first(),
  ).toBeVisible();
  await expect(
    page.getByRole('navigation', { name: 'Страницы списка' }),
  ).toHaveCount(0);
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
});

test('UX21 success feedback disappears without reload and elapsed lesson is completed', async ({
  page,
}) => {
  await login(page, c.teacher, `/teacher/courses/${c.course_id}`);
  await page.getByText('Настройки обучения', { exact: true }).click();
  await page
    .getByLabel('Описание', { exact: true })
    .fill('Проверка закрытия сообщения');
  await page
    .getByRole('button', { name: 'Сохранить курс', exact: true })
    .click();
  await expect(page.locator('.feedback')).toContainText('Курс сохранён');
  await page.mouse.move(0, 0);
  await expect(page.locator('.feedback')).toHaveCount(0, { timeout: 7000 });
  await page.goto(`/teacher/lessons/${c.past_lesson_id}`);
  await expect(page.getByText(/МСК.*Завершено/).first()).toBeVisible();
});
