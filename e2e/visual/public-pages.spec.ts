import { expect, test } from "@playwright/test";

import { waitForVisualStable } from "./helpers";

test.describe("public pages @visual", () => {
  test("login page layout @visual", async ({ page }) => {
    await page.goto("/accounts/login/");
    await waitForVisualStable(page);
    await expect(page.locator("form[action*='login']")).toBeVisible();
    await expect(page).toHaveScreenshot("login-page.png", { fullPage: true });
  });

  test("support page layout @visual", async ({ page }) => {
    await page.goto("/support/");
    await waitForVisualStable(page);
    await expect(page.locator("#support-heading")).toBeVisible();
    await expect(page).toHaveScreenshot("support-page.png", { fullPage: true });
  });
});
