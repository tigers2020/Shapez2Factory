/**
 * Playwright smoke: Lab replay sprite canvas has non-transparent pixels on transport frame.
 * Usage: node scripts/test_lab_replay_sprite_canvas.mjs <lab-page-url>
 */
import { chromium } from "playwright";

const url = process.argv[2];
if (!url) {
  console.error("Usage: node scripts/test_lab_replay_sprite_canvas.mjs <lab-page-url>");
  process.exit(2);
}

function countSpriteCanvasPixels(page) {
  return page.evaluate(async () => {
    const framesEl = document.getElementById("lab-replay-frames-data");
    if (!framesEl || !framesEl.textContent) {
      return { ok: false, reason: "missing_lab_replay_frames_data" };
    }
    let frames;
    try {
      frames = JSON.parse(framesEl.textContent);
    } catch {
      return { ok: false, reason: "invalid_frames_json" };
    }
    if (!Array.isArray(frames) || !frames.length) {
      return { ok: false, reason: "empty_frames" };
    }
    let targetIndex = -1;
    for (let i = frames.length - 1; i >= 0; i--) {
      const fr = frames[i];
      const ov = fr && fr.map_view && Array.isArray(fr.map_view.overlay_cells) ? fr.map_view.overlay_cells : [];
      if (ov.some((c) => c && (c.kind === "space_belt" || c.kind === "space_pipe") && c.tile_type)) {
        targetIndex = i;
        break;
      }
    }
    if (targetIndex < 0) {
      return { ok: false, reason: "no_transport_sprite_frame" };
    }
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
    await new Promise((r) => setTimeout(r, 800));
    const canvas = document.getElementById("lab-replay-sprite-canvas");
    if (!canvas) {
      return { ok: false, reason: "missing_sprite_canvas" };
    }
    const ctx = canvas.getContext("2d");
    if (!ctx) {
      return { ok: false, reason: "no_sprite_canvas_ctx" };
    }
    const w = canvas.width;
    const h = canvas.height;
    if (!w || !h) {
      return { ok: false, reason: "zero_canvas_dimensions", cssW: canvas.style.width, cssH: canvas.style.height };
    }
    const data = ctx.getImageData(0, 0, w, h).data;
    let opaque = 0;
    for (let i = 3; i < data.length; i += 4) {
      if (data[i] > 0) opaque += 1;
    }
    return {
      ok: opaque > 0,
      reason: opaque > 0 ? "ok" : "sprite_canvas_blank",
      opaquePixels: opaque,
      frameIndex: targetIndex,
      eventType: frames[targetIndex] && frames[targetIndex].event_type,
    };
  });
}

const browser = await chromium.launch({ headless: true });
try {
  const page = await browser.newPage();
  await page.goto(url, { waitUntil: "networkidle", timeout: 120_000 });
  await page.waitForSelector("#lab-replay-sprite-canvas", { timeout: 60_000 });
  await page.waitForSelector("#lab-replay-frames-data", { state: "attached", timeout: 60_000 });
  const result = await countSpriteCanvasPixels(page);
  if (!result.ok) {
    console.error(JSON.stringify(result, null, 2));
    process.exit(1);
  }
  console.log(JSON.stringify(result));
} finally {
  await browser.close();
}
