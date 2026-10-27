import { expect, test } from "@playwright/test";
import { fixtureUrl, signIn } from "./helpers.mjs";

test("session recovery: an expired history request offers sign-in and retains unsaved fields", async ({ page, context }) => {
  await signIn(page);
  await page.goto(fixtureUrl("/tracking"));
  await expect(page.locator("#history-status")).not.toContainText("Loading");
  await page.getByLabel("Weight (kg)", { exact: true }).fill("73");
  await context.clearCookies();
  await page.getByRole("button", { name: "Apply dates", exact: true }).click();
  await expect(page.locator("#session-notice")).toBeVisible();
  await expect(page.getByRole("link", { name: "Sign in again", exact: true })).toHaveAttribute("href", "/login");
  await expect(page.getByLabel("Weight (kg)", { exact: true })).toHaveValue("73");
  await expect(page).toHaveURL(fixtureUrl("/tracking"));
});

test("session recovery: rejected login credentials do not masquerade as an expired session", async ({ page }) => {
  await page.goto(fixtureUrl("/login"));
  await page.getByLabel("Email address", { exact: true }).fill("missing@example.test");
  await page.getByLabel("Password", { exact: true }).fill("fictional wrong password");
  await page.getByRole("button", { name: "Log in", exact: true }).click();
  await expect(page.locator("form .status")).toHaveClass(/error/);
  await expect(page.locator("#session-notice")).toHaveCount(0);
});
