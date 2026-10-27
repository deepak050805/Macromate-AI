import { expect, test } from "@playwright/test";
import { signIn } from "./helpers.mjs";

for (const invalid of [{ average_weight: 501 }, { average_calories: 20001 },
  { weight_change: 501 }, { first_date: "2024-01-01" }, { total: Number.MAX_SAFE_INTEGER + 1 }]) {
  test(`summary contract: ${JSON.stringify(invalid)} is retryable without showing invalid metrics`, async ({ page }) => {
    await page.clock.setFixedTime(new Date("2024-02-21T12:00:00Z"));
    let requests = 0;
    await page.route("**/api/tracker/summary?*", (route) => {
      requests += 1;
      return requests === 1 ? route.fulfill({
        contentType: "application/json", body: JSON.stringify({ total: 21, dated: 21,
          average_weight: 70, average_calories: 2000, weight_change: 0,
          first_date: "2024-02-01", last_date: "2024-02-21", ...invalid }),
      }) : route.continue();
    });
    await signIn(page, "browser-pages@example.test");
    await expect(page.locator("#summary-status")).toHaveText("The server returned an unreadable response. Try again.");
    await expect(page.locator("#summary-values")).toBeHidden();
    await page.getByRole("button", { name: "Refresh summary", exact: true }).click();
    await expect(page.locator("#summary-total")).toHaveText("21");
    await expect(page.locator("#summary-values")).toBeVisible();
  });
}
