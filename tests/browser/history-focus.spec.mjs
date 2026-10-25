import { expect, test } from "@playwright/test";

test.beforeEach(async ({ page }) => {
  const base = process.env.BROWSER_TEST_URL;
  if (!/^http:\/\/127\.0\.0\.1:\d+$/.test(base || ""))
    throw new Error("The isolated browser fixture did not publish its loopback URL");
  await page.goto(`${base}/login`);
  await page.getByLabel("Email address", { exact: true }).fill("browser-owner@example.test");
  await page.getByLabel("Password", { exact: true }).fill("fictional browser password");
  await page.getByRole("button", { name: "Log in", exact: true }).click();
  await expect(page).toHaveURL(`${base}/dashboard`);
  await page.goto(`${base}/tracking`);
  await expect(page.locator("#history-status")).not.toHaveText("Loading your history…");
});

async function createEntry(page, date) {
  await page.getByLabel("Date (UTC)", { exact: true }).fill(date);
  await page.getByLabel("Weight (kg)", { exact: true }).fill("70");
  await page.getByLabel("Calories consumed (kcal)", { exact: true }).fill("2000");
  await page.getByRole("button", { name: "Save entry", exact: true }).click();
  await expect(
    page.getByRole("button", { name: `Edit entry for ${date}`, exact: true }),
  ).toBeVisible();
}

test("verified owner signs in and records progress through CSRF-protected UI", async ({ page }) => {
  await createEntry(page, "2024-01-01");
  await expect(page.locator("#entry-status")).toHaveText("Entry saved.");
});
