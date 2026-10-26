import { readFile } from "node:fs/promises";
import { expect, test } from "@playwright/test";
import { fixtureUrl, signIn } from "./helpers.mjs";

test("CSV download: includes only the applied date interval", async ({ page }) => {
  await signIn(page, "browser-pages@example.test");
  await page.goto(fixtureUrl("/tracking"));
  await page.getByLabel("From date (UTC)", { exact: true }).fill("2024-02-05");
  await page.getByLabel("Through date (UTC)", { exact: true }).fill("2024-02-10");
  await page.getByRole("button", { name: "Apply dates", exact: true }).click();
  await expect(page.locator("#history-status")).toHaveText("6 entries recorded.");
  const pending = page.waitForEvent("download");
  await page.getByRole("button", { name: "Download CSV", exact: true }).click();
  const download = await pending;
  expect(download.suggestedFilename()).toBe("macromate-progress.csv");
  expect(await download.failure()).toBeNull();
  const content = await readFile(await download.path(), "utf8");
  expect(content.trim().split(/\r?\n/)).toHaveLength(7);
  expect(content).toContain("2024-02-05");
  expect(content).not.toContain("2024-02-04");
});

test("CSV download: a rejected export preserves the unsaved entry draft", async ({ page }) => {
  await signIn(page);
  await page.goto(fixtureUrl("/tracking"));
  await page.getByLabel("Weight (kg)", { exact: true }).fill("75");
  await page.route("**/api/tracker/export.csv*", (route) => route.fulfill({
    status: 400, contentType: "application/json",
    body: JSON.stringify({ message: "Select a narrower date range." }),
  }));
  await page.getByRole("button", { name: "Download CSV", exact: true }).click();
  await expect(page.locator("#export-status")).toHaveText("Select a narrower date range.");
  await expect(page.getByLabel("Weight (kg)", { exact: true })).toHaveValue("75");
  await expect(page).toHaveURL(fixtureUrl("/tracking"));
});
