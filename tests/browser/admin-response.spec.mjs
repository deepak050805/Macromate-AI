import { expect, test } from "@playwright/test";
import { fixtureUrl, signIn } from "./helpers.mjs";

const account = { id: 1, email: "response@example.test", verified: false };

for (const [name, invalid] of [
  ["missing account fields", {}],
  ["unsafe account identity", { ...account, id: Number.MAX_SAFE_INTEGER + 1 }],
  ["zero account identity", { ...account, id: 0 }],
  ["non-string email", { ...account, email: null }],
  ["blank email", { ...account, email: "  " }],
  ["overlong email", { ...account, email: "a".repeat(255) }],
  ["email control character", { ...account, email: "response\u0000@example.test" }],
  ["invalid email Unicode", { ...account, email: "response\ud800@example.test" }],
  ["string verification state", { ...account, verified: "false" }],
]) {
  test(`directory responses: ${name} preserves existing rows and retries the failed page`, async ({ page }) => {
    await signIn(page, "browser-admin@example.test");
    await page.goto(fixtureUrl("/admin"));
    await expect(page.locator("#users-rows tr")).toHaveCount(25);
    const displayedRows = await page.locator("#users-rows").textContent();
    let calls = 0;
    await page.route("**/api/auth/all-users?*", (route) => {
      calls += 1;
      if (calls !== 1) return route.continue();
      return route.fulfill({
        status: 200, contentType: "application/json",
        body: JSON.stringify({ page: 2, pages: 2, total: 30, users: [invalid] }),
      });
    });
    await page.getByRole("button", { name: "Next", exact: true }).click();
    await expect(page.locator("#admin-status")).toHaveText("The server returned an unreadable response. Try again.");
    await expect(page.locator("#users-rows")).toHaveText(displayedRows);
    await expect(page.locator("#admin-page")).toHaveText("Page 1 of 2");
    await page.getByRole("button", { name: "Retry accounts", exact: true }).click();
    await expect(page.locator("#admin-page")).toHaveText("Page 2 of 2");
    await expect(page.getByRole("button", { name: "Retry accounts", exact: true })).toBeHidden();
    expect(calls).toBe(2);
  });
}

test("directory responses: invalid empty-page metadata cannot trigger fallback requests", async ({ page }) => {
  await signIn(page, "browser-admin@example.test");
  await page.goto(fixtureUrl("/admin"));
  await expect(page.locator("#users-rows tr")).toHaveCount(25);
  let calls = 0;
  await page.route("**/api/auth/all-users?*", (route) => {
    calls += 1;
    return route.fulfill({
      status: 200, contentType: "application/json",
      body: JSON.stringify({ page: 2, pages: -1, total: 30, users: [] }),
    });
  });
  await page.getByRole("button", { name: "Next", exact: true }).click();
  await expect(page.locator("#admin-status")).toHaveText("The server returned an unreadable response. Try again.");
  await expect(page.getByRole("button", { name: "Retry accounts", exact: true })).toBeVisible();
  await expect(page.locator("#users-rows tr")).toHaveCount(25);
  expect(calls).toBe(1);
});
