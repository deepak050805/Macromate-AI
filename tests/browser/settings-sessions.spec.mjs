import { expect, test } from "@playwright/test";
import { fixtureUrl, signIn } from "./helpers.mjs";

test("account sessions: global sign-out requires confirmation and retains the password", async ({ page }) => {
  await signIn(page);
  await page.goto(fixtureUrl("/settings"));
  await page.getByLabel("Confirm current password", { exact: true }).fill("fictional browser password");
  await page.getByRole("button", { name: "Sign out all sessions", exact: true }).click();
  await expect(page).toHaveURL(fixtureUrl("/login?notice=sessions"));
  await expect(page.locator("form .status")).toHaveText("All sessions signed out. Log in to continue.");
  await page.getByLabel("Email address", { exact: true }).fill("browser-owner@example.test");
  await page.getByLabel("Password", { exact: true }).fill("fictional browser password");
  await page.getByRole("button", { name: "Log in", exact: true }).click();
  await expect(page).toHaveURL(fixtureUrl("/dashboard"));
});
