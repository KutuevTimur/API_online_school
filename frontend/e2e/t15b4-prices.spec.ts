import { test, expect, type Page } from '@playwright/test';
import { readFileSync } from 'node:fs';
import AxeBuilder from '@axe-core/playwright';
const credentials = JSON.parse(
  readFileSync('.artifacts/t15b4-credentials.json', 'utf8'),
);
test.use({ trace: 'off', screenshot: 'off', video: 'off' });
async function login(page: Page, path: string) {
  await page.goto('/login');
  await page
    .getByLabel('Логин', { exact: true })
    .fill(credentials.teacher.username);
  await page
    .getByLabel('Пароль', { exact: true })
    .fill(credentials.teacher.password);
  await page.getByRole('button', { name: 'Войти', exact: true }).click();
  await expect(page).toHaveURL('/teacher');
  await page.goto(path);
  await expect(page).toHaveURL(path);
}
const summary = (page: Page) =>
  page.getByRole('region', { name: 'Итоги выбранной недели' });
test('week totals, unfinished count, history, empty, keyboard, mobile/axe', async ({
  page,
}) => {
  const errors: string[] = [];
  page.on('pageerror', (e) => errors.push(e.message));
  await login(page, '/teacher/schedule?week=' + credentials.week);
  await expect(summary(page)).toContainText('Занятий за неделю · 3');
  await expect(summary(page)).toContainText('Известная сумма: 800,25 ₽');
  await expect(summary(page)).toContainText(
    'Итог неполный: 1 занятие без указанной цены',
  );
  await page
    .getByRole('button', { name: 'Предыдущая неделя', exact: true })
    .focus();
  await page.keyboard.press('Enter');
  await expect(summary(page)).toContainText('1 000,10 ₽');
  await expect(summary(page)).toContainText('Занятий за неделю · 1');
  await page
    .getByRole('button', { name: 'Текущая неделя', exact: true })
    .click();
  await expect(summary(page)).toContainText('800,25 ₽');
  await page
    .getByRole('button', { name: 'Следующая неделя', exact: true })
    .click();
  await expect(summary(page)).toContainText('0,00 ₽');
  await expect(summary(page)).toContainText('Занятий за неделю · 0');
  for (const width of [1280, 360]) {
    await page.setViewportSize({ width, height: 900 });
    await summary(page).scrollIntoViewIfNeeded();
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
    await page.screenshot({
      path: `.artifacts/t15b4-week-${width}.png`,
      fullPage: true,
    });
  }
  expect(errors).toEqual([]);
});
test('weekly read error/retry and loading', async ({ page }) => {
  let fail = true;
  await page.route('**/teacher-planning/weekly-earnings?*', async (route) =>
    fail
      ? route.fulfill({ status: 503, json: { detail: 'synthetic' } })
      : route.continue(),
  );
  await login(page, '/teacher/schedule?week=' + credentials.previous_week);
  await expect(
    summary(page).getByRole('button', { name: 'Повторить', exact: true }),
  ).toBeVisible();
  fail = false;
  await summary(page)
    .getByRole('button', { name: 'Повторить', exact: true })
    .click();
  await expect(summary(page)).toContainText('1 000,10 ₽');
  await page.unroute('**/teacher-planning/weekly-earnings?*');
  let release: (() => void) | undefined;
  const held = new Promise<void>((resolve) => {
    release = resolve;
  });
  await page.route('**/teacher-planning/weekly-earnings?*', async (route) => {
    await held;
    await route.continue();
  });
  await page
    .getByRole('button', { name: 'Текущая неделя', exact: true })
    .click();
  await expect(summary(page)).toContainText('Загружаем');
  release?.();
  await expect(summary(page)).toContainText('800,25 ₽');
});
test('price save/validation/conflict, keyboard and 360', async ({ page }) => {
  await page.setViewportSize({ width: 360, height: 900 });
  await login(page, `/teacher/students/${credentials.student.id}`);
  await page.getByText('Настройки ученика', { exact: true }).click();
  await page
    .locator('summary')
    .filter({ hasText: /^Цена занятия$/ })
    .click();
  await page
    .getByRole('button', { name: 'Изменить цену занятия', exact: true })
    .click();
  const field = page.getByLabel('Цена занятия, ₽', { exact: true });
  await field.fill('1,234');
  await page
    .getByRole('button', { name: 'Сохранить цену', exact: true })
    .click();
  await expect(field).toBeFocused();
  await expect(field).toHaveAttribute('aria-invalid', 'true');
  await field.fill('1000,10');
  await page
    .getByRole('button', { name: 'Сохранить цену', exact: true })
    .focus();
  await page.keyboard.press('Enter');
  await expect(
    page.getByText('Цена занятия сохранена', { exact: true }),
  ).toBeVisible();
  await page
    .getByRole('button', { name: 'Изменить цену занятия', exact: true })
    .click();
  await field.fill('0');
  let conflict = true;
  await page.route('**/teacher-planning/students/*/price', async (route) => {
    if (route.request().method() === 'PUT' && conflict) {
      conflict = false;
      await route.fulfill({ status: 409, json: { detail: 'synthetic' } });
    } else await route.continue();
  });
  await page
    .getByRole('button', { name: 'Сохранить цену', exact: true })
    .click();
  await expect(field).toHaveValue('0');
  await page
    .getByRole('button', { name: 'Загрузить актуальную цену', exact: true })
    .click();
  await page
    .getByRole('button', { name: 'Оставить мой выбор', exact: true })
    .click();
  await page
    .getByRole('button', { name: 'Сохранить цену', exact: true })
    .click();
  await expect(page.getByText('0,00 ₽', { exact: true })).toBeVisible();
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth,
    ),
  ).toBe(true);
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  await page.screenshot({
    path: '.artifacts/t15b4-price-360.png',
    fullPage: true,
  });
});
test('add student priced and unknown', async ({ page }) => {
  await login(page, '/teacher/students');
  for (const price of ['800,50', '']) {
    await page
      .getByRole('button', { name: 'Добавить ученика', exact: true })
      .click();
    await page
      .getByLabel('Логин', { exact: true })
      .fill('synthetic_t15b4_' + Date.now());
    await page.getByLabel('Имя', { exact: true }).fill('Новый');
    await page.getByLabel('Фамилия', { exact: true }).fill('Ученик');
    await page
      .getByRole('combobox', { name: 'Класс', exact: true })
      .last()
      .click();
    await page.getByRole('option', { name: '10', exact: true }).click();
    await page.getByLabel('Цена занятия, ₽', { exact: true }).fill(price);
    const saved = page.waitForResponse(
      (r) =>
        r.url().endsWith('/auth/register') && r.request().method() === 'POST',
    );
    await page
      .getByRole('button', { name: 'Создать ученика', exact: true })
      .click();
    const response = await saved;
    expect(response.status()).toBe(200);
    expect(response.request().postDataJSON().lesson_price_kopecks).toBe(
      price ? 80050 : null,
    );
    await expect(
      page.getByLabel('Ссылка приглашения', { exact: true }),
    ).toBeVisible();
    await page.getByRole('button', { name: 'Готово', exact: true }).click();
  }
});
