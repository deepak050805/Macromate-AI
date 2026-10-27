import { expect, test } from "@playwright/test";
import { fixtureUrl, signIn } from "./helpers.mjs";

for (const width of [280, 320, 360]) {
  test(`narrow forms: calculator results fit ${width}px without page scrolling`, async ({ page }) => {
    await page.setViewportSize({ width, height: 900 });
    await page.goto(fixtureUrl("/calculator"));
    await page.getByLabel("Body weight (kg)", { exact: true }).fill("350");
    await page.getByRole("button", { name: "Calculate my targets", exact: true }).click();
    await expect(page.locator("#calculator-results")).toBeVisible();
    expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  });
}

test("narrow forms: date filters stay usable with enlarged text", async ({ page }) => {
  await signIn(page);
  await page.setViewportSize({ width: 360, height: 900 });
  await page.goto(fixtureUrl("/tracking"));
  await page.evaluate(() => { document.documentElement.style.fontSize = "200%"; });
  await page.getByLabel("From date (UTC)", { exact: true }).fill("2024-02-01");
  await page.getByLabel("Through date (UTC)", { exact: true }).fill("2024-02-21");
  await page.getByRole("button", { name: "Apply dates", exact: true }).click();
  await expect(page.locator("#history-status")).not.toContainText("Loading");
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
  const from = await page.locator("#filter-date-from").boundingBox();
  const to = await page.locator("#filter-date-to").boundingBox();
  expect(to.y).toBeGreaterThan(from.y);
});
