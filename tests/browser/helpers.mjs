import { expect } from "@playwright/test";

export function fixtureUrl(path = "") {
  const base = process.env.BROWSER_TEST_URL;
  if (!/^http:\/\/127\.0\.0\.1:\d+$/.test(base || ""))
    throw new Error("The isolated browser fixture did not publish its loopback URL");
  return `${base}${path}`;
}

export async function signIn(page, email = "browser-owner@example.test") {
  await page.goto(fixtureUrl("/login"));
  await page.getByLabel("Email address", { exact: true }).fill(email);
  await page.getByLabel("Password", { exact: true }).fill("fictional browser password");
  await page.getByRole("button", { name: "Log in", exact: true }).click();
  await expect(page).toHaveURL(fixtureUrl("/dashboard"));
}
