import { expect, test } from "@playwright/test";
import { fixtureUrl, signIn } from "./helpers.mjs";

test("logout privacy: successful logout removes the email remembered in this tab", async ({ page }) => {
  await signIn(page);
  await page.getByRole("button", { name: "Log out", exact: true }).click();
  await expect(page).toHaveURL(fixtureUrl("/login"));
  await expect(page.getByLabel("Email address", { exact: true })).toHaveValue("");
  expect(await page.evaluate(() => sessionStorage.getItem("pending-email"))).toBeNull();
});

test("logout privacy: a failed logout leaves the current tab session intact", async ({ page }) => {
  await signIn(page);
  await page.route("**/api/auth/logout", (route) => route.fulfill({
    status: 503,
    contentType: "application/json",
    body: JSON.stringify({ message: "Logout unavailable." }),
  }));
  await page.getByRole("button", { name: "Log out", exact: true }).click();
  await expect(page.locator("#global-status")).toHaveText("Logout unavailable.");
  expect(await page.evaluate(() => sessionStorage.getItem("pending-email"))).toBe(
    "browser-owner@example.test",
  );
});
