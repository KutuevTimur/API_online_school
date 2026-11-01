import { test, expect, type Locator } from '@playwright/test';
import { readFileSync } from 'node:fs';
import AxeBuilder from '@axe-core/playwright';
test.use({ trace: 'off', screenshot: 'off', video: 'off' });
test('S1 student: real protected PDF, continuous 1/20/100 pages, zoom/selection/memory/download/recovery', async ({
  page,
  context,
}) => {
  test.skip(
    !process.env.LGG_T15D_PREVIEW,
    'Preserved preview read-only; synthetic document variants are HTTP fixtures.',
  );
  test.setTimeout(120000);
  const fixture = JSON.parse(
    readFileSync('.artifacts/t15d-preview.json', 'utf8'),
  );
  const checkpoint = JSON.parse(
    readFileSync('.artifacts/t15d-student-preview.json', 'utf8'),
  );
  const entry = Object.values(checkpoint.lessons)[0] as {
    id: number;
    lecture: number;
    homework: number;
    submission: { id: number };
  };
  const writes: string[] = [],
    errors: string[] = [];
  let mode = 'real',
    downloadPath = '',
    realBytes = Buffer.alloc(0),
    longName = false;
  const name = 'Конспект с очень длинным названием — '.repeat(8) + '.pdf';
  const variants = new Map(
    [1, 20, 100].map((n) => [
      String(n),
      readFileSync(`.artifacts/s1-pdf/${n}.pdf`),
    ]),
  );
  page.on('pageerror', (error) => errors.push(error.message));
  await page.route('**/api/**', async (route) => {
    const req = route.request(),
      path = new URL(req.url()).pathname;
    if (req.method() !== 'GET' && !path.startsWith('/api/auth/')) {
      writes.push(req.method() + ' ' + path);
      return route.abort();
    }
    if (path === `/api/lectures/${entry.lecture}`) {
      const response = await route.fetch(),
        data = await response.json();
      downloadPath = '/api' + data.file.download_url.split('?')[0];
      if (longName) data.file.display_name = name;
      return route.fulfill({ response, json: data });
    }
    if (downloadPath && path === downloadPath) {
      expect(req.headers().authorization).toMatch(/^Bearer /);
      if (mode === 'real') {
        const response = await route.fetch();
        expect(response.status()).toBe(200);
        realBytes = await response.body();
        return route.fulfill({ response });
      }
      if (mode === 'network') return route.abort('internetdisconnected');
      if (mode === '403' || mode === '404')
        return route.fulfill({
          status: Number(mode),
          json: { detail: 'Unavailable' },
        });
      if (mode === 'damaged')
        return route.fulfill({
          contentType: 'application/pdf',
          body: 'damaged PDF',
        });
      if (mode === 'unsupported')
        return route.fulfill({
          contentType: 'application/octet-stream',
          body: 'unknown',
        });
      if (mode === 'large')
        return route.fulfill({
          contentType: 'application/pdf',
          headers: { 'Content-Length': String(21 * 1024 * 1024) },
          body: 'large',
        });
      if (mode === 'password')
        return route.fulfill({
          contentType: 'application/pdf',
          path: '.artifacts/s1-pdf/password.pdf',
        });
      return route.fulfill({
        contentType: 'application/pdf',
        body: variants.get(mode)!,
      });
    }
    return route.continue();
  });
  await page.goto('/login');
  await page
    .getByLabel('Логин', { exact: true })
    .fill(fixture.accounts.turov.username);
  await page
    .getByLabel('Пароль', { exact: true })
    .fill(fixture.accounts.turov.password);
  await page.getByRole('button', { name: 'Войти', exact: true }).click();
  await expect(page).not.toHaveURL(/\/login/);
  const full = page.getByRole('dialog');
  const root = full.getByLabel('Область просмотра файла', { exact: true });
  async function open() {
    await page.goto(`/student/materials/${entry.lecture}`);
    const button = page.getByRole('button', { name: /^Открыть / }).first();
    await button.click();
    await expect(full).toBeVisible();
    return button;
  }
  async function rendered(region: Locator, n = 1) {
    await expect(
      region.getByLabel(`Страница ${n}`, { exact: true }),
    ).toBeVisible();
    await expect(
      region.getByLabel(`Страница ${n}`, { exact: true }).locator('..'),
    ).toHaveAttribute('aria-busy', 'false');
  }
  async function pinch(target: Locator, factor = 1.4) {
    const cdp = await context.newCDPSession(page);
    await cdp.send('Emulation.setTouchEmulationEnabled', {
      enabled: true,
      maxTouchPoints: 2,
    });
    const bounds = await root.boundingBox();
    const y = bounds!.y + 160;
    const before = (await target.boundingBox())!.width;
    await cdp.send('Input.dispatchTouchEvent', {
      type: 'touchStart',
      touchPoints: [
        { x: 130, y, id: 1 },
        { x: 230, y, id: 2 },
      ],
    });
    for (const distance of [110, 120, 100 * factor]) {
      await cdp.send('Input.dispatchTouchEvent', {
        type: 'touchMove',
        touchPoints: [
          { x: 180 - distance / 2, y, id: 1 },
          { x: 180 + distance / 2, y, id: 2 },
        ],
      });
    }
    await cdp.send('Input.dispatchTouchEvent', {
      type: 'touchEnd',
      touchPoints: [],
    });
    await expect
      .poll(async () => (await target.boundingBox())!.width / before)
      .toBeCloseTo(factor, 1);
    expect(await page.evaluate(() => visualViewport!.scale)).toBe(1);
    await cdp.detach();
  }
  async function audit() {
    const geometry = await page
      .locator('[data-modal-content]')
      .evaluate((node) => {
        const box = node.getBoundingClientRect();
        return {
          x: box.x,
          y: box.y,
          width: box.width,
          height: box.height,
          expectedWidth: innerWidth,
          expectedHeight: innerHeight,
        };
      });
    expect(geometry.x).toBeCloseTo(0, 0);
    expect(geometry.y).toBeCloseTo(0, 0);
    expect(geometry.width).toBeCloseTo(geometry.expectedWidth, 0);
    expect(geometry.height).toBeCloseTo(geometry.expectedHeight, 0);
    await expect(page.locator('.mantine-Popover-dropdown')).not.toBeAttached();
    expect(
      await page.evaluate(
        () => document.documentElement.scrollWidth <= innerWidth,
      ),
    ).toBe(true);
    expect((await new AxeBuilder({ page }).analyze()).violations).toEqual([]);
  }
  const opener = await open();
  await rendered(full);
  expect(realBytes.length).toBeGreaterThan(100);
  const downloadEvent = page.waitForEvent('download');
  await full.getByRole('button', { name: 'Скачать файл' }).click();
  const download = await downloadEvent;
  expect(readFileSync((await download.path())!)).toEqual(realBytes);
  expect(download.suggestedFilename()).toMatch(/\.pdf$/);
  await page.keyboard.press('Escape');
  await expect(full).not.toBeAttached();
  await expect(opener).toBeFocused();
  longName = true;
  for (const n of [1, 20, 100]) {
    mode = String(n);
    await open();
    await rendered(full);
    await expect(full.locator('[data-pdf-page]')).toHaveCount(n);
    expect(await full.locator('canvas').count()).toBeLessThan(10);
    await expect(full.locator('summary')).toHaveCount(0);
    if (n > 1) {
      await root.focus();
      await page.keyboard.press('PageDown');
      await expect
        .poll(() => root.evaluate((node) => node.scrollTop))
        .toBeGreaterThan(0);
      await root.evaluate((node) => {
        const page = node.querySelector<HTMLElement>('[data-pdf-page="15"]')!;
        node.scrollTop = page.offsetTop + page.offsetHeight * 0.35;
      });
      await rendered(full, 15);
      await expect(
        full.getByLabel('Страница 1', { exact: true }),
      ).not.toBeAttached();
      expect(await full.locator('canvas').count()).toBeLessThan(10);
      const offset = await root.evaluate((node) => {
        const p = node.querySelector<HTMLElement>('[data-pdf-page="15"]')!;
        return (node.scrollTop - p.offsetTop) / p.offsetHeight;
      });
      await full
        .getByRole('button', { name: 'Увеличить', exact: true })
        .click();
      await full
        .getByRole('button', { name: 'Увеличить', exact: true })
        .click();
      await expect
        .poll(() =>
          root.evaluate((node) => {
            const p = node.querySelector<HTMLElement>('[data-pdf-page="15"]')!;
            return (node.scrollTop - p.offsetTop) / p.offsetHeight;
          }),
        )
        .toBeCloseTo(offset, 1);
      await rendered(full, 15);
      // Selecting text pins the page while scrolling away; releasing it frees the canvas.
      await full
        .locator('[data-pdf-page="15"] span')
        .first()
        .evaluate((node) => {
          const r = document.createRange();
          r.selectNodeContents(node);
          const selection = getSelection()!;
          selection.removeAllRanges();
          selection.addRange(r);
        });
      await root.evaluate((node) => {
        node.scrollTop = node.scrollHeight;
      });
      await expect(
        full.getByLabel('Страница 15', { exact: true }),
      ).toBeAttached();
      await page.evaluate(() => getSelection()?.removeAllRanges());
      await expect(
        full.getByLabel('Страница 15', { exact: true }),
      ).not.toBeAttached();
      await root.evaluate((node) => {
        const p = node.querySelector<HTMLElement>('[data-pdf-page="15"]')!;
        node.scrollTop = p.offsetTop;
      });
      await rendered(full, 15);
    }
    for (const width of [1920, 1340, 768, 360]) {
      await page.setViewportSize({ width, height: 900 });
      await audit();
      const box = await root.boundingBox();
      expect(box!.y).toBeLessThanOrEqual(104);
      await expect(
        full.getByRole('button', { name: 'Увеличить', exact: true }),
      ).toBeVisible();
      if (n === 20 && width === 360) {
        await pinch(full.getByLabel('Страница 15', { exact: true }));
        const beforeScroll = await root.evaluate((node) => node.scrollTop);
        const cdp = await context.newCDPSession(page);
        await cdp.send('Input.dispatchTouchEvent', {
          type: 'touchStart',
          touchPoints: [{ x: 180, y: 600, id: 1 }],
        });
        for (const y of [550, 450, 350])
          await cdp.send('Input.dispatchTouchEvent', {
            type: 'touchMove',
            touchPoints: [{ x: 180, y, id: 1 }],
          });
        await cdp.send('Input.dispatchTouchEvent', {
          type: 'touchEnd',
          touchPoints: [],
        });
        await expect
          .poll(() => root.evaluate((node) => node.scrollTop))
          .toBeGreaterThan(beforeScroll);
        await cdp.detach();
      }
      await page.screenshot({ path: `.artifacts/s1-pdf/${n}-${width}.png` });
    }
    // Actual browser zoom via Chrome UI shortcut; confirm devicePixelRatio changed.
    const ratio = await page.evaluate(() => devicePixelRatio);
    await page.keyboard.press('ControlOrMeta+0');
    for (let i = 0; i < 4; i++) await page.keyboard.press('ControlOrMeta++');
    // Headless Chrome may not implement browser UI zoom. Do not count emulation as PASS.
    const zoomed = await page.evaluate(() => devicePixelRatio);
    test.info().annotations.push({
      type: 'browser-zoom',
      description:
        zoomed > ratio
          ? 'Browser UI zoom changed DPR; reflow inspected'
          : 'NOT RUN actual 200% browser zoom: headless shortcuts did not change DPR',
    });
    await page.keyboard.press('ControlOrMeta+0');
    await page.goBack();
    await expect(full).not.toBeAttached();
  }
  for (const variant of [
    'damaged',
    'password',
    'unsupported',
    'large',
    '403',
    '404',
    'network',
  ]) {
    mode = variant;
    await open();
    await expect(full.getByRole('alert')).toBeVisible();
    if (variant === '403')
      await expect(full.getByRole('alert')).toContainText('Нет доступа');
    if (variant === '404')
      await expect(full.getByRole('alert')).toContainText('больше недоступен');
    mode = '1';
    await full.getByRole('button', { name: 'Повторить просмотр' }).click();
    await rendered(full);
    await page.keyboard.press('Escape');
    await expect(full).not.toBeAttached();
  }
  // The preserved checked answer has a real solution image but no reviewer
  // attachment. Supply only that missing GET field and its bytes in the browser.
  await page.route(
    `**/api/submissions/${entry.submission.id}?*`,
    async (route) => {
      const response = await route.fetch(),
        data = await response.json();
      data.review_files = [
        {
          id: 99010,
          file: {
            id: 99010,
            display_name: 'Проверка S1.pdf',
            download_url: `/submissions/99010/review-files/99010?homework_id=${entry.homework}`,
            mime_type: 'application/pdf',
            size_bytes: variants.get('1')!.length,
          },
        },
      ];
      return route.fulfill({ response, json: data });
    },
  );
  await page.route('**/api/submissions/99010/review-files/99010?*', (route) =>
    route.fulfill({ contentType: 'application/pdf', body: variants.get('1')! }),
  );
  await page.goto(`/student/lessons/${entry.id}`);
  await expect(page.getByText('Оценка: 4 из 5')).toBeVisible();
  for (const [label, key] of [
    [/^Открыть ДЗ_/, 'condition-file'],
    [/^Открыть Решение_/, 'file'],
    ['Открыть Проверка S1.pdf', 'review-file'],
  ] as const) {
    const button = page.getByRole('button', { name: label }).first();
    await button.click();
    await expect(page.locator('[data-file-viewer]')).toHaveCount(1);
    expect(new URL(page.url()).searchParams.has(key)).toBe(true);
    if (key === 'file') {
      await expect(full.getByRole('img')).toBeVisible();
      await pinch(full.getByRole('img'));
    } else await rendered(full);
    await page.keyboard.press('Escape');
    await expect(full).not.toBeAttached();
    await expect(button).toBeFocused();
  }
  expect(writes).toEqual([]);
  expect(errors).toEqual([]);
  await context.close();
});
