import { expect, test } from "@playwright/test";
import { fixtureUrl, signIn } from "./helpers.mjs";

test.beforeEach(async ({ page }) => {
  await signIn(page);
  await page.goto(fixtureUrl("/tracking"));
  await expect(page.locator("#history-status")).not.toHaveText("Loading your history…");
});

async function fillEntry(page, date, weight = "70", calories = "2000") {
  await page.getByLabel("Date (UTC)", { exact: true }).fill(date);
  await page.getByLabel("Weight (kg)", { exact: true }).fill(weight);
  await page.getByLabel("Calories consumed (kcal)", { exact: true }).fill(calories);
}

function savedResponse(page, method) {
  return page.waitForResponse(
    (response) =>
      response.request().method() === method && response.url().includes("/api/tracker/"),
  );
}

async function createEntry(page, date) {
  await fillEntry(page, date);
  const saved = savedResponse(page, "POST");
  await page.locator("#save-entry").click();
  const record = (await (await saved).json()).record;
  await expect(page.locator("#save-entry")).toBeEnabled();
  return record;
}

async function holdSaves(page, method) {
  const pending = Promise.withResolvers();
  await page.route("**/api/tracker/**", async (route) => {
    if (route.request().method() === method) await pending.promise;
    await route.continue();
  });
  return pending.resolve;
}

test("progress drafts: keep fields edited while a new entry is saving", async ({ page }) => {
  await fillEntry(page, "2024-04-01");
  const release = await holdSaves(page, "POST");
  const saved = savedResponse(page, "POST");
  await page.locator("#save-entry").click();
  try {
    await expect(page.locator("#save-entry")).toBeDisabled();
    await fillEntry(page, "2024-04-02", "71", "2100");
  } finally {
    release();
  }
  const record = (await (await saved).json()).record;
  expect(record).toMatchObject({ date: "2024-04-01", weight: 70, calories: 2000 });
  await expect(page.locator("#save-entry")).toBeEnabled();
  await expect(page.getByLabel("Date (UTC)", { exact: true })).toHaveValue("2024-04-02");
  await expect(page.getByLabel("Weight (kg)", { exact: true })).toHaveValue("71");
  await expect(page.getByLabel("Calories consumed (kcal)", { exact: true })).toHaveValue("2100");
  await expect(page.locator("#entry-status")).toContainText("Your newer draft was kept.");
});

test("progress drafts: keep another selected record even when field values match", async ({
  page,
}) => {
  const first = await createEntry(page, "2024-04-03");
  const second = await createEntry(page, "2024-04-03");
  const edits = page.getByRole("button", { name: "Edit entry for 2024-04-03", exact: true });
  await edits.nth(1).click();
  await expect(page.locator("#record-id")).toHaveValue(String(first.id));
  const release = await holdSaves(page, "PUT");
  const saved = savedResponse(page, "PUT");
  await page.locator("#save-entry").click();
  try {
    await expect(page.locator("#save-entry")).toBeDisabled();
    await edits.nth(0).click();
    await expect(page.locator("#record-id")).toHaveValue(String(second.id));
  } finally {
    release();
  }
  expect((await (await saved).json()).record.id).toBe(first.id);
  await expect(page.locator("#save-entry")).toBeEnabled();
  await expect(page.locator("#record-id")).toHaveValue(String(second.id));
  await expect(page.locator("#entry-title")).toHaveText("Edit progress entry");
  await expect(page.getByLabel("Weight (kg)", { exact: true })).toHaveValue("70");
});

test("progress drafts: keep a new draft started after cancelling a pending edit", async ({
  page,
}) => {
  await createEntry(page, "2024-04-04");
  await page.getByRole("button", { name: "Edit entry for 2024-04-04", exact: true }).click();
  const release = await holdSaves(page, "PUT");
  const saved = savedResponse(page, "PUT");
  await page.locator("#save-entry").click();
  try {
    await expect(page.locator("#save-entry")).toBeDisabled();
    await page.getByRole("button", { name: "Cancel editing", exact: true }).click();
    await fillEntry(page, "2024-04-05", "72", "2200");
  } finally {
    release();
  }
  await saved;
  await expect(page.locator("#save-entry")).toBeEnabled();
  await expect(page.locator("#record-id")).toHaveValue("");
  await expect(page.locator("#entry-title")).toHaveText("Add a progress entry");
  await expect(page.getByLabel("Weight (kg)", { exact: true })).toHaveValue("72");
  await expect(page.getByRole("button", { name: "Cancel editing", exact: true })).toBeHidden();
});

test("progress drafts: keep fields edited while their original record is being deleted", async ({ page }) => {
  await createEntry(page, "2024-07-01");
  await page.getByRole("button", { name: "Edit entry for 2024-07-01", exact: true }).click();
  const release = await holdSaves(page, "DELETE");
  const deleted = savedResponse(page, "DELETE");
  page.once("dialog", (dialog) => dialog.accept());
  await page.getByRole("button", { name: "Delete entry for 2024-07-01", exact: true }).click();
  try {
    await expect(page.getByRole("button", { name: "Delete entry for 2024-07-01", exact: true })).toBeDisabled();
    await fillEntry(page, "2024-07-02", "73", "2300");
  } finally {
    release();
  }
  await deleted;
  await expect(page.locator("#entry-status")).toContainText("draft was kept as a new entry");
  await expect(page.locator("#record-id")).toHaveValue("");
  await expect(page.getByLabel("Weight (kg)", { exact: true })).toHaveValue("73");
  await expect(page.getByLabel("Date (UTC)", { exact: true })).toHaveValue("2024-07-02");
  await expect(page.locator("#entry-title")).toHaveText("Add a progress entry");
});
