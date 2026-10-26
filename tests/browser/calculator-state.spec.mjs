import { expect, test } from "@playwright/test";
import { fixtureUrl } from "./helpers.mjs";

for (const [label, body] of [
  ["missing metrics", {}],
  ["string metric", { calories: 2310, protein: "140", carbs: 311.5, fats: 56 }],
  ["null metric", { calories: null, protein: 140, carbs: 311.5, fats: 56 }],
  ["negative metric", { calories: -1, protein: 140, carbs: 311.5, fats: 56 }],
]) {
  test(`calculator response: ${label} never renders as nutrition advice`, async ({ page }) => {
    await page.goto(fixtureUrl("/calculator"));
    await page.route("**/api/macros/calculate", (route) => route.fulfill({
      contentType: "application/json", body: JSON.stringify(body),
    }));
    await page.getByLabel("Body weight (kg)", { exact: true }).fill("70");
    await page.getByRole("button", { name: "Calculate my targets", exact: true }).click();
    await expect(page.locator("#calculator-status")).toHaveText(
      "The server returned an unreadable response. Try again.",
    );
    await expect(page.locator("#calculator-results")).toBeHidden();
  });
}

test("calculator state: changing weight or goal invalidates displayed estimates", async ({ page }) => {
  await page.goto(fixtureUrl("/calculator"));
  const weight = page.getByLabel("Body weight (kg)", { exact: true });
  const submit = page.getByRole("button", { name: "Calculate my targets", exact: true });
  await weight.fill("70");
  await submit.click();
  await expect(page.locator("#calculator-results")).toBeVisible();
  await weight.fill("80");
  await expect(page.locator("#calculator-results")).toBeHidden();
  await expect(page.locator("#calculator-status")).toContainText("Calculate again");
  await submit.click();
  await expect(page.locator("#calculator-results")).toBeVisible();
  await page.getByLabel("Your goal", { exact: true }).selectOption("fat_loss");
  await expect(page.locator("#calculator-results")).toBeHidden();
});

for (const responseStatus of [200, 503]) {
  test(`calculator state: an outdated ${responseStatus} response cannot replace newer inputs`, async ({ page }) => {
    await page.goto(fixtureUrl("/calculator"));
    const pending = Promise.withResolvers();
    await page.route("**/api/macros/calculate", async (route) => {
      await pending.promise;
      await route.fulfill({
        status: responseStatus,
        contentType: "application/json",
        body: JSON.stringify(responseStatus === 200
          ? { calories: 2310, protein: 140, carbs: 311.5, fats: 56 }
          : { message: "Calculator unavailable." }),
      });
    });
    const weight = page.getByLabel("Body weight (kg)", { exact: true });
    const submit = page.getByRole("button", { name: "Calculate my targets", exact: true });
    await weight.fill("70");
    await submit.click();
    try {
      await expect(submit).toBeDisabled();
      await weight.fill("80");
    } finally {
      pending.resolve();
    }
    await expect(submit).toBeEnabled();
    await expect(page.locator("#calculator-results")).toBeHidden();
    await expect(page.locator("#calculator-status")).toHaveText(
      "Inputs changed. Calculate again to update your targets.",
    );
  });
}
