import { expect, test } from "@playwright/test";
import { fixtureUrl, signIn } from "./helpers.mjs";

test("date presets: apply inclusive UTC ranges and retain the entry draft", async ({ page }) => {
  await signIn(page, "browser-pages@example.test");
  await page.clock.setFixedTime(new Date("2024-02-21T12:00:00Z"));
  await page.goto(fixtureUrl("/tracking"));
  await expect(page.locator("#history-rows tr")).toHaveCount(20);
  await page.getByLabel("Weight (kg)", { exact: true }).fill("73");
  await page.getByRole("button", { name: "Next", exact: true }).click();
  await expect(page.locator("#page-label")).toHaveText("Page 2 of 2");
  await page.getByRole("button", { name: "Last 7 days", exact: true }).click();
  await expect(page.locator("#filter-date-from")).toHaveValue("2024-02-15");
  await expect(page.locator("#filter-date-to")).toHaveValue("2024-02-21");
  await expect(page.locator("#history-rows tr")).toHaveCount(7);
  await expect(page.locator("#page-label")).toHaveText("Page 1 of 1");
  await expect(page.getByLabel("Weight (kg)", { exact: true })).toHaveValue("73");
  await page.getByRole("button", { name: "Last 30 days", exact: true }).click();
  await expect(page.locator("#filter-date-from")).toHaveValue("2024-01-23");
  await expect(page.locator("#history-rows tr")).toHaveCount(20);
});
