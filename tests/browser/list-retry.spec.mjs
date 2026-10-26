import { expect, test } from "@playwright/test";
import { fixtureUrl, signIn } from "./helpers.mjs";

for (const [path, email, endpoint, button, heading] of [
  ["/tracking", "browser-pages@example.test", "**/api/tracker/history*", "Retry history", "Progress history"],
  ["/admin", "browser-admin@example.test", "**/api/auth/all-users*", "Retry accounts", "Registered accounts"],
  ["/dashboard", "browser-owner@example.test", "**/api/tracker/history*", "Retry overview", "Latest recorded entry"],
]) {
  test(`list retry: ${path} recovers without reloading the page`, async ({ page }) => {
    await signIn(page, email);
    await page.goto("about:blank");
    let requests = 0;
    await page.route(endpoint, (route) => {
      requests += 1;
      return requests === 1 ? route.fulfill({
        status: 503, contentType: "application/json",
        body: JSON.stringify({ message: "Fixture temporarily unavailable." }),
      }) : route.continue();
    });
    await page.goto(fixtureUrl(path));
    const retry = page.getByRole("button", { name: button, exact: true });
    await expect(retry).toBeVisible();
    await retry.click();
    await expect(page.getByRole("heading", { name: heading, exact: true })).toBeFocused();
    await expect(retry).toBeHidden();
    expect(requests).toBe(2);
  });
}
