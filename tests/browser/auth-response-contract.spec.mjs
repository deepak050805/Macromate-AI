import { expect, test } from "@playwright/test";
import { fixtureUrl } from "./helpers.mjs";

const invalidResponses = [
  ["missing message", {}],
  ["non-string message", { message: ["Unexpected array"] }],
  ["blank message", { message: "  \t " }],
];

for (const [description, data] of invalidResponses) {
  test(`auth response contract: signup rejects ${description} before redirect or persistence`, async ({ page }) => {
    await page.goto(fixtureUrl("/signup"));
    await page.evaluate(() => sessionStorage.setItem("pending-email", "previous@example.test"));
    await page.route("**/api/auth/signup", (route) => route.fulfill({
      status: 202,
      contentType: "application/json",
      body: JSON.stringify(data),
    }));
    await page.getByLabel("Email address", { exact: true }).fill("newer@example.test");
    await page.getByLabel("New password", { exact: true }).fill("fictional private password");
    const submit = page.getByRole("button", { name: "Create account", exact: true });
    await submit.click();
    await expect(page.locator("form .status"))
      .toHaveText("The server returned an unreadable response. Try again.");
    await expect(submit).toBeEnabled();
    await expect(page).toHaveURL(fixtureUrl("/signup"));
    expect(await page.evaluate(() => sessionStorage.getItem("pending-email")))
      .toBe("previous@example.test");
  });

  test(`auth response contract: resend rejects ${description} without persistence or cooldown`, async ({ page }) => {
    await page.goto(fixtureUrl("/otp"));
    await page.evaluate(() => sessionStorage.setItem("pending-email", "previous@example.test"));
    await page.route("**/api/auth/send-otp", (route) => route.fulfill({
      status: 202,
      contentType: "application/json",
      body: JSON.stringify(data),
    }));
    await page.getByLabel("Email address", { exact: true }).fill("newer@example.test");
    const resend = page.locator("#resend");
    await resend.click();
    await expect(page.locator("#verification-form .status"))
      .toHaveText("The server returned an unreadable response. Try again.");
    await expect(resend).toBeEnabled();
    await expect(resend).toHaveText("Send a new code");
    expect(await page.evaluate(() => sessionStorage.getItem("pending-email")))
      .toBe("previous@example.test");
  });
}
