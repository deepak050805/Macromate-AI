import { expect, test } from "@playwright/test";
import { fixtureUrl } from "./helpers.mjs";

test("mobile navigation: disclosure supports keyboard escape and ordinary navigation", async ({ page }) => {
  await page.setViewportSize({ width: 360, height: 800 });
  await page.goto(fixtureUrl("/"));
  const toggle = page.getByRole("button", { name: "Menu", exact: true });
  const navigation = page.getByRole("navigation", { name: "Main navigation" });
  await expect(toggle).toHaveAttribute("aria-expanded", "false");
  await expect(navigation).toBeHidden();
  await toggle.click();
  await expect(navigation).toBeVisible();
  await navigation.getByRole("link", { name: "Calculator", exact: true }).focus();
  await page.keyboard.press("Escape");
  await expect(navigation).toBeHidden();
  await expect(page.locator("#navigation-toggle")).toBeFocused();
  await page.locator("#navigation-toggle").click();
  await navigation.getByRole("link", { name: "Calculator", exact: true }).click();
  await expect(page).toHaveURL(fixtureUrl("/calculator"));
});

test("mobile navigation: breakpoint changes preserve a usable focused control", async ({ page }) => {
  await page.goto(fixtureUrl("/calculator"));
  const navigation = page.getByRole("navigation", { name: "Main navigation" });
  await navigation.getByRole("link", { name: "Calculator", exact: true }).focus();
  await page.setViewportSize({ width: 360, height: 800 });
  await expect(page.locator("#navigation-toggle")).toBeFocused();
  await expect(navigation).toBeHidden();
  await page.setViewportSize({ width: 1280, height: 800 });
  await expect(navigation).toBeVisible();
  await expect(navigation.getByRole("link", { name: "Calculator", exact: true })).toBeFocused();
});

test("mobile navigation: links remain available when JavaScript is disabled", async ({ browser }) => {
  const context = await browser.newContext({ javaScriptEnabled: false, viewport: { width: 320, height: 800 } });
  try {
    const page = await context.newPage();
    await page.goto(fixtureUrl("/"));
    await expect(page.locator("#navigation-toggle")).toBeHidden();
    await expect(page.getByRole("navigation").getByRole("link", { name: "Log in", exact: true })).toBeVisible();
  } finally {
    await context.close();
  }
});
