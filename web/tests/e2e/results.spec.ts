import { expect, test } from "@playwright/test";

const PROFILE_KEY = "cycrs.profile.v1";

test.afterEach(async ({ page }) => {
  await page.evaluate(() => window.localStorage.clear());
});

test("complete the wizard, open every panel, change the budget", async ({ page }) => {
  await page.goto("/assess/");
  await page.getByRole("button", { name: "Next" }).click();
  await expect(page.getByRole("alert").first()).toBeVisible();
  await page.getByLabel("Sector").selectOption({ index: 1 });
  await page.getByLabel("Number of employees").fill("12");
  await page.getByLabel("State or union territory").selectOption("Maharashtra");
  await page.getByLabel("City").fill("Pune");
  await page.getByRole("button", { name: "Next" }).click();
  await page.getByLabel("Computers, phones and tablets used for work").fill("5");
  await page.getByLabel("We have a website").check();
  await page.getByLabel("We take UPI or online payments").check();
  await page.getByRole("button", { name: "Next" }).click();
  await page.getByRole("button", { name: "Next" }).click();
  await page.getByRole("button", { name: "See my plan" }).click();

  await expect(page).toHaveURL(/\/results\/$/);
  await expect(page.getByRole("heading", { name: "Action plan" })).toBeVisible();
  for (const id of ["panel-persona", "panel-risk", "panel-plan", "panel-totals"]) {
    const p = page.getByTestId(id);
    await p.locator("summary").click();
    await expect(p).toHaveAttribute("open", "");
    await expect(p.getByText("Learn the model")).toBeVisible();
  }
  await expect(page.getByTestId("panel-risk").getByText(/^p = 1 \/ \(1 \+ e\^-/).first()).toBeVisible();
  await expect(page.getByTestId("panel-risk").getByText(/cap ₹/).first()).toBeVisible();
  await expect(page.getByTestId("not-scored").getByText("Phishing awareness training")).toBeVisible();
  await expect(page.getByTestId("not-scored").getByText(/no significant effect/)).toBeVisible();

  const before = await page.getByText(/^Yearly budget:/).innerText();
  const slider = page.locator("#live-budget");
  await slider.focus();
  await page.keyboard.press("End");
  await expect(page.getByText(/^Yearly budget:/)).not.toHaveText(before);
  await expect(page.getByText("Yearly budget: ₹5L")).toBeVisible();

  await page.getByLabel("Test probabilities 20% lower and higher").check();
  await expect(page.getByText(/robust to \+\/-20%|changes with \+\/-20%/).first()).toBeVisible();
});

test("tampered storage returns to /assess", async ({ page }) => {
  await page.goto("/");
  await page.evaluate((k) => window.localStorage.setItem(k, JSON.stringify({ sector: "x", budget: -5, isAdmin: true })), PROFILE_KEY);
  await page.goto("/results/");
  await expect(page).toHaveURL(/\/assess\/$/);
  expect(await page.evaluate((k) => window.localStorage.getItem(k), PROFILE_KEY)).toBeNull();
});

test("no profile redirects to /assess", async ({ page }) => {
  await page.goto("/results/");
  await expect(page).toHaveURL(/\/assess\/$/);
});
