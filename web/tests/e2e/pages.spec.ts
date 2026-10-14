import { mkdirSync } from "node:fs";
import { expect, type Page, test } from "@playwright/test";
import cards from "../../public/model/cards.json" with { type: "json" };

const PROFILE = {
  sector: "Retail Trade",
  employees: 12,
  city: "Pune",
  devices: 5,
  website: true,
  payments: true,
  customerData: true,
  cloud: false,
  controls: [],
  budget: 50000,
};

const PAGES = [
  { path: "/", name: "home" },
  { path: "/assess/", name: "assess" },
  { path: "/results/", name: "results" },
  { path: "/models/", name: "models" },
  ...cards.map((c) => ({ path: `/models/${c.id}/`, name: `model-${c.id}` })),
  { path: "/data/", name: "data" },
  { path: "/cases/", name: "cases" },
];
const WIDTHS = [1440, 390];

function watch(page: Page) {
  const errs: string[] = [];
  page.on("console", (m) => {
    if (m.type() === "error" || m.type() === "warning") errs.push(`${m.type()}: ${m.text()}`);
  });
  page.on("pageerror", (e) => errs.push(`pageerror: ${e.message}`));
  return errs;
}

test.beforeAll(() => {
  mkdirSync("screenshots", { recursive: true });
});

test.afterEach(async ({ page }) => {
  await page.evaluate(() => window.localStorage.clear());
});

for (const p of PAGES) {
  test(`${p.path} renders with no console errors`, async ({ page }) => {
    const errs = watch(page);
    if (p.name === "results") {
      await page.goto("/");
      await page.evaluate((v) => window.localStorage.setItem("cycrs.profile.v1", JSON.stringify(v)), PROFILE);
    }
    for (const w of WIDTHS) {
      await page.setViewportSize({ width: w, height: 900 });
      await page.goto(p.path);
      await page.waitForLoadState("networkidle");
      await expect(page.locator("main h1").first()).toBeVisible();
      const overflow = await page.evaluate(() => document.documentElement.scrollWidth - document.documentElement.clientWidth);
      expect(overflow, `horizontal scroll at ${w}px`).toBeLessThanOrEqual(0);
      await page.screenshot({ path: `screenshots/${p.name}-${w}.png`, fullPage: true });
    }
    expect(errs).toEqual([]);
  });
}

test("every model page has seven numbered sections and pipeline links", async ({ page }) => {
  await page.goto("/models/");
  const links = await page.locator("svg a").evaluateAll((as) => as.map((a) => a.getAttribute("href")));
  for (const c of cards) expect(links).toContain(`/models/${c.id}/`);
  for (const c of cards) {
    await page.goto(`/models/${c.id}/`);
    await expect(page.locator("[data-section]")).toHaveCount(7);
  }
});

test("cases show plan, verdict, source and an openable trace panel", async ({ page }) => {
  await page.goto("/cases/");
  const items = page.locator("[data-case]");
  const n = await items.count();
  expect(n).toBeGreaterThanOrEqual(4);
  for (let i = 0; i < n; i++) {
    const it = items.nth(i);
    await expect(it.getByText("Verdict")).toBeVisible();
    await expect(it.getByRole("link", { name: "Source" })).toHaveAttribute("href", /^https:\/\//);
    await expect(it.locator("ol li").first()).toBeVisible();
    const p = page.getByTestId(`panel-case-${i}`);
    await p.locator("summary").click();
    await expect(p).toHaveAttribute("open", "");
    await expect(p.getByText(/^Step 1: picked/)).toBeVisible();
  }
});
