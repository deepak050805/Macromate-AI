import { expect, test } from "@playwright/test";
import { fixtureUrl } from "./helpers.mjs";

test("password entry: keyboard reveal preserves the value and accessible state", async ({ page }) => {
  await page.goto(fixtureUrl("/login"));
  const password = page.getByLabel("Password", { exact: true });
  await password.fill("fictional private password");
  const show = page.getByRole("button", { name: "Show password", exact: true });
  await show.focus();
  await page.keyboard.press("Space");
  await expect(password).toHaveAttribute("type", "text");
  const hide = page.getByRole("button", { name: "Hide password", exact: true });
  await expect(hide).toHaveAttribute("aria-pressed", "true");
  await expect(hide).toBeFocused();
  await hide.click();
  await expect(password).toHaveAttribute("type", "password");
  await expect(password).toHaveValue("fictional private password");
});

test("password entry: new-password autocomplete survives reveal", async ({ page }) => {
  await page.goto(fixtureUrl("/signup"));
  const password = page.getByLabel("New password", { exact: true });
  await page.getByRole("button", { name: "Show new password", exact: true }).click();
  await expect(password).toHaveAttribute("autocomplete", "new-password");
  await expect(password).toHaveAttribute("type", "text");
});
