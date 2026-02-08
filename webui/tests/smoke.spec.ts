import { test, expect } from "@playwright/test";

const E2E = process.env.E2E === "1";
const CONNECTOR_BASE_URL = process.env.CONNECTOR_BASE_URL ?? "http://localhost:8080";
const SIMULATOR_BASE_URL = process.env.SIMULATOR_BASE_URL ?? "http://localhost:8989";

test.describe("React WebUI smoke", () => {
  test.beforeEach(() => {
    test.skip(!E2E, "Set E2E=1 and run servers locally to enable");
  });

  test("connector loads React UI", async ({ page }) => {
    await page.goto(CONNECTOR_BASE_URL, { waitUntil: "domcontentloaded" });
    await expect(page.getByRole("heading", { name: "Unified OT Connector" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Legacy UI" })).toBeVisible();
  });

  test("simulator loads React UI", async ({ page }) => {
    await page.goto(SIMULATOR_BASE_URL, { waitUntil: "domcontentloaded" });
    await expect(page.getByRole("heading", { name: "OT Simulator" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Legacy UI" })).toBeVisible();
  });
});

