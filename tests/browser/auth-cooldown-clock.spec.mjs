import { expect, test } from "@playwright/test";
import { fixtureUrl } from "./helpers.mjs";

test.beforeEach(async ({ page }) => {
  await page.clock.install({ time: new Date("2026-10-27T00:00:00Z") });
  await page.goto(fixtureUrl("/otp"));
  await page.clock.pauseAt(new Date("2026-10-27T00:00:05Z"));
  await page.route("**/api/auth/send-otp", (route) => route.fulfill({
    status: 202, contentType: "application/json", body: JSON.stringify({ message: "Verification requested." }),
  }));
  await page.getByLabel("Email address", { exact: true }).fill("countdown@example.test");
});

test("resend countdown: remaining time updates and a delayed timer releases the button", async ({ page }) => {
  const button = page.locator("#resend");
  await button.click();
  await expect(button).toHaveText("Wait 60 seconds before requesting another code");
  await page.clock.runFor(15000);
  await expect(button).toHaveText("Wait 45 seconds before requesting another code");
  await page.clock.fastForward(45000);
  await expect(button).toBeEnabled();
  await expect(button).toHaveText("Send a new code");
});

test("resend countdown: returning after the deadline immediately clears a stale timer", async ({ page }) => {
  const button = page.locator("#resend");
  await button.click();
  await expect(button).toBeDisabled();
  await page.clock.setSystemTime(new Date("2026-10-27T00:02:00Z"));
  await page.evaluate(() => document.dispatchEvent(new Event("visibilitychange")));
  await expect(button).toBeEnabled();
  await expect(button).toHaveText("Send a new code");
});

test("resend countdown: an explicitly disabled cooldown does not create a delay", async ({ page }) => {
  await page.locator("#resend").evaluate((button) => { button.dataset.cooldown = "0"; });
  await page.locator("#resend").click();
  await expect(page.locator("#verification-form .status")).toHaveText("Verification requested.");
  await expect(page.locator("#resend")).toBeEnabled();
  await expect(page.locator("#resend")).toHaveText("Send a new code");
});
