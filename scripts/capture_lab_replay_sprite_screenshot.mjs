/**
 * Capture Lab replay sprite canvas + stage screenshots.
 * Usage: node scripts/capture_lab_replay_sprite_screenshot.mjs <lab-page-url> [out-dir]
 */
import { chromium } from "playwright";
import fs from "node:fs";
import path from "node:path";

const url = process.argv[2];
const outDir = process.argv[3] || "var/log/lab_replay_sprite_capture";

if (!url) {
  console.error("Usage: node scripts/capture_lab_replay_sprite_screenshot.mjs <lab-page-url> [out-dir]");
  process.exit(2);
}

fs.mkdirSync(outDir, { recursive: true });

const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage({ viewport: { width: 1440, height: 900 } });
  await page.goto(url, { waitUntil: "networkidle", timeout: 120_000 });
  await page.waitForSelector("#lab-replay-sprite-canvas", { timeout: 60_000 });
  await page.waitForSelector("#lab-replay-frames-data", { state: "attached", timeout: 60_000 });

  const meta = await page.evaluate(async () => {
    const frames = JSON.parse(document.getElementById("lab-replay-frames-data").textContent);
    let targetIndex = -1;
    for (let i = frames.length - 1; i >= 0; i--) {
      const ov =
        frames[i] && frames[i].map_view && Array.isArray(frames[i].map_view.overlay_cells)
          ? frames[i].map_view.overlay_cells
          : [];
      if (ov.some((c) => c && (c.kind === "space_belt" || c.kind === "space_pipe") && c.tile_type)) {
        targetIndex = i;
        break;
      }
    }
    if (targetIndex < 0) targetIndex = Math.max(0, frames.length - 1);
    const scrub = document.getElementById("lab-timeline-scrub");
    if (scrub) {
      scrub.value = String(targetIndex);
      scrub.dispatchEvent(new Event("input", { bubbles: true }));
      scrub.dispatchEvent(new Event("change", { bubbles: true }));
    }
    const api = window.AsteroidLabReplay;
    if (api && typeof api.renderReplayFrame === "function") {
      api.renderReplayFrame(frames[targetIndex]);
    }
    await new Promise((r) => setTimeout(r, 1200));
    const canvas = document.getElementById("lab-replay-sprite-canvas");
    const ctx = canvas.getContext("2d");
    const w = canvas.width;
    const h = canvas.height;
    const data = ctx.getImageData(0, 0, w, h).data;
    let opaque = 0;
    for (let i = 3; i < data.length; i += 4) {
      if (data[i] > 0) opaque += 1;
    }
    return {
      frameIndex: targetIndex,
      frameCount: frames.length,
      eventType: frames[targetIndex] && frames[targetIndex].event_type,
      opaquePixels: opaque,
      canvasCss: { w: canvas.style.width, h: canvas.style.height },
      canvasPx: { w, h },
    };
  });

  const stamp = new Date().toISOString().replace(/[:.]/g, "-");
  const base = path.join(outDir, `lab_replay_sprite_${stamp}`);
  await page.screenshot({ path: `${base}_viewport.png`, fullPage: false });
  await page.locator("#lab-replay-grid-stage").screenshot({ path: `${base}_grid_stage.png` });
  await page.locator("#lab-replay-sprite-canvas").screenshot({ path: `${base}_sprite_canvas.png` });
  fs.writeFileSync(`${base}_meta.json`, JSON.stringify(meta, null, 2) + "\n", "utf-8");
  console.log(JSON.stringify({ ok: true, opaquePixels: meta.opaquePixels, paths: { base } }));
  if (!meta.opaquePixels) {
    process.exit(1);
  }
} finally {
  await browser.close();
}
