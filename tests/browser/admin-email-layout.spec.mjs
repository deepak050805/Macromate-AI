import { expect, test } from "@playwright/test";
import { fixtureUrl, signIn } from "./helpers.mjs";

test("directory layout: long email addresses wrap without truncating account information", async ({ page }) => {
  await signIn(page, "browser-admin@example.test");
  await page.setViewportSize({ width: 320, height: 900 });
  const email = `${"a".repeat(60)}@${"b".repeat(63)}.${"c".repeat(63)}.test`;
  await page.route("**/api/auth/all-users?*", (route) => route.fulfill({
    contentType: "application/json",
    body: JSON.stringify({ page: 1, pages: 1, total: 1, users: [{ id: 1, email, verified: true }] }),
  }));
  await page.goto(fixtureUrl("/admin"));
  const cell = page.locator("#users-rows .account-email");
  await expect(cell).toHaveText(email);
  expect(await cell.evaluate((element) => element.scrollWidth <= element.clientWidth + 1)).toBe(true);
  expect((await cell.boundingBox()).width).toBeLessThan(320);
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true);
});
