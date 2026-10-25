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

test("cancelling an edit returns keyboard focus to the entry form", async ({ page }) => {
  const date = "2024-01-02";
  await createEntry(page, date);
  await page.getByRole("button", { name: `Edit entry for ${date}`, exact: true }).focus();
  await page.keyboard.press("Enter");
  const weight = page.getByLabel("Weight (kg)", { exact: true });
  await expect(weight).toBeFocused();
  for (let step = 0; step < 3; step += 1) await page.keyboard.press("Tab");
  const cancel = page.getByRole("button", { name: "Cancel editing", exact: true });
  await expect(cancel).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(cancel).toBeHidden();
  await expect(weight).toBeFocused();
  await expect(weight).toHaveValue("");
});

test("deleting an entry returns keyboard focus to the history heading", async ({ page }) => {
  const date = "2024-01-03";
  await createEntry(page, date);
  const remove = page.getByRole("button", { name: `Delete entry for ${date}`, exact: true });
  await remove.focus();
  page.once("dialog", (dialog) => dialog.accept());
  await page.keyboard.press("Enter");
  await expect(remove).toHaveCount(0);
  await expect(page.getByRole("heading", { name: "Progress history", exact: true })).toBeFocused();
});

test("failed deletion returns keyboard focus to the enabled delete action", async ({ page }) => {
  const date = "2024-01-04";
  await createEntry(page, date);
  await page.route("**/api/tracker/*", (route) => {
    if (route.request().method() !== "DELETE") return route.continue();
    return route.fulfill({
      status: 503,
      contentType: "application/json",
      body: JSON.stringify({ message: "Progress is temporarily unavailable." }),
    });
  });
  const remove = page.getByRole("button", { name: `Delete entry for ${date}`, exact: true });
  await remove.focus();
  page.once("dialog", (dialog) => dialog.accept());
  await page.keyboard.press("Enter");
  await expect(page.locator("#entry-status")).toHaveText("Progress is temporarily unavailable.");
  await expect(remove).toBeEnabled();
  await expect(remove).toBeFocused();
});

test("completed deletion preserves focus moved elsewhere during the request", async ({ page }) => {
  const date = "2024-01-05";
  await createEntry(page, date);
  let release;
  const pending = new Promise((resolve) => {
    release = resolve;
  });
  await page.route("**/api/tracker/*", async (route) => {
    if (route.request().method() === "DELETE") await pending;
    await route.continue();
  });
  const remove = page.getByRole("button", { name: `Delete entry for ${date}`, exact: true });
  await remove.focus();
  page.once("dialog", (dialog) => dialog.accept());
  await page.keyboard.press("Enter");
  try {
    await expect(remove).toBeDisabled();
    await page.getByLabel("Weight (kg)", { exact: true }).focus();
  } finally {
    release();
  }
  await expect(remove).toHaveCount(0);
  await expect(page.getByLabel("Weight (kg)", { exact: true })).toBeFocused();
});

test("dismissing deletion preserves the entry and focused action", async ({ page }) => {
  const date = "2024-01-06";
  await createEntry(page, date);
  const remove = page.getByRole("button", { name: `Delete entry for ${date}`, exact: true });
  await remove.focus();
  page.once("dialog", (dialog) => dialog.dismiss());
  await page.keyboard.press("Enter");
  await expect(remove).toBeEnabled();
  await expect(remove).toBeFocused();
  await expect(
    page.getByRole("button", { name: `Edit entry for ${date}`, exact: true }),
  ).toBeVisible();
});
