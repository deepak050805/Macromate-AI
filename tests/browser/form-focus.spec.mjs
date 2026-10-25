import { expect, test } from "@playwright/test";
import { fixtureUrl, signIn } from "./helpers.mjs";

async function fillLogin(page) {
  await page.goto(fixtureUrl("/login"));
  await page.getByLabel("Email address", { exact: true }).fill("browser-owner@example.test");
  await page.getByLabel("Password", { exact: true }).fill("fictional browser password");
}

function unavailable(route, message) {
  return route.fulfill({
    status: 503,
    contentType: "application/json",
    body: JSON.stringify({ message }),
  });
}

test("form loading: failed sign-in restores submit focus", async ({ page }) => {
  await fillLogin(page);
  await page.route("**/api/auth/login", (route) => unavailable(route, "Sign-in unavailable."));
  const submit = page.getByRole("button", { name: "Log in", exact: true });
  await submit.focus();
  await page.keyboard.press("Enter");
  await expect(page.locator("form .status")).toHaveText("Sign-in unavailable.");
  await expect(submit).toBeEnabled();
  await expect(submit).toBeFocused();
});

test("form loading: existing disabled controls stay disabled", async ({ page }) => {
  await fillLogin(page);
  await page.locator("form[data-auth]").evaluate((form) => {
    const other = form.ownerDocument.createElement("button");
    other.type = "submit";
    other.textContent = "Unavailable action";
    other.disabled = true;
    form.append(other);
  });
  await page.route("**/api/auth/login", (route) => unavailable(route, "Sign-in unavailable."));
  await page.getByRole("button", { name: "Log in", exact: true }).click();
  await expect(page.locator("form .status")).toHaveText("Sign-in unavailable.");
  await expect(
    page.getByRole("button", { name: "Unavailable action", exact: true }),
  ).toBeDisabled();
});

test("form loading: pending sign-in preserves focus moved elsewhere", async ({ page }) => {
  await fillLogin(page);
  let release;
  const pending = new Promise((resolve) => {
    release = resolve;
  });
  await page.route("**/api/auth/login", async (route) => {
    await pending;
    await unavailable(route, "Sign-in unavailable.");
  });
  const submit = page.getByRole("button", { name: "Log in", exact: true });
  await submit.focus();
  await page.keyboard.press("Enter");
  const email = page.getByLabel("Email address", { exact: true });
  try {
    await expect(submit).toBeDisabled();
    await email.focus();
  } finally {
    release();
  }
  await expect(page.locator("form .status")).toHaveText("Sign-in unavailable.");
  await expect(email).toBeFocused();
});

test("form loading: successful calculation restores submit focus", async ({ page }) => {
  await page.goto(fixtureUrl("/calculator"));
  await page.getByLabel("Body weight (kg)", { exact: true }).fill("70");
  const submit = page.getByRole("button", { name: "Calculate my targets", exact: true });
  await submit.focus();
  await page.keyboard.press("Enter");
  await expect(page.locator("#calculator-results")).toBeVisible();
  await expect(page.locator("#calculator-status")).toContainText("Targets updated:");
  await expect(submit).toBeFocused();
});

test("form loading: failed progress save restores submit focus", async ({ page }) => {
  await signIn(page);
  await page.goto(fixtureUrl("/tracking"));
  await page.getByLabel("Date (UTC)", { exact: true }).fill("2024-03-01");
  await page.getByLabel("Weight (kg)", { exact: true }).fill("70");
  await page.getByLabel("Calories consumed (kcal)", { exact: true }).fill("2000");
  await page.route("**/api/tracker/add", (route) => unavailable(route, "Progress unavailable."));
  const submit = page.getByRole("button", { name: "Save entry", exact: true });
  await submit.focus();
  await page.keyboard.press("Enter");
  await expect(page.locator("#entry-status")).toHaveText("Progress unavailable.");
  await expect(submit).toBeFocused();
  await expect(page.getByLabel("Weight (kg)", { exact: true })).toHaveValue("70");
});
