import { expect, test } from "@playwright/test";
import { fixtureUrl } from "./helpers.mjs";

test("password privacy: pagehide masks revealed values and restores toggle state", async ({ page }) => {
  await page.goto(fixtureUrl("/login"));
  const password = page.getByLabel("Password", { exact: true });
  await password.fill("fictional private password");
  await page.getByRole("button", { name: "Show password", exact: true }).click();
  await expect(password).toHaveAttribute("type", "text");
  await page.evaluate(() => {
    window.dispatchEvent(new PageTransitionEvent("pagehide", { persisted: true }));
  });
  await expect(password).toHaveAttribute("type", "password");
  await expect(password).toHaveValue("fictional private password");
  const show = page.getByRole("button", { name: "Show password", exact: true });
  await expect(show).toHaveAttribute("aria-pressed", "false");
  await show.click();
  await expect(password).toHaveAttribute("type", "text");
});

test("password privacy: only hiding the document masks a revealed new password", async ({ page }) => {
  await page.goto(fixtureUrl("/signup"));
  const password = page.getByLabel("New password", { exact: true });
  await password.fill("fictional private password");
  await page.getByRole("button", { name: "Show new password", exact: true }).click();
  await page.evaluate(() => {
    Object.defineProperty(document, "hidden", { configurable: true, value: false });
    document.dispatchEvent(new Event("visibilitychange"));
  });
  await expect(password).toHaveAttribute("type", "text");
  await page.evaluate(() => {
    Object.defineProperty(document, "hidden", { configurable: true, value: true });
    document.dispatchEvent(new Event("visibilitychange"));
  });
  await expect(password).toHaveAttribute("type", "password");
  await expect(password).toHaveValue("fictional private password");
  await expect(password).toHaveAttribute("autocomplete", "new-password");
  await expect(page.getByRole("button", { name: "Show new password", exact: true }))
    .toHaveAttribute("aria-pressed", "false");
});
