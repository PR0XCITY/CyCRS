import { defineConfig, devices } from "@playwright/test";

export default defineConfig({
  testDir: "tests/e2e",
  fullyParallel: false,
  retries: 0,
  use: { baseURL: "http://127.0.0.1:4173", trace: "off" },
  webServer: { command: "node tests/e2e/serve.mjs", url: "http://127.0.0.1:4173", reuseExistingServer: true, timeout: 60000 },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});
