import { expect, test } from "@playwright/test";
import { fixtureUrl, signIn } from "./helpers.mjs";

test("account filters: literal email search and clear retain directory pagination", async ({ page }) => {
  await signIn(page, "browser-admin@example.test");
  await page.goto(fixtureUrl("/admin"));
  await page.getByLabel("Email contains", { exact: true }).fill("browser-admin@");
  await page.getByRole("button", { name: "Apply account filters", exact: true }).click();
  await expect(page.locator("#users-rows tr")).toHaveCount(1);
  await expect(page.locator("#users-rows")).toContainText("browser-admin@example.test");
  await expect(page.locator("#admin-pagination")).toBeHidden();
  await page.getByRole("button", { name: "Clear account filters", exact: true }).click();
  await expect(page.locator("#admin-pagination")).toBeVisible();
});

test("account filters: unmatched search explains the empty result", async ({ page }) => {
  await signIn(page, "browser-admin@example.test");
  await page.goto(fixtureUrl("/admin"));
  await page.getByLabel("Email contains", { exact: true }).fill("absent-filter-account");
  await page.getByRole("button", { name: "Apply account filters", exact: true }).click();
  await expect(page.locator("#admin-status")).toHaveText("No accounts match these filters.");
});
