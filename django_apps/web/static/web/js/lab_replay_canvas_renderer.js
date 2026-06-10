/**
 * Canvas hybrid replay renderer (PR-RENDER-5): overlay + sprite layers.
 * Island-local layout only (FD-2). Attach to window.LabReplayCanvas.
 */
(function (global) {
  "use strict";

  const OVERLAY_FILL_DEFAULT = "rgba(139, 92, 246, 0.28)";

  const OVERLAY_FILL_BY_KIND = Object.freeze({
    space_belt: "rgba(34, 211, 238, 0.38)",
    space_pipe: "rgba(34, 211, 238, 0.38)",
    fluid_miner: "rgba(251, 191, 36, 0.42)",
    shape_miner: "rgba(251, 191, 36, 0.42)",
    fluid_miner_extension: "rgba(252, 211, 77, 0.32)",
    shape_miner_extension: "rgba(252, 211, 77, 0.32)",
    candidate_miner: "rgba(244, 114, 182, 0.35)",
    candidate_transport_stub: "rgba(251, 146, 60, 0.35)",
    candidate_route_path: "rgba(56, 189, 248, 0.35)",
    route_path: "rgba(56, 189, 248, 0.35)",
    route_probe: "rgba(56, 189, 248, 0.3)",
    route_probe_path: "rgba(56, 189, 248, 0.3)",
    confirmed_route: "rgba(74, 222, 128, 0.35)",
    route_goal: "rgba(250, 204, 21, 0.4)",
    inner_field_block: "rgba(167, 139, 250, 0.38)",
    diff_removed: "rgba(239, 68, 68, 0.4)",
    diff_added: "rgba(52, 211, 153, 0.38)",
    diff_changed: "rgba(250, 204, 21, 0.35)",
  });

  function normalizeQuarterTurns(q) {
    const n = Number(q);
    if (!Number.isFinite(n)) return 0;
    return ((Math.trunc(n) % 4) + 4) % 4;
  }

  function rotationToDeg(q) {
    return normalizeQuarterTurns(q) * 90;
  }

  function syncCanvasDimensions(canvas, layout, cellPx, gapPx) {
    if (!canvas || !layout) return { w: 0, h: 0, cellPx: 0, gapPx: 0, step: 0 };
    const px = Math.max(4, Math.round(Number(cellPx) || 20));
    const gap = Math.max(0, Math.round(Number(gapPx) || 0));
    const step = px + gap;
    const gw = layout.gridW;
    const gh = layout.gridH;
    const w = gw * px + Math.max(0, gw - 1) * gap;
    const h = gh * px + Math.max(0, gh - 1) * gap;
    const dpr = global.devicePixelRatio || 1;
    canvas.style.width = w + "px";
    canvas.style.height = h + "px";
    canvas.width = Math.max(1, Math.round(w * dpr));
    canvas.height = Math.max(1, Math.round(h * dpr));
    return { w: w, h: h, cellPx: px, gapPx: gap, step: step, dpr: dpr };
  }

  function applyCanvasTransform(ctx, dims) {
    const dpr = dims.dpr || 1;
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
  }

  function cellTopLeft(idx, layout, step, cellPx) {
    const gw = layout.gridW;
    const col = idx % gw;
    const row = Math.floor(idx / gw);
    return { x: col * step, y: row * step, w: cellPx, h: cellPx };
  }

  function overlayFill(fill, kind) {
    if (fill) return fill;
    if (kind && OVERLAY_FILL_BY_KIND[kind]) return OVERLAY_FILL_BY_KIND[kind];
    return OVERLAY_FILL_DEFAULT;
  }

  function createLabCanvasRenderer(options) {
    const opts = options || {};
    const overlayCanvas = opts.overlayCanvas;
    const spriteCanvas = opts.spriteCanvas;
    let layout = opts.layout;
    let cellPx = opts.cellPx;
    let gapPx = opts.gapPx;
    const spriteBaseUrl = String(opts.spriteBaseUrl || "").replace(/\/?$/, "/");
    const overlayCtx = overlayCanvas ? overlayCanvas.getContext("2d") : null;
    const spriteCtx = spriteCanvas ? spriteCanvas.getContext("2d") : null;
    const imgCache = new Map();
    let dims = { w: 0, h: 0, step: 0, cellPx: 0, gapPx: 0, dpr: 1 };

    function syncSize(nextLayout, nextCellPx, nextGapPx) {
      if (nextLayout) {
        layout = nextLayout;
      }
      if (nextCellPx != null) {
        cellPx = nextCellPx;
      }
      if (nextGapPx != null) {
        gapPx = nextGapPx;
      }
      if (!layout) return dims;
      if (overlayCanvas && overlayCtx) {
        dims = syncCanvasDimensions(overlayCanvas, layout, cellPx, gapPx);
        applyCanvasTransform(overlayCtx, dims);
      }
      if (spriteCanvas && spriteCtx) {
        const sd = syncCanvasDimensions(spriteCanvas, layout, cellPx, gapPx);
        applyCanvasTransform(spriteCtx, sd);
      }
      return dims;
    }

    function clearLayers() {
      if (overlayCtx && overlayCanvas) {
        overlayCtx.clearRect(0, 0, dims.w, dims.h);
      }
      if (spriteCtx && spriteCanvas) {
        spriteCtx.clearRect(0, 0, dims.w, dims.h);
      }
    }

    function drawOverlayCell(entry) {
      if (!overlayCtx || !layout || entry == null || entry.idx == null) return;
      const box = cellTopLeft(entry.idx, layout, dims.step, dims.cellPx);
      overlayCtx.fillStyle = overlayFill(entry.fill, entry.kind);
      overlayCtx.fillRect(box.x, box.y, box.w, box.h);
      if (entry.stroke) {
        overlayCtx.strokeStyle = entry.stroke;
        overlayCtx.lineWidth = 1;
        overlayCtx.strokeRect(box.x + 0.5, box.y + 0.5, box.w - 1, box.h - 1);
      }
    }

    function loadSprite(rel) {
      if (!rel) return null;
      if (imgCache.has(rel)) {
        return imgCache.get(rel);
      }
      const img = new Image();
      img.decoding = "async";
      img.src = spriteBaseUrl + rel;
      imgCache.set(rel, img);
      return img;
    }

    function drawSpriteCell(entry) {
      if (!spriteCtx || !layout || !entry || entry.idx == null || !entry.rel) return;
      const img = loadSprite(entry.rel);
      if (!img) return;
      const draw = function () {
        if (!img.naturalWidth) return;
        const box = cellTopLeft(entry.idx, layout, dims.step, dims.cellPx);
        const cx = box.x + box.w / 2;
        const cy = box.y + box.h / 2;
        const deg = rotationToDeg(entry.rotation);
        spriteCtx.save();
        spriteCtx.translate(cx, cy);
        if (deg !== 0) {
          spriteCtx.rotate((deg * Math.PI) / 180);
        }
        const scale = Math.min(box.w / img.naturalWidth, box.h / img.naturalHeight);
        const dw = img.naturalWidth * scale;
        const dh = img.naturalHeight * scale;
        spriteCtx.drawImage(img, -dw / 2, -dh / 2, dw, dh);
        spriteCtx.restore();
      };
      if (img.complete) {
        draw();
      } else {
        img.addEventListener("load", draw, { once: true });
      }
    }

    function drawFrame(paintPlan) {
      const plan = paintPlan || {};
      syncSize();
      clearLayers();
      const overlays = Array.isArray(plan.overlays) ? plan.overlays : [];
      const sprites = Array.isArray(plan.sprites) ? plan.sprites : [];
      for (let i = 0; i < overlays.length; i++) {
        drawOverlayCell(overlays[i]);
      }
      for (let j = 0; j < sprites.length; j++) {
        drawSpriteCell(sprites[j]);
      }
    }

    function hitTest(wx, wy) {
      if (!layout || !dims.step) return null;
      const gw = layout.gridW;
      const gh = layout.gridH;
      const px = dims.cellPx;
      let x = 0;
      let col = -1;
      for (let c = 0; c < gw; c++) {
        if (wx >= x && wx < x + px) {
          col = c;
          break;
        }
        x += dims.step;
      }
      if (col < 0) return null;
      let y = 0;
      let row = -1;
      for (let r = 0; r < gh; r++) {
        if (wy >= y && wy < y + px) {
          row = r;
          break;
        }
        y += dims.step;
      }
      if (row < 0) return null;
      return row * gw + col;
    }

    function destroy() {
      imgCache.clear();
    }

    syncSize(layout, cellPx, gapPx);

    return {
      drawFrame: drawFrame,
      hitTest: hitTest,
      syncSize: syncSize,
      destroy: destroy,
    };
  }

  global.LabReplayCanvas = global.LabReplayCanvas || {};
  global.LabReplayCanvas.createLabCanvasRenderer = createLabCanvasRenderer;
  global.LabReplayCanvas.overlayFillForKind = function (kind) {
    return overlayFill(null, kind);
  };
})(typeof window !== "undefined" ? window : globalThis);
