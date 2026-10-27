import { expect, test } from "@playwright/test";
import { fixtureUrl, signIn } from "./helpers.mjs";

test.beforeEach(async ({ page }) => {
  await signIn(page);
  await page.clock.setFixedTime(new Date("2024-04-10T23:59:50Z"));
  await page.goto(fixtureUrl("/tracking"));
});

test("default date: beginning an untouched form after midnight uses the new UTC day", async ({ page }) => {
  await expect(page.locator("#record-date")).toHaveValue("2024-04-10");
  await page.clock.setFixedTime(new Date("2024-04-11T00:00:10Z"));
  await page.getByLabel("Weight (kg)", { exact: true }).focus();
  await expect(page.locator("#record-date")).toHaveValue("2024-04-11");
  await expect(page.locator("#record-date")).toHaveAttribute("max", "2024-04-11");
});

test("default date: an explicit older date remains part of the draft", async ({ page }) => {
  await page.locator("#record-date").fill("2024-04-09");
  await page.clock.setFixedTime(new Date("2024-04-11T00:00:10Z"));
  await page.getByLabel("Weight (kg)", { exact: true }).focus();
  await expect(page.locator("#record-date")).toHaveValue("2024-04-09");
});

test("default date: a draft begun before midnight retains its original date", async ({ page }) => {
  await page.getByLabel("Weight (kg)", { exact: true }).fill("70");
  await page.clock.setFixedTime(new Date("2024-04-11T00:00:10Z"));
  await page.getByLabel("Calories consumed (kcal)", { exact: true }).focus();
  await expect(page.locator("#record-date")).toHaveValue("2024-04-10");
  await expect(page.getByLabel("Weight (kg)", { exact: true })).toHaveValue("70");
});

test("date limits: an already-focused filter accepts the new day after midnight", async ({ page }) => {
  const date = page.locator("#filter-date-to");
  await date.focus();
  await page.clock.setFixedTime(new Date("2024-04-11T00:00:10Z"));
  await date.fill("2024-04-11");
  await expect(date).toHaveAttribute("max", "2024-04-11");
  expect(await date.evaluate((input) => input.validity.rangeOverflow)).toBe(false);
});
