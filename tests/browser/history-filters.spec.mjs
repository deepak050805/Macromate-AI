import { expect, test } from "@playwright/test";
import { fixtureUrl, signIn } from "./helpers.mjs";

test.beforeEach(async ({ page }) => {
  await signIn(page, "browser-pages@example.test");
  await page.goto(fixtureUrl("/tracking"));
  await expect(page.locator("#history-status")).toContainText("21 entries");
});

test("history dates: filter a range and clear back to the complete history", async ({ page }) => {
  await page.getByLabel("From date (UTC)", { exact: true }).fill("2024-02-05");
  await page.getByLabel("Through date (UTC)", { exact: true }).fill("2024-02-10");
  await page.getByRole("button", { name: "Apply dates", exact: true }).click();
  await expect(page.locator("#history-status")).toHaveText("6 entries recorded.");
  await expect(page.locator("#history-rows tr")).toHaveCount(6);
  await expect(page.locator("#history-pagination")).toBeHidden();
  await page.getByRole("button", { name: "Clear dates", exact: true }).click();
  await expect(page.locator("#history-status")).toHaveText("21 entries recorded.");
  await expect(page.locator("#page-label")).toHaveText("Page 1 of 2");
});

test("history dates: reversed bounds retain the displayed records", async ({ page }) => {
  await page.getByLabel("From date (UTC)", { exact: true }).fill("2024-02-20");
  await page.getByLabel("Through date (UTC)", { exact: true }).fill("2024-02-10");
  await page.getByRole("button", { name: "Apply dates", exact: true }).click();
  await expect(page.locator("#history-status")).toHaveText("Start date must be on or before end date");
  await expect(page.locator("#history-rows tr")).toHaveCount(20);
});
