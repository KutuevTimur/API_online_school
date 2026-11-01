import { test, expect } from '@playwright/test';
import { existsSync, readFileSync } from 'node:fs';
import AxeBuilder from '@axe-core/playwright';
test.use({ trace: 'off', screenshot: 'off', video: 'off' });
const storage = '.artifacts/t15d-e-session.json';
test('package F: secondary clarity, explicit notification open and preserved forms, read-only preview', async ({
  browser,
}) => {
  test.skip(
    !process.env.LGG_T15D_PREVIEW,
    'Preserved preview; no seed/reset or real business writes.',
  );
  test.setTimeout(120000);
  const fixture = JSON.parse(
    readFileSync('.artifacts/t15d-preview.json', 'utf8'),
  );
  const context = await browser.newContext({
    baseURL: 'http://127.0.0.1:5173',
    ...(existsSync(storage) ? { storageState: storage } : {}),
  });
  const page = await context.newPage();
  page.setDefaultTimeout(10000);
  const writes: string[] = [],
    errors: string[] = [],
    opens: string[] = [];
  let mode = 'real',
    marked = false,
    noticeMode = 'fixture';
  let release = () => {},
    waiting = Promise.resolve();
  const courseId = fixture.courses.vasilisa;
  const coursePath = `/teacher/courses/${courseId}`;
  page.on('pageerror', (e) => errors.push(e.message));
  await page.route('**/api/**', async (route) => {
    const req = route.request(),
      url = new URL(req.url()),
      path = url.pathname;
    if (path === '/api/notifications/99991/read') {
      opens.push('read');
      marked = true;
      return route.fulfill({
        json: { id: 99991, read_at: '2026-10-22T16:00:00Z' },
      });
    }
    if (req.method() !== 'GET' && !path.startsWith('/api/auth/')) {
      writes.push(req.method() + ' ' + path);
      return route.abort();
    }
    if (path === '/api/notifications/99991/target') {
      opens.push('target');
      return route.fulfill({
        json:
          mode === 'unavailable'
            ? { available: false }
            : {
                available: true,
                object_type: 'lesson',
                object_id: fixture.lessons['0-3-16'].id,
              },
      });
    }
    if (path === '/api/notifications' && noticeMode !== 'real') {
      if (mode === 'loading') await waiting;
      if (mode === 'error')
        return route.fulfill({ status: 503, json: { detail: 'Unavailable' } });
      return route.fulfill({
        json: {
          total: mode === 'empty' ? 0 : 2,
          items:
            mode === 'empty'
              ? []
              : [
                  {
                    id: 99991,
                    event_type: 'solution_submitted',
                    object_type: 'submission',
                    object_id: 15,
                    created_at: '2026-10-22T12:00:00Z',
                    read_at: marked ? '2026-10-22T16:00:00Z' : null,
                  },
                  {
                    id: 99992,
                    event_type: 'lesson_cancelled',
                    object_type: 'lesson',
                    object_id: 9,
                    created_at: '2026-10-21T12:00:00Z',
                    read_at: '2026-10-22T12:00:00Z',
                  },
                ],
        },
      });
    }
    if (path === `/api/courses/${courseId}` && mode === 'readonly') {
      const response = await route.fetch();
      return route.fulfill({
        response,
        json: {
          ...(await response.json()),
          access_mode: 'read_only',
          read_only_reason: 'course_archived',
          can_manage: false,
          is_deleted: true,
        },
      });
    }
    if (/^\/api\/users\/\d+$/.test(path) && mode.startsWith('profile-')) {
      if (mode === 'profile-loading') await waiting;
      if (mode === 'profile-error')
        return route.fulfill({ status: 503, json: { detail: 'Unavailable' } });
    }
    return route.continue();
  });
  async function audit() {
    // Measure settled dialog colors, not intermediate fade-in compositing.
    const modal = page.locator('.mantine-Modal-content:visible');
    if (await modal.count()) await expect(modal).toHaveCSS('opacity', '1');
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  }
  async function toggle(text: string) {
    const summary = page
      .locator('summary')
      .filter({ hasText: new RegExp('^' + text + '$') });
    expect((await summary.boundingBox())!.height).toBeGreaterThanOrEqual(44);
    const wasOpen = await summary.locator('..').getAttribute('open');
    await summary.press('Enter');
    if (wasOpen === null)
      await expect(summary.locator('..')).toHaveAttribute('open', '');
    else await expect(summary.locator('..')).not.toHaveAttribute('open');
    return summary;
  }
  try {
    // Existing storage first. A login is only used if the saved session has expired.
    await page.goto('/profile');
    await expect
      .poll(
        async () =>
          new URL(page.url()).pathname === '/login' ||
          (await page.getByLabel('Имя', { exact: true }).isVisible()),
      )
      .toBe(true);
    if (new URL(page.url()).pathname === '/login') {
      await page
        .getByLabel('Логин', { exact: true })
        .fill(fixture.accounts.teacher.username);
      await page
        .getByLabel('Пароль', { exact: true })
        .fill(fixture.accounts.teacher.password);
      await page.getByRole('button', { name: 'Войти', exact: true }).click();
      await expect(page).not.toHaveURL(/\/login/);
      await page.goto('/profile');
    }
    await expect(page.getByLabel('Имя', { exact: true })).toBeVisible();
    await context.storageState({ path: storage });
    for (const width of [1340, 768, 360]) {
      await page.setViewportSize({ width, height: 950 });
      await expect(
        page.getByRole('button', { name: 'Сохранить профиль' }),
      ).toBeDisabled();
      const summary = await toggle('Изменить пароль');
      await expect(
        page.getByText(
          'После смены пароля нужно войти снова. Другие сессии завершатся.',
        ),
      ).toBeVisible();
      await expect(
        page.getByLabel('Текущий пароль', { exact: true }),
      ).toHaveAttribute('autocomplete', 'current-password');
      await expect(
        page.getByRole('button', { name: 'Изменить пароль', exact: true }),
      ).toBeDisabled();
      await audit();
      await summary.press('Space');
      await toggle('Аватар профиля');
      await expect(
        page.getByLabel('Новый аватар', { exact: true }),
      ).toBeVisible();
      await audit();
      await toggle('Аватар профиля');
      await page.getByRole('heading', { level: 1 }).scrollIntoViewIfNeeded();
      await page.screenshot({ path: `.artifacts/t15d-f-profile-${width}.png` });
    }
    const first = page.getByLabel('Имя', { exact: true }),
      original = await first.inputValue();
    await first.fill(original + ' draft F');
    await toggle('Изменить пароль');
    await page
      .getByLabel('Текущий пароль', { exact: true })
      .fill('local-draft-F');
    await toggle('Изменить пароль');
    // A real in-app transition exercises the existing dirty guard while password is collapsed.
    await page.getByRole('link', { name: 'Мой день', exact: true }).click();
    const dialog = page.getByRole('dialog', { name: 'Уйти без сохранения?' });
    await expect(dialog).toBeVisible();
    await audit();
    await dialog.getByRole('button', { name: 'Отмена', exact: true }).click();
    await expect(dialog).toBeHidden();
    await expect(first).toHaveValue(original + ' draft F');
    await toggle('Изменить пароль');
    await expect(
      page.getByLabel('Текущий пароль', { exact: true }),
    ).toHaveValue('local-draft-F');
    await page.getByLabel('Текущий пароль', { exact: true }).fill('');
    await first.fill(original);
    await toggle('Изменить пароль');
    for (const state of ['profile-loading', 'profile-error']) {
      mode = state;
      if (state === 'profile-loading')
        waiting = new Promise<void>((resolve) => {
          release = resolve;
        });
      await page.reload();
      if (state === 'profile-loading') {
        await expect(
          page.getByRole('status').filter({ hasText: 'Загружаем' }),
        ).toBeVisible();
        mode = 'real';
        release();
      } else {
        await expect(
          page.getByRole('button', { name: 'Повторить', exact: true }),
        ).toBeVisible();
        mode = 'real';
        await page
          .getByRole('button', { name: 'Повторить', exact: true })
          .click();
      }
      await expect(first).toBeVisible();
    }
    await page.goto(coursePath);
    await expect(page.getByRole('heading', { level: 1 })).toBeVisible();
    const participation = page.locator('details').filter({
      has: page.locator('summary').filter({ hasText: /^Участие в курсе$/ }),
    });
    await expect(participation).not.toHaveAttribute('open');
    await expect(
      page.getByRole('button', { name: 'Открепить от курса' }),
    ).toBeHidden();
    for (const width of [1340, 768, 360]) {
      await page.setViewportSize({ width, height: 950 });
      await toggle('Участие в курсе');
      await expect(participation.getByRole('link').first()).not.toContainText(
        /ученик \d+/i,
      );
      const detach = participation.getByRole('button', {
        name: 'Открепить от курса',
      });
      await detach.click();
      const confirm = page.getByRole('dialog');
      await expect(confirm).toBeVisible();
      await audit();
      await page.keyboard.press('Escape');
      await expect(confirm).toBeHidden();
      await expect(detach).toBeFocused();
      await toggle('Участие в курсе');
      await toggle('Настройки обучения');
      await expect(
        page.getByRole('heading', { name: 'Обложка курса', exact: true }),
      ).toBeVisible();
      await expect(
        page.getByLabel('Новая обложка', { exact: true }),
      ).toBeVisible();
      await expect(page.getByText('Аватар', { exact: true })).toHaveCount(0);
      const description = page.getByLabel('Описание', { exact: true });
      const savedDescription = await description.inputValue();
      await description.fill(savedDescription + ' local F draft');
      await toggle('Настройки обучения');
      await toggle('Настройки обучения');
      await expect(description).toHaveValue(
        savedDescription + ' local F draft',
      );
      await description.fill(savedDescription);
      await audit();
      await toggle('Настройки обучения');
      await page.getByRole('heading', { level: 1 }).scrollIntoViewIfNeeded();
      await page.screenshot({ path: `.artifacts/t15d-f-course-${width}.png` });
    }
    mode = 'readonly';
    await page.reload();
    await expect(page.getByText(/Только просмотр/).first()).toBeVisible();
    await toggle('Участие в курсе');
    await expect(
      page.getByRole('button', { name: /Открепить|Прикрепить|Архивировать/ }),
    ).toHaveCount(0);
    await expect(
      page.getByText('Настройки обучения', { exact: true }),
    ).toHaveCount(0);
    await audit();
    mode = 'real';
    await page.goto('/teacher/archive');
    await expect(page.getByText('Архивных курсов пока нет.')).toBeVisible();
    await page.getByRole('link', { name: 'К ученикам', exact: true }).click();
    await expect(page).toHaveURL(/\/teacher\/students$/);
    await page.goto('/notifications');
    for (const width of [1340, 768, 360]) {
      await page.setViewportSize({ width, height: 950 });
      await expect(page.getByRole('article')).toHaveCount(2);
      await expect(page.getByText('Новое · не прочитано')).toBeVisible();
      await expect(page.getByText('Прочитано', { exact: true })).toBeVisible();
      const article = page.getByRole('article').first();
      if (width === 1340)
        expect((await article.boundingBox())!.height).toBeLessThan(110);
      expect(opens).toEqual([]);
      await audit();
      await page.screenshot({
        path: `.artifacts/t15d-f-notifications-${width}.png`,
      });
    }
    await page.getByRole('checkbox').click();
    await expect(page).toHaveURL(/unread=1/);
    await expect(page.getByRole('checkbox')).toBeChecked();
    expect(opens).toEqual([]);
    mode = 'unavailable';
    await page.getByRole('article').first().getByRole('button').press('Enter');
    await expect(page.getByText(/Материал больше недоступен/)).toBeVisible();
    expect(opens).toEqual(['read', 'target']);
    await expect(page.getByText('Прочитано', { exact: true })).toHaveCount(2);
    mode = 'real';
    await page.getByRole('article').first().getByRole('button').click();
    await expect(page).toHaveURL(/\/teacher\/lessons\//);
    expect(opens).toEqual(['read', 'target', 'read', 'target']);
    for (const state of ['loading', 'empty', 'error']) {
      mode = state;
      if (state === 'loading')
        waiting = new Promise<void>((resolve) => {
          release = resolve;
        });
      await page.goto('/notifications');
      if (state === 'loading') {
        await expect(
          page.getByRole('status').filter({ hasText: 'Загружаем' }),
        ).toBeVisible();
        mode = 'real';
        release();
        await expect(page.getByRole('article')).toHaveCount(2);
      }
      if (state === 'empty')
        await expect(page.getByText('Уведомлений пока нет.')).toBeVisible();
      if (state === 'error') {
        await expect(
          page.getByRole('button', { name: 'Повторить', exact: true }),
        ).toBeVisible();
        mode = 'real';
        await page
          .getByRole('button', { name: 'Повторить', exact: true })
          .click();
        await expect(page.getByRole('article')).toHaveCount(2);
      }
      await audit();
    }
    noticeMode = 'real';
    mode = 'real';
    await page.reload();
    await expect(page.getByRole('heading', { level: 1 })).toHaveText(
      'Уведомления',
    );
    // Actual preview list is read-only: no opening/marking real notification IDs.
    await expect(page.getByRole('article').first()).toBeVisible();
    expect(writes).toEqual([]);
    expect(errors).toEqual([]);
  } finally {
    await context.storageState({ path: storage });
    await context.close();
  }
});
