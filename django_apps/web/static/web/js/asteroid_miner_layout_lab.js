/**
 * Client-side replay controls for the asteroid mining lab page (shell UI).
 *
 * Shapez2 asteroid map invariant (Lab + server replay):
 * - There is no x == 0 column. Horizontal order: ..., -2, -1, 1, 2, ...
 * - (-1, y) is horizontally adjacent to (1, y), not (0, y).
 * - World (1, 0) is the UI anchor: visual column index 0, row y = 0 at grid center (symmetric padding).
 */
(function () {
  "use strict";

  const GRID_W = 23;
  const GRID_H = 15;

  /** Base cell look; replay grid uses grid cell size instead of h-5 w-5. */
  const LAB_CELL_BASE =
    "lab-cell shrink-0 overflow-hidden rounded-[5px] border bg-slate-950 border-slate-900";

  /** Filenames under ``web/assets/sprites/`` (whitelist for ``tile_type`` → URL). */
  const LAB_SPRITE_KNOWN = new Set([
    "layout_fluid_miner.svg",
    "layout_fluid_miner_extension.svg",
    "space_pipe_forward.svg",
    "space_pipe_left_fwd_merger.svg",
    "space_pipe_left_turn.svg",
    "space_pipe_right_fwd_merger.svg",
    "space_pipe_right_fwd_splitter.svg",
    "space_pipe_right_turn.svg",
    "space_pipe_triple_merger.svg",
    "space_pipe_triple_splitter.svg",
    "space_pipe_y_merger.svg",
  ]);

  /**
   * Blueprint ``R`` is quarter-turns from **East (0)**, **clockwise** on the map; server bundle
   * topology and port dirs use that raw ``R`` (no extra offset).
   *
   * Lab SVG assets are authored with default "forward" toward screen-up; ``LAB_SPRITE_ROTATION_OFFSET_Q``
   * is **CSS sprite art only** — it does not change decode or ``equipment_bundles`` from the API.
   */
  const LAB_SPRITE_ROTATION_OFFSET_Q = 1;

  /** Set in ``init`` from ``#lab-root`` ``data-lab-sprite-base`` (Django ``{% static %}``). */
  let labSpriteBaseUrl = "";

  const rawTotal = window.__ASTEROID_LAB_TOTAL_FRAMES__;
  const TOTAL_FRAMES = Number.isFinite(rawTotal) ? rawTotal : 0;

  /** Extra empty cells beyond union bbox on each side (visual col / row), symmetric around (1,0). */
  const REPLAY_GRID_EDGE_PADDING = 5;

  const LAB_VIEWPORT_MIN_SCALE = 0.35;
  const LAB_VIEWPORT_MAX_SCALE = 3.5;
  const LAB_VIEWPORT_DRAG_THRESHOLD_PX = 6;

  let labViewportInteractionsBound = false;

  function clampNumber(value, min, max) {
    return Math.min(max, Math.max(min, value));
  }

  /** HUD: ``data-overlay-role``, ``data-cell-kind``, ``data-tile-type`` (cleared in ``resetGridBase``). */
  function applyLabCellHudAttributes(el, cell, overlayRoleForAttr) {
    if (!el) return;
    const r =
      overlayRoleForAttr != null && String(overlayRoleForAttr) !== ""
        ? String(overlayRoleForAttr)
        : "";
    if (r) {
      el.setAttribute("data-overlay-role", r);
    } else {
      el.removeAttribute("data-overlay-role");
    }
    if (cell && cell.cell_kind != null) {
      el.setAttribute("data-cell-kind", String(cell.cell_kind));
    } else {
      el.removeAttribute("data-cell-kind");
    }
    if (cell && cell.tile_type != null && String(cell.tile_type) !== "") {
      el.setAttribute("data-tile-type", String(cell.tile_type));
    } else {
      el.removeAttribute("data-tile-type");
    }
  }

  function labSpriteFilenameFromTileType(tileType) {
    const t = tileType == null ? "" : String(tileType);
    if (!t) return null;
    let name = null;
    if (t.startsWith("SpacePipe_")) {
      const rest = t.slice("SpacePipe_".length);
      if (!rest) return null;
      const parts = rest.split("_");
      let slug = "";
      for (let i = 0; i < parts.length; i++) {
        slug += (i ? "_" : "") + String(parts[i]).toLowerCase();
      }
      name = "space_pipe_" + slug + ".svg";
    } else if (t === "Layout_FluidMiner") {
      name = "layout_fluid_miner.svg";
    } else if (t === "Layout_FluidMinerExtension") {
      name = "layout_fluid_miner_extension.svg";
    }
    if (!name || !LAB_SPRITE_KNOWN.has(name)) return null;
    return name;
  }

  function clearLabCellSprite(el) {
    el.style.backgroundImage = "";
    el.style.backgroundSize = "";
    el.style.backgroundPosition = "";
    el.style.backgroundRepeat = "";
    el.style.transform = "";
    el.removeAttribute("data-lab-sprite");
  }

  function applyLabCellSprite(el, cell) {
    clearLabCellSprite(el);
    if (!labSpriteBaseUrl || !cell || typeof cell !== "object") return;
    const fn = labSpriteFilenameFromTileType(cell.tile_type);
    if (!fn) return;
    const base = String(labSpriteBaseUrl).replace(/\/?$/, "/");
    const url = base + fn;
    el.style.backgroundImage = 'url("' + url.replace(/\\/g, "\\\\").replace(/"/g, '\\"') + '")';
    el.style.backgroundSize = "contain";
    el.style.backgroundPosition = "center";
    el.style.backgroundRepeat = "no-repeat";
    const rot = Number(cell.rotation);
    const q = Number.isFinite(rot) ? ((Math.trunc(rot) % 4) + 4) % 4 : 0;
    const displayQ = (q + LAB_SPRITE_ROTATION_OFFSET_Q) % 4;
    // Blueprint R: quarter-turns from East (0), clockwise. CSS rotate(+) is clockwise on screen.
    if (displayQ !== 0) {
      el.style.transform = "rotate(" + String(displayQ * 90) + "deg)";
    }
    el.setAttribute("data-lab-sprite", fn);
  }

  function readJsonScript(id) {
    const el = document.getElementById(id);
    if (!el || !el.textContent) {
      return null;
    }
    try {
      return JSON.parse(el.textContent);
    } catch {
      return null;
    }
  }

  function getCookie(name) {
    const prefix = "; " + name + "=";
    const raw = document.cookie;
    const start = raw.indexOf(prefix);
    if (start < 0) {
      return "";
    }
    const from = start + prefix.length;
    const end = raw.indexOf(";", from);
    const token = end < 0 ? raw.substring(from) : raw.substring(from, end);
    try {
      return decodeURIComponent(token);
    } catch {
      return token;
    }
  }

  function replayPhaseForFrame(frame) {
    if (frame < 40) return "Decode + Reconstruction";
    if (frame < 90) return "Candidate Expansion";
    if (frame < 150) return "Route Feasibility";
    return "Final Validation";
  }

  function replayOverlayForFrame(frame) {
    if (frame < 90) return "candidates";
    if (frame < 150) return "routes";
    return "confirmed";
  }

  function overlayIndex(overlay) {
    if (overlay === "routes") return 1;
    if (overlay === "confirmed") return 2;
    return 0;
  }

  /** World x to dense column index (no x===0); mirrors server_coords.raw_x_to_dense_x. */
  function rawXToDenseX(x) {
    const xi = Number(x);
    if (!Number.isFinite(xi) || xi === 0) return null;
    if (xi < 0) return Math.floor((xi + 1) / 2);
    return Math.floor((xi - 1) / 2) + 1;
  }

  /** World x to dense visual column; x === 0 is invalid (null). Legacy Lab anchor. */
  function visualCol(x) {
    const xi = Number(x);
    if (!Number.isFinite(xi)) return null;
    if (xi === 0) return null;
    if (xi < 0) return xi;
    return xi - 1;
  }

  function cellIndexDemo(x, y) {
    const xi = Number(x);
    const yi = Number(y);
    if (!Number.isFinite(xi) || !Number.isFinite(yi)) return null;
    if (xi < 0 || yi < 0 || xi >= GRID_W || yi >= GRID_H) return null;
    return yi * GRID_W + xi;
  }

  function pushCellList(out, list, defaultRole) {
    if (!Array.isArray(list)) return;
    for (let i = 0; i < list.length; i++) {
      const c = list[i];
      if (!c || typeof c !== "object") continue;
      const role = c.overlay_role != null ? String(c.overlay_role) : defaultRole;
      if (role) {
        out.push({ cell: c, role: role });
      } else {
        out.push({ cell: c, role: "" });
      }
    }
  }

  function pushFromComponentBlocks(out, blocks, roleForCells) {
    if (!Array.isArray(blocks)) return;
    for (let j = 0; j < blocks.length; j++) {
      const block = blocks[j];
      if (!block || typeof block !== "object") continue;
      if (Array.isArray(block.cells)) {
        pushCellList(out, block.cells, roleForCells);
      } else if (block.x != null && block.y != null) {
        out.push({ cell: block, role: roleForCells });
      }
    }
  }

  function fullMapCellsFromFrame(frame) {
    if (!frame || typeof frame !== "object") return [];
    if (Array.isArray(frame.full_map) && frame.full_map.length) return frame.full_map;
    const p = frame.frame_payload;
    if (p && typeof p === "object") {
      const nested = p.full_map;
      if (Array.isArray(nested) && nested.length) return nested;
    }
    const ov = frame.cell_overlay_json;
    if (ov && typeof ov === "object" && Array.isArray(ov.cells) && ov.cells.length) return ov.cells;
    return [];
  }

  function frameDiffFromFrame(frame) {
    if (!frame || typeof frame !== "object") return null;
    let d = frame.diff;
    if (d && typeof d === "object") return d;
    const p = frame.frame_payload;
    if (p && typeof p === "object" && p.diff && typeof p.diff === "object") return p.diff;
    return null;
  }

  function pushDiffCells(out, arr, role) {
    if (!Array.isArray(arr)) return;
    for (let i = 0; i < arr.length; i++) {
      const c = arr[i];
      if (!c || typeof c !== "object") continue;
      out.push({ cell: c, role: role });
    }
  }

  function collectDiffPaintTargets(frame) {
    const out = [];
    if (!frame || typeof frame !== "object") return out;
    const d = frameDiffFromFrame(frame);
    if (!d || typeof d !== "object") return out;
    pushDiffCells(out, d.removed, "diff_removed");
    pushDiffCells(out, d.added, "diff_added");
    const ch = d.changed;
    if (!Array.isArray(ch)) return out;
    for (let i = 0; i < ch.length; i++) {
      const item = ch[i];
      if (item && typeof item === "object" && item.after) {
        out.push({ cell: item.after, role: "diff_changed" });
      }
    }
    return out;
  }

  function collectFrameSpatialTargets(frame) {
    const out = [];
    pushCellList(out, fullMapCellsFromFrame(frame), "");
    const diffT = collectDiffPaintTargets(frame);
    for (let i = 0; i < diffT.length; i++) out.push(diffT[i]);
    return out;
  }

  /** Collect drawable cells from tolerant overlay shapes (decode / existing_layout). */
  function collectOverlayPaintTargets(overlay) {
    const out = [];
    if (!overlay || typeof overlay !== "object") return out;

    pushCellList(out, overlay.cells, "");
    pushCellList(out, overlay.equipment_cells, "equipment");
    pushCellList(out, overlay.equipment, "equipment");
    pushCellList(out, overlay.adjacent_transport, "adjacent_transport");
    pushFromComponentBlocks(out, overlay.components, "transport");
    pushFromComponentBlocks(out, overlay.transport_components, "transport");
    pushCellList(out, overlay.transport, "transport");

    const main = overlay.main_component_candidate;
    if (main && typeof main === "object") {
      if (Array.isArray(main.cells_json)) {
        pushCellList(out, main.cells_json, "main_component");
      } else if (main.x != null && main.y != null) {
        out.push({ cell: main, role: "main_component" });
      }
    }
    pushCellList(out, overlay.cleanup_candidate_cells, "cleanup_candidate");

    const handled = new Set([
      "cells",
      "equipment_cells",
      "equipment",
      "adjacent_transport",
      "components",
      "transport_components",
      "transport",
      "main_component_candidate",
      "cleanup_candidate_cells",
    ]);
    const keys = Object.keys(overlay);
    for (let k = 0; k < keys.length; k++) {
      const key = keys[k];
      if (handled.has(key)) continue;
      const val = overlay[key];
      if (val && typeof val === "object" && !Array.isArray(val) && Array.isArray(val.cells_json)) {
        pushCellList(out, val.cells_json, key);
      }
    }
    return out;
  }

  function computeReplayGridLayout(replayFrames) {
    /* Lab grid uses ``visualCol`` (raw world X/Y) only. ``server_x``/``server_y`` on cells are for
     * backend/fingerprint; mapping them to pixel columns via dense inverse makes X step by 2 on
     * the positive side, which is confusing in this UI.
     */
    let minD = Infinity;
    let maxD = -Infinity;
    let minR = Infinity;
    let maxR = -Infinity;
    let any = false;
    for (let fi = 0; fi < replayFrames.length; fi++) {
      const fr = replayFrames[fi];
      if (!fr || typeof fr !== "object") continue;
      const targets = collectFrameSpatialTargets(fr);
      for (let ti = 0; ti < targets.length; ti++) {
        const cell = targets[ti].cell;
        if (!cell || typeof cell !== "object") continue;
        const d = visualCol(cell.x);
        if (d == null) continue;
        const yi = Number(cell.y);
        if (!Number.isFinite(yi)) continue;
        any = true;
        if (d < minD) minD = d;
        if (d > maxD) maxD = d;
        if (yi < minR) minR = yi;
        if (yi > maxR) maxR = yi;
      }
    }
    if (!any) {
      minD = maxD = minR = maxR = 0;
    }
    const coreHalfX = Math.max(Math.max(0, -minD), Math.max(0, maxD), 1);
    const coreHalfY = Math.max(Math.max(0, -minR), Math.max(0, maxR), 1);
    const halfX = coreHalfX + REPLAY_GRID_EDGE_PADDING;
    const halfY = coreHalfY + REPLAY_GRID_EDGE_PADDING;
    return {
      minD: -halfX,
      maxD: halfX,
      minR: -halfY,
      maxR: halfY,
      gridW: 2 * halfX + 1,
      gridH: 2 * halfY + 1,
    };
  }

  function overlayToneClasses(role, cell) {
    const r = String(role || "");
    if (r === "equipment" || r === "equipment_cells") {
      return "ring-1 ring-inset ring-amber-400/50 bg-amber-950/20";
    }
    if (r === "transport" || r === "adjacent_transport" || r === "main_component") {
      return "ring-1 ring-inset ring-cyan-400/40 bg-cyan-950/20";
    }
    if (r === "cleanup_candidate") {
      return "ring-1 ring-inset ring-orange-400/45 bg-orange-950/20";
    }
    if (r === "decode") {
      return "lab-decode-cell-tone";
    }
    return "ring-1 ring-inset ring-violet-400/35 bg-violet-950/15";
  }

  function toneForFullMapCell(cell) {
    const ck = cell && cell.cell_kind != null ? String(cell.cell_kind) : "";
    if (ck === "space_pipe" || ck === "space_belt") {
      return "ring-1 ring-inset ring-cyan-400/40 bg-cyan-950/20";
    }
    if (ck === "fluid_miner" || ck === "shape_miner") {
      return "ring-1 ring-inset ring-amber-400/50 bg-amber-950/20";
    }
    if (ck === "fluid_miner_extension" || ck === "shape_miner_extension") {
      return "ring-1 ring-inset ring-amber-300/40 bg-amber-950/12";
    }
    if (ck === "asteroid_fluid_field") {
      return "ring-1 ring-inset ring-teal-400/50 bg-teal-950/28";
    }
    if (ck === "asteroid_shape_field") {
      return "ring-1 ring-inset ring-emerald-400/50 bg-emerald-950/28";
    }
    return overlayToneClasses("", cell);
  }

  function toneForDiffRole(role) {
    const r = String(role || "");
    if (r === "diff_removed") {
      return "opacity-75 ring-1 ring-inset ring-red-500/70 bg-red-950/35";
    }
    if (r === "diff_added") {
      return "ring-1 ring-inset ring-emerald-400/55 bg-emerald-950/25";
    }
    if (r === "diff_changed") {
      return "ring-1 ring-inset ring-yellow-400/50 bg-yellow-950/20";
    }
    return "";
  }

  function renderFullMapCells(baseClasses, domCells, cells, resolveCellIndex) {
    if (!Array.isArray(cells)) return;
    for (let i = 0; i < cells.length; i++) {
      const cell = cells[i];
      if (!cell || typeof cell !== "object") continue;
      const idx = resolveCellIndex(cell);
      if (idx == null || idx < 0 || idx >= domCells.length) continue;
      const base = baseClasses[idx] || "";
      const tone = toneForFullMapCell(cell);
      const el = domCells[idx];
      el.className = base + " " + tone;
      applyLabCellHudAttributes(
        el,
        cell,
        cell.overlay_role != null ? String(cell.overlay_role) : "",
      );
      applyLabCellSprite(el, cell);
    }
  }

  function renderDiffOverlays(baseClasses, domCells, frame, resolveCellIndex) {
    const targets = collectDiffPaintTargets(frame);
    for (let i = 0; i < targets.length; i++) {
      const cell = targets[i].cell;
      const role = targets[i].role;
      const idx = resolveCellIndex(cell);
      if (idx == null || idx < 0 || idx >= domCells.length) continue;
      const tone = toneForDiffRole(role);
      if (!tone) continue;
      const base = baseClasses[idx] || "";
      const el = domCells[idx];
      el.className = base + " " + tone;
      applyLabCellHudAttributes(el, cell, role);
      applyLabCellSprite(el, cell);
    }
  }

  /** Bright per-bundle stroke on outer edges (``equipment_bundles`` from replay overlay). */
  var BUNDLE_EDGE_PALETTE = [
    { n: "border-t-2 border-t-yellow-300", e: "border-r-2 border-r-yellow-300", s: "border-b-2 border-b-yellow-300", w: "border-l-2 border-l-yellow-300" },
    { n: "border-t-2 border-t-lime-300", e: "border-r-2 border-r-lime-300", s: "border-b-2 border-b-lime-300", w: "border-l-2 border-l-lime-300" },
    { n: "border-t-2 border-t-cyan-300", e: "border-r-2 border-r-cyan-300", s: "border-b-2 border-b-cyan-300", w: "border-l-2 border-l-cyan-300" },
    { n: "border-t-2 border-t-fuchsia-300", e: "border-r-2 border-r-fuchsia-300", s: "border-b-2 border-b-fuchsia-300", w: "border-l-2 border-l-fuchsia-300" },
    { n: "border-t-2 border-t-orange-300", e: "border-r-2 border-r-orange-300", s: "border-b-2 border-b-orange-300", w: "border-l-2 border-l-orange-300" },
    { n: "border-t-2 border-t-sky-300", e: "border-r-2 border-r-sky-300", s: "border-b-2 border-b-sky-300", w: "border-l-2 border-l-sky-300" },
  ];

  /** Inset fill per bundle id (paired with ``BUNDLE_EDGE_PALETTE``); not Tailwind — avoids purge. */
  var BUNDLE_FILL_INSET_RGBA = [
    "rgba(253, 224, 71, 0.14)",
    "rgba(190, 242, 100, 0.14)",
    "rgba(103, 232, 249, 0.14)",
    "rgba(240, 171, 252, 0.14)",
    "rgba(254, 215, 170, 0.14)",
    "rgba(125, 211, 252, 0.14)",
  ];

  function cellOverlayJsonFromFrame(frame) {
    if (!frame || typeof frame !== "object") return null;
    var top = frame.cell_overlay_json;
    if (top && typeof top === "object") return top;
    var p = frame.frame_payload;
    if (p && typeof p === "object" && p.cell_overlay_json && typeof p.cell_overlay_json === "object") {
      return p.cell_overlay_json;
    }
    return null;
  }

  /** ``cell_overlay_json`` shape: ``{ equipment_bundles: [ { bundle_id, cells_json } ] }``. */
  function applyEquipmentBundleGroupVisualsFromOverlay(ov, domCells, resolveCellIndex) {
    if (!ov || typeof ov !== "object") return;
    var bundles = ov.equipment_bundles;
    if (!Array.isArray(bundles) || bundles.length === 0) return;
    for (var bi = 0; bi < bundles.length; bi++) {
      var block = bundles[bi];
      if (!block || typeof block !== "object") continue;
      var bid = Number(block.bundle_id);
      var pi = (Number.isFinite(bid) ? bid - 1 : 0) % BUNDLE_EDGE_PALETTE.length;
      if (pi < 0) pi = 0;
      var colors = BUNDLE_EDGE_PALETTE[pi];
      var fillRgba = BUNDLE_FILL_INSET_RGBA[pi % BUNDLE_FILL_INSET_RGBA.length];
      var cells = block.cells_json;
      if (!Array.isArray(cells)) continue;
      for (var ci = 0; ci < cells.length; ci++) {
        var cell = cells[ci];
        if (!cell || typeof cell !== "object") continue;
        var idx = resolveCellIndex(cell);
        if (idx == null || idx < 0 || idx >= domCells.length) continue;
        var el = domCells[idx];
        el.style.boxShadow = "inset 0 0 0 9999px " + fillRgba;
        var edges = cell.bundle_edges != null ? String(cell.bundle_edges) : "";
        var parts = [];
        if (edges.indexOf("n") >= 0) parts.push(colors.n);
        if (edges.indexOf("e") >= 0) parts.push(colors.e);
        if (edges.indexOf("s") >= 0) parts.push(colors.s);
        if (edges.indexOf("w") >= 0) parts.push(colors.w);
        if (parts.length) {
          el.className = el.className + " " + parts.join(" ");
        }
      }
    }
  }

  function applyEquipmentBundleStrokeClasses(frame, domCells, resolveCellIndex) {
    applyEquipmentBundleGroupVisualsFromOverlay(cellOverlayJsonFromFrame(frame), domCells, resolveCellIndex);
  }

  function renderDecodedCells(baseClasses, domCells, cells, resolveCellIndex) {
    if (!Array.isArray(cells)) return;
    const targets = [];
    pushCellList(targets, cells, "");
    for (let i = 0; i < targets.length; i++) {
      const cell = targets[i].cell;
      const role = targets[i].role;
      const idx = resolveCellIndex(cell);
      if (idx == null || idx < 0 || idx >= domCells.length) continue;
      const base = baseClasses[idx] || "";
      const tone = overlayToneClasses("decode", cell);
      const el = domCells[idx];
      el.className = base + " " + tone;
      applyLabCellHudAttributes(el, cell, role != null ? String(role) : "");
      applyLabCellSprite(el, cell);
    }
  }

  function renderExistingLayoutOverlay(baseClasses, domCells, overlay, resolveCellIndex) {
    const targets = collectOverlayPaintTargets(overlay);
    for (let i = 0; i < targets.length; i++) {
      const cell = targets[i].cell;
      const role = targets[i].role;
      const idx = resolveCellIndex(cell);
      if (idx == null || idx < 0 || idx >= domCells.length) continue;
      const base = baseClasses[idx] || "";
      const tone = overlayToneClasses(role, cell);
      const el = domCells[idx];
      el.className = base + " " + tone;
      applyLabCellHudAttributes(el, cell, role != null ? String(role) : "");
      applyLabCellSprite(el, cell);
    }
  }

  function renderCellOverlay(baseClasses, domCells, overlay, resolveCellIndex) {
    if (!overlay || typeof overlay !== "object") return;
    const cells = overlay.cells;
    if (Array.isArray(cells) && cells.length > 0) {
      renderDecodedCells(baseClasses, domCells, cells, resolveCellIndex);
      applyEquipmentBundleGroupVisualsFromOverlay(overlay, domCells, resolveCellIndex);
      return;
    }
    renderExistingLayoutOverlay(baseClasses, domCells, overlay, resolveCellIndex);
    applyEquipmentBundleGroupVisualsFromOverlay(overlay, domCells, resolveCellIndex);
  }

  function resetGridBase(domCells, baseClasses) {
    for (let i = 0; i < domCells.length; i++) {
      domCells[i].className = baseClasses[i] || "";
      domCells[i].style.boxShadow = "";
      domCells[i].removeAttribute("data-cell-kind");
      domCells[i].removeAttribute("data-overlay-role");
      domCells[i].removeAttribute("data-tile-type");
      clearLabCellSprite(domCells[i]);
    }
  }

  function renderReplayFrame(frame, baseClasses, domCells, resolveCellIndex) {
    resetGridBase(domCells, baseClasses);
    if (!frame || typeof frame !== "object") return;
    const fm = fullMapCellsFromFrame(frame);
    if (fm.length) {
      renderFullMapCells(baseClasses, domCells, fm, resolveCellIndex);
      renderDiffOverlays(baseClasses, domCells, frame, resolveCellIndex);
      applyEquipmentBundleStrokeClasses(frame, domCells, resolveCellIndex);
      return;
    }
    const ov = frame.cell_overlay_json;
    if (ov && typeof ov === "object") {
      renderCellOverlay(baseClasses, domCells, ov, resolveCellIndex);
    }
  }

  function updateFrameInfo(frame, totalCount, phaseEl, frameEl, gridEl) {
    const dash = "—";
    if (!frame || typeof frame !== "object") {
      if (phaseEl) phaseEl.textContent = dash;
      const et = document.getElementById("lab-replay-event-type");
      const ti = document.getElementById("lab-replay-title");
      const de = document.getElementById("lab-replay-description");
      if (et) et.textContent = dash;
      if (ti) ti.textContent = dash;
      if (de) de.textContent = dash;
      if (frameEl) frameEl.textContent = "0 / " + String(totalCount);
      return;
    }
    if (phaseEl) phaseEl.textContent = frame.phase != null ? String(frame.phase) : dash;
    const et = document.getElementById("lab-replay-event-type");
    const ti = document.getElementById("lab-replay-title");
    const de = document.getElementById("lab-replay-description");
    if (et) et.textContent = frame.event_type ? String(frame.event_type) : dash;
    if (ti) ti.textContent = frame.title != null ? String(frame.title) : dash;
    if (de) de.textContent = frame.description != null ? String(frame.description) : dash;
    const denom = Number.isFinite(totalCount) ? totalCount : 0;
    const fi = frame.frame_index != null ? String(frame.frame_index) : "?";
    if (frameEl) frameEl.textContent = fi + " / " + String(denom);
    if (gridEl) gridEl.dataset.overlay = frame.frame_key ? String(frame.frame_key) : "";
  }

  function init() {
    const matrix = readJsonScript("lab-cell-overlay-matrix-data");
    const runs = readJsonScript("lab-runs-data");
    const uiInitial = readJsonScript("lab-ui-initial-state");
    const replayFramesRaw = readJsonScript("lab-replay-frames-data");
    let replayFrames = Array.isArray(replayFramesRaw) ? replayFramesRaw : [];
    let hasServerReplay = replayFrames.length > 0;
    let initialFromServer = Object.assign(
      {},
      uiInitial && typeof uiInitial === "object" ? uiInitial : {},
    );

    const gridViewport = document.getElementById("lab-replay-grid-viewport");
    const cells = document.querySelectorAll("[data-lab-cell-index]");
    const phaseEl = document.getElementById("lab-replay-phase");
    const frameEl = document.getElementById("lab-frame-display");
    const gridEl = document.getElementById("lab-replay-grid");
    const playBtn = document.getElementById("lab-timeline-play");
    const playIcon = document.getElementById("lab-timeline-play-icon");
    const pauseIcon = document.getElementById("lab-timeline-pause-icon");
    const modal = document.getElementById("lab-topology-modal");
    const openTopology = document.getElementById("lab-open-topology");
    const closeTopology = document.getElementById("lab-close-topology");
    const blueprintInput = document.getElementById("lab-blueprint-input");

    if (!gridEl) {
      return;
    }

    const gridStage = document.getElementById("lab-replay-grid-stage");
    const gridHudCoord = document.getElementById("lab-replay-grid-hud-coord");
    const gridHudRole = document.getElementById("lab-replay-grid-hud-role");

    let labViewportTransform = { scale: 1, tx: 0, ty: 0 };
    let labPanState = null;

    function applyLabViewportTransform() {
      if (!gridStage) {
        return;
      }
      const t = labViewportTransform;
      gridStage.style.transformOrigin = "0 0";
      gridStage.style.transform = "translate(" + t.tx + "px, " + t.ty + "px) scale(" + t.scale + ")";
    }

    function resetLabViewportTransform() {
      labViewportTransform = { scale: 1, tx: 0, ty: 0 };
      applyLabViewportTransform();
    }

    let domCells;
    let baseClasses;
    let resolveCellIndex = function (cell) {
      if (!cell || typeof cell !== "object") return null;
      return cellIndexDemo(cell.x, cell.y);
    };
    let replayLayout = null;
    let resizeObserver = null;
    let replayResizeMode = null;
    let replayCleanup = function () {};

    function initializeServerReplaySurface(framesArr) {
      const neutralClass = LAB_CELL_BASE;
      replayLayout = computeReplayGridLayout(framesArr);
      const gw = replayLayout.gridW;
      const gh = replayLayout.gridH;
      gridEl.textContent = "";
      for (let i = 0; i < gw * gh; i++) {
        const div = document.createElement("div");
        div.setAttribute("data-lab-cell-index", String(i));
        div.className = neutralClass;
        gridEl.appendChild(div);
      }
      domCells = Array.prototype.slice.call(gridEl.querySelectorAll("[data-lab-cell-index]"));
      baseClasses = domCells.map(function (el) {
        return String(el.className || "");
      });

      resolveCellIndex = function (cell) {
        if (!cell || typeof cell !== "object") return null;
        const gw = replayLayout.gridW;
        const gh = replayLayout.gridH;
        const d = visualCol(cell.x);
        if (d == null) return null;
        const yi = Number(cell.y);
        if (!Number.isFinite(yi)) return null;
        const col = d - replayLayout.minD;
        const row = yi - replayLayout.minR;
        if (col < 0 || row < 0 || col >= gw || row >= gh) return null;
        return row * gw + col;
      };

      const padPx = 16;
      const minCell = 4;
      const maxCell = 28;

      function applyReplayGridSizing() {
        if (!gridViewport || !replayLayout) return;
        const cw = gridViewport.clientWidth - padPx * 2;
        const ch = gridViewport.clientHeight - padPx * 2;
        const px = Math.max(
          minCell,
          Math.min(maxCell, Math.floor(Math.min(cw / replayLayout.gridW, ch / replayLayout.gridH))),
        );
        gridEl.style.gridTemplateColumns = "repeat(" + replayLayout.gridW + ", minmax(0, " + px + "px))";
        gridEl.style.gridTemplateRows = "repeat(" + replayLayout.gridH + ", minmax(0, " + px + "px))";
      }

      function labReplayViewportOnWindowResize() {
        applyReplayGridSizing();
        resetLabViewportTransform();
      }

      applyReplayGridSizing();
      resizeObserver = null;
      replayResizeMode = null;
      if (gridViewport && typeof ResizeObserver !== "undefined") {
        resizeObserver = new ResizeObserver(function () {
          applyReplayGridSizing();
          resetLabViewportTransform();
        });
        resizeObserver.observe(gridViewport);
        replayResizeMode = "observer";
      } else if (gridViewport) {
        window.addEventListener("resize", labReplayViewportOnWindowResize);
        replayResizeMode = "window";
      }

      return function cleanupReplaySurface() {
        if (replayResizeMode === "observer" && resizeObserver) {
          try {
            resizeObserver.disconnect();
          } catch (e) {
            /* ignore */
          }
          resizeObserver = null;
        }
        if (replayResizeMode === "window" && gridViewport) {
          window.removeEventListener("resize", labReplayViewportOnWindowResize);
        }
        replayResizeMode = null;
      };
    }

    if (hasServerReplay) {
      if (!matrix || !Array.isArray(matrix)) {
        return;
      }
      replayCleanup = initializeServerReplaySurface(replayFrames);
    } else {
      if (!matrix || !Array.isArray(matrix) || cells.length !== matrix.length) {
        return;
      }
      domCells = Array.prototype.slice.call(cells);
      baseClasses = domCells.map(function (el) {
        return String(el.className || "");
      });
    }

    const rootEl = document.getElementById("lab-root");
    labSpriteBaseUrl =
      rootEl && rootEl.dataset && rootEl.dataset.labSpriteBase != null
        ? String(rootEl.dataset.labSpriteBase)
        : "";
    const parseFrame = function (v, fallback) {
      const n = parseInt(String(v), 10);
      return Number.isNaN(n) ? fallback : n;
    };
    const datasetFrame = parseFrame(rootEl?.dataset.labInitialFrame, 0);
    let baselineFrame = parseFrame(initialFromServer.frame, datasetFrame);
    let baselineBlueprint =
      typeof initialFromServer.blueprintCode === "string"
        ? initialFromServer.blueprintCode
        : blueprintInput
          ? String(blueprintInput.value)
          : "";
    const baselineRun =
      initialFromServer.defaultRun && typeof initialFromServer.defaultRun === "object"
        ? initialFromServer.defaultRun
        : Array.isArray(runs) && runs.length
          ? runs[0]
          : null;
    const baselineRunId =
      typeof initialFromServer.defaultRunId === "string"
        ? initialFromServer.defaultRunId
        : baselineRun && baselineRun.id
          ? String(baselineRun.id)
          : null;

    function replaySlotForServerInitialFrame() {
      if (!hasServerReplay || !replayFrames.length) return 0;
      const wantFi = parseFrame(initialFromServer.frame, datasetFrame);
      let i = 0;
      for (; i < replayFrames.length; i++) {
        const fr = replayFrames[i];
        if (!fr || typeof fr !== "object") continue;
        const fi = Number(fr.frame_index);
        if (Number.isFinite(fi) && fi === wantFi) {
          return i;
        }
      }
      for (let j = 0; j < replayFrames.length; j++) {
        if (fullMapCellsFromFrame(replayFrames[j]).length) {
          return j;
        }
      }
      return 0;
    }

    let frame = baselineFrame;
    let isPlaying = false;
    let timerId = null;

    let replayArrayIndex = replaySlotForServerInitialFrame();

    function getCurrentReplayFrame() {
      if (!hasServerReplay) return null;
      return replayFrames[replayArrayIndex] || null;
    }

    function applyFrame() {
      if (hasServerReplay) {
        if (replayArrayIndex < 0) replayArrayIndex = 0;
        if (replayArrayIndex >= replayFrames.length) replayArrayIndex = replayFrames.length - 1;
        const fr = getCurrentReplayFrame();
        renderReplayFrame(fr, baseClasses, domCells, resolveCellIndex);
        updateFrameInfo(fr, replayFrames.length, phaseEl, frameEl, gridEl);
        const cycle = document.getElementById("lab-computation-cycle");
        if (cycle) {
          cycle.textContent = fr && fr.frame_key != null ? "frame_key " + String(fr.frame_key) : "frame —";
        }
        const hint = document.getElementById("lab-replay-footer-hint");
        if (hint) {
          hint.textContent =
            fr && fr.id != null
              ? "ReplayFrame id " + String(fr.id) + (fr.is_keyframe ? " · keyframe" : "")
              : "—";
        }
        return;
      }

      if (frame < 0) frame = 0;
      if (frame > TOTAL_FRAMES) frame = TOTAL_FRAMES;
      const overlay = TOTAL_FRAMES <= 0 ? "candidates" : replayOverlayForFrame(frame);
      const oi = overlayIndex(overlay);
      for (let i = 0; i < domCells.length; i++) {
        const row = matrix[i];
        if (row && row[oi]) {
          domCells[i].className = row[oi];
        }
      }
      if (phaseEl) {
        phaseEl.textContent = TOTAL_FRAMES <= 0 ? "—" : replayPhaseForFrame(frame);
      }
      if (frameEl) frameEl.textContent = String(frame) + " / " + String(TOTAL_FRAMES);
      if (gridEl) gridEl.dataset.overlay = overlay;
      const cycle = document.getElementById("lab-computation-cycle");
      if (cycle) cycle.textContent = "computation_cycle #" + String(frame);
    }

    function setPlaying(next) {
      let wantPlay = next;
      const cap = hasServerReplay ? replayFrames.length : TOTAL_FRAMES;
      if (wantPlay && cap <= 0) {
        wantPlay = false;
      }
      isPlaying = wantPlay;
      if (timerId !== null) {
        window.clearInterval(timerId);
        timerId = null;
      }
      if (isPlaying && cap > 0) {
        timerId = window.setInterval(function () {
          if (hasServerReplay) {
            replayArrayIndex += 1;
            if (replayArrayIndex >= replayFrames.length) replayArrayIndex = 0;
          } else {
            frame += 1;
            if (frame >= TOTAL_FRAMES) frame = 0;
          }
          applyFrame();
        }, 220);
      }
      if (playIcon && pauseIcon) {
        playIcon.classList.toggle("hidden", isPlaying);
        pauseIcon.classList.toggle("hidden", !isPlaying);
      }
    }

    function closeTopologyModal() {
      if (!modal) return;
      modal.classList.add("hidden");
      modal.classList.remove("flex");
    }

    function applyRunSelectionHighlight(runId) {
      document.querySelectorAll("[data-lab-run-id]").forEach(function (b) {
        const on = runId != null && b.getAttribute("data-lab-run-id") === runId;
        b.classList.toggle("border-cyan-500", on);
        b.classList.toggle("bg-cyan-500/10", on);
        b.classList.toggle("border-slate-800", !on);
        b.classList.toggle("bg-slate-900", !on);
        b.classList.toggle("hover:border-slate-700", !on);
      });
    }

    function setRunDetail(run) {
      const dash = "—";
      const detailIds = [
        "lab-detail-score",
        "lab-detail-miners",
        "lab-detail-extension-cap",
        "lab-detail-connected",
        "lab-detail-cost",
        "lab-detail-belts",
        "lab-detail-pipes",
        "lab-detail-saturation",
      ];
      if (!run) {
        for (const id of detailIds) {
          const el = document.getElementById(id);
          if (el) el.textContent = dash;
        }
        const title = document.getElementById("lab-detail-run-id");
        if (title) title.textContent = dash;
        return;
      }
      const ext =
        run.extension_cap != null && run.extension_cap !== ""
          ? String(run.extension_cap)
          : dash;
      const map = [
        ["lab-detail-score", run.score != null ? run.score : dash],
        ["lab-detail-miners", run.miners != null ? run.miners : dash],
        ["lab-detail-extension-cap", ext],
        ["lab-detail-connected", run.connected != null ? run.connected : dash],
        ["lab-detail-cost", run.cost != null ? run.cost : dash],
        ["lab-detail-belts", run.belts != null ? run.belts : dash],
        ["lab-detail-pipes", run.pipes != null ? run.pipes : dash],
        [
          "lab-detail-saturation",
          run.saturation != null && run.saturation !== "" ? String(run.saturation) + "%" : dash,
        ],
      ];
      for (const [id, val] of map) {
        const n = document.getElementById(id);
        if (n) n.textContent = String(val);
      }
      const title = document.getElementById("lab-detail-run-id");
      if (title) title.textContent = run.id != null ? String(run.id) : dash;
    }

    function resetToInitial() {
      setPlaying(false);
      if (hasServerReplay) {
        replayArrayIndex = replaySlotForServerInitialFrame();
      } else {
        frame = baselineFrame;
      }
      closeTopologyModal();
      closeCellDetailModal();
      if (blueprintInput) blueprintInput.value = baselineBlueprint;
      applyRunSelectionHighlight(baselineRunId);
      setRunDetail(baselineRun);
      applyFrame();
    }

    document.getElementById("lab-header-reset")?.addEventListener("click", function () {
      resetToInitial();
    });

    document.getElementById("lab-header-run")?.addEventListener("click", function () {
      setPlaying(true);
      applyFrame();
    });

    document.getElementById("lab-timeline-prev")?.addEventListener("click", function () {
      if (hasServerReplay) {
        replayArrayIndex = Math.max(0, replayArrayIndex - 1);
      } else {
        frame = Math.max(0, frame - 1);
      }
      applyFrame();
    });

    playBtn?.addEventListener("click", function () {
      const cap = hasServerReplay ? replayFrames.length : TOTAL_FRAMES;
      if (cap <= 0) return;
      setPlaying(!isPlaying);
      applyFrame();
    });

    document.getElementById("lab-timeline-next")?.addEventListener("click", function () {
      if (hasServerReplay) {
        replayArrayIndex = Math.min(replayFrames.length - 1, replayArrayIndex + 1);
      } else {
        frame = Math.min(TOTAL_FRAMES, frame + 1);
      }
      applyFrame();
    });

    document.querySelectorAll("[data-lab-run-id]").forEach(function (btn) {
      btn.addEventListener("click", function () {
        const rid = btn.getAttribute("data-lab-run-id");
        const run = (runs || []).find(function (r) {
          return r.id === rid;
        });
        applyRunSelectionHighlight(rid);
        setRunDetail(run);
      });
    });

    openTopology?.addEventListener("click", function () {
      modal?.classList.remove("hidden");
      modal?.classList.add("flex");
    });
    closeTopology?.addEventListener("click", function () {
      closeTopologyModal();
    });
    modal?.addEventListener("click", function (ev) {
      if (ev.target === modal) {
        closeTopologyModal();
      }
    });

    function replaceLabReplayPayload(payload) {
      if (!payload || typeof payload !== "object") return;
      const redirectTo = typeof payload.redirect === "string" ? payload.redirect : "";
      if (blueprintInput && typeof payload.blueprint_code === "string") {
        blueprintInput.value = payload.blueprint_code;
        baselineBlueprint = payload.blueprint_code;
      }
      if (payload.lab_ui_initial && typeof payload.lab_ui_initial === "object") {
        Object.assign(initialFromServer, payload.lab_ui_initial);
      }
      if (rootEl && payload.lab_ui_initial && typeof payload.lab_ui_initial === "object") {
        const tid = payload.lab_ui_initial.replayTrackId;
        rootEl.dataset.labReplayTrackId = tid != null ? String(tid) : "";
      }
      baselineFrame = parseFrame(initialFromServer.frame, datasetFrame);
      const next = Array.isArray(payload.lab_replay_frames_json) ? payload.lab_replay_frames_json : [];
      replayFrames = next;
      hasServerReplay = replayFrames.length > 0;
      if (!hasServerReplay) {
        window.location.assign(redirectTo || window.location.href);
        return;
      }
      replayCleanup();
      replayCleanup = initializeServerReplaySurface(replayFrames);
      resetLabViewportTransform();
      replayArrayIndex = replaySlotForServerInitialFrame();
      setPlaying(false);
      applyFrame();
    }

    function syncProjectSlugHiddenFromRedirect(form, redirectUrl) {
      if (!form || !redirectUrl) return;
      try {
        const u = new URL(redirectUrl, window.location.origin);
        const m = u.pathname.match(/\/asteroid-miner-layout\/p\/([^/]+)\/?/);
        if (!m) return;
        const slug = decodeURIComponent(m[1]);
        let hi = form.querySelector('input[name="project_slug"]');
        if (!hi) {
          hi = document.createElement("input");
          hi.type = "hidden";
          hi.name = "project_slug";
          form.appendChild(hi);
        }
        hi.value = slug;
      } catch {
        /* ignore */
      }
    }

    const importForm = document.getElementById("lab-import-project-form");
    if (importForm) {
      importForm.addEventListener("submit", function (ev) {
        ev.preventDefault();
        const fd = new FormData(importForm);
        fetch(importForm.action, {
          method: "POST",
          body: fd,
          credentials: "same-origin",
          headers: { Accept: "application/json" },
        })
          .then(function (res) {
            return res
              .json()
              .catch(function () {
                return { ok: false };
              })
              .then(function (data) {
                return { res: res, data: data };
              });
          })
          .then(function (bundle) {
            const res = bundle.res;
            const data = bundle.data;
            if (!res.ok || !data || data.ok === false) {
              if (data && data.redirect) {
                window.location.assign(data.redirect);
              } else {
                window.location.reload();
              }
              return;
            }
            if (data.in_place) {
              replaceLabReplayPayload(data);
              return;
            }
            if (data.redirect) {
              if (typeof history.pushState === "function") {
                try {
                  history.pushState(null, "", data.redirect);
                  syncProjectSlugHiddenFromRedirect(importForm, data.redirect);
                } catch {
                  window.location.assign(data.redirect);
                  return;
                }
              } else {
                window.location.assign(data.redirect);
                return;
              }
            }
            replaceLabReplayPayload(data);
          })
          .catch(function () {
            importForm.submit();
          });
      });
    }

    function domIndexToWorldXY(domIdx) {
      if (!hasServerReplay || !replayLayout) {
        return null;
      }
      const gw = replayLayout.gridW;
      const i = Number(domIdx);
      if (!Number.isFinite(i) || i < 0) {
        return null;
      }
      const col = i % gw;
      const row = Math.floor(i / gw);
      const d = col + replayLayout.minD;
      const y = row + replayLayout.minR;
      const xWorld = d < 0 ? d : d + 1;
      return { x: xWorld, y: y };
    }

    function findLabCellFromPoint(clientX, clientY) {
      const el = document.elementFromPoint(clientX, clientY);
      if (!el) {
        return null;
      }
      return el.closest("[data-lab-cell-index]");
    }

    function updateLabGridHudEmpty() {
      if (gridHudCoord) {
        gridHudCoord.textContent = "—";
      }
      if (gridHudRole) {
        gridHudRole.textContent = "—";
      }
    }

    function getLabCellDisplayCoord(cellEl) {
      const indexText = cellEl && cellEl.getAttribute ? cellEl.getAttribute("data-lab-cell-index") : null;
      const idx = Number.parseInt(indexText || "", 10);
      if (!Number.isFinite(idx)) {
        return "—";
      }
      if (hasServerReplay && replayLayout) {
        const coord = domIndexToWorldXY(idx);
        if (!coord) {
          return "—";
        }
        return "(" + coord.x + ", " + coord.y + ")";
      }
      const demoX = idx % GRID_W;
      const demoY = Math.floor(idx / GRID_W);
      return "(" + demoX + ", " + demoY + ")";
    }

    function getLabCellDisplayRole(cellEl) {
      if (!cellEl) {
        return "—";
      }
      const ov = cellEl.getAttribute("data-overlay-role");
      if (ov != null && ov !== "") {
        return ov;
      }
      const ck = cellEl.getAttribute("data-cell-kind");
      if (ck != null && ck !== "") {
        return ck;
      }
      const tt = cellEl.getAttribute("data-tile-type");
      if (tt != null && tt !== "") {
        return tt;
      }
      return "—";
    }

    function updateLabGridHudFromPoint(clientX, clientY) {
      const cellEl = findLabCellFromPoint(clientX, clientY);
      if (!cellEl || !gridEl.contains(cellEl)) {
        updateLabGridHudEmpty();
        return;
      }
      if (gridHudCoord) {
        gridHudCoord.textContent = getLabCellDisplayCoord(cellEl);
      }
      if (gridHudRole) {
        gridHudRole.textContent = getLabCellDisplayRole(cellEl);
      }
    }

    function handleLabViewportWheel(event) {
      if (!gridViewport || !gridStage) {
        return;
      }
      event.preventDefault();
      const rect = gridViewport.getBoundingClientRect();
      const anchorX = event.clientX - rect.left;
      const anchorY = event.clientY - rect.top;
      const oldScale = labViewportTransform.scale;
      const zoomFactor = event.deltaY < 0 ? 1.12 : 1 / 1.12;
      const nextScale = clampNumber(oldScale * zoomFactor, LAB_VIEWPORT_MIN_SCALE, LAB_VIEWPORT_MAX_SCALE);
      if (nextScale === oldScale) {
        updateLabGridHudFromPoint(event.clientX, event.clientY);
        return;
      }
      const worldX = (anchorX - labViewportTransform.tx) / oldScale;
      const worldY = (anchorY - labViewportTransform.ty) / oldScale;
      labViewportTransform.scale = nextScale;
      labViewportTransform.tx = anchorX - worldX * nextScale;
      labViewportTransform.ty = anchorY - worldY * nextScale;
      applyLabViewportTransform();
      updateLabGridHudFromPoint(event.clientX, event.clientY);
    }

    function handleLabViewportPointerDown(event) {
      if (!gridViewport || event.button !== 0) {
        return;
      }
      labPanState = {
        pointerId: event.pointerId,
        startClientX: event.clientX,
        startClientY: event.clientY,
        startTx: labViewportTransform.tx,
        startTy: labViewportTransform.ty,
        dragging: false,
      };
    }

    function handleLabViewportPointerMove(event) {
      updateLabGridHudFromPoint(event.clientX, event.clientY);
      if (!labPanState || labPanState.pointerId !== event.pointerId) {
        return;
      }
      const dx = event.clientX - labPanState.startClientX;
      const dy = event.clientY - labPanState.startClientY;
      const distance = Math.hypot(dx, dy);
      if (!labPanState.dragging) {
        if (distance < LAB_VIEWPORT_DRAG_THRESHOLD_PX) {
          return;
        }
        labPanState.dragging = true;
        gridViewport.setPointerCapture(event.pointerId);
      }
      event.preventDefault();
      labViewportTransform.tx = labPanState.startTx + dx;
      labViewportTransform.ty = labPanState.startTy + dy;
      applyLabViewportTransform();
    }

    function handleLabViewportPointerUp(event) {
      if (!labPanState || labPanState.pointerId !== event.pointerId) {
        return;
      }
      if (
        labPanState.dragging &&
        typeof gridViewport.releasePointerCapture === "function" &&
        typeof gridViewport.hasPointerCapture === "function" &&
        gridViewport.hasPointerCapture(event.pointerId)
      ) {
        gridViewport.releasePointerCapture(event.pointerId);
      }
      labPanState = null;
    }

    function handleLabViewportPointerLeave(event) {
      updateLabGridHudEmpty();
      if (!labPanState || labPanState.pointerId !== event.pointerId) {
        return;
      }
      labPanState = null;
    }

    function bindLabViewportInteractions() {
      if (labViewportInteractionsBound || !gridViewport) {
        return;
      }
      labViewportInteractionsBound = true;
      gridViewport.addEventListener("wheel", handleLabViewportWheel, { passive: false });
      gridViewport.addEventListener("pointerdown", handleLabViewportPointerDown);
      gridViewport.addEventListener("pointermove", handleLabViewportPointerMove);
      gridViewport.addEventListener("pointerup", handleLabViewportPointerUp);
      gridViewport.addEventListener("pointercancel", handleLabViewportPointerUp);
      gridViewport.addEventListener("pointerleave", handleLabViewportPointerLeave);
    }

    function labCsrfToken() {
      const mc = document.querySelector("[name=csrfmiddlewaretoken]");
      if (mc && mc.value) {
        return mc.value;
      }
      return getCookie("csrftoken") || "";
    }

    const LAB_CELL_DETAIL_KEY_ORDER = [
      "x",
      "y",
      "server_x",
      "server_y",
      "layer",
      "rotation",
      "cell_kind",
      "tile_type",
      "transport_kind",
    ];

    function labCellDetailEscapeHtml(s) {
      return String(s)
        .replace(/&/g, "&amp;")
        .replace(/</g, "&lt;")
        .replace(/>/g, "&gt;")
        .replace(/"/g, "&quot;");
    }

    function labCellDetailOrderedKeys(obj) {
      const keys = Object.keys(obj || {});
      const seen = {};
      const out = [];
      for (let i = 0; i < LAB_CELL_DETAIL_KEY_ORDER.length; i++) {
        const k = LAB_CELL_DETAIL_KEY_ORDER[i];
        if (keys.indexOf(k) >= 0) {
          out.push(k);
          seen[k] = true;
        }
      }
      const rest = keys
        .filter(function (k) {
          return !seen[k];
        })
        .sort();
      return out.concat(rest);
    }

    function labCellDetailFormatValue(v) {
      if (v === null || v === undefined) {
        return '<span class="text-slate-500">—</span>';
      }
      if (typeof v === "number" || typeof v === "boolean") {
        return labCellDetailEscapeHtml(String(v));
      }
      if (typeof v === "string") {
        const t = v.trim();
        if (t === "") {
          return '<span class="text-slate-500">(empty)</span>';
        }
        return labCellDetailEscapeHtml(v);
      }
      const json = JSON.stringify(v);
      if (json.length <= 140) {
        return (
          '<span class="wrap-break-word font-mono text-[11px]">' + labCellDetailEscapeHtml(json) + "</span>"
        );
      }
      return (
        '<details class="mt-1">' +
        '<summary class="cursor-pointer text-xs text-slate-400">JSON (' +
        String(json.length) +
        " chars)</summary>" +
        '<pre class="mt-2 max-h-40 overflow-auto whitespace-pre-wrap wrap-break-word rounded border border-slate-800 bg-slate-900/80 p-2 font-mono text-[11px] leading-snug">' +
        labCellDetailEscapeHtml(JSON.stringify(v, null, 2)) +
        "</pre></details>"
      );
    }

    function labCellDetailKvTableHtml(obj) {
      if (!obj || typeof obj !== "object") {
        return '<p class="text-slate-500">—</p>';
      }
      const keys = labCellDetailOrderedKeys(obj);
      if (!keys.length) {
        return '<p class="text-slate-500">(empty object)</p>';
      }
      let rows = "";
      for (let i = 0; i < keys.length; i++) {
        const k = keys[i];
        rows +=
          '<div class="grid grid-cols-[minmax(0,auto)_1fr] gap-x-3 border-b border-slate-800/80 py-2 last:border-b-0">' +
          '<dt class="shrink-0 font-mono text-xs text-slate-500">' +
          labCellDetailEscapeHtml(k) +
          "</dt>" +
          '<dd class="min-w-0 text-slate-200">' +
          labCellDetailFormatValue(obj[k]) +
          "</dd></div>";
      }
      return '<dl class="rounded-lg border border-slate-800/80 px-3">' + rows + "</dl>";
    }

    function labCellDetailFrameMetaHtml(data) {
      const parts = [];
      if (data.frame_index !== undefined && data.frame_index !== null) {
        parts.push("frame_index: " + String(data.frame_index));
      }
      if (data.frame_key !== undefined && data.frame_key !== null && String(data.frame_key) !== "") {
        parts.push("frame_key: " + String(data.frame_key));
      }
      if (!parts.length) {
        return "";
      }
      return (
        '<p class="mb-3 font-mono text-[11px] leading-relaxed text-slate-500">' +
        labCellDetailEscapeHtml(parts.join(" · ")) +
        "</p>"
      );
    }

    function labCellDetailSourceBlockHtml(sourceKey, val, mergedCell) {
      if (
        sourceKey === "full_map" &&
        mergedCell &&
        typeof mergedCell === "object" &&
        val &&
        typeof val === "object" &&
        !Array.isArray(val) &&
        JSON.stringify(val) === JSON.stringify(mergedCell)
      ) {
        return (
          '<div class="mb-4 last:mb-0">' +
          '<h4 class="mb-1 font-mono text-xs text-slate-400">' +
          labCellDetailEscapeHtml(sourceKey) +
          "</h4>" +
          '<p class="text-xs text-slate-500">Same as merged cell above.</p></div>'
        );
      }
      const head =
        '<h4 class="mb-2 font-mono text-xs text-slate-400">' +
        labCellDetailEscapeHtml(sourceKey) +
        "</h4>";
      if (val !== null && val !== undefined && typeof val === "object" && !Array.isArray(val)) {
        return '<div class="mb-4 last:mb-0">' + head + labCellDetailKvTableHtml(val) + "</div>";
      }
      return (
        '<div class="mb-4 last:mb-0">' +
        head +
        '<div class="text-slate-200">' +
        labCellDetailFormatValue(val) +
        "</div></div>"
      );
    }

    function labCellDetailRenderSuccess(cellDetailEl, data) {
      const cell = data.cell;
      const sources = data.sources || {};
      const frameMeta = labCellDetailFrameMetaHtml(data);
      let html = '<div class="space-y-6">';
      if (cell && typeof cell === "object") {
        html +=
          '<section class="space-y-2">' +
          '<h3 class="text-xs font-semibold uppercase tracking-wide text-slate-400">Merged cell</h3>' +
          frameMeta +
          labCellDetailKvTableHtml(cell) +
          "</section>";
      } else {
        const msg = data.message || "no_cell_at_xy";
        html +=
          '<section class="space-y-2">' +
          '<p class="text-slate-300">' +
          labCellDetailEscapeHtml(msg) +
          "</p>" +
          frameMeta +
          "</section>";
      }
      const srcKeys = Object.keys(sources);
      if (srcKeys.length) {
        let srcHtml = "";
        for (let s = 0; s < srcKeys.length; s++) {
          srcHtml += labCellDetailSourceBlockHtml(srcKeys[s], sources[srcKeys[s]], cell);
        }
        html +=
          '<section class="space-y-3">' +
          '<h3 class="text-xs font-semibold uppercase tracking-wide text-slate-400">Sources (server)</h3>' +
          srcHtml +
          "</section>";
      }
      html += "</div>";
      cellDetailEl.innerHTML = html;
    }

    const cellDetailModal = document.getElementById("lab-cell-detail-modal");
    const cellDetailBody = document.getElementById("lab-cell-detail-body");
    const closeCellDetailBtn = document.getElementById("lab-close-cell-detail");

    function closeCellDetailModal() {
      if (!cellDetailModal) {
        return;
      }
      cellDetailModal.classList.add("hidden");
      cellDetailModal.classList.remove("flex");
    }

    function openCellDetailModal() {
      if (!cellDetailModal) {
        return;
      }
      cellDetailModal.classList.remove("hidden");
      cellDetailModal.classList.add("flex");
    }

    if (gridEl && cellDetailModal) {
      gridEl.addEventListener("click", function (ev) {
        if (!hasServerReplay || !replayLayout) {
          return;
        }
        const hit = ev.target.closest("[data-lab-cell-index]");
        if (!hit || !gridEl.contains(hit)) {
          return;
        }
        const idx = parseInt(hit.getAttribute("data-lab-cell-index") || "", 10);
        const xy = domIndexToWorldXY(idx);
        if (!xy) {
          return;
        }
        const fr = getCurrentReplayFrame();
        if (!fr || fr.id == null) {
          return;
        }
        const cellUrl = rootEl && rootEl.dataset ? rootEl.dataset.labReplayCellUrl || "" : "";
        const trackIdStr =
          rootEl && rootEl.dataset && rootEl.dataset.labReplayTrackId != null
            ? String(rootEl.dataset.labReplayTrackId)
            : "";
        if (!cellUrl || !trackIdStr) {
          return;
        }
        const projectSlug =
          rootEl && rootEl.dataset && rootEl.dataset.labProjectSlug != null
            ? String(rootEl.dataset.labProjectSlug)
            : "";
        const payload = {
          replay_frame_id: fr.id,
          replay_track_id: parseInt(trackIdStr, 10),
          x: xy.x,
          y: xy.y,
        };
        if (projectSlug) {
          payload.project_slug = projectSlug;
        }
        if (cellDetailBody) {
          cellDetailBody.textContent = "Loading…";
        }
        openCellDetailModal();
        fetch(cellUrl, {
          method: "POST",
          credentials: "same-origin",
          headers: {
            Accept: "application/json",
            "Content-Type": "application/json",
            "X-CSRFToken": labCsrfToken(),
          },
          body: JSON.stringify(payload),
        })
          .then(function (res) {
            return res
              .json()
              .catch(function () {
                return { ok: false, error: "bad_json" };
              })
              .then(function (data) {
                return { res: res, data: data };
              });
          })
          .then(function (bundle) {
            const res = bundle.res;
            const data = bundle.data;
            if (!cellDetailBody) {
              return;
            }
            if (!res.ok || !data || data.ok !== true) {
              const err = data && data.error ? String(data.error) : "request_failed " + res.status;
              cellDetailBody.textContent = err;
              return;
            }
            labCellDetailRenderSuccess(cellDetailBody, data);
          })
          .catch(function () {
            if (cellDetailBody) {
              cellDetailBody.textContent = "Network error.";
            }
          });
      });
    }

    closeCellDetailBtn?.addEventListener("click", function () {
      closeCellDetailModal();
    });
    cellDetailModal?.addEventListener("click", function (ev) {
      if (ev.target === cellDetailModal) {
        closeCellDetailModal();
      }
    });
    document.addEventListener("keydown", function (ev) {
      if (ev.key === "Escape" && cellDetailModal && !cellDetailModal.classList.contains("hidden")) {
        closeCellDetailModal();
      }
    });

    window.AsteroidLabReplay = {
      getCurrentReplayFrame: getCurrentReplayFrame,
      renderReplayFrame: function (fr) {
        renderReplayFrame(fr, baseClasses, domCells, resolveCellIndex);
      },
      renderCellOverlay: function (ov) {
        resetGridBase(domCells, baseClasses);
        renderCellOverlay(baseClasses, domCells, ov, resolveCellIndex);
      },
      applyEquipmentBundleHighlight: function (ov) {
        applyEquipmentBundleGroupVisualsFromOverlay(ov, domCells, resolveCellIndex);
      },
      renderDecodedCells: function (list) {
        resetGridBase(domCells, baseClasses);
        renderDecodedCells(baseClasses, domCells, list, resolveCellIndex);
      },
      renderExistingLayoutOverlay: function (ov) {
        resetGridBase(domCells, baseClasses);
        renderExistingLayoutOverlay(baseClasses, domCells, ov, resolveCellIndex);
      },
      updateFrameInfo: function (fr) {
        updateFrameInfo(fr, hasServerReplay ? replayFrames.length : 0, phaseEl, frameEl, gridEl);
      },
      collectOverlayPaintTargets: collectOverlayPaintTargets,
      visualCol: visualCol,
      rawXToDenseX: rawXToDenseX,
      replaceLabReplayPayload: replaceLabReplayPayload,
    };

    applyLabViewportTransform();
    updateLabGridHudEmpty();
    bindLabViewportInteractions();

    setRunDetail(baselineRun);
    applyFrame();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
