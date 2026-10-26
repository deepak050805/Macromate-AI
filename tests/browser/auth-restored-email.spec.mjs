import { expect, test } from "@playwright/test";
import { fixtureUrl } from "./helpers.mjs";

test("email restoration: stored pending email fills only empty fields", async ({ page }) => {
  await page.addInitScript(() => {
    sessionStorage.setItem("pending-email", "pending@example.test");
  });
  const moduleReady = Promise.withResolvers();
  await page.route("**/static/js/auth.js", async (route) => {
    await moduleReady.promise;
    await route.continue();
  });
  await page.goto(fixtureUrl("/reset-password"), { waitUntil: "commit" });
  try {
    await page.locator("#request-email").fill("restored@example.test");
  } finally {
    moduleReady.resolve();
  }
  await expect(page.locator("#reset-email")).toHaveValue("pending@example.test");
  await expect(page.locator("#request-email")).toHaveValue("restored@example.test");
});
