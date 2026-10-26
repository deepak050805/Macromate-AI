import { expect, test } from "@playwright/test";
import { signIn } from "./helpers.mjs";

test("dashboard summary: shows the recent UTC window without medical inference", async ({ page }) => {
  await page.clock.setFixedTime(new Date("2024-02-21T12:00:00Z"));
  await signIn(page, "browser-pages@example.test");
  await expect(page.locator("#summary-total")).toHaveText("21");
  await expect(page.locator("#summary-weight")).toHaveText("70 kg");
  await expect(page.locator("#summary-change")).toHaveText("0 kg");
  await expect(page.locator("#summary-range")).toHaveText("2024-01-23 through 2024-02-21 (UTC)");
});

test("dashboard summary: an independent failure can be retried without losing the overview", async ({ page }) => {
  let requests = 0;
  await page.route("**/api/tracker/summary*", (route) => {
    requests += 1;
    return requests === 1 ? route.fulfill({
      status: 503, contentType: "application/json",
      body: JSON.stringify({ message: "Summary unavailable." }),
    }) : route.continue();
  });
  await signIn(page);
  await expect(page.locator("#summary-status")).toHaveText("Summary unavailable.");
  await page.getByRole("button", { name: "Refresh summary", exact: true }).click();
  await expect(page.locator("#summary-values")).toBeVisible();
  await expect(page.locator("#summary-status")).toContainText("No dated entries");
  await expect(page.locator("#dashboard-status")).not.toHaveText("Summary unavailable.");
});
