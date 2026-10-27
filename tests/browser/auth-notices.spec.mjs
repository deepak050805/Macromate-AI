import { expect, test } from "@playwright/test";
import { fixtureUrl } from "./helpers.mjs";

for (const notice of ["toString", "constructor", "__proto__", "unknown"]) {
  test(`auth notices: unknown key ${notice} cannot render inherited object properties`, async ({ page }) => {
    await page.goto(fixtureUrl(`/login?notice=${encodeURIComponent(notice)}`));
    await expect(page.locator("form .status")).toHaveText("");
  });
}

test("auth notices: a known password-reset notice is still displayed", async ({ page }) => {
  await page.goto(fixtureUrl("/login?notice=reset"));
  await expect(page.locator("form .status")).toHaveText("Password updated. Log in with your new password.");
});
