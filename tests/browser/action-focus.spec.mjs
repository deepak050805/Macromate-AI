import { expect, test } from "@playwright/test";
import { fixtureUrl, signIn } from "./helpers.mjs";

test("manual actions: failed logout restores action focus", async ({ page }) => {
  await signIn(page);
  await page.route("**/api/auth/logout", (route) =>
    route.fulfill({
      status: 503,
      contentType: "application/json",
      body: JSON.stringify({ message: "Logout unavailable." }),
    }),
  );
  const logout = page.getByRole("button", { name: "Log out", exact: true });
  await logout.focus();
  await page.keyboard.press("Enter");
  await expect(page.locator("#global-status")).toHaveText("Logout unavailable.");
  await expect(logout).toBeEnabled();
  await expect(logout).toBeFocused();
});

test("manual actions: failed resend restores action focus", async ({ page }) => {
  await page.goto(fixtureUrl("/otp"));
  await page.getByLabel("Email address", { exact: true }).fill("pending@example.test");
  await page.route("**/api/auth/send-otp", (route) =>
    route.fulfill({
      status: 503,
      contentType: "application/json",
      body: JSON.stringify({ message: "Delivery unavailable." }),
    }),
  );
  const resend = page.locator("#resend");
  await resend.focus();
  await page.keyboard.press("Enter");
  await expect(page.locator("#verification-form .status")).toHaveText("Delivery unavailable.");
  await expect(resend).toBeEnabled();
  await expect(resend).toBeFocused();
});

test("manual actions: successful resend focuses the code while preserving cooldown", async ({
  page,
}) => {
  await page.goto(fixtureUrl("/otp"));
  await page.getByLabel("Email address", { exact: true }).fill("pending@example.test");
  await page.route("**/api/auth/send-otp", (route) =>
    route.fulfill({
      status: 202,
      contentType: "application/json",
      body: JSON.stringify({ message: "Verification requested." }),
    }),
  );
  const resend = page.locator("#resend");
  await resend.focus();
  await page.keyboard.press("Enter");
  await expect(page.locator("#verification-form .status")).toHaveText("Verification requested.");
  await expect(resend).toBeDisabled();
  await expect(resend).toHaveText("Wait 60 seconds before requesting another code");
  await expect(page.getByLabel("Six-digit verification code", { exact: true })).toBeFocused();
});
