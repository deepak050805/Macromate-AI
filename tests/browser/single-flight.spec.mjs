import { expect, test } from "@playwright/test";
import { fixtureUrl, signIn } from "./helpers.mjs";

for (const kind of ["login", "calculator", "tracking"]) {
  test(`pending forms: ${kind} submits only once while a request is in flight`, async ({ page }) => {
    if (kind === "tracking") await signIn(page);
    await page.goto(fixtureUrl(kind === "tracking" ? "/tracking" : `/${kind}`));
    const selector = kind === "login" ? "form[data-auth]" : `#${kind}-form`;
    if (kind === "login") {
      await page.getByLabel("Email address", { exact: true }).fill("fixture@example.test");
      await page.getByLabel("Password", { exact: true }).fill("fictional browser password");
    } else if (kind === "calculator") {
      await page.getByLabel("Body weight (kg)", { exact: true }).fill("70");
    } else {
      await page.getByLabel("Date (UTC)", { exact: true }).fill("2024-05-01");
      await page.getByLabel("Weight (kg)", { exact: true }).fill("70");
      await page.getByLabel("Calories consumed (kcal)", { exact: true }).fill("2000");
    }
    const endpoint = kind === "login" ? "/api/auth/login"
      : kind === "calculator" ? "/api/macros/calculate" : "/api/tracker/add";
    let requests = 0;
    const pending = Promise.withResolvers();
    await page.route(`**${endpoint}`, async (route) => {
      requests += 1;
      await pending.promise;
      await route.fulfill({
        status: 503,
        contentType: "application/json",
        body: JSON.stringify({ message: "Fixture unavailable." }),
      });
    });
    const form = page.locator(selector);
    await form.evaluate((element) => element.requestSubmit());
    await expect(form.locator('button[type="submit"]')).toBeDisabled();
    await form.evaluate((element) => element.requestSubmit());
    pending.resolve();
    await expect(form.locator(".status")).toHaveText("Fixture unavailable.");
    await page.waitForLoadState("networkidle");
    expect(requests).toBe(1);
    await expect(form.locator('button[type="submit"]')).toBeEnabled();
  });
}
