import { expect, test } from "@playwright/test";
import { fixtureUrl } from "./helpers.mjs";

test("resend persistence: reload restores the address of the successful code request", async ({ page }) => {
  await page.goto(fixtureUrl("/otp"));
  await page.evaluate(() => {
    sessionStorage.setItem("pending-email", "older@example.test");
  });
  await page.reload();
  const email = page.getByLabel("Email address", { exact: true });
  await expect(email).toHaveValue("older@example.test");
  await email.fill("newer@example.test");
  await page.route("**/api/auth/send-otp", (route) => route.fulfill({
    status: 202,
    contentType: "application/json",
    body: JSON.stringify({ message: "Verification requested." }),
  }));
  await page.locator("#resend").click();
  await expect(page.locator("#verification-form .status")).toHaveText("Verification requested.");
  await page.reload();
  await expect(email).toHaveValue("newer@example.test");
});
