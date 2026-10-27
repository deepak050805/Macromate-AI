import { expect, test } from "@playwright/test";
import { fixtureUrl } from "./helpers.mjs";

function luminance(color) {
  const channels = color.match(/[\d.]+/g).slice(0, 3).map(Number).map((channel) => {
    const value = channel / 255;
    return value <= 0.04045 ? value / 12.92 : ((value + 0.055) / 1.055) ** 2.4;
  });
  return channels[0] * 0.2126 + channels[1] * 0.7152 + channels[2] * 0.0722;
}
function contrast(first, second) {
  const values = [luminance(first), luminance(second)].sort((a, b) => b - a);
  return (values[0] + 0.05) / (values[1] + 0.05);
}

for (const appearance of ["light", "dark"]) {
  test(`appearance contrast: ${appearance} text, input boundaries and errors remain legible`, async ({ page }) => {
    await page.emulateMedia({ colorScheme: appearance });
    await page.goto(fixtureUrl("/calculator"));
    await page.route("**/api/macros/calculate", (route) => route.fulfill({
      status: 503, contentType: "application/json", body: JSON.stringify({ message: "Try again later." }),
    }));
    await page.getByLabel("Body weight (kg)", { exact: true }).fill("70");
    await page.getByRole("button", { name: "Calculate my targets", exact: true }).click();
    await expect(page.locator("#calculator-status")).toHaveClass(/error/);
    const colors = await page.evaluate(() => {
      const style = (selector) => getComputedStyle(document.querySelector(selector));
      const background = style("html").backgroundColor;
      const card = style(".card").backgroundColor;
      const button = style("#calculator-form button[type=submit]");
      const input = style("#weight");
      return {
        text: [style("body").color, background],
        muted: [style(".page-heading .muted").color, background],
        action: [button.color, button.backgroundColor],
        error: [style("#calculator-status").color, card],
        input: [input.color, input.backgroundColor],
        boundary: [input.borderTopColor, input.backgroundColor],
      };
    });
    for (const [name, pair] of Object.entries(colors))
      expect(contrast(...pair), `${appearance} ${name} contrast`).toBeGreaterThanOrEqual(name === "boundary" ? 3 : 4.5);
  });
}
