import { test, expect, type Page } from '@playwright/test';
import { readFileSync } from 'node:fs';
import AxeBuilder from '@axe-core/playwright';
const credentials = JSON.parse(
  readFileSync('.artifacts/t14e-credentials.json', 'utf8'),
);
test.use({ trace: 'off', screenshot: 'off', video: 'off', hasTouch: true });
test.describe.configure({ mode: 'serial' });
async function open(page: Page) {
  await page.addInitScript(() => {
    const live = new Set<string>();
    const create = URL.createObjectURL.bind(URL);
    const revoke = URL.revokeObjectURL.bind(URL);
    URL.createObjectURL = (value) => {
      const url = create(value);
      live.add(url);
      return url;
    };
    URL.revokeObjectURL = (value) => {
      live.delete(value);
      revoke(value);
    };
    Object.defineProperty(window, '__lggBlobCount', { get: () => live.size });
  });
  await page.goto('/login');
  await page
    .getByLabel('Логин', { exact: true })
    .fill(credentials.files_student.username);
  await page
    .getByLabel('Пароль', { exact: true })
    .fill(credentials.files_student.password);
  await page.getByRole('button', { name: 'Войти', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Мой день' })).toBeVisible();
  await page.goto('/__ui/files');
  await page
    .getByRole('button', { name: 'Открыть тестовые файлы', exact: true })
    .click();
  await expect(
    page.getByRole('heading', { name: 'Файлы ответа' }),
  ).toBeVisible();
}
function photo(name: string) {
  return {
    name,
    mimeType: 'image/png',
    buffer: readFileSync('e2e/fixtures/notebook.png'),
  };
}
async function upload(page: Page) {
  await page
    .getByRole('button', { name: 'Загрузить выбранные файлы', exact: true })
    .click();
  await expect(
    page.getByRole('button', { name: 'Остановить загрузку', exact: true }),
  ).toHaveCount(0);
}
test('real API: three photos plus fourth, PDF pages/text/zoom/download, exact replace/delete', async ({
  page,
}) => {
  await open(page);
  while (await page.getByRole('button', { name: /^Удалить / }).count()) {
    await page
      .getByRole('button', { name: /^Удалить / })
      .first()
      .click();
    await page
      .getByRole('button', { name: 'Удалить файл', exact: true })
      .click();
    await expect(page.getByRole('dialog')).toHaveCount(0);
  }
  await page
    .getByLabel('Добавить файлы', { exact: true })
    .setInputFiles([
      photo('first.png'),
      photo('second.png'),
      photo('third.png'),
    ]);
  await upload(page);
  await expect(page.getByRole('article', { name: /^Сохранён:/ })).toHaveCount(
    3,
  );
  await page
    .getByLabel('Добавить файлы', { exact: true })
    .setInputFiles(photo('fourth.png'));
  await upload(page);
  await expect(page.getByRole('article', { name: /^Сохранён:/ })).toHaveCount(
    4,
  );
  await page
    .getByLabel('Добавить файлы', { exact: true })
    .setInputFiles('e2e/fixtures/math.pdf');
  await upload(page);
  await expect(page.getByRole('article', { name: /^Сохранён:/ })).toHaveCount(
    5,
  );
  await page
    .getByRole('button', { name: 'Открыть math.pdf', exact: true })
    .click();
  await expect(
    page.getByText('Страница 1 из 2', { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText('Synthetic math - page 1', { exact: true }),
  ).toHaveCount(1);
  await page
    .getByRole('button', { name: 'Следующая страница', exact: true })
    .click();
  await expect(
    page.getByText('Synthetic math - page 2', { exact: true }),
  ).toHaveCount(1);
  await page.getByRole('button', { name: 'Увеличить', exact: true }).click();
  await expect(page.getByText('125%', { exact: true })).toBeVisible();
  const download = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Скачать файл', exact: true }).click();
  expect((await download).suggestedFilename()).toBe('math.pdf');
  await page.screenshot({ path: '.artifacts/t14f-pdf.png' });
  await page.keyboard.press('Escape');
  await expect(page.getByRole('dialog')).toHaveCount(0);
  await expect(
    page.getByRole('button', { name: 'Открыть math.pdf', exact: true }),
  ).toBeFocused();
  await page
    .getByLabel('Заменить second.webp', { exact: true })
    .setInputFiles(photo('replacement.png'));
  await upload(page);
  await expect(
    page.getByRole('button', { name: 'Открыть replacement.webp', exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole('button', { name: 'Открыть first.webp', exact: true }),
  ).toBeVisible();
  await expect(
    page.getByRole('button', { name: 'Открыть third.webp', exact: true }),
  ).toBeVisible();
  await page
    .getByRole('button', { name: 'Удалить replacement.webp', exact: true })
    .click();
  await page.getByRole('button', { name: 'Удалить файл', exact: true }).click();
  await expect(page.getByRole('article', { name: /^Сохранён:/ })).toHaveCount(
    4,
  );
  await page
    .getByRole('button', { name: 'Открыть first.webp', exact: true })
    .click();
  await expect(
    page.getByRole('img', { name: 'first.webp', exact: true }),
  ).toBeVisible();
  await page.getByRole('button', { name: 'Увеличить', exact: true }).click();
  await page.screenshot({ path: '.artifacts/t14f-photo.png' });
  await page.keyboard.press('Escape');
});
test('narrow keyboard, dirty navigation, local validation, session overlay and cleanup', async ({
  page,
  context,
}) => {
  await page.setViewportSize({ width: 360, height: 780 });
  await page.emulateMedia({ reducedMotion: 'reduce' });
  await open(page);
  await page
    .getByLabel('Добавить файлы', { exact: true })
    .setInputFiles(photo('pending.png'));
  await page
    .getByRole('link', { name: 'К примеру кабинета', exact: true })
    .click();
  await expect(
    page.getByRole('dialog', { name: 'Уйти без сохранения?' }),
  ).toBeVisible();
  await page.keyboard.press('Escape');
  await expect(
    page.getByRole('article', { name: 'pending.png', exact: true }),
  ).toBeVisible();
  await page.getByLabel('Добавить файлы', { exact: true }).setInputFiles({
    name: 'bad.svg',
    mimeType: 'image/svg+xml',
    buffer: Buffer.from('<svg/>'),
  });
  await expect(page.getByText(/bad.svg: Выберите PDF/)).toBeVisible();
  // Force refresh denial: the pending in-memory file must survive the reauth overlay.
  await context.clearCookies();
  await page.route('**/api/submissions/*/student?*', (route) =>
    route.fulfill({ status: 401, contentType: 'application/json', body: '{}' }),
  );
  await upload(page);
  await expect(
    page.getByRole('dialog', { name: 'Войдите снова', exact: true }),
  ).toBeVisible();
  await page
    .getByLabel('Логин', { exact: true })
    .fill(credentials.files_student.username);
  await page
    .getByLabel('Пароль', { exact: true })
    .fill(credentials.files_student.password);
  await page.getByRole('button', { name: 'Войти', exact: true }).click();
  await expect(page.getByRole('dialog')).toHaveCount(0);
  await expect(
    page.getByRole('article', { name: 'pending.png', exact: true }),
  ).toBeVisible();
  await page.unroute('**/api/submissions/*/student?*');
  await page
    .getByRole('button', { name: 'Проверить сохранение файлов', exact: true })
    .click();
  await expect(page.getByText(/Список обновлён/)).toBeVisible();
  await page
    .getByRole('button', { name: 'Убрать из очереди pending.png', exact: true })
    .click();
  await page
    .getByRole('button', { name: 'Открыть math.pdf', exact: true })
    .click();
  await expect(
    page.getByText('Страница 1 из 2', { exact: true }),
  ).toBeVisible();
  await page.getByRole('button', { name: 'Увеличить', exact: true }).tap();
  await page.keyboard.press('Tab');
  await page.keyboard.press('Shift+Tab');
  const axe = await new AxeBuilder({ page }).analyze();
  expect(axe.violations).toEqual([]);
  await page.screenshot({ path: '.artifacts/t14f-mobile.png' });
  await page.keyboard.press('Escape');
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= window.innerWidth,
    ),
  ).toBe(true);
  await page
    .getByLabel('Добавить файлы', { exact: true })
    .setInputFiles(photo('logout.png'));
  const other = await context.newPage();
  await other.goto('/student');
  await other.getByRole('button', { name: 'Выйти', exact: true }).click();
  await expect(
    page.getByRole('heading', { name: 'Файлы ответа', exact: true }),
  ).toHaveCount(0);
  await expect
    .poll(() => page.evaluate(() => Reflect.get(window, '__lggBlobCount')))
    .toBe(0);
  await other.close();
});
test('transport failure, 403/413/409, corrupt PDF: local recovery without clearing adjacent files', async ({
  page,
  context,
}) => {
  await open(page);
  for (const status of [0, 413, 409, 403]) {
    await page
      .getByLabel('Добавить файлы', { exact: true })
      .setInputFiles(photo(`failure-${status}.png`));
    await page.route('**/api/submissions/*/student?*', (route) =>
      status === 0
        ? route.abort()
        : route.fulfill({
            status,
            contentType: 'application/json',
            body: '{}',
          }),
    );
    await upload(page);
    await expect(
      page
        .getByRole('article', { name: `failure-${status}.png`, exact: true })
        .getByRole('alert'),
    ).toBeVisible();
    await page.unroute('**/api/submissions/*/student?*');
    await page
      .getByRole('button', { name: 'Проверить сохранение файлов', exact: true })
      .click();
    await expect(page.getByText(/Список обновлён/)).toBeVisible();
    await page
      .getByRole('button', {
        name: `Убрать из очереди failure-${status}.png`,
        exact: true,
      })
      .click();
    if (status === 403) break;
  }
  await page
    .getByRole('button', { name: 'Открыть math.pdf', exact: true })
    .click();
  await expect(
    page.getByText('Страница 1 из 2', { exact: true }),
  ).toBeVisible();
  await page.keyboard.press('Escape');
  await page.route('**/api/submissions/*/files/*?*', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/pdf',
      body: 'corrupt synthetic',
    }),
  );
  await page
    .getByRole('button', { name: 'Открыть math.pdf', exact: true })
    .click();
  await expect(page.getByText(/Не удалось открыть PDF/)).toBeVisible();
  await page.keyboard.press('Escape');
  await page.unroute('**/api/submissions/*/files/*?*');
  await context.setOffline(true);
  await page
    .getByRole('button', { name: 'Открыть math.pdf', exact: true })
    .click();
  await expect(
    page.getByText('Нет связи. Проверьте подключение', { exact: true }),
  ).toBeVisible();
  await context.setOffline(false);
  await page
    .getByRole('button', { name: 'Повторить просмотр', exact: true })
    .click();
  await expect(
    page.getByText('Страница 1 из 2', { exact: true }),
  ).toBeVisible();
  await page.keyboard.press('Escape');
});

test('abort requires read, large legacy fallback, protected 403 and browser back close', async ({
  page,
}) => {
  await open(page);
  await page
    .getByLabel('Добавить файлы', { exact: true })
    .setInputFiles(photo('abort.png'));
  let release!: () => void;
  const paused = new Promise<void>((resolve) => {
    release = resolve;
  });
  await page.route('**/api/submissions/*/student?*', async (route) => {
    await paused;
    await route.abort().catch(() => {});
  });
  await page
    .getByRole('button', { name: 'Загрузить выбранные файлы', exact: true })
    .click();
  await expect(
    page.getByRole('button', { name: 'Остановить загрузку', exact: true }),
  ).toBeVisible();
  await page
    .getByRole('button', { name: 'Остановить загрузку', exact: true })
    .click();
  release();
  await expect(
    page
      .getByRole('article', { name: 'abort.png', exact: true })
      .getByText('Сохранение не подтверждено', { exact: true }),
  ).toBeVisible();
  await page.unroute('**/api/submissions/*/student?*');
  await page
    .getByRole('button', { name: 'Проверить сохранение файлов', exact: true })
    .click();
  await expect(page.getByText(/Список обновлён/)).toBeVisible();
  await page
    .getByRole('button', { name: 'Убрать из очереди abort.png', exact: true })
    .click();
  await page.route('**/api/submissions/*/files/*?*', (route) =>
    route.fulfill({ status: 403, contentType: 'application/json', body: '{}' }),
  );
  await page
    .getByRole('button', { name: 'Открыть math.pdf', exact: true })
    .click();
  await expect(
    page.getByText('Нет доступа к этому материалу', { exact: true }),
  ).toBeVisible();
  await page.keyboard.press('Escape');
  await page.unroute('**/api/submissions/*/files/*?*');
  await page.route('**/api/submissions/*/files/*?*', (route) =>
    route.fulfill({
      status: 200,
      contentType: 'application/pdf',
      body: Buffer.alloc(21 * 1024 * 1024, 32),
    }),
  );
  await page
    .getByRole('button', { name: 'Открыть math.pdf', exact: true })
    .click();
  await expect(
    page.getByText('Файл больше лимита предпросмотра. Доступно скачивание', {
      exact: true,
    }),
  ).toBeVisible();
  const downloading = page.waitForEvent('download');
  await page.getByRole('button', { name: 'Скачать файл', exact: true }).click();
  expect((await downloading).suggestedFilename()).toBe('math.pdf');
  await page.keyboard.press('Escape');
  await page.unroute('**/api/submissions/*/files/*?*');
  await page
    .getByRole('button', { name: 'Открыть math.pdf', exact: true })
    .click();
  await expect(
    page.getByText('Страница 1 из 2', { exact: true }),
  ).toBeVisible();
  await page.goBack();
  await expect(page.getByRole('dialog')).toHaveCount(0);
  await expect
    .poll(() => page.evaluate(() => Reflect.get(window, '__lggBlobCount')))
    .toBe(0);
  await expect(
    page.getByRole('heading', {
      name: 'Файлы · техническая галерея',
      exact: true,
    }),
  ).toBeVisible();
});

test('dev recovery examples: authored select, field422 focus and preserved local comparison', async ({
  page,
}) => {
  await page.goto('/__ui/files');
  await page
    .getByText('Состояния файлов · примеры без отправки', { exact: true })
    .click();
  await page
    .getByRole('combobox', { name: 'Пример состояния', exact: true })
    .click();
  await expect(
    page.getByRole('option', { name: 'Размер / квота', exact: true }),
  ).toBeVisible();
  await page
    .getByRole('option', { name: 'Размер / квота', exact: true })
    .click();
  await expect(
    page.getByText(
      'Превышен размер или квота хранилища. Другие файлы и текст сохранены.',
      { exact: true },
    ),
  ).toBeVisible();
  await page
    .getByRole('combobox', { name: 'Пример состояния', exact: true })
    .click();
  await page
    .getByRole('option', { name: 'Ошибка поля 422', exact: true })
    .click();
  await page
    .getByRole('button', { name: 'Показать ошибку поля', exact: true })
    .click();
  await expect(
    page.getByLabel('Название · пример', { exact: true }),
  ).toBeFocused();
  await expect(
    page.getByLabel('Название · пример', { exact: true }),
  ).toHaveValue('Локальный ответ');
  await page
    .getByRole('combobox', { name: 'Пример состояния', exact: true })
    .click();
  await page
    .getByRole('option', { name: 'Конфликт версий', exact: true })
    .click();
  await page
    .getByRole('button', { name: 'Открыть обновлённый ответ', exact: true })
    .click();
  await expect(
    page.getByText('Обновлённая серверная версия 3', { exact: true }),
  ).toBeVisible();
  await expect(
    page.getByText('Локальный ответ', { exact: true }),
  ).toBeVisible();
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
});
