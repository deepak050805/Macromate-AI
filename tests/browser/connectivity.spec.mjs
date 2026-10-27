import { expect, test } from "@playwright/test";
import { fixtureUrl, signIn } from "./helpers.mjs";

test("connectivity: network changes retain a draft and never replay a mutation", async ({ page, context }) => {
  await signIn(page);
  await page.goto(fixtureUrl("/tracking"));
  await expect(page.locator("#history-status")).not.toContainText("Loading");
  await expect(page.locator("#connection-status")).toBeHidden();
  await page.getByLabel("Weight (kg)", { exact: true }).fill("74");
  const mutations = [];
  page.on("request", (request) => {
    if (request.method() !== "GET") mutations.push(request.url());
  });
  try {
    await context.setOffline(true);
    await expect(page.locator("#connection-status")).toContainText("Your browser is offline");
    await expect(page.getByLabel("Weight (kg)", { exact: true })).toHaveValue("74");
    await context.setOffline(false);
    await expect(page.locator("#connection-status")).toContainText("online again");
    await expect(page.getByLabel("Weight (kg)", { exact: true })).toHaveValue("74");
    expect(mutations).toEqual([]);
  } finally {
    await context.setOffline(false);
  }
});
