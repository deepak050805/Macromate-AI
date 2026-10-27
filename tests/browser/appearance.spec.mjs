import { expect, test } from "@playwright/test";
import { fixtureUrl } from "./helpers.mjs";

test("appearance: system preference and explicit choice survive navigation", async ({ page }) => {
  await page.emulateMedia({ colorScheme: "dark" });
  await page.goto(fixtureUrl("/"));
  await expect(page.locator("html")).toHaveCSS("color-scheme", "dark");
  await page.getByLabel("Appearance", { exact: true }).selectOption("light");
  await expect(page.locator("html")).toHaveCSS("color-scheme", "light");
  await page.goto(fixtureUrl("/calculator"));
  await expect(page.getByLabel("Appearance", { exact: true })).toHaveValue("light");
  await expect(page.locator("html")).toHaveCSS("color-scheme", "light");
  await page.getByLabel("Appearance", { exact: true }).selectOption("system");
  await expect(page.locator("html")).toHaveCSS("color-scheme", "dark");
});

test("appearance: storage denial does not prevent changing this document", async ({ page }) => {
  await page.emulateMedia({ colorScheme: "light" });
  await page.addInitScript(() => {
    for (const method of ["getItem", "setItem", "removeItem"])
      Storage.prototype[method] = () => { throw new DOMException("Blocked", "SecurityError"); };
  });
  await page.goto(fixtureUrl("/"));
  await page.getByLabel("Appearance", { exact: true }).selectOption("dark");
  await expect(page.locator("html")).toHaveCSS("color-scheme", "dark");
});

test("appearance: a changed preference propagates to another open tab", async ({ page, context }) => {
  const second = await context.newPage();
  try {
    await page.goto(fixtureUrl("/"));
    await second.goto(fixtureUrl("/calculator"));
    await page.getByLabel("Appearance", { exact: true }).selectOption("dark");
    await expect(second.getByLabel("Appearance", { exact: true })).toHaveValue("dark");
    await expect(second.locator("html")).toHaveCSS("color-scheme", "dark");
  } finally { await second.close(); }
});
