import { expect, test } from "@playwright/test";
import { fixtureUrl, signIn } from "./helpers.mjs";

test("owner navigates only their seeded progress pages", async ({ page }) => {
  await signIn(page, "browser-pages@example.test");
  await page.goto(fixtureUrl("/tracking"));
  await expect(page.locator("#page-label")).toHaveText("Page 1 of 2");
  await expect(page.locator("#history-rows tr")).toHaveCount(20);
  await page.locator("#next-page").click();
  await expect(page.locator("#page-label")).toHaveText("Page 2 of 2");
  await expect(page.locator("#history-rows tr")).toHaveCount(1);
  await expect(page.locator("#history-rows")).toContainText("2024-02-01");
  await page.locator("#previous-page").click();
  await expect(page.locator("#page-label")).toHaveText("Page 1 of 2");
});

test("administrator navigates the account directory", async ({ page }) => {
  await signIn(page, "browser-admin@example.test");
  await page.goto(fixtureUrl("/admin"));
  await expect(
    page.getByRole("heading", { name: "Registered accounts", exact: true }),
  ).toBeVisible();
  await expect(page.locator("#admin-page")).toHaveText("Page 1 of 2");
  await expect(page.locator("#users-rows tr")).toHaveCount(25);
  await page.locator("#admin-next").click();
  await expect(page.locator("#admin-page")).toHaveText("Page 2 of 2");
  await expect(page.locator("#users-rows tr")).toHaveCount(4);
  await page.locator("#admin-previous").click();
  await expect(page.locator("#admin-page")).toHaveText("Page 1 of 2");
});
