import { test, expect, type Page } from '@playwright/test';
import { readFileSync } from 'node:fs';
import AxeBuilder from '@axe-core/playwright';
const credentials = JSON.parse(
  readFileSync('.artifacts/t14e-credentials.json', 'utf8'),
);
test.use({ trace: 'off', screenshot: 'off', video: 'off' });
async function login(
  page: Page,
  path = '/teacher/students',
  key = 'teacher_recovery',
) {
  await page.goto('/login?returnTo=' + encodeURIComponent(path));
  await page
    .getByLabel('Логин', { exact: true })
    .fill(credentials[key].username);
  await page
    .getByLabel('Пароль', { exact: true })
    .fill(credentials[key].password);
  await page.getByRole('button', { name: 'Войти', exact: true }).click();
  await expect(page).toHaveURL(path);
}
async function createStudent(page: Page) {
  await page
    .getByRole('button', { name: 'Добавить ученика', exact: true })
    .click();
  const username = 'synthetic_grade_' + Date.now();
  await page.getByLabel('Логин', { exact: true }).fill(username);
  await page.getByLabel('Имя', { exact: true }).fill('Иван');
  await page.getByLabel('Фамилия', { exact: true }).fill('Петров');
  await page
    .getByRole('combobox', { name: 'Класс', exact: true })
    .last()
    .click();
  await page.getByRole('option', { name: '10', exact: true }).click();
  await page
    .getByRole('button', { name: 'Создать ученика', exact: true })
    .click();
  await expect(
    page.getByLabel('Ссылка приглашения', { exact: true }),
  ).toHaveValue(/^http:\/\/127.0.0.1:5173\/activate#token=/);
  expect(page.url()).not.toContain('token');
  await page.evaluate(() =>
    Object.defineProperty(navigator, 'clipboard', {
      configurable: true,
      value: { writeText: () => Promise.reject(new Error('synthetic denied')) },
    }),
  );
  await page
    .getByRole('button', { name: 'Скопировать ссылку', exact: true })
    .click();
  await expect(
    page.getByText(/Не удалось скопировать. Ссылка выделена/),
  ).toBeVisible();
  await page.getByRole('button', { name: 'Готово', exact: true }).click();
  await page.getByLabel('Поиск по имени или логину').fill(username);
  await page
    .getByRole('link', { name: /Иван Петров.*10/ })
    .first()
    .click();
  return username;
}
test('student first: grade, invitation, atomic workspace, settings and archive, keyboard/mobile/axe', async ({
  page,
}) => {
  await login(page);
  await createStudent(page);
  await expect(
    page.getByRole('heading', { name: /Иван Петров.*10/ }),
  ).toBeVisible();
  await page
    .getByRole('button', { name: 'Начать занятия', exact: true })
    .click();
  await expect(
    page.getByRole('heading', { name: 'Занятия и материалы', exact: true }),
  ).toBeVisible();
  const path = new URL(page.url()).pathname;
  await expect(page.getByLabel('Название курса', { exact: true })).toHaveCount(
    0,
  );
  await expect(
    page.getByRole('link', { name: 'Курсы', exact: true }),
  ).toHaveCount(0);
  await page.getByText('Настройки обучения', { exact: true }).click();
  await page
    .getByLabel('Ссылка встречи', { exact: true })
    .fill('https://example.org/synthetic');
  await page
    .getByRole('button', { name: 'Сохранить настройки', exact: true })
    .click();
  await expect(page).toHaveURL(path);
  await page.reload();
  await page.getByText('Настройки обучения', { exact: true }).click();
  await expect(page.getByLabel('Ссылка встречи', { exact: true })).toHaveValue(
    'https://example.org/synthetic',
  );
  await page
    .getByLabel('Новый аватар', { exact: true })
    .setInputFiles('e2e/fixtures/notebook.png');
  await expect(
    page.getByText('Аватар обновлён', { exact: true }),
  ).toBeVisible();
  await page.setViewportSize({ width: 360, height: 800 });
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  await page.screenshot({
    path: '.artifacts/t15b1-student-workspace-mobile.png',
    fullPage: true,
  });
  await page
    .getByRole('button', { name: 'Архивировать курс', exact: true })
    .click();
  await expect(
    page.getByRole('button', { name: 'Отмена', exact: true }),
  ).toBeFocused();
  await page.keyboard.press('Escape');
  await page
    .getByRole('button', { name: 'Архивировать курс', exact: true })
    .click();
  await page
    .getByRole('dialog')
    .getByRole('button', { name: 'Архивировать курс', exact: true })
    .click();
  await expect(
    page.getByRole('button', { name: 'Начать занятия', exact: true }),
  ).toBeVisible();
});
test('grade filter, full name search, clear and shared grade conflict preserve choice', async ({
  page,
}) => {
  await login(page);
  await createStudent(page);
  const studentPath = new URL(page.url()).pathname;
  if (
    !(await page
      .getByRole('button', { name: 'Изменить класс', exact: true })
      .isVisible())
  )
    await page.getByText('Настройки ученика', { exact: true }).click();
  await page
    .getByRole('button', { name: 'Изменить класс', exact: true })
    .click();
  await page.getByRole('combobox', { name: 'Класс', exact: true }).click();
  await page.getByRole('option', { name: '11', exact: true }).click();
  await page
    .getByRole('button', { name: 'Сохранить класс', exact: true })
    .click();
  await expect(
    page.getByRole('heading', { name: /Иван Петров.*11/ }),
  ).toBeVisible();
  if (
    !(await page
      .getByRole('button', { name: 'Изменить класс', exact: true })
      .isVisible())
  )
    await page.getByText('Настройки ученика', { exact: true }).click();
  await page
    .getByRole('button', { name: 'Изменить класс', exact: true })
    .click();
  await page.getByRole('combobox', { name: 'Класс', exact: true }).click();
  await page.getByRole('option', { name: '10', exact: true }).click();
  let first = true;
  await page.route(/\/api\/users\/\d+\/school-grade$/, async (route) => {
    if (first) {
      first = false;
      await route.fulfill({ status: 409, json: {} });
    } else await route.continue();
  });
  await page
    .getByRole('button', { name: 'Сохранить класс', exact: true })
    .click();
  await expect(
    page.getByRole('button', { name: 'Сохранить класс', exact: true }),
  ).toBeDisabled();
  await page
    .getByRole('button', { name: 'Загрузить актуальный класс', exact: true })
    .click();
  await expect(
    page.getByText('Сейчас в профиле: 11. Ваш выбор: 10.'),
  ).toBeVisible();
  await page
    .getByRole('button', {
      name: 'Использовать актуальную версию',
      exact: true,
    })
    .click();
  await page
    .getByRole('button', { name: 'Сохранить класс', exact: true })
    .click();
  await expect(
    page.getByRole('heading', { name: /Иван Петров.*10/ }),
  ).toBeVisible();
  await page.goto('/teacher/students');
  await page.getByRole('combobox', { name: 'Класс', exact: true }).click();
  await page.getByRole('option', { name: '10', exact: true }).click();
  await expect(page).toHaveURL(/school_grade=10/);
  await page.getByLabel('Поиск по имени или логину').fill('Иван Петров');
  await expect(
    page.getByRole('link', { name: /Иван Петров.*10/ }).first(),
  ).toBeVisible();
  expect(page.url()).not.toContain('Иван');
  await page
    .getByLabel('Поиск по имени или логину')
    .fill('synthetic_missing_zz');
  await expect(
    page.getByText('Ничего не найдено. Очистите поиск.'),
  ).toBeVisible();
  await page
    .getByRole('button', { name: 'Очистить поиск', exact: true })
    .click();
  await expect(page.getByLabel('Поиск по имени или логину')).toBeFocused();
  await page.setViewportSize({ width: 360, height: 800 });
  await page.screenshot({
    path: '.artifacts/t15b1-student-list-mobile.png',
    fullPage: true,
  });
  await page.goto(studentPath);
  await expect(
    page.getByRole('heading', { name: /Иван Петров.*10/ }),
  ).toBeVisible();
});
test('lost start response and two tabs recover same workspace without creating copies', async ({
  page,
  browser,
}) => {
  await login(page, '/teacher/students', 'teacher_recovery');
  await page
    .getByRole('link', { name: /^Synthetic Student/ })
    .first()
    .click();
  const path = new URL(page.url()).pathname;
  let posts = 0;
  await page.route(/\/api\/courses\/personal\/\d+$/, async (route) => {
    if (route.request().method() === 'POST') {
      posts++;
      await route.fetch();
      await route.abort();
    } else await route.continue();
  });
  await page
    .getByRole('button', { name: 'Начать занятия', exact: true })
    .click();
  await expect(
    page.getByRole('heading', { name: 'Занятия и материалы', exact: true }),
  ).toBeVisible();
  expect(posts).toBe(1);
  const context = await browser.newContext();
  const second = await context.newPage();
  await login(second, path, 'teacher_recovery');
  await expect(
    second.getByRole('heading', { name: 'Занятия и материалы', exact: true }),
  ).toBeVisible();
  await expect(
    second.getByRole('button', { name: 'Начать занятия', exact: true }),
  ).toHaveCount(0);
  await context.close();
});
test('legacy archive PDF/download, foreign course boundary and old courses entry redirects to students', async ({
  page,
}) => {
  await login(
    page,
    '/teacher/courses/' + credentials.student_read.courses[2],
    'teacher',
  );
  await expect(page.getByText(/Только просмотр:/).first()).toBeVisible();
  await page
    .getByRole('button', { name: 'Открыть материалы', exact: true })
    .first()
    .click();
  await page
    .getByRole('combobox', {
      name: 'Ученик — получатель материалов',
      exact: true,
    })
    .click();
  await page.getByRole('option').first().click();
  await page
    .getByRole('button', { name: 'Открыть Учебный пример.pdf', exact: true })
    .click();
  await expect(
    page.getByText('Страница 1 из 2', { exact: true }),
  ).toBeVisible();
  const download = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Скачать файл', exact: true }).click();
  await download;
  await page.keyboard.press('Escape');
  await expect(page.getByRole('dialog')).toHaveCount(0);
  await page.goto('/teacher/courses/' + credentials.student_read.courses[1]);
  await expect(
    page.getByText('Материал больше недоступен', { exact: true }),
  ).toBeVisible();
  await page.goto('/teacher/courses');
  await expect(page).toHaveURL('/teacher/students');
  await expect(
    page.getByRole('link', { name: 'Курсы', exact: true }),
  ).toHaveCount(0);
  await page.screenshot({
    path: '.artifacts/t15b1-students-desktop.png',
    fullPage: true,
  });
});

test('student list sorting and readable lesson rows on desktop/mobile, empty/error recovery', async ({
  page,
}) => {
  await login(page, '/teacher/students', 'teacher');
  for (const [value, label] of [
    ['grade_asc', 'Класс: по возрастанию'],
    ['grade_desc', 'Класс: по убыванию'],
    ['name', 'По имени'],
    ['recent', 'Недавно добавленные'],
  ]) {
    await page
      .getByRole('combobox', { name: 'Сортировка', exact: true })
      .click();
    const response = page.waitForResponse(
      (r) =>
        r.url().includes('/api/users/students?') &&
        new URL(r.url()).searchParams.get('sort') === value,
    );
    await page.getByRole('option', { name: label, exact: true }).click();
    // Recent can legitimately reuse the fresh initial query; reload proves its server contract.
    if (value === 'recent') await page.reload();
    expect((await response).status()).toBe(200);
    await expect(page).toHaveURL(new RegExp('sort=' + value));
  }
  for (const width of [1280, 360]) {
    await page.setViewportSize({ width, height: 900 });
    await page
      .getByRole('heading', { name: 'Свои ученики', exact: true })
      .click();
    await page.screenshot({
      path: `.artifacts/t15b1-refined-list-${width}.png`,
      fullPage: false,
    });
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
    // Use the protected fixture student's verified route, preserving its actual material data.
    await page.goto(
      '/teacher/students/' +
        credentials.student_read.lessons[0].student_user_id,
    );
    await expect(
      page.getByRole('list', {
        name: 'Прошедшие занятия ученика',
        exact: true,
      }),
    ).toBeVisible();
    await expect(
      page.getByRole('combobox', {
        name: 'Занятие для просмотра материалов',
        exact: true,
      }),
    ).toHaveCount(0);
    await page
      .getByRole('list', { name: 'Прошедшие занятия ученика', exact: true })
      .locator('li')
      .filter({
        has: page.getByRole('link', { name: /Квадратные уравнения/ }),
      })
      .getByRole('button', { name: 'Открыть материалы', exact: true })
      .press('Enter');
    await expect(
      page.getByRole('heading', { name: 'Конспекты', exact: true }),
    ).toBeVisible();
    await expect(
      page.getByRole('button', {
        name: 'Открыть Учебный пример.pdf',
        exact: true,
      }),
    ).toBeVisible();
    await expect(
      page.getByRole('link', { name: 'К ученику', exact: true }),
    ).toHaveCount(0);
    await expect(
      page.getByRole('button', { name: 'Изменить класс', exact: true }),
    ).toBeHidden();
    await page
      .getByRole('heading', { name: 'Занятия и материалы', exact: true })
      .click();
    await page.screenshot({
      path: `.artifacts/t15b1-refined-detail-${width}.png`,
      fullPage: false,
    });
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
    await page.getByRole('link', { name: 'Свои ученики', exact: true }).click();
  }
  await page
    .getByLabel('Поиск по имени или логину')
    .fill('synthetic_missing_zz');
  await expect(
    page.getByText('Ничего не найдено. Очистите поиск.'),
  ).toBeVisible();
  await page
    .getByRole('button', { name: 'Очистить поиск', exact: true })
    .click();
  await expect(
    page
      .getByRole('list', { name: 'Свои ученики', exact: true })
      .getByRole('link')
      .first(),
  ).toBeVisible();
  await page.route('**/api/users/students?**', (route) =>
    route.fulfill({ status: 500, json: {} }),
  );
  await page.reload();
  await expect(
    page.getByRole('button', { name: 'Повторить', exact: true }),
  ).toBeVisible();
  await page.unroute('**/api/users/students?**');
  await page.getByRole('button', { name: 'Повторить', exact: true }).click();
  await expect(
    page
      .getByRole('list', { name: 'Свои ученики', exact: true })
      .getByRole('link')
      .first(),
  ).toBeVisible();
});
