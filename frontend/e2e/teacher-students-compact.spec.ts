import { test, expect } from '@playwright/test';
import { readFileSync } from 'node:fs';
import AxeBuilder from '@axe-core/playwright';
test.use({ trace: 'off', video: 'off', screenshot: 'off' });
test('teacher student list: compact filters, attention and read-only HTTP states', async ({
  page,
}) => {
  test.skip(
    !process.env.LGG_T15D_PREVIEW,
    'Retained preview; no seeds or business writes',
  );
  const { accounts } = JSON.parse(
    readFileSync('.artifacts/t15d-preview.json', 'utf8'),
  );
  let mode = 'real',
    writes = 0;
  let sample: Record<string, unknown> = {};
  const queries: URLSearchParams[] = [],
    errors: string[] = [];
  page.on('pageerror', (e) => errors.push(e.message));
  await page.route('**/api/**', async (route) => {
    const req = route.request(),
      url = new URL(req.url());
    if (req.method() !== 'GET' && !url.pathname.startsWith('/api/auth/')) {
      writes++;
      return route.abort();
    }
    if (url.pathname === '/api/users/students') {
      queries.push(url.searchParams);
      if (mode === 'empty')
        return route.fulfill({ json: { items: [], total: 0 } });
      if (mode === 'error')
        return route.fulfill({
          status: 503,
          json: { detail: 'Explicit HTTP fixture unavailable' },
        });
      if (mode === 'fixture')
        return route.fulfill({
          json: {
            total: 4,
            items: [0, 1, 2, 3].map((i) => ({
              ...sample,
              user_id: 99000 + i,
              first_name: i === 0 ? 'Александра' : 'HTTP fixture',
              last_name:
                i === 0 ? 'Константинопольская-Соколова' : 'Ученик ' + i,
              username: 'http_fixture_long_username_' + i,
              school_grade: i === 0 ? null : 7 + i,
              missing_homework: i === 1 || i === 3 ? 12 : 0,
              missing_lecture: i === 2 || i === 3 ? 3 : 0,
            })),
          },
        });
      const response = await route.fetch();
      const data = await response.json();
      sample = data.items[0] || sample;
      return route.fulfill({ response, json: data });
    }
    return route.continue();
  });
  await page.setViewportSize({ width: 1340, height: 900 });
  await page.goto('/login');
  await page
    .getByLabel('Логин', { exact: true })
    .fill(accounts.teacher.username);
  await page
    .getByLabel('Пароль', { exact: true })
    .fill(accounts.teacher.password);
  await page.getByRole('button', { name: 'Войти', exact: true }).click();
  await expect(page).toHaveURL(/\/teacher$/);
  await page.goto('/teacher/students');
  const list = page.getByRole('list', { name: 'Свои ученики', exact: true });
  await expect(list.getByRole('link').first()).toBeVisible();
  const noOverflow = async () =>
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
  for (const width of [1340, 1024, 768, 390, 360]) {
    await page.setViewportSize({ width, height: 900 });
    await noOverflow();
  }
  await page.setViewportSize({ width: 1340, height: 900 });
  const controls = [
    'Поиск по имени или логину',
    'Класс',
    'Сортировка',
    'Материалы занятий',
  ];
  const bottoms = await Promise.all(
    controls.map(async (name) => {
      const b = await page
        .getByRole(
          name === 'Поиск по имени или логину' ? 'textbox' : 'combobox',
          { name, exact: true },
        )
        .boundingBox();
      return b!.y + b!.height;
    }),
  );
  expect(Math.max(...bottoms) - Math.min(...bottoms)).toBeLessThanOrEqual(1);
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  await page.screenshot({
    path: '.artifacts/teacher-students-real-desktop.png',
    fullPage: true,
  });
  await page
    .getByRole('combobox', { name: 'Материалы занятий', exact: true })
    .click();
  await page.getByRole('option', { name: 'Без ДЗ', exact: true }).click();
  await expect.poll(() => queries.at(-1)?.get('attention')).toBe('homework');
  await page.getByRole('combobox', { name: 'Сортировка', exact: true }).click();
  await page.getByRole('option', { name: 'По имени', exact: true }).click();
  await expect.poll(() => queries.at(-1)?.get('sort')).toBe('name');
  const search = page.getByLabel('Поиск по имени или логину', { exact: true });
  await search.fill('Василиса');
  await expect.poll(() => queries.at(-1)?.get('q')).toBe('Василиса');
  await page
    .getByRole('button', { name: 'Очистить поиск', exact: true })
    .click();
  await expect(search).toHaveValue('');
  await expect(search).toBeFocused();
  mode = 'fixture';
  await page.goto('/teacher/students');
  await expect(list.getByRole('link')).toHaveCount(4);
  await expect(list.getByText('Без ДЗ: 12', { exact: true })).toHaveCount(2);
  await expect(list.getByText('Без конспекта: 3', { exact: true })).toHaveCount(
    2,
  );
  const flag = list.getByText('Без ДЗ: 12', { exact: true }).first();
  expect(await flag.evaluate((el) => getComputedStyle(el).color)).toBe(
    'rgb(180, 35, 24)',
  );
  expect(
    await flag.evaluate(
      (el) => getComputedStyle(el, '::before').backgroundColor,
    ),
  ).toBe('rgb(180, 35, 24)');
  await expect(list.getByRole('link').first()).toHaveAttribute(
    'href',
    '/teacher/students/99000',
  );
  await list.getByRole('link').first().focus();
  await expect(list.getByRole('link').first()).toBeFocused();
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  await page.setViewportSize({ width: 360, height: 844 });
  const materialWidth = (await page
    .getByRole('combobox', { name: 'Материалы занятий', exact: true })
    .boundingBox())!.width;
  const searchWidth = (await search.boundingBox())!.width;
  expect(materialWidth).toBeGreaterThanOrEqual(searchWidth - 1);

  await noOverflow();
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  await page.screenshot({
    path: '.artifacts/teacher-students-http-mobile.png',
    fullPage: true,
  });
  mode = 'empty';
  await page.reload();
  await expect(
    page.getByText('Пока нет учеников. Добавьте первого ученика.', {
      exact: true,
    }),
  ).toBeVisible();
  mode = 'error';
  await page.reload();
  await expect(
    page.getByRole('button', { name: 'Повторить', exact: true }),
  ).toBeVisible();
  expect(writes).toBe(0);
  expect(errors).toEqual([]);
  console.log(
    'Teacher list real GET + explicit HTTP states; source business writes0.',
  );
});
