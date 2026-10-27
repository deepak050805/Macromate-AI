import { expect, test } from "@playwright/test";
import { fixtureUrl } from "./helpers.mjs";

async function fillVerification(page) {
  await page.goto(fixtureUrl("/otp"));
  await page.getByLabel("Email address", { exact: true }).fill("actions@example.test");
  await page.getByLabel("Six-digit verification code", { exact: true }).fill("123456");
  await page.getByLabel("New password", { exact: true }).fill("fictional new password");
}

test("verification actions: a pending resend blocks verification without clearing the code", async ({ page }) => {
  await fillVerification(page);
  const pending = Promise.withResolvers();
  let verificationRequests = 0;
  await page.route("**/api/auth/verify-otp", (route) => {
    verificationRequests += 1;
    return route.fulfill({ status: 503, contentType: "application/json", body: JSON.stringify({ message: "Unexpected verification." }) });
  });
  await page.route("**/api/auth/send-otp", async (route) => {
    await pending.promise;
    await route.fulfill({ status: 202, contentType: "application/json", body: JSON.stringify({ message: "Verification requested." }) });
  });
  await page.locator("#resend").click();
  try {
    await expect(page.getByRole("button", { name: "Verify email", exact: true })).toBeDisabled();
    await page.locator("#verification-form").evaluate((form) => form.requestSubmit());
  } finally { pending.resolve(); }
  await expect(page.getByRole("button", { name: "Verify email", exact: true })).toBeEnabled();
  await expect(page.getByLabel("Six-digit verification code", { exact: true })).toHaveValue("123456");
  expect(verificationRequests).toBe(0);
});

test("verification actions: cooldown expiry cannot enable resend during verification", async ({ page }) => {
  await page.clock.install({ time: new Date("2026-10-27T00:00:00Z") });
  await fillVerification(page);
  await page.clock.pauseAt(new Date("2026-10-27T00:00:05Z"));
  await page.route("**/api/auth/send-otp", (route) => route.fulfill({
    status: 202, contentType: "application/json", body: JSON.stringify({ message: "Verification requested." }),
  }));
  const pending = Promise.withResolvers();
  await page.route("**/api/auth/verify-otp", async (route) => {
    await pending.promise;
    await route.fulfill({ status: 503, contentType: "application/json", body: JSON.stringify({ message: "Try verification again." }) });
  });
  await page.locator("#resend").click();
  await expect(page.locator("#resend")).toHaveText(/Wait 60 seconds/);
  await page.getByRole("button", { name: "Verify email", exact: true }).click();
  try {
    await expect(page.getByRole("button", { name: "Verify email", exact: true })).toBeDisabled();
    await page.clock.fastForward(60000);
    await expect(page.locator("#resend")).toHaveText("Send a new code");
    await expect(page.locator("#resend")).toBeDisabled();
  } finally { pending.resolve(); }
  await expect(page.locator("#resend")).toBeEnabled();
  await expect(page.getByRole("button", { name: "Verify email", exact: true })).toBeEnabled();
});
