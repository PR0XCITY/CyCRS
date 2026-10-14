import { chromium } from "playwright";

const [, , base, dir] = process.argv;
const browser = await chromium.launch();
const ctx = await browser.newContext({ viewport: { width: 1200, height: 760 }, recordVideo: { dir, size: { width: 1200, height: 760 } } });
const page = await ctx.newPage();

async function pause(ms) {
  await page.waitForTimeout(ms);
}

async function glide(y) {
  await page.evaluate((t) => window.scrollTo({ top: t, behavior: "smooth" }), y);
  await pause(900);
}

await page.goto(`${base}/`);
await pause(1200);
await page.getByRole("link", { name: "Assess my business" }).click();
await page.waitForURL(/assess/);
await pause(600);
await page.getByLabel("Sector").selectOption("Retail Trade");
await page.getByLabel("Number of employees").pressSequentially("12", { delay: 90 });
await page.getByLabel("State or union territory").selectOption("Maharashtra");
await page.getByLabel("City").pressSequentially("Pune", { delay: 90 });
await pause(500);
await page.getByRole("button", { name: "Next" }).click();
await page.getByLabel("Computers, phones and tablets used for work").pressSequentially("5", { delay: 90 });
await page.getByLabel("We have a website").check();
await page.getByLabel("We take UPI or online payments").check();
await page.getByLabel("We store customer data (records, documents, drives)").check();
await pause(500);
await page.getByRole("button", { name: "Next" }).click();
await page.getByLabel("MFA").check();
await pause(500);
await page.getByRole("button", { name: "Next" }).click();
const s = page.locator('input[type="range"]');
await s.focus();
for (let k = 0; k < 18; k++) await page.keyboard.press("ArrowRight");
await pause(700);
await page.getByRole("button", { name: "See my plan" }).click();
await page.waitForURL(/results/);
await pause(1500);
await glide(900);
await page.getByTestId("panel-risk").locator("summary").click();
await pause(600);
await page.getByTestId("panel-risk").scrollIntoViewIfNeeded();
await glide((await page.getByTestId("panel-risk").boundingBox()).y + (await page.evaluate(() => window.scrollY)) - 60);
await pause(1800);
await page.getByTestId("panel-risk").getByRole("link", { name: /Attack likelihood/ }).click();
await page.waitForURL(/models\/attack-likelihood/);
await pause(1200);
await glide(700);
await glide(1500);
await pause(800);
await ctx.close();
await browser.close();
