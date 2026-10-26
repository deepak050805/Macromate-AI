import { expect, test } from "@playwright/test";
import { fixtureUrl, signIn } from "./helpers.mjs";

test("responsive identity: a long account email does not widen the dashboard viewport", async ({ page }) => {
  await page.setViewportSize({ width: 320, height: 700 });
  await signIn(page);
  await page.locator(".page-heading .muted").evaluate((element) => {
    element.textContent = `Signed in as ${"a".repeat(230)}@example.test.`;
  });
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= innerWidth)).toBe(true);
});

for (const [path, email, label] of [
  ["/tracking", "browser-pages@example.test", "Progress history table"],
  ["/admin", "browser-admin@example.test", "Account directory table"],
]) {
  test(`table keyboard: ${path} can scroll horizontally without a pointer`, async ({ page }) => {
    await page.setViewportSize({ width: 320, height: 700 });
    await signIn(page, email);
    await page.goto(fixtureUrl(path));
    const region = page.getByRole("region", { name: label, exact: true });
    await expect(region.getByRole("table")).toBeVisible();
    await region.focus();
    await expect(region).toBeFocused();
    await page.keyboard.press("ArrowRight");
    await expect.poll(() => region.evaluate((element) => element.scrollLeft)).toBeGreaterThan(0);
  });
}
