import { defineConfig, devices } from "@playwright/test";

const port = process.env.PLAYWRIGHT_DJANGO_PORT ?? "8765";
const baseURL = `http://127.0.0.1:${port}`;

export default defineConfig({
  testDir: "./e2e",
  testMatch: "**/*.spec.ts",
  fullyParallel: false,
  forbidOnly: Boolean(process.env.CI),
  retries: process.env.CI ? 1 : 0,
  workers: 1,
  reporter: [["list"]],
  outputDir: "output/playwright/test-results",
  snapshotPathTemplate:
    "{testDir}/{testFileDir}/{testFileName}-snapshots/{arg}{ext}",
  use: {
    baseURL,
    trace: "on-first-retry",
    viewport: { width: 1280, height: 720 },
    deviceScaleFactor: 1,
    locale: "en-US",
    colorScheme: "dark",
  },
  expect: {
    toHaveScreenshot: {
      maxDiffPixels: 120,
      animations: "disabled",
    },
  },
  webServer: {
    command: "python scripts/playwright_webserver.py",
    url: baseURL,
    reuseExistingServer: !process.env.CI,
    timeout: 180_000,
  },
  projects: [
    {
      name: "chromium",
      use: { ...devices["Desktop Chrome"] },
    },
  ],
});
