import { test, expect, type Locator } from '@playwright/test';
import { existsSync, readFileSync } from 'node:fs';
import AxeBuilder from '@axe-core/playwright';
test.use({ trace: 'off', screenshot: 'off', video: 'off' });
const storage = '.artifacts/t15d-e-session.json';
test('E2: one shared embedded/fullscreen renderer, PDF pages/zoom, image, recovery and drafts', async ({
  browser,
}) => {
  test.skip(
    !process.env.LGG_T15D_PREVIEW,
    'Read-only preserved preview; file variants are browser fixtures.',
  );
  test.setTimeout(120000);
  const fixture = JSON.parse(
    readFileSync('.artifacts/t15d-preview.json', 'utf8'),
  );
  // Owner may have cleared the real queue. Replay only the preserved GET snapshot
  // for this answer; all downloads remain real and business writes stay blocked.
  const submitted = fixture.answers['0-2-20'];
  const context = await browser.newContext({
    baseURL: 'http://127.0.0.1:5173',
    ...(existsSync(storage) ? { storageState: storage } : {}),
    viewport: { width: 1340, height: 1000 },
  });
  const page = await context.newPage();
  page.setDefaultTimeout(10000);
  await page.addInitScript(() => {
    const live = new Set<string>(),
      create = URL.createObjectURL.bind(URL),
      revoke = URL.revokeObjectURL.bind(URL);
    Object.assign(window, { previewUrls: live });
    URL.createObjectURL = (value) => {
      const url = create(value);
      live.add(url);
      return url;
    };
    URL.revokeObjectURL = (url) => {
      live.delete(url);
      revoke(url);
    };
  });
  const writes: string[] = [],
    errors: string[] = [],
    fileGets: string[] = [];
  let mode = 'real',
    fileMode = 'real',
    targetId = submitted.id;
  let release = () => {},
    waiting = Promise.resolve();
  const pdf = {
    id: 99001,
    display_name: 'Решение — несколько страниц.pdf',
    download_url: '/submissions/99001/files/99001?homework_id=99001',
    mime_type: 'application/pdf',
    size_bytes: 5000,
  };
  page.on('pageerror', (e) => errors.push(e.message));
  await page.route('**/api/**', async (route) => {
    const req = route.request(),
      path = new URL(req.url()).pathname;
    if (req.method() !== 'GET' && !path.startsWith('/api/auth/')) {
      writes.push(req.method() + ' ' + path);
      return route.abort();
    }
    if (/\/(file|files\/\d+)$/.test(path)) fileGets.push(path);
    if (path === '/api/submissions/99001/files/99001') {
      if (fileMode === 'slow') await waiting;
      if (fileMode === 'error')
        return route.fulfill({ status: 503, json: { detail: 'Unavailable' } });
      if (fileMode === 'corrupt')
        return route.fulfill({
          contentType: 'application/pdf',
          body: 'not a PDF',
        });
      if (fileMode === 'unsupported')
        return route.fulfill({
          contentType: 'application/octet-stream',
          body: 'unknown format',
        });
      if (fileMode === 'large')
        return route.fulfill({
          contentType: 'application/pdf',
          headers: { 'Content-Length': String(21 * 1024 * 1024) },
          body: 'too large',
        });
      return route.fulfill({
        path: 'e2e/fixtures/math.pdf',
        contentType: 'application/pdf',
      });
    }
    if (path === `/api/homeworks/${submitted.homework_id}`) {
      const response = await route.fetch();
      return route.fulfill({
        response,
        json: { ...(await response.json()), can_review: true },
      });
    }
    if (path === `/api/submissions/${targetId}`) {
      const response = await route.fetch(),
        data = submitted;
      if (mode === 'real') return route.fulfill({ response, json: data });
      if (mode === 'text')
        return route.fulfill({
          response,
          json: {
            ...data,
            text_content: 'Полноценное решение текстом без вложений.',
            files: [],
          },
        });
      return route.fulfill({
        response,
        json: { ...data, files: [{ id: pdf.id, file: pdf }, ...data.files] },
      });
    }
    return route.continue();
  });
  async function zoomIn(region: Locator) {
    await region
      .getByRole('button', { name: 'Увеличить', exact: true })
      .click();
  }
  async function selectFile(name: string) {
    await page
      .getByRole('button', { name: 'Открыть ' + name, exact: true })
      .click();
    await page
      .getByRole('dialog')
      .getByRole('button', { name: 'Закрыть просмотр', exact: true })
      .click();
  }
  async function onlyOne() {
    await expect(page.locator('[data-file-viewer]')).toHaveCount(1);
  }
  async function audit() {
    const dialog = page.getByRole('dialog');
    if (await dialog.count()) {
      const content = page.locator('[data-modal-content]:visible');
      await expect(content).toHaveCSS('opacity', '1');
      if (await page.locator('[data-file-viewer="fullscreen"]').count()) {
        const box = await content.boundingBox();
        const size = page.viewportSize()!;
        expect(box!.x).toBeCloseTo(0, 0);
        expect(box!.y).toBeCloseTo(0, 0);
        expect(box!.width).toBeCloseTo(size.width, 0);
        expect(box!.height).toBeCloseTo(size.height, 0);
      }
    }
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  }
  async function draft() {
    await expect(
      page.getByLabel('Комментарий ученику', { exact: true }),
    ).toHaveValue('Черновик E2');
    await expect(
      page.getByRole('radio', { name: '0', exact: true }),
    ).toBeChecked();
    await expect(page.getByText('math.pdf', { exact: true })).toBeVisible();
  }
  try {
    await page.goto(
      `/teacher/review/${targetId}?homework_id=${submitted.homework_id}`,
    );
    await expect
      .poll(
        async () =>
          new URL(page.url()).pathname === '/login' ||
          (await page
            .getByRole('heading', { name: 'Решение ученика', exact: true })
            .isVisible()),
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
      await page.goto(
        `/teacher/review/${targetId}?homework_id=${submitted.homework_id}`,
      );
    }
    await context.storageState({ path: storage });
    const realURL = page.url();
    targetId = Number(new URL(realURL).pathname.split('/').at(-1));
    const embedded = page.getByRole('region', {
      name: 'Просмотр файла решения',
    });
    await expect(embedded.getByRole('img')).toBeVisible();
    await onlyOne();
    await page
      .getByRole('heading', { name: 'Решение ученика', exact: true })
      .locator('../..')
      .screenshot({ path: '.artifacts/t15d-e2-real-desktop.png' });
    const realImage = await embedded.getByRole('img').getAttribute('alt');
    expect(realImage).toBeTruthy();
    // Read real API first, then inject a second, multipage file without creating records.
    mode = 'multiple';
    await page.reload();
    await expect(
      embedded.getByLabel('Страница 1', { exact: true }),
    ).toBeVisible();
    await onlyOne();
    await expect(embedded.locator('[data-pdf-page]')).toHaveCount(2);
    const viewport = embedded.getByLabel('Область просмотра файла', {
      exact: true,
    });
    const canvas = embedded.getByLabel('Страница 1', { exact: true });
    expect((await canvas.boundingBox())!.width).toBeLessThanOrEqual(
      (await viewport.boundingBox())!.width + 1,
    );
    await expect
      .poll(() => canvas.locator('..').locator('div').textContent())
      .not.toBe('');
    await page.getByRole('radio', { name: '0', exact: true }).check();
    await page
      .getByLabel('Комментарий ученику', { exact: true })
      .fill('Черновик E2');
    await page
      .getByLabel('Добавить файлы к проверке', { exact: true })
      .setInputFiles('e2e/fixtures/math.pdf');
    await embedded.locator('[data-pdf-page="2"]').evaluate((node) => {
      node.parentElement!.scrollTop = (node as HTMLElement).offsetTop;
    });
    await expect(
      embedded.getByLabel('Страница 2', { exact: true }),
    ).toBeVisible();
    await zoomIn(embedded);
    await expect(
      embedded.getByRole('status').filter({ hasText: 'Масштаб 125%' }),
    ).toHaveText('Масштаб 125%');
    const opener = embedded.getByRole('button', { name: 'Открыть крупно' });
    await opener.focus();
    await opener.press('Enter');
    const full = page.getByRole('dialog');
    await expect(full).toBeVisible();
    await expect(full.getByLabel('Страница 2', { exact: true })).toBeVisible();
    await expect(
      full.getByRole('status').filter({ hasText: 'Масштаб 125%' }),
    ).toHaveText('Масштаб 125%');
    await onlyOne();
    await audit();
    const before = new URL(realURL);
    before.searchParams.set('file', String(pdf.id));
    await expect(page).toHaveURL(before.toString());
    await zoomIn(full);
    await page.keyboard.press('Escape');
    await expect(full).not.toBeAttached();
    await expect(opener).toBeFocused();
    await expect(page).toHaveURL(realURL);
    await expect(
      embedded.getByRole('status').filter({ hasText: 'Масштаб 150%' }),
    ).toHaveText('Масштаб 150%');
    await expect(
      embedded.getByLabel('Страница 2', { exact: true }),
    ).toBeVisible();
    await onlyOne();
    await draft();
    const download = page.waitForEvent('download');
    await embedded.getByRole('button', { name: 'Скачать файл' }).click();
    expect((await download).suggestedFilename()).toBe(pdf.display_name);
    // Inline file switching is independent from browser history and preserves per-file view.
    await selectFile(realImage!);
    await expect(embedded.getByRole('img', { name: realImage! })).toBeVisible();
    await onlyOne();
    await expect(page).toHaveURL(realURL);
    await selectFile(pdf.display_name);
    await expect(
      embedded.getByLabel('Страница 2', { exact: true }),
    ).toBeVisible();
    await expect(
      embedded.getByRole('status').filter({ hasText: 'Масштаб 150%' }),
    ).toHaveText('Масштаб 150%');
    // A condition fullscreen also suspends the embedded solution renderer.
    await page
      .locator('details')
      .filter({
        has: page.locator('summary').filter({ hasText: 'Условие задания' }),
      })
      .getByRole('button', { name: /^Открыть .*\.pdf$/ })
      .first()
      .click();
    await expect(full).toBeVisible();
    await onlyOne();
    await page.goBack();
    await expect(full).not.toBeAttached();
    await expect(page).toHaveURL(realURL);
    await draft();
    for (const width of [1340, 1024, 768, 360]) {
      await page.setViewportSize({ width, height: 1000 });
      if (width >= 1024) {
        await expect(
          embedded.getByLabel('Страница 2', { exact: true }),
        ).toBeVisible();
        await onlyOne();
      } else {
        await expect(embedded).toHaveCount(0);
        await expect(page.locator('[data-file-viewer]')).toHaveCount(0);
      }
      await draft();
      await audit();
      await page
        .getByRole('heading', { name: 'Решение ученика', exact: true })
        .scrollIntoViewIfNeeded();
      await page.screenshot({ path: `.artifacts/t15d-e2-review-${width}.png` });
    }
    const narrowOpener = page.getByRole('button', {
      name: 'Открыть ' + pdf.display_name,
      exact: true,
    });
    await narrowOpener.click();
    await expect(full.getByLabel('Страница 2', { exact: true })).toBeVisible();
    await onlyOne();
    await audit();
    await page.keyboard.press('Escape');
    await expect(full).not.toBeAttached();
    await expect(narrowOpener).toBeFocused();
    await draft();
    await page.setViewportSize({ width: 1340, height: 1000 });
    await page
      .getByRole('button', { name: 'Завершить проверку', exact: true })
      .click();
    const confirm = page.getByRole('dialog', { name: 'Завершить проверку?' });
    await expect(confirm).toBeVisible();
    await audit();
    await confirm.getByRole('button', { name: 'Отмена', exact: true }).click();
    await expect(confirm).not.toBeAttached();
    await draft();
    await page.getByRole('link', { name: 'К очереди', exact: true }).click();
    const leave = page.getByRole('dialog', { name: 'Уйти без сохранения?' });
    await leave.getByRole('button', { name: 'Отмена', exact: true }).click();
    await expect(leave).not.toBeAttached();
    await draft();
    // Finish local draft without submitting, then test read-only response variants.
    await page.getByLabel('Комментарий ученику', { exact: true }).fill('');
    await page.getByRole('link', { name: 'К очереди', exact: true }).click();
    await page
      .getByRole('dialog')
      .getByRole('button', { name: 'Уйти без сохранения', exact: true })
      .click();
    await expect(page).toHaveURL(/\/teacher\/review$/);
    await expect
      .poll(() =>
        page.evaluate(
          () =>
            (window as unknown as { previewUrls: Set<string> }).previewUrls
              .size,
        ),
      )
      .toBe(0);
    for (const variant of [
      'slow',
      'error',
      'corrupt',
      'unsupported',
      'large',
    ]) {
      fileMode = variant;
      mode = 'multiple';
      if (variant === 'slow')
        waiting = new Promise<void>((resolve) => {
          release = resolve;
        });
      await page.goto(realURL);
      if (variant === 'slow') {
        await expect(
          embedded.getByRole('status').filter({ hasText: 'Загружаем файл' }),
        ).toBeVisible();
        await selectFile(realImage!);
        await expect(embedded.getByRole('img')).toBeVisible();
        fileMode = 'real';
        release();
        await selectFile(pdf.display_name);
      } else {
        await expect(embedded.getByRole('alert')).toBeVisible();
        await expect(
          embedded.getByRole('button', { name: 'Скачать файл' }),
        ).toBeEnabled();
        fileMode = 'real';
        await embedded
          .getByRole('button', { name: 'Повторить просмотр' })
          .click();
      }
      await expect(
        embedded.getByLabel('Страница 1', { exact: true }),
      ).toBeVisible();
      await onlyOne();
      await audit();
    }
    mode = 'text';
    await page.reload();
    await expect(
      page.getByText('Полноценное решение текстом без вложений.'),
    ).toBeVisible();
    await expect(embedded).toHaveCount(0);
    await expect(page.locator('[data-file-viewer]')).toHaveCount(0);
    await expect(
      page.getByLabel('Комментарий ученику', { exact: true }),
    ).toBeEnabled();
    mode = 'real';
    const checked = fixture.answers['0-1-18'];
    await page.goto(
      `/teacher/review/${checked.id}?homework_id=${checked.homework_id}`,
    );
    await expect(page.getByText(/Проверено · Оценка:/)).toBeVisible();
    await expect(page.getByRole('radio')).toHaveCount(0);
    await expect(embedded).toHaveCount(0);
    const checkedWithFiles = fixture.answers['0-1-17'];
    await page.goto(
      `/teacher/review/${checkedWithFiles.id}?homework_id=${checkedWithFiles.homework_id}`,
    );
    await expect(page.getByText(/Проверено · Оценка:/)).toBeVisible();
    await expect(page.getByRole('radio')).toHaveCount(0);
    await expect(embedded.getByRole('img')).toBeVisible();
    await onlyOne();
    await audit();
    expect(fileGets.length).toBeGreaterThan(0);
    expect(writes).toEqual([]);
    expect(errors).toEqual([]);
  } finally {
    release();
    await context.storageState({ path: storage });
    await context.close();
  }
});
