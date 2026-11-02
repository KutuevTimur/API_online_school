import { defineConfig } from '@playwright/test';
process.env.PLAYWRIGHT_NO_COPY_PROMPT = '1';
process.env.LGG_F014_UI_REVIEW = '1';
export default defineConfig({
  testDir: './e2e',
  testMatch: 'f014.spec.ts',
  workers: 1,
  expect: { timeout: 15000 },
  use: {
    baseURL: 'http://127.0.0.1:5175',
    actionTimeout: 10000,
    trace: 'off',
    screenshot: 'off',
    video: 'off',
    launchOptions: {
      executablePath:
        '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
    },
  },
  reporter: [['list']],
  outputDir: '.artifacts/f014-ux-test-results',
});
