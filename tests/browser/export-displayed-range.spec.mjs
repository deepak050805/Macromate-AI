import { expect, test } from "@playwright/test";
import { fixtureUrl, signIn } from "./helpers.mjs";

test("displayed export: failed filters cannot silently change the exported interval", async ({ page }) => {
  await signIn(page, "browser-pages@example.test");
  await page.goto(fixtureUrl("/tracking"));
  await expect(page.locator("#history-rows tr")).toHaveCount(20);
  let failed = false;
  await page.route("**/api/tracker/history?*", (route) => {
    const url = new URL(route.request().url());
    if (!failed && url.searchParams.has("date_from")) {
      failed = true;
      return route.fulfill({ status: 503, contentType: "application/json", body: JSON.stringify({ message: "Filter unavailable." }) });
    }
    return route.continue();
  });
  await page.getByLabel("From date (UTC)", { exact: true }).fill("2024-02-15");
  await page.getByLabel("Through date (UTC)", { exact: true }).fill("2024-02-21");
  await page.getByRole("button", { name: "Apply dates", exact: true }).click();
  await expect(page.locator("#history-status")).toHaveText("Filter unavailable.");
  await expect(page.locator("#history-range")).toHaveText("All dates, including undated entries.");
  const exports = [];
  page.on("request", (request) => {
    const url = new URL(request.url());
    if (url.pathname === "/api/tracker/export.csv") exports.push(url.searchParams.toString());
  });
  const firstDownload = page.waitForEvent("download");
  await page.getByRole("button", { name: "Download CSV", exact: true }).click();
  await firstDownload;
  expect(exports).toEqual([""]);
  await page.getByRole("button", { name: "Retry history", exact: true }).click();
  await expect(page.locator("#history-rows tr")).toHaveCount(7);
  await expect(page.locator("#history-range")).toHaveText("2024-02-15 through 2024-02-21 (UTC)");
  const secondDownload = page.waitForEvent("download");
  await page.getByRole("button", { name: "Download CSV", exact: true }).click();
  await secondDownload;
  expect(exports[1]).toBe("date_from=2024-02-15&date_to=2024-02-21");
});

test("displayed export: CSV remains unavailable until history has loaded successfully", async ({ page }) => {
  await signIn(page);
  await page.route("**/api/tracker/history?*", (route) => route.fulfill({
    status: 503, contentType: "application/json", body: JSON.stringify({ message: "History unavailable." }),
  }));
  await page.goto(fixtureUrl("/tracking"));
  await expect(page.locator("#history-status")).toHaveText("History unavailable.");
  await expect(page.getByRole("button", { name: "Download CSV", exact: true })).toBeDisabled();
});
