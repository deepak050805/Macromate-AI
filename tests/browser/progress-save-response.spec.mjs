import { expect, test } from "@playwright/test";
import { fixtureUrl, signIn } from "./helpers.mjs";

for (const malformed of [{}, { record: { id: 901, date: "2024-05-01", weight: 71, calories: 2000 } }]) {
  test(`save responses: ${JSON.stringify(malformed)} cannot clear a draft or complete its retry key`, async ({ page }) => {
    await signIn(page);
    await page.goto(fixtureUrl("/tracking"));
    const requests = [];
    await page.route("**/api/tracker/add", async (route) => {
      requests.push(route.request().postDataJSON());
      await route.fulfill({
        status: 201, contentType: "application/json",
        body: JSON.stringify(requests.length === 1 ? malformed : {
          record: { id: 901, date: "2024-05-01", weight: 70, calories: 2000 },
        }),
      });
    });
    await page.getByLabel("Date (UTC)", { exact: true }).fill("2024-05-01");
    await page.getByLabel("Weight (kg)", { exact: true }).fill("70");
    await page.getByLabel("Calories consumed (kcal)", { exact: true }).fill("2000");
    await page.locator("#save-entry").click();
    await expect(page.locator("#entry-status")).toHaveText("The server returned an unreadable response. Try again.");
    await expect(page.getByLabel("Weight (kg)", { exact: true })).toHaveValue("70");
    await page.locator("#save-entry").click();
    await expect(page.locator("#entry-status")).toHaveText("Entry saved.");
    await expect(page.getByLabel("Weight (kg)", { exact: true })).toHaveValue("");
    expect(requests).toHaveLength(2);
    expect(requests[0].request_key).toBe(requests[1].request_key);
  });
}
