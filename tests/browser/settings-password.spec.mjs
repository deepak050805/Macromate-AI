import { expect, test } from "@playwright/test";
import { fixtureUrl, signIn } from "./helpers.mjs";

test("account settings: rotate a password and sign in with the replacement", async ({ page }) => {
  const email = "browser-settings@example.test";
  await signIn(page, email);
  await page.getByRole("link", { name: "Account", exact: true }).click();
  await page.getByLabel("Current password", { exact: true }).fill("fictional browser password");
  await page.getByLabel("New password", { exact: true }).fill("replacement fixture password");
  await page.getByRole("button", { name: "Update password", exact: true }).click();
  await expect(page).toHaveURL(fixtureUrl("/login?notice=reset"));
  await page.getByLabel("Email address", { exact: true }).fill(email);
  await page.getByLabel("Password", { exact: true }).fill("replacement fixture password");
  await page.getByRole("button", { name: "Log in", exact: true }).click();
  await expect(page).toHaveURL(fixtureUrl("/dashboard"));
});

test("account settings: anonymous requests cannot render the password form", async ({ page }) => {
  const response = await page.goto(fixtureUrl("/settings"));
  expect(response.status()).toBe(401);
  await expect(page.locator('form[data-auth="/api/auth/change-password"]')).toHaveCount(0);
});
