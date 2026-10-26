import { expect, test } from "@playwright/test";
import { fixtureUrl, signIn } from "./helpers.mjs";

const records = [
  { id: 701, date: "2024-05-01", weight: 70, calories: 2000 },
  { id: 702, date: "2024-05-02", weight: 71, calories: 2100 },
];

test.beforeEach(async ({ page }) => {
  await signIn(page);
  await page.route("**/api/tracker/history?*", (route) => route.fulfill({
    status: 200,
    contentType: "application/json",
    body: JSON.stringify({ page: 1, pages: 1, total: 2, records }),
  }));
  await page.goto(fixtureUrl("/tracking"));
  await expect(page.locator("#history-rows tr")).toHaveCount(2);
});

function edit(page, date) {
  return page.getByRole("button", { name: `Edit entry for ${date}`, exact: true });
}

function watchDialogs(page) {
  const dialogs = [];
  page.on("dialog", async (dialog) => {
    dialogs.push(dialog.message());
    await dialog.dismiss();
  });
  return dialogs;
}

test("progress discard: replacing a new draft requires confirmation", async ({ page }) => {
  const weight = page.getByLabel("Weight (kg)", { exact: true });
  await weight.fill("74");
  page.once("dialog", async (dialog) => {
    expect(dialog.message()).toBe("Discard your unsaved progress changes?");
    await dialog.dismiss();
  });
  await edit(page, "2024-05-01").click();
  await expect(weight).toHaveValue("74");
  await expect(page.locator("#record-id")).toHaveValue("");
  page.once("dialog", (dialog) => dialog.accept());
  await edit(page, "2024-05-01").click();
  await expect(weight).toHaveValue("70");
  await expect(page.locator("#record-id")).toHaveValue("701");
});

test("progress discard: cancelling an edited record preserves a rejected draft", async ({ page }) => {
  await edit(page, "2024-05-01").click();
  const weight = page.getByLabel("Weight (kg)", { exact: true });
  await weight.fill("74");
  const cancel = page.getByRole("button", { name: "Cancel editing", exact: true });
  page.once("dialog", (dialog) => dialog.dismiss());
  await cancel.click();
  await expect(weight).toHaveValue("74");
  await expect(page.locator("#record-id")).toHaveValue("701");
  page.once("dialog", (dialog) => dialog.accept());
  await cancel.click();
  await expect(weight).toHaveValue("");
  await expect(page.locator("#record-id")).toHaveValue("");
});

test("progress discard: editing the selected record never replaces its draft", async ({ page }) => {
  const dialogs = watchDialogs(page);
  await edit(page, "2024-05-01").click();
  const weight = page.getByLabel("Weight (kg)", { exact: true });
  await weight.fill("74");
  await edit(page, "2024-05-01").click();
  await expect(weight).toHaveValue("74");
  expect(dialogs).toEqual([]);
});

test("progress discard: pristine and numerically equivalent values need no confirmation", async ({ page }) => {
  const dialogs = watchDialogs(page);
  await edit(page, "2024-05-01").click();
  await page.getByLabel("Weight (kg)", { exact: true }).fill("70.0");
  await edit(page, "2024-05-02").click();
  await expect(page.locator("#record-id")).toHaveValue("702");
  await page.getByRole("button", { name: "Cancel editing", exact: true }).click();
  await expect(page.locator("#record-id")).toHaveValue("");
  expect(dialogs).toEqual([]);
});

test("progress discard: a submitted draft can be switched while its save is pending", async ({ page }) => {
  const dialogs = watchDialogs(page);
  await edit(page, "2024-05-01").click();
  await page.getByLabel("Weight (kg)", { exact: true }).fill("74");
  const pending = Promise.withResolvers();
  await page.route("**/api/tracker/701", async (route) => {
    await pending.promise;
    await route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({ record: { ...records[0], weight: 74 } }),
    });
  });
  const save = page.locator("#save-entry");
  await save.click();
  try {
    await expect(save).toBeDisabled();
    await edit(page, "2024-05-02").click();
    await expect(page.locator("#record-id")).toHaveValue("702");
  } finally {
    pending.resolve();
  }
  await expect(save).toBeEnabled();
  await expect(page.locator("#record-id")).toHaveValue("702");
  expect(dialogs).toEqual([]);
});

test("progress discard: a failed save remains an unsaved draft", async ({ page }) => {
  await edit(page, "2024-05-01").click();
  await page.getByLabel("Weight (kg)", { exact: true }).fill("74");
  await page.route("**/api/tracker/701", (route) => route.fulfill({
    status: 503,
    contentType: "application/json",
    body: JSON.stringify({ message: "Save unavailable." }),
  }));
  await page.locator("#save-entry").click();
  await expect(page.locator("#entry-status")).toHaveText("Save unavailable.");
  await expect(page.locator("#save-entry")).toBeEnabled();
  page.once("dialog", (dialog) => dialog.dismiss());
  await edit(page, "2024-05-02").click();
  await expect(page.locator("#record-id")).toHaveValue("701");
  await expect(page.getByLabel("Weight (kg)", { exact: true })).toHaveValue("74");
});
