import { expect, test } from "@playwright/test";
import { fixtureUrl, signIn } from "./helpers.mjs";

for (const [path, code, title] of [["/missing-ui-page", 404, "Page not found"], ["/tracking", 401, "Sign in to continue"]]) {
  test(`error recovery: ${code} explains the problem and offers working navigation`, async ({ page }) => {
    const response = await page.goto(fixtureUrl(path));
    expect(response.status()).toBe(code);
    await expect(page.getByRole("heading", { name: title, exact: true })).toBeVisible();
    await expect(page.locator("#error-reference")).toHaveText(/^[0-9a-f]{32}$/);
    expect(await page.locator("#error-reference").textContent()).toBe(response.headers()["x-request-id"]);
    await page.getByRole("link", { name: "Return home", exact: true }).click();
    await expect(page).toHaveURL(fixtureUrl("/"));
  });
}

test("error recovery: permission errors do not expose an account directory", async ({ page }) => {
  await signIn(page);
  expect((await page.goto(fixtureUrl("/admin"))).status()).toBe(403);
  await expect(page.getByRole("heading", { name: "Access restricted", exact: true })).toBeVisible();
  await expect(page.locator("#users-rows")).toHaveCount(0);
});

for (const denied of [false, true]) {
  test(`error reference: clipboard ${denied ? "denial gives a manual fallback" : "copy uses only the opaque ID"}`, async ({ page }) => {
    await page.addInitScript((deny) => {
      Object.defineProperty(navigator, "clipboard", { configurable: true, value: {
        writeText: async (value) => {
          if (deny) throw new DOMException("Blocked", "NotAllowedError");
          window.copiedReference = value;
        },
      } });
    }, denied);
    await page.goto(fixtureUrl("/missing-ui-page"));
    await page.getByRole("button", { name: "Copy reference", exact: true }).click();
    await expect(page.locator("#reference-status")).toHaveText(denied ? "Select and copy the reference above." : "Reference copied.");
    await expect(page.getByRole("button", { name: "Copy reference", exact: true })).toBeEnabled();
    if (!denied) expect(await page.evaluate(() => window.copiedReference)).toBe(await page.locator("#error-reference").textContent());
  });
}
