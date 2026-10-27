import { expect, test } from "@playwright/test";
import { fixtureUrl, signIn } from "./helpers.mjs";

const records = [
  { id: 701, date: "2024-05-01", weight: 70, calories: 2000 },
  { id: 702, date: "2024-05-02", weight: 71, calories: 2100 },
];
const unconfirmed = "This save has not been confirmed. Discard your unsaved progress changes?";

test.beforeEach(async ({ page }) => {
  await signIn(page);
  await page.route("**/api/tracker/history?*", (route) => route.fulfill({
    contentType: "application/json",
    body: JSON.stringify({ page: 1, pages: 1, total: 2, records }),
  }));
  await page.goto(fixtureUrl("/tracking"));
  await expect(page.locator("#history-rows tr")).toHaveCount(2);
});

for (const editing of [false, true]) {
  test(`unconfirmed draft: declining a pending ${editing ? "update" : "create"} switch preserves a failed save for retry`, async ({ page }) => {
    if (editing)
      await page.getByRole("button", { name: "Edit entry for 2024-05-01", exact: true }).click();
    else {
      await page.getByLabel("Date (UTC)", { exact: true }).fill("2024-05-01");
      await page.getByLabel("Calories consumed (kcal)", { exact: true }).fill("2000");
    }
    await page.getByLabel("Weight (kg)", { exact: true }).fill("74");
    const pending = Promise.withResolvers();
    const requests = [];
    await page.route(editing ? "**/api/tracker/701" : "**/api/tracker/add", async (route) => {
      requests.push(route.request().postDataJSON());
      if (requests.length === 1) {
        await pending.promise;
        return route.fulfill({ status: 503, contentType: "application/json", body: JSON.stringify({ message: "Save unavailable." }) });
      }
      return route.fulfill({ status: editing ? 200 : 201, contentType: "application/json", body: JSON.stringify({
        record: { id: editing ? 701 : 703, date: "2024-05-01", weight: 74, calories: 2000 },
      }) });
    });
    await page.locator("#save-entry").click();
    try {
      await expect(page.locator("#save-entry")).toBeDisabled();
      page.once("dialog", async (dialog) => {
        expect(dialog.message()).toBe(unconfirmed);
        await dialog.dismiss();
      });
      await page.getByRole("button", { name: "Edit entry for 2024-05-02", exact: true }).click();
      await expect(page.locator("#record-id")).toHaveValue(editing ? "701" : "");
      await expect(page.getByLabel("Weight (kg)", { exact: true })).toHaveValue("74");
    } finally {
      pending.resolve();
    }
    await expect(page.locator("#entry-status")).toHaveText("Save unavailable.");
    await expect(page.locator("#save-entry")).toBeEnabled();
    await page.locator("#save-entry").click();
    await expect(page.locator("#entry-status")).toHaveText(editing ? "Entry updated." : "Entry saved.");
    await expect(page.getByLabel("Weight (kg)", { exact: true })).toHaveValue("");
    expect(requests).toHaveLength(2);
    expect(requests[1]).toEqual(requests[0]);
    if (!editing) expect(requests[0].request_key).toMatch(/^[0-9a-f-]{36}$/);
  });
}

test("unconfirmed draft: declining cancellation preserves a pending update after failure", async ({ page }) => {
  await page.getByRole("button", { name: "Edit entry for 2024-05-01", exact: true }).click();
  await page.getByLabel("Weight (kg)", { exact: true }).fill("74");
  const pending = Promise.withResolvers();
  await page.route("**/api/tracker/701", async (route) => {
    await pending.promise;
    return route.fulfill({ status: 503, contentType: "application/json", body: JSON.stringify({ message: "Save unavailable." }) });
  });
  await page.locator("#save-entry").click();
  try {
    await expect(page.locator("#save-entry")).toBeDisabled();
    page.once("dialog", async (dialog) => {
      expect(dialog.message()).toBe(unconfirmed);
      await dialog.dismiss();
    });
    await page.getByRole("button", { name: "Cancel editing", exact: true }).click();
  } finally {
    pending.resolve();
  }
  await expect(page.locator("#entry-status")).toHaveText("Save unavailable.");
  await expect(page.locator("#record-id")).toHaveValue("701");
  await expect(page.getByLabel("Weight (kg)", { exact: true })).toHaveValue("74");
  await expect(page.getByRole("button", { name: "Cancel editing", exact: true })).toBeVisible();
});
