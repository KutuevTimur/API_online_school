import { test, expect, type Page } from '@playwright/test';
import { readFileSync } from 'node:fs';
import AxeBuilder from '@axe-core/playwright';
const credentials = JSON.parse(
  readFileSync('.artifacts/t14e-credentials.json', 'utf8'),
);
test.use({ trace: 'off', screenshot: 'off', video: 'off' });
async function login(page: Page, path = '/teacher/schedule') {
  await page.goto('/login?returnTo=' + encodeURIComponent(path));
  await page
    .getByLabel('Логин', { exact: true })
    .fill(credentials.planning_teacher.username);
  await page
    .getByLabel('Пароль', { exact: true })
    .fill(credentials.planning_teacher.password);
  await page.getByRole('button', { name: 'Войти', exact: true }).click();
  await expect(page).toHaveURL(path);
}
async function api(page: Page, path: string, method = 'GET', body?: unknown) {
  return page.evaluate(
    async ({ path, method, body }) => {
      const { request } = await import(String('/src/shared/api/client.ts'));
      return request(path, { method, body });
    },
    { path, method, body },
  );
}
async function chooseStudent(page: Page) {
  await page
    .getByRole('combobox', { name: 'Ученик', exact: true })
    .fill(credentials.planning_student.username);
  await page
    .getByRole('option', { name: /Synthetic read_student/ })
    .first()
    .click();
  await expect(
    page.getByRole('combobox', { name: 'Курс ученика', exact: true }),
  ).toHaveValue(/Алгебра/);
}
test('calendar to four-week series, move, extend, unknown confirmation receipt and narrow keyboard', async ({
  page,
}) => {
  await login(page);
  await page
    .getByRole('button', { name: 'Следующая неделя', exact: true })
    .click();
  await page
    .getByRole('button', { name: 'Добавить занятие', exact: true })
    .click();
  await page.getByLabel('Дата занятия', { exact: true }).click();
  await expect(
    page.getByRole('button', { name: 'Следующий месяц', exact: true }),
  ).toBeVisible();
  await page.keyboard.press('Escape');
  await expect(
    page.getByRole('dialog', { name: 'Добавить занятие', exact: true }),
  ).toBeVisible();
  await chooseStudent(page);
  const freeTime = await page.evaluate(async () => {
    const { request } = await import(String('/src/shared/api/client.ts'));
    const data = await request<{ items: { scheduled_at: string }[] }>(
      '/lessons',
      { params: { limit: 1000, view: 'active' } },
    );
    const occupied = new Set(
      data.items.map((l) =>
        new Intl.DateTimeFormat('en-GB', {
          hour: '2-digit',
          minute: '2-digit',
          timeZone: 'Europe/Moscow',
        }).format(new Date(l.scheduled_at)),
      ),
    );
    for (let minute = 8 * 60; minute < 18 * 60; minute++) {
      const time = `${String(Math.floor(minute / 60)).padStart(2, '0')}:${String(minute % 60).padStart(2, '0')}`;
      if (!occupied.has(time)) return time;
    }
    throw new Error('No free synthetic series time');
  });
  await page.getByLabel('Время начала, МСК', { exact: true }).fill(freeTime);
  await page
    .getByLabel('Название занятия', { exact: true })
    .fill('Synthetic regular UI');
  await page.getByLabel('Закрепить время еженедельно', { exact: true }).check();
  await page
    .getByRole('button', { name: 'Предпросмотр записи', exact: true })
    .click();
  await expect(
    page.getByRole('dialog', {
      name: 'Регулярное расписание · МСК',
      exact: true,
    }),
  ).toBeVisible();
  await expect(
    page.getByText(/4 встреч. Продление только вручную/),
  ).toBeVisible();
  const confirm = '**/api/lessons/regular/operations/*/confirm';
  await page.route(confirm, async (route) => {
    const response = await route.fetch();
    expect(response.status()).toBe(200);
    await route.abort('failed');
  });
  await page
    .getByRole('button', { name: 'Подтвердить запись', exact: true })
    .click();
  await expect(
    page.getByRole('button', {
      name: 'Проверить результат операции',
      exact: true,
    }),
  ).toBeVisible();
  await page.unroute(confirm);
  await page
    .getByRole('button', { name: 'Проверить результат операции', exact: true })
    .click();
  await expect(
    page.getByText('Synthetic regular UI', { exact: true }),
  ).toBeVisible();
  await page
    .getByText('Управление встречей и обучением', { exact: true })
    .click();
  await page.getByRole('button', { name: 'Перенести', exact: true }).click();
  await page.getByLabel('Время начала, МСК', { exact: true }).fill('18:30');
  await page
    .getByRole('button', { name: 'Проверить перенос', exact: true })
    .click();
  await expect(page.getByText(/Было:.*станет:/)).toBeVisible();
  await page.route('**/api/lessons/*', (route) =>
    route.request().method() === 'PATCH'
      ? route.fulfill({
          status: 409,
          json: { detail: 'Synthetic stale version' },
        })
      : route.continue(),
  );
  await page
    .getByRole('button', { name: 'Подтвердить перенос', exact: true })
    .click();
  await expect(
    page.getByRole('button', {
      name: 'Проверить результат сохранения',
      exact: true,
    }),
  ).toBeVisible();
  await expect(
    page.getByLabel('Время начала, МСК', { exact: true }),
  ).toHaveValue('18:30');
  await page.unroute('**/api/lessons/*');
  await page
    .getByRole('button', {
      name: 'Проверить результат сохранения',
      exact: true,
    })
    .click();
  await page
    .getByRole('button', {
      name: 'Сравнение выполнено, разрешить осознанный повтор',
      exact: true,
    })
    .click();
  await page
    .getByRole('button', { name: 'Проверить перенос', exact: true })
    .click();
  await page
    .getByRole('button', { name: 'Подтвердить перенос', exact: true })
    .click();
  await expect(
    page.getByRole('dialog', { name: 'Перенести занятие', exact: true }),
  ).toHaveCount(0);
  await expect(page.getByText(/18:30.*Запланировано/)).toBeVisible();
  await page.getByText('Регулярное время', { exact: true }).click();
  await page.getByLabel('Добавить недель, 1–12', { exact: true }).fill('2');
  await page
    .getByRole('button', { name: 'Предпросмотр продления', exact: true })
    .click();
  await expect(
    page.getByText(/2 встреч. Продление только вручную/),
  ).toBeVisible();
  await page
    .getByRole('button', { name: 'Подтвердить запись', exact: true })
    .click();
  await expect(page.getByRole('dialog')).toHaveCount(0);
  await page.getByRole('link', { name: 'К расписанию', exact: true }).click();
  await expect(page).toHaveURL(/week=/);
  await page.setViewportSize({ width: 360, height: 800 });
  await page
    .getByRole('button', { name: 'Добавить занятие', exact: true })
    .press('Enter');
  await expect(
    page.getByRole('dialog', { name: 'Добавить занятие', exact: true }),
  ).toBeVisible();
  await page.getByRole('button', { name: 'Отмена', exact: true }).click();
  await page
    .getByRole('button', { name: 'Закрыть форму', exact: true })
    .click();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  await page.screenshot({ path: '.artifacts/t15b2-calendar-360.png' });
  await page.setViewportSize({ width: 1280, height: 900 });
  await page.reload();
  await expect(
    page
      .getByLabel('Календарь недели', { exact: true })
      .getByText(/18:30/)
      .first(),
  ).toBeVisible();
  await page.screenshot({ path: '.artifacts/t15b2-calendar-1280.png' });
});
test('recipient reminders, lecture, homework deadline, debt, read-only archive and student filter', async ({
  page,
}) => {
  await login(page);
  const f = credentials.planning_read.lessons[0];
  const lesson = (await api(page, '/lessons', 'POST', {
    course_id: f.course_id,
    student_user_id: f.student_user_id,
    title: 'Synthetic materials UI',
    scheduled_at: '2026-10-01T10:00:00+03:00',
  })) as { id: number };
  const source = (await api(page, '/lessons', 'POST', {
    course_id: f.course_id,
    student_user_id: f.student_user_id,
    title: 'Synthetic prior debt lesson',
    scheduled_at: '2026-09-01T10:00:00+03:00',
  })) as { id: number };
  const debtTitle = 'Synthetic old debt ' + lesson.id;
  const oldHomework = (await page.evaluate(
    async ({ source, student, title }) => {
      const { request } = await import(String('/src/shared/api/client.ts'));
      const body = new FormData();
      body.append('lesson_id', String(source));
      body.append('student_user_id', String(student));
      body.append('title', title);
      body.append('description', 'Synthetic prior work');
      return request('/homeworks', { method: 'POST', body });
    },
    { source: source.id, student: f.student_user_id, title: debtTitle },
  )) as { id: number };
  await page.goto(`/teacher/lessons/${lesson.id}?student=${f.student_user_id}`);
  await expect(
    page.getByText('Нужно выдать ДЗ', { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText('Нужно добавить конспект', { exact: true }),
  ).toBeVisible();
  await page
    .getByRole('button', { name: 'Не задавать ДЗ', exact: true })
    .click();
  await expect(
    page.getByText('ДЗ не требуется', { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText('Нужно добавить конспект', { exact: true }),
  ).toBeVisible();
  await page
    .getByRole('button', { name: 'Снова напоминать о ДЗ', exact: true })
    .click();
  await page.route('**/api/lectures', (route) =>
    route.request().method() === 'POST'
      ? route.fulfill({ status: 500, json: {} })
      : route.continue(),
  );
  await page.getByLabel('Добавить конспект', { exact: true }).setInputFiles({
    name: 'Synthetic note.pdf',
    mimeType: 'application/pdf',
    buffer: readFileSync('e2e/fixtures/math.pdf'),
  });
  await expect(
    page.getByRole('button', { name: 'Проверить загрузку', exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText('Нужно выдать ДЗ', { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText('Нужно добавить конспект', { exact: true }),
  ).toBeVisible();
  await page.unroute('**/api/lectures');
  await page
    .getByRole('button', { name: 'Проверить загрузку', exact: true })
    .click();
  await expect(page.getByText(/Список обновлён/)).toBeVisible();
  await page
    .getByRole('button', { name: 'Загрузить файл', exact: true })
    .click();
  await expect(
    page.getByText('Конспект загружен', { exact: true }),
  ).toBeVisible();
  await page
    .getByRole('button', { name: 'Выдать задание', exact: true })
    .click();
  await page
    .getByLabel('Название задания', { exact: true })
    .fill('Synthetic homework UI');
  await page.getByLabel('Условие', { exact: true }).fill('Решите x²=4');
  await page
    .getByRole('button', { name: 'Выдать задание', exact: true })
    .click();
  await expect(
    page.getByRole('heading', { name: 'Synthetic homework UI', exact: true }),
  ).toBeVisible();
  await page
    .getByRole('button', { name: 'Добавить долг', exact: true })
    .click();
  await page
    .getByRole('button', {
      name: `Добавить «${debtTitle}» как долг`,
      exact: true,
    })
    .click();
  await expect
    .poll(() =>
      page.evaluate(
        async ({ lesson, student, id }) => {
          const { request } = await import(String('/src/shared/api/client.ts'));
          const items = await request('/homeworks', {
            params: { lesson_id: lesson, student_user_id: student },
          });
          return items.filter(
            (h: { id: number; placement_kind: string }) =>
              h.id === id && h.placement_kind === 'debt',
          ).length;
        },
        { lesson: lesson.id, student: f.student_user_id, id: oldHomework.id },
      ),
    )
    .toBe(1);
  await page.screenshot({ path: '.artifacts/t15b2-materials-1280.png' });
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  await page.setViewportSize({ width: 360, height: 800 });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await page.screenshot({ path: '.artifacts/t15b2-materials-360.png' });
  await page
    .getByText('Управление встречей и обучением', { exact: true })
    .click();
  await page.getByRole('button', { name: 'В архив', exact: true }).click();
  await page.getByRole('button', { name: 'Архивировать', exact: true }).click();
  await expect(page.getByText(/Только просмотр:/)).toBeVisible();
  await expect(
    page.getByRole('button', { name: 'Выдать задание', exact: true }),
  ).toHaveCount(0);
});
test('norm exception and pause, calendar error/loading/recovery and empty reminders', async ({
  page,
}) => {
  await login(page, '/teacher/students');
  await page.goto('/teacher/students?sort=attention&attention=lecture');
  await page
    .getByRole('link')
    .filter({ hasText: credentials.planning_student.username })
    .click();
  await page
    .getByRole('list', { name: 'Прошедшие занятия ученика', exact: true })
    .getByRole('link', { name: /Квадратные уравнения/ })
    .click();
  await page.getByRole('link', { name: 'К ученику', exact: true }).click();
  await page.getByRole('link', { name: 'Свои ученики', exact: true }).click();
  await expect(page).toHaveURL(/sort=attention&attention=lecture/);
  await page
    .getByRole('link')
    .filter({ hasText: credentials.planning_student.username })
    .click();
  await page.getByText('Настройки ученика', { exact: true }).click();
  await page.getByText('Недельная норма', { exact: true }).click();
  await page
    .getByRole('button', { name: 'Изменить недельную норму', exact: true })
    .click();
  await page
    .getByLabel('Занятий в неделю (пусто — норма не задана)', { exact: true })
    .fill('2');
  await page
    .getByRole('button', { name: 'Сохранить норму', exact: true })
    .click();
  await expect(
    page.getByText('Норма сохранена', { exact: true }),
  ).toBeVisible();
  await page.getByLabel('Пауза без недобора', { exact: true }).check();
  await page
    .getByRole('button', { name: 'Сохранить норму', exact: true })
    .click();
  await expect(page.getByText(/пауза без недобора · все курсы/)).toBeVisible();
  await page.route('**/api/lessons?**', (route) =>
    route.fulfill({ status: 500, json: {} }),
  );
  await page.goto('/teacher/schedule');
  await expect(
    page.getByRole('button', { name: 'Повторить', exact: true }).first(),
  ).toBeVisible();
  await page.unroute('**/api/lessons?**');
  await page
    .getByRole('button', { name: 'Повторить', exact: true })
    .first()
    .click();
  await expect(
    page.getByLabel('Календарь недели', { exact: true }),
  ).toBeVisible();
  await page.setViewportSize({ width: 360, height: 800 });
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
});
