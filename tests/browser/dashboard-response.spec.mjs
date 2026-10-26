import { expect, test } from "@playwright/test";
import { fixtureUrl, signIn } from "./helpers.mjs";

test("dashboard responses: invalid latest-entry data is retryable without displaying undefined values", async ({ page }) => {
  await signIn(page, "browser-pages@example.test");
  let requests = 0;
  await page.route("**/api/tracker/history", (route) => {
    requests += 1;
    return requests === 1 ? route.fulfill({
      status: 200, contentType: "application/json",
      body: JSON.stringify({ page: 1, pages: 2, total: 21, records: [{ id: 1, date: null, weight: "70", calories: 2000 }] }),
    }) : route.continue();
  });
  await page.goto(fixtureUrl("/dashboard"));
  await expect(page.locator("#dashboard-status")).toHaveText("The server returned an unreadable response. Try again.");
  await expect(page.locator("#latest-entry")).toBeHidden();
  await page.getByRole("button", { name: "Retry overview", exact: true }).click();
  await expect(page.locator("#latest-weight")).toHaveText("70 kg");
  await expect(page.locator("#retry-dashboard")).toBeHidden();
  expect(requests).toBe(2);
});
