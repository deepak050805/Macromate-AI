import { expect, test } from "@playwright/test";
import { fixtureUrl, signIn } from "./helpers.mjs";

for (const view of [
  { path: "/tracking", email: "browser-owner@example.test", api: "**/api/tracker/history?*", rows: "#history-rows tr", button: "Refresh history", field: "From date (UTC)", draft: "2024-05-03", key: "date_from" },
  { path: "/admin", email: "browser-admin@example.test", api: "**/api/auth/all-users?*", rows: "#users-rows tr", button: "Refresh accounts", field: "Email contains", draft: "unsubmitted@example.test", key: "q" },
]) {
  test(`list refresh: ${view.path} updates the displayed view without replacing drafts`, async ({ page }) => {
    await signIn(page, view.email);
    const requests = [];
    await page.route(view.api, (route) => {
      requests.push(new URL(route.request().url()));
      const count = Math.min(2, requests.length);
      const records = [
        { id: 802, date: "2024-05-02", weight: 71, calories: 2100 },
        { id: 801, date: "2024-05-01", weight: 70, calories: 2000 },
      ].slice(0, count);
      const users = [
        { id: 1, email: "one@example.test", verified: true },
        { id: 2, email: "two@example.test", verified: false },
      ].slice(0, count);
      return route.fulfill({ contentType: "application/json", body: JSON.stringify({ page: 1, pages: 1, total: count, records, users }) });
    });
    await page.goto(fixtureUrl(view.path));
    await expect(page.locator(view.rows)).toHaveCount(1);
    await page.getByLabel(view.field, { exact: true }).fill(view.draft);
    if (view.path === "/tracking") await page.getByLabel("Weight (kg)", { exact: true }).fill("75");
    const refresh = page.getByRole("button", { name: view.button, exact: true });
    await refresh.click();
    await expect(page.locator(view.rows)).toHaveCount(2);
    await expect(refresh).toBeFocused();
    await expect(page.getByLabel(view.field, { exact: true })).toHaveValue(view.draft);
    expect(requests).toHaveLength(2);
    expect(requests[1].searchParams.has(view.key)).toBe(false);
    if (view.path === "/tracking") await expect(page.getByLabel("Weight (kg)", { exact: true })).toHaveValue("75");
  });
}
