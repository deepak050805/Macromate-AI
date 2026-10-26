import { expect, test } from "@playwright/test";
import { fixtureUrl, signIn } from "./helpers.mjs";

test("history responses: malformed successful refresh retains the displayed rows and retry target", async ({ page }) => {
  await signIn(page, "browser-pages@example.test");
  await page.goto(fixtureUrl("/tracking"));
  await expect(page.locator("#history-rows tr")).toHaveCount(20);
  const displayedRows = await page.locator("#history-rows").textContent();
  let calls = 0;
  await page.route("**/api/tracker/history?*", async (route) => {
    calls += 1;
    if (calls !== 1) return route.continue();
    return route.fulfill({
      status: 200, contentType: "application/json",
      body: JSON.stringify({ page: 2, pages: 2, total: 21, records: [{}] }),
    });
  });
  await page.getByRole("button", { name: "Next", exact: true }).click();
  await expect(page.locator("#history-status")).toHaveText("The server returned an unreadable response. Try again.");
  await expect(page.locator("#history-rows")).toHaveText(displayedRows);
  await expect(page.locator("#page-label")).toHaveText("Page 1 of 2");
  await page.getByRole("button", { name: "Retry history", exact: true }).click();
  await expect(page.locator("#page-label")).toHaveText("Page 2 of 2");
  await expect(page.locator("#history-rows tr")).toHaveCount(1);
  expect(calls).toBe(2);
});

test("history responses: invalid pagination cannot trigger fallback requests", async ({ page }) => {
  await signIn(page, "browser-pages@example.test");
  await page.goto(fixtureUrl("/tracking"));
  await expect(page.locator("#history-rows tr")).toHaveCount(20);
  let calls = 0;
  await page.route("**/api/tracker/history?*", (route) => {
    calls += 1;
    return route.fulfill({
      status: 200, contentType: "application/json",
      body: JSON.stringify({ page: 2, pages: 1e30, total: 21, records: [] }),
    });
  });
  await page.getByRole("button", { name: "Next", exact: true }).click();
  await expect(page.locator("#history-status")).toHaveText("The server returned an unreadable response. Try again.");
  await expect(page.getByRole("button", { name: "Retry history", exact: true })).toBeVisible();
  await expect(page.locator("#history-rows tr")).toHaveCount(20);
  expect(calls).toBe(1);
});
