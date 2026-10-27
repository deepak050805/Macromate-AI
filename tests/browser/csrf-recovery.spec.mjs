import { expect, test } from "@playwright/test";
import { fixtureUrl } from "./helpers.mjs";

test("CSRF recovery: missing page credentials produce reload guidance without sending a mutation", async ({ page }) => {
  await page.goto(fixtureUrl("/calculator"));
  await page.getByLabel("Body weight (kg)", { exact: true }).fill("70");
  await page.locator('meta[name="csrf-token"]').evaluate((element) => element.remove());
  const requests = [];
  page.on("request", (request) => { if (request.method() === "POST") requests.push(request.url()); });
  await page.getByRole("button", { name: "Calculate my targets", exact: true }).click();
  await expect(page.locator("#calculator-status")).toHaveText("Your session expired. Reload the page and try again.");
  await expect(page.getByLabel("Body weight (kg)", { exact: true })).toHaveValue("70");
  await expect(page.getByRole("button", { name: "Calculate my targets", exact: true })).toBeEnabled();
  expect(requests).toEqual([]);
});
