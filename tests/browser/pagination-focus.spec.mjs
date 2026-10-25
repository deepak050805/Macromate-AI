import { expect, test } from "@playwright/test";
import { fixtureUrl, signIn } from "./helpers.mjs";

test("pagination: owner retains focus at page boundaries", async ({ page }) => {
  await signIn(page, "browser-pages@example.test");
  await page.goto(fixtureUrl("/tracking"));
  await expect(page.locator("#page-label")).toHaveText("Page 1 of 2");
  await expect(page.locator("#history-rows tr")).toHaveCount(20);
  const next = page.locator("#next-page");
  const previous = page.locator("#previous-page");
  await next.focus();
  await page.keyboard.press("Enter");
  await expect(page.locator("#page-label")).toHaveText("Page 2 of 2");
  await expect(page.locator("#history-rows tr")).toHaveCount(1);
  await expect(page.locator("#history-rows")).toContainText("2024-02-01");
  await expect(previous).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page.locator("#page-label")).toHaveText("Page 1 of 2");
  await expect(next).toBeFocused();
});

test("pagination: administrator retains focus at page boundaries", async ({ page }) => {
  await signIn(page, "browser-admin@example.test");
  await page.goto(fixtureUrl("/admin"));
  await expect(
    page.getByRole("heading", { name: "Registered accounts", exact: true }),
  ).toBeVisible();
  await expect(page.locator("#admin-page")).toHaveText("Page 1 of 2");
  await expect(page.locator("#users-rows tr")).toHaveCount(25);
  const next = page.locator("#admin-next");
  const previous = page.locator("#admin-previous");
  await next.focus();
  await page.keyboard.press("Enter");
  await expect(page.locator("#admin-page")).toHaveText("Page 2 of 2");
  await expect(page.locator("#users-rows tr")).toHaveCount(4);
  await expect(previous).toBeFocused();
  await page.keyboard.press("Enter");
  await expect(page.locator("#admin-page")).toHaveText("Page 1 of 2");
  await expect(next).toBeFocused();
});

test("pagination: failed owner page restores the initiating control", async ({ page }) => {
  await signIn(page, "browser-pages@example.test");
  await page.goto(fixtureUrl("/tracking"));
  await expect(page.locator("#page-label")).toHaveText("Page 1 of 2");
  await page.route(/\/api\/tracker\/history\?page=2$/, (route) =>
    route.fulfill({
      status: 503,
      contentType: "application/json",
      body: JSON.stringify({ message: "History unavailable." }),
    }),
  );
  const next = page.locator("#next-page");
  await next.focus();
  await page.keyboard.press("Enter");
  await expect(page.locator("#history-status")).toHaveText("History unavailable.");
  await expect(page.locator("#page-label")).toHaveText("Page 1 of 2");
  await expect(page.locator("#history-rows tr")).toHaveCount(20);
  await expect(next).toBeFocused();
});

test("pagination: failed administrator page restores the initiating control", async ({ page }) => {
  await signIn(page, "browser-admin@example.test");
  await page.goto(fixtureUrl("/admin"));
  await expect(page.locator("#admin-page")).toHaveText("Page 1 of 2");
  await page.route(/\/api\/auth\/all-users\?page=2$/, (route) =>
    route.fulfill({
      status: 503,
      contentType: "application/json",
      body: JSON.stringify({ message: "Directory unavailable." }),
    }),
  );
  const next = page.locator("#admin-next");
  await next.focus();
  await page.keyboard.press("Enter");
  await expect(page.locator("#admin-status")).toHaveText("Directory unavailable.");
  await expect(page.locator("#admin-page")).toHaveText("Page 1 of 2");
  await expect(page.locator("#users-rows tr")).toHaveCount(25);
  await expect(next).toBeFocused();
});

test("pagination: shrinking history keeps focus when page controls disappear", async ({ page }) => {
  await signIn(page, "browser-pages@example.test");
  await page.goto(fixtureUrl("/tracking"));
  await expect(page.locator("#page-label")).toHaveText("Page 1 of 2");
  await page.route(/\/api\/tracker\/history\?page=[12]$/, (route) => {
    const requested = Number(new URL(route.request().url()).searchParams.get("page"));
    return route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        records:
          requested === 2 ? [] : [{ id: 901, date: "2024-02-21", weight: 70, calories: 2000 }],
        page: requested,
        pages: 1,
        total: 1,
      }),
    });
  });
  await page.locator("#next-page").focus();
  await page.keyboard.press("Enter");
  await expect(page.locator("#page-label")).toHaveText("Page 1 of 1");
  await expect(page.locator("#history-rows tr")).toHaveCount(1);
  await expect(page.locator("#history-pagination")).toBeHidden();
  await expect(page.getByRole("heading", { name: "Progress history", exact: true })).toBeFocused();
});

test("pagination: shrinking directory keeps focus when page controls disappear", async ({
  page,
}) => {
  await signIn(page, "browser-admin@example.test");
  await page.goto(fixtureUrl("/admin"));
  await expect(page.locator("#admin-page")).toHaveText("Page 1 of 2");
  await page.locator("#admin-next").click();
  await expect(page.locator("#admin-page")).toHaveText("Page 2 of 2");
  await page.route(/\/api\/auth\/all-users\?page=1$/, (route) =>
    route.fulfill({
      status: 200,
      contentType: "application/json",
      body: JSON.stringify({
        users: [{ id: 3, email: "browser-admin@example.test", verified: true }],
        page: 1,
        pages: 1,
        total: 1,
      }),
    }),
  );
  await page.locator("#admin-previous").focus();
  await page.keyboard.press("Enter");
  await expect(page.locator("#admin-page")).toHaveText("Page 1 of 1");
  await expect(page.locator("#users-rows tr")).toHaveCount(1);
  await expect(page.locator("#admin-pagination")).toBeHidden();
  await expect(
    page.getByRole("heading", { name: "Registered accounts", exact: true }),
  ).toBeFocused();
});
