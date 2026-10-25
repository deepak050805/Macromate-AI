import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "./tests/browser",
  testMatch: "**/*.spec.mjs",
  outputDir: ".task-work/browser-results",
  fullyParallel: false,
  workers: 1,
  retries: 0,
  forbidOnly: Boolean(process.env.CI),
  timeout: 45000,
  projects: [
    {
      name: "chromium",
      use: {
        ...devices["Desktop Chrome"],
        ...(process.env.BROWSER_CHANNEL ? { channel: process.env.BROWSER_CHANNEL } : {}),
      },
    },
  ],
  webServer: {
    command: "node tests/browser/server.mjs",
    wait: { stdout: /BROWSER_TEST_URL=(?<BROWSER_TEST_URL>http:\/\/127\.0\.0\.1:\d+)/ },
    timeout: 60000,
    stdout: "pipe",
    stderr: "pipe",
    gracefulShutdown: { signal: "SIGTERM", timeout: 5000 },
  },
});
