import { expect, test } from "@playwright/test";
import { fixtureUrl } from "./helpers.mjs";

for (const responseStatus of [202, 503]) {
  test(`resend state: an edited email ignores a delayed ${responseStatus} response`, async ({ page }) => {
    await page.goto(fixtureUrl("/otp"));
    const email = page.getByLabel("Email address", { exact: true });
    const resend = page.locator("#resend");
    const pending = Promise.withResolvers();
    let submittedEmail;
    await page.route("**/api/auth/send-otp", async (route) => {
      submittedEmail = route.request().postDataJSON().email;
      await pending.promise;
      await route.fulfill({
        status: responseStatus,
        contentType: "application/json",
        body: JSON.stringify({ message: "Response for the original email." }),
      });
    });
    await email.fill("original@example.test");
    await resend.click();
    try {
      await expect(resend).toBeDisabled();
      await email.fill("newer@example.test");
    } finally {
      pending.resolve();
    }
    await expect(resend).toBeEnabled();
    expect(submittedEmail).toBe("original@example.test");
    await expect(resend).toHaveText("Send a new code");
    await expect(email).toHaveValue("newer@example.test");
    await expect(email).toBeFocused();
    await expect(page.locator("#verification-form .status")).toBeEmpty();
  });
}

test("resend state: an email change releases only the old address's cooldown", async ({ page }) => {
  await page.goto(fixtureUrl("/otp"));
  const email = page.getByLabel("Email address", { exact: true });
  const resend = page.locator("#resend");
  const requestedEmails = [];
  await page.route("**/api/auth/send-otp", async (route) => {
    requestedEmails.push(route.request().postDataJSON().email);
    await route.fulfill({
      status: 202,
      contentType: "application/json",
      body: JSON.stringify({ message: "Verification requested." }),
    });
  });
  await email.fill("original@example.test");
  await resend.click();
  await expect(resend).toHaveText("Wait 60 seconds before requesting another code");
  await expect(resend).toBeDisabled();
  await email.fill("newer@example.test");
  await expect(resend).toBeEnabled();
  await expect(page.locator("#verification-form .status")).toBeEmpty();
  await resend.click();
  await expect(resend).toHaveText("Wait 60 seconds before requesting another code");
  await expect(resend).toBeDisabled();
  expect(requestedEmails).toEqual(["original@example.test", "newer@example.test"]);
});
