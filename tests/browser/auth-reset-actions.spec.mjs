import { expect, test } from "@playwright/test";
import { fixtureUrl } from "./helpers.mjs";

for (const active of ["request-reset", "reset-password"]) {
  test(`reset actions: pending ${active} blocks the conflicting action`, async ({ page }) => {
    await page.goto(fixtureUrl("/reset-password"));
    await page.locator("#request-email").fill("recovery@example.test");
    await page.locator("#reset-email").fill("recovery@example.test");
    await page.locator("#reset-code").fill("123456");
    await page.locator("#new-password").fill("fictional replacement password");

    const pending = Promise.withResolvers();
    const requests = [];
    const other = active === "request-reset" ? "reset-password" : "request-reset";
    for (const endpoint of [active, other]) {
      await page.route(`**/api/auth/${endpoint}`, async (route) => {
        requests.push(endpoint);
        if (endpoint === active) await pending.promise;
        await route.fulfill({
          status: endpoint === "request-reset" ? 202 : 503,
          contentType: "application/json",
          body: JSON.stringify({ message: "Fixture reset response." }),
        });
      });
    }

    const activeForm = page.locator(`form[data-auth="/api/auth/${active}"]`);
    const otherForm = page.locator(`form[data-auth="/api/auth/${other}"]`);
    const activeSubmit = activeForm.locator('button[type="submit"]');
    const otherSubmit = otherForm.locator('button[type="submit"]');
    await activeSubmit.focus();
    await page.keyboard.press("Enter");
    try {
      await expect(activeSubmit).toBeDisabled();
      await expect(otherSubmit).toBeDisabled();
      await expect(activeForm).toHaveAttribute("aria-busy", "true");
      await expect(otherForm).toHaveAttribute("aria-busy", "true");
      await otherForm.evaluate((form) => form.requestSubmit());
    } finally {
      pending.resolve();
    }

    await expect(activeForm.locator(".status")).toHaveText("Fixture reset response.");
    await expect(activeSubmit).toBeEnabled();
    await expect(otherSubmit).toBeEnabled();
    await expect(activeSubmit).toBeFocused();
    await page.waitForLoadState("networkidle");
    expect(requests).toEqual([active]);
    await expect(page.locator("#reset-code")).toHaveValue("123456");
    await expect(page.locator("#new-password")).toHaveValue("fictional replacement password");
    await expect(otherForm.locator(".status")).toBeEmpty();

    await activeForm.evaluate((form) => {
      const button = form.ownerDocument.createElement("button");
      button.type = "submit";
      button.disabled = true;
      button.textContent = "Unavailable reset action";
      form.append(button);
    });
    await otherForm.evaluate((form) => form.requestSubmit());
    await expect(otherForm.locator(".status")).toHaveText("Fixture reset response.");
    await expect(page.getByRole("button", { name: "Unavailable reset action", exact: true }))
      .toBeDisabled();
  });
}
