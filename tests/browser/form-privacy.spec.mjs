import { expect, test } from "@playwright/test";
import { fixtureUrl } from "./helpers.mjs";

test.use({ javaScriptEnabled: false });

for (const path of ["/login", "/signup", "/otp", "/reset-password"]) {
  test(`form privacy: ${path} never places credentials in a URL without JavaScript`, async ({ page }) => {
    await page.goto(fixtureUrl(path));
    await expect(page.getByText("JavaScript is required", { exact: false })).toBeVisible();
    const form = page.locator("form[data-auth]").first();
    await form.locator('input[name="email"]').fill("fictional@example.test");
    const password = form.locator('input[name="password"]');
    if (await password.count()) await password.fill("fictional-private-password");
    const code = form.locator('input[name="otp"]');
    if (await code.count()) await code.fill("123456");
    const sent = page.waitForRequest((request) => request.isNavigationRequest() && request.method() === "POST");
    await form.locator('button[type="submit"]').click();
    const request = await sent;
    expect(new URL(request.url()).search).toBe("");
    expect(request.url()).not.toContain("fictional");
  });
}
