import { test, expect, type Page } from '@playwright/test';
import { readFileSync } from 'node:fs';
import AxeBuilder from '@axe-core/playwright';
test.use({ trace: 'off', video: 'off', screenshot: 'off' });
async function login(page: Page, accountKey: string) {
  const { accounts } = JSON.parse(
    readFileSync('.artifacts/t15d-preview.json', 'utf8'),
  );
  let writes = 0,
    forbidden = 0;
  await page.route('**/api/**', (route) => {
    const req = route.request(),
      u = new URL(req.url());
    if (req.method() !== 'GET' && !u.pathname.startsWith('/api/auth/')) {
      writes++;
      return route.abort();
    }
    if (
      /^\/api\/homeworks\/58(?:\/|$)/.test(u.pathname) ||
      u.searchParams.get('homework_id') === '58'
    ) {
      forbidden++;
      return route.abort();
    }
    return route.continue();
  });
  await page.goto('/login');
  await page
    .getByLabel('Логин', { exact: true })
    .fill(accounts[accountKey].username);
  await page
    .getByLabel('Пароль', { exact: true })
    .fill(accounts[accountKey].password);
  await page.getByRole('button', { name: 'Войти', exact: true }).click();
  await expect(page).not.toHaveURL(/\/login/);
  return () => {
    expect(writes).toBe(0);
    expect(forbidden).toBe(0);
  };
}
const back = (page: Page) =>
  page.getByRole('banner').getByRole('button', { name: 'Назад', exact: true });
test('teacher: month query/reload, profile remount, dirty cancel/confirm and direct entry', async ({
  page,
}) => {
  test.skip(!process.env.LGG_T15D_PREVIEW, 'Read-only retained preview');
  const verify = await login(page, 'teacher');
  await page.setViewportSize({ width: 1340, height: 900 });
  await page.goto('/teacher/students?school_grade=7&sort=name');
  const origin = page.url();
  await page.locator('main a[href="/teacher/students/33"]').click();
  await expect(
    page.getByRole('region', { name: 'Последнее проведённое занятие' }),
  ).toBeVisible();
  await page
    .getByRole('button', { name: 'сентябрь 2026', exact: true })
    .click();
  await expect(page).toHaveURL(/history-month=2026-09/);
  await page.reload();
  await expect(
    page.getByRole('region', { name: 'История занятий', exact: true }),
  ).toBeVisible();
  await back(page).click();
  await expect(page).toHaveURL(origin);
  await page
    .getByRole('banner')
    .getByRole('link', { name: 'Профиль', exact: true })
    .click();
  await expect(page).toHaveURL(/\/profile$/);
  const name = page.getByLabel('Имя', { exact: true });
  await expect(name).toBeVisible();
  await name.fill('HTTP fixture draft — не сохранять');
  await back(page).click();
  const dialog = page.getByRole('dialog', { name: 'Уйти без сохранения?' });
  await expect(dialog).toBeVisible();
  await dialog.getByRole('button', { name: 'Отмена', exact: true }).click();
  await expect(page).toHaveURL(/\/profile$/);
  await expect(name).toHaveValue('HTTP fixture draft — не сохранять');
  await back(page).click();
  await dialog
    .getByRole('button', { name: 'Уйти без сохранения', exact: true })
    .click();
  await expect(page).toHaveURL(origin);
  await page.goto('/teacher');
  const review = page
    .locator('main a[href^="/teacher/review/"]:not([href*="homework_id=58"])')
    .first();
  await expect(review).toBeVisible();
  await review.click();
  await expect(page).toHaveURL(/\/teacher\/review\/\d+/);
  await back(page).click();
  await expect(page).toHaveURL(/\/teacher$/);
  await page.evaluate(() => sessionStorage.removeItem('lgg.page-back.v1'));
  await page.goto('/teacher/students/33');
  await expect(
    page.getByRole('region', { name: 'Последнее проведённое занятие' }),
  ).toBeVisible();
  await back(page).click();
  await expect(page).toHaveURL(/\/teacher\/students$/);
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  await page.screenshot({ path: '.artifacts/page-back-teacher-desktop.png' });
  verify();
});
test('student: day lesson back, narrow geometry, direct lesson parent and role isolation', async ({
  page,
}) => {
  test.skip(!process.env.LGG_T15D_PREVIEW, 'Read-only retained preview');
  const verify = await login(page, 'turov');
  await page.setViewportSize({ width: 390, height: 844 });
  await expect(page).toHaveURL(/\/student$/);
  const lesson = page
    .getByRole('region', { name: 'Ближайшее занятие', exact: true })
    .getByRole('link', { name: 'Открыть занятие', exact: true });
  await expect(lesson).toBeVisible();
  const target = await lesson.getAttribute('href');
  await lesson.click();
  await expect(page).toHaveURL(new RegExp(target + '$'));
  for (const width of [360, 390, 768, 1024, 1340]) {
    await page.setViewportSize({ width, height: 844 });
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    const box = (await back(page).boundingBox())!;
    expect(box.width).toBeGreaterThanOrEqual(44);
    expect(box.height).toBeGreaterThanOrEqual(44);
  }
  await page.setViewportSize({ width: 390, height: 844 });
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  await page.screenshot({ path: '.artifacts/page-back-student-mobile.png' });
  await back(page).click();
  await expect(page).toHaveURL(/\/student$/);
  await page.evaluate(() => sessionStorage.removeItem('lgg.page-back.v1'));
  await page.goto(target!);
  await expect(back(page)).toBeEnabled();
  await back(page).click();
  await expect(page).toHaveURL(/\/student\/schedule$/);
  await page
    .getByRole('banner')
    .getByRole('link', { name: 'Уведомления', exact: false })
    .click();
  await expect(page).toHaveURL(/\/notifications$/);
  await back(page).click();
  await expect(page).toHaveURL(/\/student\/schedule$/);
  verify();
});
