import { test, expect, type Page } from '@playwright/test';
import { readFileSync } from 'node:fs';
import AxeBuilder from '@axe-core/playwright';
const credentials = JSON.parse(
  readFileSync('.artifacts/t14e-credentials.json', 'utf8'),
);
const fixture = credentials.student_read;
test.use({ trace: 'off', screenshot: 'off', video: 'off', hasTouch: true });
async function login(page: Page, empty = false) {
  await page.goto('/login');
  const account = credentials[empty ? 'read_empty' : 'read_student'];
  await page.getByLabel('Логин', { exact: true }).fill(account.username);
  await page.getByLabel('Пароль', { exact: true }).fill(account.password);
  await page.getByRole('button', { name: 'Войти', exact: true }).click();
  await expect(
    page.getByRole('heading', { name: 'Мой день', exact: true }),
  ).toBeVisible();
}
test('real API my day, two teachers, course → lesson → PDF, direct reload and archive reading', async ({
  page,
}) => {
  await login(page);
  await expect(page.locator('p').filter({ hasText: /^Оценка:/ })).toContainText(
    '0 из 5',
  );
  await expect(
    page.getByText('Ссылка на встречу ещё не добавлена'),
  ).toBeVisible();
  await page.screenshot({
    path: '.artifacts/t15a-myday-desktop.png',
    fullPage: true,
  });
  await page.goto('/student/courses');
  await expect(
    page.getByRole('link', { name: 'Алгебра · учебный курс', exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole('link', {
      name: 'Геометрия · второй преподаватель',
      exact: true,
    }),
  ).toBeVisible();
  await expect(page.getByText('HIDDEN foreign course')).toHaveCount(0);
  await page
    .getByRole('link', { name: 'Алгебра · учебный курс', exact: true })
    .click();
  await page
    .getByRole('link', { name: 'Квадратные уравнения', exact: true })
    .click();
  await page.reload();
  await expect(
    page.getByRole('heading', { name: 'Квадратные уравнения', exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText(/МСК · 55 мин · (Запланировано|Идёт|Завершено)/),
  ).toBeVisible();
  await page
    .getByRole('button', { name: 'Открыть Учебный пример.pdf', exact: true })
    .click();
  await expect(
    page.getByText('Страница 1 из 2', { exact: true }),
  ).toBeVisible();
  await page
    .getByRole('button', { name: 'Следующая страница', exact: true })
    .click();
  await expect(
    page.getByText('Synthetic math - page 2', { exact: true }),
  ).toHaveCount(1);
  await page.keyboard.press('Escape');
  await expect(
    page.getByRole('button', {
      name: 'Открыть Учебный пример.pdf',
      exact: true,
    }),
  ).toBeFocused();
  await page.goto('/student/courses?view=archive');
  await page
    .getByRole('link', { name: 'Архив · повторение', exact: true })
    .click();
  await page.getByRole('button', { name: 'Архив', exact: true }).click();
  await page
    .getByRole('link', { name: 'Квадратные уравнения', exact: true })
    .click();
  await expect(
    page.getByText(/Только просмотр: Курс в архиве/).first(),
  ).toBeVisible();
  await page
    .getByRole('button', { name: 'Открыть Учебный пример.pdf', exact: true })
    .click();
  await expect(
    page.getByText('Страница 1 из 2', { exact: true }),
  ).toBeVisible();
  const download = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Скачать файл', exact: true }).click();
  expect((await download).suggestedFilename()).toContain('.pdf');
  await page.keyboard.press('Escape');
  await expect(
    page.getByRole('button', { name: /Отправить|Загрузить|Создать|Перенести/ }),
  ).toHaveCount(0);
  await expect(page.getByRole('dialog')).toHaveCount(0);
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  await page.screenshot({
    path: '.artifacts/t15a-lesson-desktop.png',
    fullPage: true,
  });
});
test('compact week without hour grid, URL restoration, mobile day switch, keyboard and zoom', async ({
  page,
}) => {
  await login(page);
  // Synthetic lessons are relative to seed time and may span Moscow weeks.
  // Read actual dates rather than assuming all three statuses are in today's week.
  const lessons: { id: number; scheduled_at: string }[] = [];
  for (const item of fixture.lessons.slice(0, 3)) {
    const response = page.waitForResponse(
      (r) =>
        new URL(r.url()).pathname === `/api/lessons/${item.id}` &&
        r.status() === 200,
    );
    await page.goto(`/student/lessons/${item.id}`);
    lessons.push(await (await response).json());
  }
  const moscowDate = (value: string | number) =>
    new Intl.DateTimeFormat('en-CA', {
      timeZone: 'Europe/Moscow',
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
    }).format(new Date(value));
  const todayMonday = new Date(moscowDate(Date.now()) + 'T00:00:00Z');
  todayMonday.setUTCDate(
    todayMonday.getUTCDate() - ((todayMonday.getUTCDay() + 6) % 7),
  );
  const schedulePath =
    '/student/schedule?view=all&week=' + moscowDate(lessons[0].scheduled_at);

  await page.goto('/student/schedule?view=all');
  await expect(page.getByLabel('Календарь недели')).toBeVisible();
  await expect(
    page.getByLabel('Календарь недели').locator('section'),
  ).toHaveCount(7);
  await expect(page.getByText('08:00', { exact: true })).toHaveCount(0);
  await expect(page.getByRole('heading', { name: /МСК/ })).toBeVisible();
  await page
    .getByRole('button', { name: 'Следующая неделя', exact: true })
    .click();
  const next = page.url();
  await page.reload();
  expect(page.url()).toBe(next);
  await page
    .getByRole('button', { name: 'Текущая неделя', exact: true })
    .click();
  await expect(page).toHaveURL(
    new RegExp('week=' + todayMonday.toISOString().slice(0, 10)),
  );
  await page.goto(schedulePath);
  await expect(
    page
      .locator(`[href="/student/lessons/${fixture.lessons[0].id}"]`)
      .filter({ hasText: 'Квадратные уравнения' }),
  ).toBeVisible();
  await expect(page.getByText('Загружаем…', { exact: true })).toHaveCount(0);
  await expect(
    page
      .getByRole('link', { name: 'Алгебра · учебный курс', exact: true })
      .first(),
  ).toBeVisible();
  for (const [index, status] of [
    [1, 'Завершено'],
    [2, 'Отменено'],
  ] as const) {
    await page.goto(
      '/student/schedule?view=all&week=' +
        moscowDate(lessons[index].scheduled_at),
    );
    await expect(
      page.getByRole('article').filter({
        has: page.locator(`[href="/student/lessons/${lessons[index].id}"]`),
      }),
    ).toContainText('55 мин · ' + status);
  }
  await page.goto(schedulePath);
  await expect(
    page.locator(`[href="/student/lessons/${lessons[0].id}"]`),
  ).toBeVisible();
  const emptyDay = (
    await page
      .getByLabel('Календарь недели')
      .locator('section')
      .allTextContents()
  ).findIndex((text) => text.includes('В этот день занятий нет.'));
  expect(emptyDay).toBeGreaterThanOrEqual(0);
  await page.screenshot({
    path: '.artifacts/t15a-schedule-desktop.png',
    fullPage: true,
  });
  const lessonLink = page
    .getByRole('link', {
      name: 'Открыть занятие: Квадратные уравнения',
      exact: true,
    })
    .first();
  await lessonLink.focus();
  await page.keyboard.press('Enter');
  await expect(
    page.getByRole('heading', { name: 'Квадратные уравнения', exact: true }),
  ).toBeVisible();
  await page.goBack();
  const courseLink = page
    .getByRole('link', { name: 'Алгебра · учебный курс', exact: true })
    .first();
  await courseLink.click();
  await expect(
    page.getByRole('heading', { name: 'Алгебра · учебный курс', exact: true }),
  ).toBeVisible();
  await page.goBack();
  await page.setViewportSize({ width: 360, height: 780 });
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await page
    .getByLabel('День недели', { exact: true })
    .getByRole('button')
    .nth(emptyDay)
    .click();
  await expect(
    page
      .getByText('В этот день занятий нет.', { exact: true })
      .filter({ visible: true }),
  ).toBeVisible();
  await page
    .getByLabel('День недели', { exact: true })
    .getByRole('button')
    .nth(5)
    .click();
  await expect(
    page.getByLabel('День недели', { exact: true }).getByRole('button').nth(5),
  ).toHaveAttribute('aria-pressed', 'true');
  expect(new URL(page.url()).searchParams.get('day')).toBe('5');
  await page.reload();
  await expect(
    page.getByLabel('День недели', { exact: true }).getByRole('button').nth(5),
  ).toHaveAttribute('aria-pressed', 'true');
  await page
    .getByLabel('День недели', { exact: true })
    .getByRole('button')
    .nth(5)
    .focus();
  await page.keyboard.press('Tab');
  await expect(
    page.getByLabel('День недели', { exact: true }).getByRole('button').nth(6),
  ).toBeFocused();
  await page.keyboard.press('Enter');
  await expect(
    page.getByLabel('День недели', { exact: true }).getByRole('button').nth(6),
  ).toHaveAttribute('aria-pressed', 'true');
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await expect(page.getByRole('dialog')).toHaveCount(0);
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  await page.screenshot({
    path: '.artifacts/t15a-schedule-mobile.png',
    fullPage: true,
  });
  await page.setViewportSize({ width: 640, height: 450 });
  await page.evaluate(() => {
    document.body.style.zoom = '2';
  });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await expect(
    page.getByRole('button', { name: 'Текущая неделя', exact: true }),
  ).toBeVisible();
});
test('empty student, independent failure, loading, retry, offline and 403/404 recovery', async ({
  page,
  context,
}) => {
  await login(page, true);
  await expect(page.getByText(/Пока нет предстоящих занятий/)).toBeVisible();
  await expect(page.getByText('Заданий к выполнению пока нет.')).toBeVisible();
  await page.getByRole('button', { name: 'Выйти', exact: true }).click();
  await expect(
    page.getByRole('button', { name: 'Войти', exact: true }),
  ).toBeVisible();
  await login(page);
  await page.route('**/api/homeworks/my/page?*', (route) =>
    route.fulfill({ status: 503, contentType: 'application/json', body: '{}' }),
  );
  await page.reload();
  await expect(
    page.getByRole('link', { name: 'Открыть занятие', exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole('button', { name: 'Повторить', exact: true }).first(),
  ).toBeVisible();
  await page.unroute('**/api/homeworks/my/page?*');
  await page
    .getByRole('button', { name: 'Повторить', exact: true })
    .first()
    .click();
  await expect(page.getByText('К выполнению', { exact: true })).toBeVisible();
  for (const status of [403, 404]) {
    await page.route('**/api/lessons/999999', (route) =>
      route.fulfill({ status, contentType: 'application/json', body: '{}' }),
    );
    await page.goto('/student/lessons/999999');
    await expect(
      page.getByText(
        status === 403
          ? 'Нет доступа к этому материалу'
          : 'Материал больше недоступен',
        { exact: true },
      ),
    ).toBeVisible();
    await expect(
      page.getByRole('link', { name: 'В мой день', exact: true }),
    ).toBeVisible();
    await page.unroute('**/api/lessons/999999');
  }
  let release!: () => void;
  const paused = new Promise<void>((resolve) => {
    release = resolve;
  });
  await page.route('**/api/courses?*', async (route) => {
    await paused;
    await route.continue();
  });
  await page.goto('/student/courses');
  await expect(page.getByText('Загружаем…', { exact: true })).toBeVisible();
  release();
  await expect(
    page.getByRole('link', { name: 'Алгебра · учебный курс', exact: true }),
  ).toBeVisible();
  await page.unroute('**/api/courses?*');
  await context.setOffline(true);
  await page.getByRole('button', { name: 'Архив', exact: true }).click();
  await expect(
    page.getByRole('button', { name: 'Повторить', exact: true }),
  ).toBeVisible();
  await context.setOffline(false);
  await page.getByRole('button', { name: 'Повторить', exact: true }).click();
  await expect(
    page.getByRole('link', { name: 'Архив · повторение', exact: true }),
  ).toBeVisible();
});

test('meeting link is explicit, safe and external; unsafe protocol has no action', async ({
  page,
}) => {
  await login(page);
  const id = fixture.lessons[0].id;
  await page.route(`**/api/lessons/${id}`, async (route) => {
    const response = await route.fetch();
    const body = await response.json();
    await route.fulfill({
      json: {
        ...body,
        effective_call_url: 'https://example.test/synthetic-meeting',
      },
    });
  });
  await page.goto(`/student/lessons/${id}`);
  const link = page.getByRole('link', { name: 'Открыть встречу', exact: true });
  await expect(link).toHaveAttribute('target', '_blank');
  await expect(link).toHaveAttribute('rel', 'noopener noreferrer');
  await expect(link).toHaveAttribute(
    'href',
    'https://example.test/synthetic-meeting',
  );
  await page.unroute(`**/api/lessons/${id}`);
  await page.route(`**/api/lessons/${id}`, async (route) => {
    const response = await route.fetch();
    await route.fulfill({
      json: {
        ...(await response.json()),
        effective_call_url: 'javascript:alert(1)',
      },
    });
  });
  await page.reload();
  await expect(
    page.getByText('Ссылка на встречу ещё не добавлена'),
  ).toBeVisible();
  await expect(
    page.getByRole('link', { name: 'Открыть встречу', exact: true }),
  ).toHaveCount(0);
});

test('student pages and protected PDF remain usable at360 with touch and keyboard', async ({
  page,
}) => {
  await page.setViewportSize({ width: 360, height: 780 });
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await login(page);
  await expect(
    page.getByRole('heading', { name: 'Ближайшее занятие', exact: true }),
  ).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  await expect(
    page.getByText('Ссылка на встречу ещё не добавлена'),
  ).toBeVisible();
  await expect(
    page.getByRole('link', { name: 'Открыть задание', exact: true }),
  ).toHaveCount(2);
  await expect(page.locator('p').filter({ hasText: /^Оценка:/ })).toContainText(
    '0 из 5',
  );
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  await page.screenshot({
    path: '.artifacts/t15a-myday-mobile.png',
    fullPage: true,
  });
  const task = page
    .getByRole('link', { name: 'Открыть задание', exact: true })
    .first();
  const destination = await task.getAttribute('href');
  await task.focus();
  await expect(task).toBeFocused();
  await page.keyboard.press('Enter');
  await expect(page).toHaveURL(destination!);
  await expect(
    page.getByRole('heading', { name: 'Условие', exact: true }),
  ).toBeVisible();
  await page.goto(`/student/lessons/${fixture.lessons[0].id}`);
  const open = page.getByRole('button', {
    name: 'Открыть Учебный пример.pdf',
    exact: true,
  });
  await open.click();
  await expect(
    page.getByText('Страница 1 из 2', { exact: true }),
  ).toBeVisible();
  await page
    .getByRole('button', { name: 'Следующая страница', exact: true })
    .tap();
  await expect(
    page.getByText('Страница 2 из 2', { exact: true }),
  ).toBeVisible();
  await page.keyboard.press('Escape');
  await expect(page.getByRole('dialog')).toHaveCount(0);
  await expect(open).toBeFocused();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  await page.screenshot({
    path: '.artifacts/t15a-lesson-mobile.png',
    fullPage: true,
  });
  await page.goto('/student/courses');
  await expect(
    page.getByRole('heading', { name: 'Мои курсы', exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole('link', { name: 'Алгебра · учебный курс', exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole('combobox', { name: 'На странице', exact: true }),
  ).toHaveCount(0);
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
});

test('elapsed lesson is quietly marked after its end, cancellation stays separate', async ({
  page,
}) => {
  await login(page);
  const date = new Intl.DateTimeFormat('sv-SE', {
    timeZone: 'Europe/Moscow',
  }).format(new Date());
  await page.clock.setFixedTime(new Date(`${date}T12:00:00+03:00`));
  await page.route('**/api/lessons?*', async (route) => {
    const response = await route.fetch();
    const body = await response.json();
    // Keep the whole scenario on one Moscow day, including runs at 00:00–00:02.
    const past = new Date(`${date}T09:00:00+03:00`).toISOString();
    const upcoming = new Date(`${date}T13:00:00+03:00`).toISOString();
    await route.fulfill({
      json: {
        ...body,
        items: body.items
          .slice(0, 3)
          .map((item: Record<string, unknown>, i: number) => ({
            ...item,
            scheduled_at: i === 1 ? upcoming : past,
            duration_minutes: 1,
            status: i === 2 ? 'cancelled' : 'scheduled',
          })),
      },
    });
  });
  await page.goto('/student/schedule?view=all');
  await expect(page.getByText('Уже прошло', { exact: true })).toHaveCount(1);
  await expect(page.getByText('Уже прошло', { exact: true })).toBeVisible();
  await expect(
    page.locator('article[data-status="cancelled"]').getByText('Уже прошло'),
  ).toHaveCount(0);
  await page.screenshot({
    path: '.artifacts/t15a-elapsed-desktop.png',
    fullPage: true,
  });
  await page.setViewportSize({ width: 360, height: 780 });
  await page
    .getByRole('button', { name: 'Текущая неделя', exact: true })
    .click();
  await expect(page.getByText('Уже прошло', { exact: true })).toBeVisible();
  await page.screenshot({
    path: '.artifacts/t15a-elapsed-mobile.png',
    fullPage: true,
  });
});
