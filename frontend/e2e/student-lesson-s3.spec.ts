import { test, expect, type Page } from '@playwright/test';
import { readFileSync } from 'node:fs';
import AxeBuilder from '@axe-core/playwright';
test.use({ trace: 'off', screenshot: 'off', video: 'off' });
async function geometry(page: Page) {
  expect(
    await page.evaluate(
      () => document.documentElement.scrollWidth <= innerWidth + 1,
    ),
  ).toBe(true);
  expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
}
test('S3 retained real API read-only and explicitly intercepted state fixtures', async ({
  page,
}) => {
  test.skip(!process.env.LGG_T15D_PREVIEW, 'Retained private preview required');
  test.setTimeout(180000);
  const account = JSON.parse(
    readFileSync('.artifacts/t15d-preview.json', 'utf8'),
  ).accounts.turov;
  const writes: string[] = [];
  const errors: string[] = [];
  page.on('pageerror', (e) => errors.push(e.message));
  await page.route('**/api/**', (route) => {
    const req = route.request();
    if (
      req.method() !== 'GET' &&
      !new URL(req.url()).pathname.startsWith('/api/auth/')
    ) {
      writes.push(req.method() + ' ' + new URL(req.url()).pathname);
      return route.abort();
    }
    return route.continue();
  });
  await page.goto('/login');
  await page.getByLabel('Логин', { exact: true }).fill(account.username);
  await page.getByLabel('Пароль', { exact: true }).fill(account.password);
  await page.getByRole('button', { name: 'Войти', exact: true }).click();
  await expect(page).not.toHaveURL(/\/login/);
  const hwResponse = page.waitForResponse(
    (r) => new URL(r.url()).pathname === '/api/homeworks/56',
  );
  await page.goto('/student/homeworks/56');
  const baseHomework = await (await hwResponse).json();
  expect(baseHomework.id).toBe(56);
  await expect(
    page.getByRole('region', { name: 'Ваше решение', exact: true }),
  ).toBeVisible();
  // Capture only authorized GET data to reuse in the explicitly mocked phase.
  const answerResponse = page.waitForResponse(
    (r) =>
      new URL(r.url()).pathname ===
      `/api/submissions/${baseHomework.working_submission_id}`,
  );
  await page.reload();
  const baseAnswer = await (await answerResponse).json();
  for (const width of [1340, 768, 360]) {
    await page.setViewportSize({ width, height: 900 });
    for (const id of [123, 120, 124]) {
      await page.goto(`/student/lessons/${id}`);
      await expect(
        page.getByRole('heading', { name: 'Конспект', exact: true }),
      ).toBeVisible();
      await expect(
        page.getByRole('heading', { name: 'Домашние задания', exact: true }),
      ).toBeVisible();
      if (id === 120) {
        const action = page.getByRole('button', {
          name: 'Посмотреть результат',
          exact: true,
        });
        await action.focus();
        await action.press('Enter');
        await expect(
          page.getByRole('region', { name: /^Результат проверки:/ }),
        ).toBeFocused();
      }
      if (id === 123) {
        const action = page.getByRole('link', {
          name: 'Открыть отправленное решение',
          exact: true,
        });
        if (await action.count()) {
          await expect(action).toBeVisible();
          await action.click();
          await expect(
            page.getByText(/Решение отправлено. До проверки/),
          ).toBeVisible();
          await page.goBack();
          await expect(action).toBeVisible();
        } else {
          // Owner can check the retained work; never restore its old submitted state.
          const checkedAction = page.getByRole('button', {
            name: 'Посмотреть результат',
            exact: true,
          });
          await expect(checkedAction).toBeVisible();
          await checkedAction.click();
          await expect(
            page.getByRole('region', { name: /^Результат проверки:/ }),
          ).toBeFocused();
        }
      }
      await geometry(page);
    }
    await page.screenshot({
      path: `.artifacts/s3-real-empty-${width}.png`,
      fullPage: true,
    });
  }
  expect(writes).toEqual([]);
  // HTTP fixtures below do NOT certify real submit/edit/review API behavior.
  let mode = 'empty';
  await page.route('**/api/homeworks/56', (route) =>
    route.fulfill({
      json: {
        ...baseHomework,
        working_submission_id: mode === 'empty' ? null : baseAnswer.id,
        access_mode: mode === 'readonly' ? 'read_only' : 'active',
        read_only_reason: mode === 'readonly' ? 'course_archived' : null,
      },
    }),
  );
  await page.route(`**/api/submissions/${baseAnswer.id}?*`, async (route) => {
    if (mode === 'error')
      return route.fulfill({ status: 503, json: { detail: 'Unavailable' } });
    if (mode === 'loading') await new Promise((r) => setTimeout(r, 1500));
    return route.fulfill({
      json: {
        ...baseAnswer,
        status: mode.startsWith('checked')
          ? 'checked'
          : mode === 'submitted'
            ? 'submitted'
            : 'draft',
        grade: mode === 'checked0' ? 0 : mode === 'checked5' ? 5 : null,
        teacher_comment: mode === 'checked5' ? 'Все шаги верны' : null,
        review_files:
          mode === 'checked5' && baseHomework.file
            ? [
                {
                  id: 99002,
                  file: {
                    ...baseHomework.file,
                    display_name: 'Проверка — пример.pdf',
                  },
                },
              ]
            : [],
      },
    });
  });
  for (const width of [1340, 768, 360]) {
    await page.setViewportSize({ width, height: 900 });
    for (mode of [
      'empty',
      'draft',
      'submitted',
      'checked0',
      'checked5',
      'readonly',
      'error',
      'loading',
    ]) {
      await page.goto('/student/homeworks/56');
      const answer = page.getByRole('region', {
        name: 'Ваше решение',
        exact: true,
      });
      if (mode === 'error') {
        await expect(
          page.getByRole('button', { name: 'Повторить', exact: true }),
        ).toBeVisible();
        await expect(answer).toHaveCount(0);
        mode = 'draft';
        await page
          .getByRole('button', { name: 'Повторить', exact: true })
          .click();
        await expect(answer).toBeVisible();
      } else if (mode === 'loading') {
        await expect(page.getByText('Загружаем…').first()).toBeVisible();
        await expect(answer).toBeVisible();
      } else {
        await expect(answer).toBeVisible();
        if (mode === 'empty') {
          await expect(answer).toHaveAttribute('data-state', 'empty');
          await page
            .getByLabel('Текст решения или вопросы')
            .fill('Локальное решение');
          await expect(answer).toHaveAttribute('data-state', 'local');
          const expand = page.getByRole('button', {
            name: 'Развернуть файл задания',
            exact: true,
          });
          if (await expand.isVisible()) await expand.click();
          const condition = page
            .getByRole('region', {
              name: 'Просмотр: файл задания',
              exact: true,
            })
            .getByRole('button', { name: 'Открыть крупно', exact: true });
          await condition.click();
          const viewer = page.getByRole('dialog');
          await expect(viewer).toBeVisible();
          await expect(
            viewer.getByRole('button', { name: 'Увеличить', exact: true }),
          ).toBeVisible();
          await page.goBack();
          await expect(viewer).toHaveCount(0);
          await expect(condition).toBeFocused();
          await expect(
            page.getByLabel('Текст решения или вопросы'),
          ).toHaveValue('Локальное решение');

          await page
            .getByRole('link', { name: 'Все домашние задания', exact: true })
            .click();
          const guard = page.getByRole('dialog', {
            name: 'Уйти без сохранения?',
          });
          await expect(guard).toBeVisible();
          await guard
            .getByRole('button', { name: 'Отмена', exact: true })
            .click();
          await expect(
            page.getByLabel('Текст решения или вопросы'),
          ).toHaveValue('Локальное решение');
          // Leave explicitly through the existing dirty guard before the next fixture.
          await page
            .getByRole('link', { name: 'Все домашние задания', exact: true })
            .click();
          await guard
            .getByRole('button', { name: 'Уйти без сохранения', exact: true })
            .click();
          await expect(page).not.toHaveURL(/\/homeworks\/56/);
          continue;
        }
        if (mode.startsWith('checked'))
          await expect(
            page.getByText(`Оценка: ${mode === 'checked0' ? 0 : 5} из 5`),
          ).toBeVisible();
        if (mode === 'readonly')
          await expect(page.getByLabel('Добавить файлы')).toHaveCount(0);
      }
      if (mode === 'checked5') {
        await page
          .getByRole('button', {
            name: 'Открыть Проверка — пример.pdf',
            exact: true,
          })
          .click();
        await expect(page.getByRole('dialog')).toBeVisible();
        await page
          .getByRole('dialog')
          .getByRole('button', { name: 'Закрыть просмотр', exact: true })
          .click();
        await expect(page.getByRole('dialog')).toHaveCount(0);
      }
      await geometry(page);
      if (mode === 'submitted')
        await page.screenshot({
          path: `.artifacts/s3-fixture-submitted-${width}.png`,
          fullPage: true,
        });
    }
  }
  mode = 'checked0';
  await page.route('**/api/homeworks?*', (route) => {
    if (new URL(route.request().url()).searchParams.get('lesson_id') !== '123')
      return route.continue();
    return route.fulfill({
      json: [
        { ...baseHomework, placement_id: 99001, placement_kind: 'debt' },
        {
          ...baseHomework,
          id: 99002,
          placement_id: 99002,
          title: 'Второе задание',
          working_submission_id: null,
          placement_kind: 'original',
        },
      ],
    });
  });
  for (const width of [1340, 768, 360]) {
    await page.setViewportSize({ width, height: 900 });
    await page.goto('/student/lessons/123');
    await expect(page.getByRole('article')).toHaveCount(2);
    await expect(
      page.getByRole('link', { name: 'Подготовить решение', exact: true }),
    ).toHaveAttribute('href', '/student/homeworks/99002');
    const prepareLabel = page
      .getByRole('link', { name: 'Подготовить решение', exact: true })
      .locator('.mantine-Button-label');
    expect(
      await prepareLabel.evaluate(
        (el) =>
          el.scrollWidth <= el.clientWidth + 1 &&
          el.scrollHeight <= el.clientHeight + 1,
      ),
    ).toBe(true);

    await page
      .getByRole('button', { name: 'Посмотреть результат', exact: true })
      .click();
    await expect(
      page.getByRole('region', { name: /^Результат проверки:/ }),
    ).toBeFocused();
    await geometry(page);
    await page.screenshot({
      path: `.artifacts/s3-fixture-multiple-${width}.png`,
      fullPage: true,
    });
  }
  expect(writes).toEqual([]);
  expect(errors).toEqual([]);
});
