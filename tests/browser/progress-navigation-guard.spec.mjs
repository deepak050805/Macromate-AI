import { expect, test } from "@playwright/test";
import { fixtureUrl, signIn } from "./helpers.mjs";

const record = { id: 701, date: "2024-05-01", weight: 70, calories: 2000 };
test.beforeEach(async ({ page }) => {
  await signIn(page);
  await page.route("**/api/tracker/history?*", (route) => route.fulfill({
    contentType: "application/json",
    body: JSON.stringify({ page: 1, pages: 1, total: 1, records: [record] }),
  }));
  await page.goto(fixtureUrl("/tracking"));
  await expect(page.locator("#history-rows tr")).toHaveCount(1);
});

test("progress navigation: declining a full-page navigation preserves the draft", async ({ page }) => {
  await page.getByLabel("Weight (kg)", { exact: true }).fill("73");
  const dialog = page.waitForEvent("dialog");
  const navigation = page.goto(fixtureUrl("/calculator")).catch(() => null);
  const prompt = await dialog;
  expect(prompt.type()).toBe("beforeunload");
  await prompt.dismiss();
  await navigation;
  await expect(page).toHaveURL(fixtureUrl("/tracking"));
  await expect(page.getByLabel("Weight (kg)", { exact: true })).toHaveValue("73");
});

test("progress navigation: accepting the warning allows normal navigation", async ({ page }) => {
  await page.getByLabel("Weight (kg)", { exact: true }).fill("73");
  const dialog = page.waitForEvent("dialog");
  const navigation = page.getByRole("navigation").getByRole("link", { name: "Calculator", exact: true }).click();
  const prompt = await dialog;
  expect(prompt.type()).toBe("beforeunload");
  await prompt.accept();
  await navigation;
  await expect(page).toHaveURL(fixtureUrl("/calculator"));
});

test("progress navigation: reverting to the pristine draft removes the warning", async ({ page }) => {
  const dialogs = [];
  page.on("dialog", async (dialog) => { dialogs.push(dialog.type()); await dialog.accept(); });
  const weight = page.getByLabel("Weight (kg)", { exact: true });
  await weight.fill("73");
  await weight.fill("");
  await page.getByRole("navigation").getByRole("link", { name: "Calculator", exact: true }).click();
  await expect(page).toHaveURL(fixtureUrl("/calculator"));
  expect(dialogs).toEqual([]);
});

test("progress navigation: an in-flight save is protected even for a pristine edited record", async ({ page }) => {
  await page.getByRole("button", { name: "Edit entry for 2024-05-01", exact: true }).click();
  const pending = Promise.withResolvers();
  await page.route("**/api/tracker/701", async (route) => {
    await pending.promise;
    await route.fulfill({ status: 503, contentType: "application/json", body: JSON.stringify({ message: "Save unavailable." }) });
  });
  await page.locator("#save-entry").click();
  try {
    await expect(page.locator("#save-entry")).toBeDisabled();
    const dialog = page.waitForEvent("dialog");
    const navigation = page.goto(fixtureUrl("/calculator")).catch(() => null);
    const prompt = await dialog;
    expect(prompt.type()).toBe("beforeunload");
    await prompt.dismiss();
    await navigation;
    await expect(page).toHaveURL(fixtureUrl("/tracking"));
  } finally {
    pending.resolve();
  }
  await expect(page.locator("#save-entry")).toBeEnabled();
});
