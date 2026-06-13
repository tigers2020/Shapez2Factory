/**
 * Static terrain layer for Asteroid Lab replay (PR-RENDER-4).
 * Island-local x/y only; no server_coords bridge (FD-2).
 */
(function (global) {
  "use strict";

  const TERRAIN_KINDS = Object.freeze({
    asteroid_fluid_field: true,
    asteroid_shape_field: true,
    internal_void: true,
  });

  const TERRAIN_FILL = Object.freeze({
    asteroid_fluid_field: "rgba(19, 78, 74, 0.72)",
    asteroid_shape_field: "rgba(6, 78, 59, 0.72)",
    internal_void: "rgba(74, 4, 78, 0.72)",
    default: "rgb(2, 6, 23)",
  });

  /** Island-local replay column; ``X==0`` valid (matches solver / replay ``map_view``). */
  const LAB_COORD_FRAME_BUILD = "island_raw_v2";

  function visualCol(x) {
    const xi = Number(x);
    if (!Number.isFinite(xi)) return null;
    return xi;
  }

  function overlayCellKind(cell) {
    if (!cell || typeof cell !== "object") return "";
    if (cell.cell_kind != null) return String(cell.cell_kind);
    if (cell.kind != null) return String(cell.kind);
    return "";
  }

  function isStaticTerrainCell(cell) {
    if (!cell || typeof cell !== "object") return false;
    if (cell.overlay_role != null && String(cell.overlay_role) !== "") {
      return false;
    }
    const ck = overlayCellKind(cell);
    if (TERRAIN_KINDS[ck]) return true;
    return false;
  }

  function terrainFillForCell(cell) {
    const ck = overlayCellKind(cell);
    if (TERRAIN_FILL[ck]) return TERRAIN_FILL[ck];
    return TERRAIN_FILL.default;
  }

  function cellIndexForLayout(cell, layout) {
    if (!layout || typeof layout !== "object") return null;
    const d = visualCol(cell.x);
    if (d == null) return null;
    const yi = Number(cell.y);
    if (!Number.isFinite(yi)) return null;
    const col = d - layout.minD;
    const row = yi - layout.minR;
    const gw = layout.gridW;
    const gh = layout.gridH;
    if (col < 0 || row < 0 || col >= gw || row >= gh) return null;
    return row * gw + col;
  }

  function drawTerrainLayer(ctx, cells, layout, cellPx, gapPx, viewportScale) {
    if (!ctx || !layout) return;
    const px = Math.max(4, Math.round(Number(cellPx) || 20));
    const gap = Math.max(0, Math.round(Number(gapPx) || 0));
    const step = px + gap;
    const gw = layout.gridW;
    const gh = layout.gridH;
    const w = gw * px + Math.max(0, gw - 1) * gap;
    const h = gh * px + Math.max(0, gh - 1) * gap;
    const canvas = ctx.canvas;
    const zoom = Number(viewportScale);
    const viewport = Number.isFinite(zoom) && zoom > 0 ? zoom : 1;
    const dpr = (global.devicePixelRatio || 1) * viewport;
    canvas.style.width = w + "px";
    canvas.style.height = h + "px";
    canvas.width = Math.max(1, Math.round(w * dpr));
    canvas.height = Math.max(1, Math.round(h * dpr));
    ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    ctx.clearRect(0, 0, w, h);
    ctx.fillStyle = TERRAIN_FILL.default;
    ctx.fillRect(0, 0, w, h);
    if (!Array.isArray(cells)) return;
    for (let i = 0; i < cells.length; i++) {
      const cell = cells[i];
      if (!isStaticTerrainCell(cell)) continue;
      const idx = cellIndexForLayout(cell, layout);
      if (idx == null) continue;
      const col = idx % gw;
      const row = Math.floor(idx / gw);
      ctx.fillStyle = terrainFillForCell(cell);
      ctx.fillRect(col * step, row * step, px, px);
    }
  }

  global.LabReplayCanvas = global.LabReplayCanvas || {};
  global.LabReplayCanvas.drawTerrainLayer = drawTerrainLayer;
  global.LabReplayCanvas.isStaticTerrainCell = isStaticTerrainCell;
  global.LabReplayCanvas.terrainFillForCell = terrainFillForCell;
  global.LabReplayCanvas.cellIndexForLayout = cellIndexForLayout;
})(typeof window !== "undefined" ? window : globalThis);
