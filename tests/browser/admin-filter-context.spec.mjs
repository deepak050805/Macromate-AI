import { expect, test } from "@playwright/test";
import { fixtureUrl, signIn } from "./helpers.mjs";

test("directory context: a failed search cannot relabel the retained account rows", async ({ page }) => {
  await signIn(page, "browser-admin@example.test");
  await page.goto(fixtureUrl("/admin"));
  const summary = page.locator("#directory-filter-summary");
  await expect(summary).toHaveText("Any email; All verification states");
  let fail = true;
  await page.route("**/api/auth/all-users?*", (route) => {
    if (fail) {
      fail = false;
      return route.fulfill({ status: 503, contentType: "application/json", body: JSON.stringify({ message: "Search unavailable." }) });
    }
    return route.continue();
  });
  await page.getByLabel("Email contains", { exact: true }).fill("directory-");
  await page.getByLabel("Verification state", { exact: true }).selectOption("pending");
  await page.getByRole("button", { name: "Apply account filters", exact: true }).click();
  await expect(page.locator("#admin-status")).toHaveText("Search unavailable.");
  await expect(summary).toHaveText("Any email; All verification states");
  await page.getByRole("button", { name: "Retry accounts", exact: true }).click();
  await expect(summary).toHaveText('Email contains "directory-"; Pending verification');
  await expect(page.locator("#users-rows")).not.toContainText("browser-owner@");
});
