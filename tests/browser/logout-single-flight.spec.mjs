import { expect, test } from "@playwright/test";
import { signIn } from "./helpers.mjs";

test("logout: repeated dispatched clicks cannot create overlapping requests", async ({ page }) => {
  await signIn(page);
  await page.waitForLoadState("networkidle");
  const requests = await page.evaluate(() => {
    const original = window.fetch;
    let count = 0;
    window.fetch = (path, options) => {
      if (path !== "/api/auth/logout") return original(path, options);
      count += 1;
      return new Promise((resolve) => { window.finishLogout = resolve; });
    };
    const button = document.querySelector("#logout");
    button.dispatchEvent(new MouseEvent("click", { bubbles: true }));
    button.dispatchEvent(new MouseEvent("click", { bubbles: true }));
    return count;
  });
  expect(requests).toBe(1);
  await page.evaluate(() => window.finishLogout(new Response(
    JSON.stringify({ message: "Try logout again." }), { status: 503 },
  )));
  await expect(page.locator("#logout")).toBeEnabled();
  await expect(page.locator("#global-status")).toHaveText("Try logout again.");
});
