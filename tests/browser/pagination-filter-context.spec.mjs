import { expect, test } from "@playwright/test";
import { fixtureUrl, signIn } from "./helpers.mjs";

for (const view of [
  { path: "/tracking", email: "browser-pages@example.test", api: "**/api/tracker/history?*", key: "date_from", label: "#page-label", status: "#history-status", apply: "Apply dates" },
  { path: "/admin", email: "browser-admin@example.test", api: "**/api/auth/all-users?*", key: "q", label: "#admin-page", status: "#admin-status", apply: "Apply account filters" },
]) {
  test(`filter context: ${view.path} pagination follows the retained rows after a failed filter`, async ({ page }) => {
    await signIn(page, view.email);
    await page.goto(fixtureUrl(view.path));
    await expect(page.locator(view.label)).toHaveText("Page 1 of 2");
    const requests = [];
    let failed = false;
    await page.route(view.api, (route) => {
      const url = new URL(route.request().url());
      requests.push(url);
      if (!failed && url.searchParams.has(view.key)) {
        failed = true;
        return route.fulfill({ status: 503, contentType: "application/json", body: JSON.stringify({ message: "Filter failed." }) });
      }
      return route.continue();
    });
    if (view.path === "/tracking") await page.getByLabel("From date (UTC)", { exact: true }).fill("2024-02-15");
    else await page.getByLabel("Email contains", { exact: true }).fill("directory-");
    await page.getByRole("button", { name: view.apply, exact: true }).click();
    await expect(page.locator(view.status)).toHaveText("Filter failed.");
    await page.getByRole("button", { name: "Next", exact: true }).click();
    await expect(page.locator(view.label)).toHaveText("Page 2 of 2");
    expect(requests.at(-1).searchParams.get("page")).toBe("2");
    expect(requests.at(-1).searchParams.has(view.key)).toBe(false);
  });
}
