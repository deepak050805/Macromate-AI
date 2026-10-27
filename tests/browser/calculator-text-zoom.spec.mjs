import { expect, test } from "@playwright/test";
import { fixtureUrl } from "./helpers.mjs";

for (const width of [360, 768]) {
  test(`calculator text zoom: maximum targets fit ${width}px at 200% text size`, async ({ page }) => {
    await page.setViewportSize({ width, height: 1100 });
    await page.goto(fixtureUrl("/calculator"));
    await page.evaluate(() => { document.documentElement.style.fontSize = "200%"; });
    await page.getByLabel("Body weight (kg)", { exact: true }).fill("350");
    await page.getByLabel("Your goal", { exact: true }).selectOption("gain");
    await page.getByRole("button", { name: "Calculate my targets", exact: true }).click();
    await expect(page.locator("#calculator-results")).toBeVisible();
    await expect(page.locator("#result-calories")).not.toBeEmpty();
    const geometry = await page.locator(".calorie-target").evaluate((target) => {
      const card = target.closest(".card").getBoundingClientRect();
      const range = document.createRange();
      range.selectNodeContents(target);
      return {
        viewport: window.innerWidth,
        pageWidth: document.documentElement.scrollWidth,
        cardLeft: card.left,
        cardRight: card.right,
        fragments: [...range.getClientRects()].map(({ left, right }) => ({ left, right })),
      };
    });
    expect(geometry.pageWidth).toBeLessThanOrEqual(geometry.viewport);
    for (const fragment of geometry.fragments) {
      expect(fragment.left).toBeGreaterThanOrEqual(geometry.cardLeft);
      expect(fragment.right).toBeLessThanOrEqual(geometry.cardRight);
    }
  });
}
