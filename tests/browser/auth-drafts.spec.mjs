import { expect, test } from "@playwright/test";
import { fixtureUrl } from "./helpers.mjs";

for (const editedField of ["request-email", "reset-email"]) {
  test(`reset drafts: a delayed code response preserves edits to ${editedField}`, async ({ page }) => {
    await page.goto(fixtureUrl("/reset-password"));
    await page.locator("#request-email").fill("first@example.test");
    const pending = Promise.withResolvers();
    await page.route("**/api/auth/request-reset", async (route) => {
      await pending.promise;
      await route.fulfill({
        status: 202,
        contentType: "application/json",
        body: JSON.stringify({ message: "Code request accepted." }),
      });
    });
    const submit = page.getByRole("button", { name: "Email a reset code", exact: true });
    await submit.click();
    try {
      await expect(submit).toBeDisabled();
      await page.locator(`#${editedField}`).fill("newer@example.test");
    } finally {
      pending.resolve();
    }
    await expect(submit).toBeEnabled();
    await expect(page.locator(`#${editedField}`)).toHaveValue("newer@example.test");
  });
}

test("reset drafts: an untouched confirmation field receives the requested email", async ({ page }) => {
  await page.goto(fixtureUrl("/reset-password"));
  await page.route("**/api/auth/request-reset", (route) => route.fulfill({
    status: 202,
    contentType: "application/json",
    body: JSON.stringify({ message: "Code request accepted." }),
  }));
  await page.locator("#request-email").fill("first@example.test");
  await page.getByRole("button", { name: "Email a reset code", exact: true }).click();
  await expect(page.locator("#reset-email")).toHaveValue("first@example.test");
});
