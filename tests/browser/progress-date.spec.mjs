import { expect, test } from "@playwright/test";
import { fixtureUrl, signIn } from "./helpers.mjs";

test.beforeEach(async ({ page }) => {
  await signIn(page);
  await page.clock.setFixedTime(new Date("2024-04-10T23:59:50Z"));
  await page.goto(fixtureUrl("/tracking"));
});

test("progress dates: an overnight page accepts the new UTC date", async ({ page }) => {
  const date = page.getByLabel("Date (UTC)", { exact: true });
  await expect(date).toHaveAttribute("max", "2024-04-10");
  await page.clock.setFixedTime(new Date("2024-04-11T00:00:10Z"));
  await date.focus();
  await expect(date).toHaveAttribute("max", "2024-04-11");
  await date.fill("2024-04-11");
  expect(await date.evaluate((input) => input.validity.rangeOverflow)).toBe(false);
});

test("progress dates: resetting an edit uses the current UTC date", async ({ page }) => {
  await page.getByLabel("Date (UTC)", { exact: true }).fill("2024-04-10");
  await page.getByLabel("Weight (kg)", { exact: true }).fill("70");
  await page.getByLabel("Calories consumed (kcal)", { exact: true }).fill("2000");
  await page.locator("#save-entry").click();
  const edit = page.getByRole("button", { name: "Edit entry for 2024-04-10", exact: true });
  await expect(edit).toBeVisible();
  await page.clock.setFixedTime(new Date("2024-04-11T00:00:10Z"));
  await edit.click();
  await page.getByRole("button", { name: "Cancel editing", exact: true }).click();
  await expect(page.getByLabel("Date (UTC)", { exact: true })).toHaveValue("2024-04-11");
  await expect(page.getByLabel("Date (UTC)", { exact: true })).toHaveAttribute("max", "2024-04-11");
});
