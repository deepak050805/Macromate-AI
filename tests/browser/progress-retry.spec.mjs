import { expect, test } from "@playwright/test";
import { fixtureUrl, signIn } from "./helpers.mjs";

async function fillEntry(page, date) {
  await page.getByLabel("Date (UTC)", { exact: true }).fill(date);
  await page.getByLabel("Weight (kg)", { exact: true }).fill("70");
  await page.getByLabel("Calories consumed (kcal)", { exact: true }).fill("2000");
}

test("progress retries: a committed save with a lost response is not inserted twice", async ({ page }) => {
  await signIn(page);
  await page.goto(fixtureUrl("/tracking"));
  const bodies = [];
  await page.route("**/api/tracker/add", async (route) => {
    bodies.push(route.request().postDataJSON());
    if (bodies.length === 1) {
      const response = await route.fetch();
      expect(response.status()).toBe(201);
      await route.abort("failed");
    } else await route.continue();
  });
  await fillEntry(page, "2024-06-01");
  await page.locator("#save-entry").click();
  await expect(page.locator("#entry-status")).toContainText("Connection failed");
  await page.locator("#save-entry").click();
  await expect(page.locator("#entry-status")).toHaveText("Entry saved.");
  await expect(page.getByRole("button", { name: "Edit entry for 2024-06-01", exact: true })).toHaveCount(1);
  expect(bodies).toHaveLength(2);
  expect(bodies[0].request_key).toBe(bodies[1].request_key);
});

test("progress retries: a successful reset starts a distinct create intent", async ({ page }) => {
  await signIn(page);
  await page.goto(fixtureUrl("/tracking"));
  const keys = [];
  page.on("request", (request) => {
    if (request.method() === "POST" && new URL(request.url()).pathname === "/api/tracker/add")
      keys.push(request.postDataJSON().request_key);
  });
  for (let count = 0; count < 2; count += 1) {
    await fillEntry(page, "2024-06-02");
    await page.locator("#save-entry").click();
    await expect(page.locator("#save-entry")).toBeEnabled();
  }
  expect(keys).toHaveLength(2);
  expect(keys[0]).not.toBe(keys[1]);
});

test("progress retries: a confirmed create releases its key while retaining a newer draft", async ({ page }) => {
  await signIn(page);
  await page.goto(fixtureUrl("/tracking"));
  const pending = Promise.withResolvers();
  const keys = [];
  const records = [];
  await page.route("**/api/tracker/add", async (route) => {
    keys.push(route.request().postDataJSON().request_key);
    const response = await route.fetch();
    records.push((await response.json()).record.id);
    if (keys.length === 1) await pending.promise;
    await route.fulfill({ response });
  });
  await fillEntry(page, "2024-06-03");
  await page.locator("#save-entry").click();
  try {
    await expect(page.locator("#save-entry")).toBeDisabled();
    await page.getByLabel("Weight (kg)", { exact: true }).fill("71");
  } finally {
    pending.resolve();
  }
  await expect(page.locator("#save-entry")).toBeEnabled();
  await expect(page.locator("#entry-status")).toContainText("newer draft was kept");
  await page.getByLabel("Weight (kg)", { exact: true }).fill("70");
  await page.locator("#save-entry").click();
  await expect(page.locator("#save-entry")).toBeEnabled();
  expect(keys).toHaveLength(2);
  expect(keys[0]).not.toBe(keys[1]);
  expect(records[0]).not.toBe(records[1]);
});
