/**
 * Client-side replay controls for the asteroid mining lab page (shell UI).
 *
 * Shapez2 asteroid map invariant (Lab + runtime replay):
 * - There is no x == 0 column. Horizontal order: ..., -2, -1, 1, 2, ...
 * - (-1, y) is horizontally adjacent to (1, y), not (0, y).
 * - World (1, 0) is the UI anchor: visual column index 0, row y = 0 at grid center (symmetric padding).
 *
 * Domain rotation contract (blueprint JSON; never mutate ``cell.rotation`` in JS):
 * - R = 0 means East; R increases by quarter-turns clockwise (0..3).
 * - Lab SVGs are East-facing; display rotation is CSS ``rotate`` on the sprite ``img`` from ``R`` only.
 *   Do not apply ad-hoc R+1 or rewrite domain rotation.
 */
(function () {
  "use strict";

  const GRID_W = 23;
  const GRID_H = 15;

  /** Canonical map rotation: 0 = East, 1 = South, 2 = West, 3 = North; quarter-turns clockwise. */
  const DIR = Object.freeze({
    EAST: 0,
    SOUTH: 1,
    WEST: 2,
    NORTH: 3,
  });

  const LINK_KEY_TO_DIR = Object.freeze({
    e: DIR.EAST,
    s: DIR.SOUTH,
    w: DIR.WEST,
    n: DIR.NORTH,
  });

  const DIR_TO_BRIDGE_SUFFIX = Object.freeze({
    0: "e",
    1: "s",
    2: "w",
    3: "n",
  });

  function normalizeQuarterTurns(q) {
    const n = Number(q);
    if (!Number.isFinite(n)) return 0;
    return ((Math.trunc(n) % 4) + 4) % 4;
  }

  /* Sprite canonical direction contract (East-facing assets; CSS rotate only):
   * quarter 0 = E = 0deg, 1 = S = 90deg clockwise on screen, 2 = W = 180deg, 3 = N = 270deg.
   * Row/col grid mapping must not alter this rotation (no scaleX/rotateY mirror tricks). */
  function rotationToDeg(q) {
    return normalizeQuarterTurns(q) * 90;
  }

  function snapToDevicePixel(value) {
    const dpr = window.devicePixelRatio || 1;
    return Math.round(Number(value) * dpr) / dpr;
  }

  /** Base cell look; replay grid uses grid cell size instead of h-5 w-5. ``relative`` anchors the sprite layer. */
  const LAB_CELL_BASE =
    "lab-cell relative shrink-0 overflow-visible border bg-slate-950 border-slate-900";

  /** Map blueprint ``T`` (:class:`ShapezGameIdentifier` ``value``) → ``sprite_static_relpath``; from ``json_script`` id ``lab-identifier-sprite-paths-data``. */
  let labIdentifierSpriteRelpaths = {};

  /** When ``#lab-root`` has ``data-lab-debug-rotation="1"``, grid shows R overlay on cells with sprites. */
  function labRotationDebugEnabled(rootEl) {
    return Boolean(rootEl && rootEl.dataset && rootEl.dataset.labDebugRotation === "1");
  }

  /** ``cell_kind`` → blueprint ``T`` when ``tile_type`` is missing (not used for ambiguous kinds like ``space_pipe``). */
  const LAB_SPRITE_CELL_KIND_TO_IDENTIFIER = Object.freeze({
    fluid_miner: "Layout_FluidMiner",
    fluid_miner_extension: "Layout_FluidMinerExtension",
    shape_miner: "Layout_ShapeMiner",
    shape_miner_extension: "Layout_ShapeMinerExtension",
  });

  /** Blueprint ``T`` alias when art matches another identifier (mirrors ``lab_sprite_path.py``). */
  const LAB_SPRITE_TILE_TYPE_ALIASES = Object.freeze({
    Layout_ProMiner: "Layout_ShapeMiner",
    SpaceBelt_Left: "SpaceBelt_LeftTurn",
    SpacePipe_Left: "SpacePipe_LeftTurn",
    SpaceBelt_Right: "SpaceBelt_RightTurn",
    SpacePipe_Right: "SpacePipe_RightTurn",
  });

  /** Mineable asteroid field tiles (``cell_kind`` wins over export ``Layout_*MinerExtension`` ``T``). */
  const LAB_SPRITE_CELL_KIND_STATIC_RELPATH = Object.freeze({
    asteroid_fluid_field: "AsteroidField_Fluid.svg",
    asteroid_shape_field: "AsteroidField_Shape.svg",
  });

  /** Sprite stack container; styles in ``assets/css/input.css`` (``.lab-cell-sprite-layer``). */
  const LAB_CELL_SPRITE_LAYER_CLASS = "lab-cell-sprite-layer";

  /** Set in ``init`` from ``#lab-root`` ``data-lab-sprite-base`` (Django ``{% static %}``). */
  let labSpriteBaseUrl = "";

  const labRootForTotals = document.getElementById("lab-root");
  const rawTotal = labRootForTotals
    ? Number(labRootForTotals.dataset.labTotalFrames)
    : NaN;
  const TOTAL_FRAMES = Number.isFinite(rawTotal) ? rawTotal : 0;

  /** Extra empty cells beyond union bbox on each side (visual col / row), symmetric around (1,0). */
  const REPLAY_GRID_EDGE_PADDING = 5;

  const LAB_VIEWPORT_MIN_SCALE = 0.35;
  const LAB_VIEWPORT_MAX_SCALE = 7;
  const LAB_VIEWPORT_DRAG_THRESHOLD_PX = 6;

  let labViewportInteractionsBound = false;

  function clampNumber(value, min, max) {
    return Math.min(max, Math.max(min, value));
  }

  /** Human-readable timeline position (1-based slot / total frame count). */
  function formatLabFrameCounter(zeroBasedSlot, totalCount) {
    const total = Number.isFinite(totalCount) && totalCount > 0 ? Math.floor(totalCount) : 0;
    if (total <= 0) {
      return "0 / 0";
    }
    const slot = Number.isFinite(zeroBasedSlot) ? Math.floor(zeroBasedSlot) : 0;
    const clamped = clampNumber(slot, 0, total - 1);
    return String(clamped + 1) + " / " + String(total);
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

  function canonicalLabTileType(tileType) {
    const t = tileType == null ? "" : String(tileType).trim();
    if (!t) return "";
    const alias = LAB_SPRITE_TILE_TYPE_ALIASES[t];
    return alias || t;
  }

  function labSpriteRelpathFromTileType(tileType) {
    const t = canonicalLabTileType(tileType);
    if (!t) return null;
    const rel = labIdentifierSpriteRelpaths[t];
    if (typeof rel === "string" && rel.length) return rel;
    if (t.startsWith("SpaceBelt_")) return "SpaceBelt/" + t + ".svg";
    if (t.startsWith("SpacePipe_")) return "SpacePipe/" + t + ".svg";
    if (t.startsWith("Layout_")) return "Miner/" + t + ".svg";
    return null;
  }

  function labSpriteRelpathFromCellKind(cellKind) {
    const ck = cellKind == null ? "" : String(cellKind);
    if (!ck) return null;
    const ident = LAB_SPRITE_CELL_KIND_TO_IDENTIFIER[ck];
    if (!ident) return null;
    return labSpriteRelpathFromTileType(ident);
  }

  /** Last-resort: infer Forward-only sprite from transport kind when tile_type is absent.
   * Turn/splitter/merger variants require replay-provided tile_type — no topology inference here. */
  function inferTransportSpriteIdentifier(cell) {
    const tk = cell.transport_kind || cell.transport;
    if (!tk) return null;
    if (tk === "shape_belt" || cell.cell_kind === "space_belt") return "SpaceBelt_Forward";
    if (tk === "fluid_pipe" || cell.cell_kind === "space_pipe") return "SpacePipe_Forward";
    return null;
  }

  function labSpriteRelpathForCell(cell) {
    if (!cell || typeof cell !== "object") return null;
    const ck = cell.cell_kind != null ? String(cell.cell_kind) : "";
    const fieldRel = ck ? LAB_SPRITE_CELL_KIND_STATIC_RELPATH[ck] : null;
    if (fieldRel) return fieldRel;
    // sprite_identifier is the alias emitted alongside tile_type; prefer it so either field works.
    const tileKey = cell.sprite_identifier || cell.tile_type;
    let rel = labSpriteRelpathFromTileType(tileKey);
    if (!rel && cell.cell_kind != null) {
      rel = labSpriteRelpathFromCellKind(cell.cell_kind);
    }
    if (!rel) {
      const inferred = inferTransportSpriteIdentifier(cell);
      if (inferred) rel = labSpriteRelpathFromTileType(inferred);
    }
    return rel;
  }

  function attachLabSpriteImgNoDrag(img) {
    if (!img || img.__labSpriteNoDrag) return;
    img.__labSpriteNoDrag = true;
    img.draggable = false;
    img.setAttribute("draggable", "false");
    img.addEventListener("dragstart", function (ev) {
      ev.preventDefault();
    });
  }

  function ensureLabCellSpriteLayer(cellEl) {
    let layer = cellEl.querySelector("[data-lab-sprite-layer]");
    if (!layer) {
      layer = document.createElement("div");
      layer.setAttribute("data-lab-sprite-layer", "1");
      layer.setAttribute("aria-hidden", "true");
      layer.className = LAB_CELL_SPRITE_LAYER_CLASS;
      const img = document.createElement("img");
      img.className = "lab-cell-sprite";
      img.alt = "";
      img.setAttribute("aria-hidden", "true");
      attachLabSpriteImgNoDrag(img);
      layer.appendChild(img);
      cellEl.appendChild(layer);
    }
    return layer;
  }

  function clearLabCellSprite(el) {
    const layer = el.querySelector("[data-lab-sprite-layer]");
    if (layer) {
      layer.remove();
    }
    el.style.backgroundImage = "";
    el.style.backgroundSize = "";
    el.style.backgroundPosition = "";
    el.style.backgroundRepeat = "";
    el.style.transform = "";
    el.removeAttribute("data-lab-sprite");
    el.removeAttribute("data-r");
    el.removeAttribute("data-sprite-q");
    el.removeAttribute("data-sprite-file");
  }

  function applyLabCellSprite(el, cell) {
    clearLabCellSprite(el);
    if (!labSpriteBaseUrl || !cell || typeof cell !== "object") return;
    const ck = cell.cell_kind != null ? String(cell.cell_kind) : "";
    if (isRouteOverlayCellKind(ck)) return;
    const rel = labSpriteRelpathForCell(cell);
    if (!rel) return;
    const layer = ensureLabCellSpriteLayer(el);
    const img = layer.querySelector("img.lab-cell-sprite");
    if (!img) return;
    attachLabSpriteImgNoDrag(img);
    const base = String(labSpriteBaseUrl).replace(/\/?$/, "/");
    img.src = base + rel;
    const logicalQ = normalizeQuarterTurns(cell.rotation);
    const deg = rotationToDeg(logicalQ);
    if (deg !== 0) {
      img.style.transform = "rotate(" + String(deg) + "deg)";
    } else {
      img.style.transform = "";
    }
    layer.setAttribute("data-lab-sprite", rel);
    const rootDbg = document.getElementById("lab-root");
    if (labRotationDebugEnabled(rootDbg)) {
      el.setAttribute("data-r", String(logicalQ));
      el.setAttribute("data-sprite-file", rel);
    }
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

  function runCapacityFailed(run) {
    if (!run || typeof run !== "object") return false;
    if (run.run_success === true) return false;
    if (
      run.throughput_target &&
      typeof run.throughput_target === "object" &&
      run.throughput_budget_satisfied === false
    ) {
      return true;
    }
    if (run.throughput_budget_satisfied === true) return false;
    if (run.capacity_satisfied === true) return false;
    if (run.status === "partial") return true;
    return run.validation_passed === true && run.capacity_satisfied === false;
  }

  function capacityFailedStatusText(run) {
    const placed =
      run.placed != null && run.placed !== "" && run.placed !== "—" ? run.placed : "—";
    const target =
      run.target_miner_bundle_count != null && run.target_miner_bundle_count !== ""
        ? run.target_miner_bundle_count
        : run.target_placement_count != null
          ? run.target_placement_count
          : "—";
    let text =
      "validation passed, capacity failed, placements short: " +
      String(placed) +
      " / " +
      String(target);
    if (run.throughput_budget_satisfied === true) {
      const tp =
        run.confirmed_throughput != null && run.confirmed_throughput !== ""
          ? run.confirmed_throughput
          : "—";
      const tgtTp =
        run.target_throughput != null && run.target_throughput !== ""
          ? run.target_throughput
          : target;
      text += ", throughput OK: " + String(tp) + " / " + String(tgtTp);
    }
    return text;
  }

  function formatMacroCommitHudLine(summary) {
    if (!summary || typeof summary !== "object") {
      return "";
    }
    const hud = summary.macro_commit_summary;
    if (!hud || typeof hud !== "object") {
      return "";
    }
    const macroIds = Array.isArray(hud.committed_macro_ids) ? hud.committed_macro_ids.length : 0;
    const childIds = Array.isArray(hud.committed_child_ids) ? hud.committed_child_ids.length : 0;
    const domainVersion =
      hud.domain_version != null && hud.domain_version !== "" ? String(hud.domain_version) : "—";
    const validation =
      hud.validation_passed === true ? "true" : hud.validation_passed === false ? "false" : "—";
    const conflicts =
      hud.conflict_count != null && hud.conflict_count !== "" ? String(hud.conflict_count) : "0";
    return (
      "macro: on | macros: " +
      String(macroIds) +
      " | children: " +
      String(childIds) +
      " | domain_v: " +
      domainVersion +
      " | validation: " +
      validation +
      " | conflicts: " +
      conflicts
    );
  }

  function renderMacroCommitHud(summary) {
    const hudEl = document.getElementById("lab-macro-commit-hud");
    if (!hudEl) return;
    const line = formatMacroCommitHudLine(summary);
    if (!line) {
      hudEl.textContent = "—";
      hudEl.classList.add("hidden");
      return;
    }
    hudEl.textContent = line;
    hudEl.classList.remove("hidden");
  }

  function renderReplayRunStatus(feedback) {
    const runEl = document.getElementById("lab-replay-run-status");
    if (!runEl) return;
    const dash = "—";
    if (!feedback || typeof feedback !== "object") {
      runEl.textContent = dash;
      renderMacroCommitHud(null);
      return;
    }
    if (feedback.running === true) {
      runEl.textContent = "run: running…";
    } else if (typeof feedback.error_code === "string" && feedback.error_code) {
      runEl.textContent = "run: error " + feedback.error_code;
    } else if (feedback.solver_run_id != null) {
      const vp =
        feedback.validation_passed === true
          ? "passed"
          : feedback.validation_passed === false
            ? "failed"
            : "—";
      let statusText = "run: id " + String(feedback.solver_run_id) + " validation " + vp;
      const rs = feedback.run_summary;
      if (rs && runCapacityFailed(rs)) {
        statusText += " (" + capacityFailedStatusText(rs) + ")";
      }
      if (feedback.gene_template_source && feedback.gene_template_source.gene_count != null) {
        statusText += " genes:" + String(feedback.gene_template_source.gene_count);
      }
      runEl.textContent = statusText;
      renderMacroCommitHud(rs || feedback.run_summary || null);
    } else {
      runEl.textContent = dash;
      renderMacroCommitHud(null);
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

  /** World x to dense visual column index (lab map: no x == 0 column). */
  function rawXToDenseX(x) {
    const xi = Number(x);
    if (!Number.isFinite(xi)) return null;
    if (xi < 0) return Math.floor((xi + 1) / 2);
    if (xi > 0) return Math.floor((xi - 1) / 2) + 1;
    return 0;
  }

  /** World x to dense visual column for replay grid layout (Lab anchor). */
  function visualCol(x) {
    const xi = Number(x);
    if (!Number.isFinite(xi)) return null;
    if (xi < 0) return xi;
    if (xi > 0) return xi - 1;
    return 0;
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

  function labCellsFromMapView(mapView) {
    if (!mapView || typeof mapView !== "object") return [];
    const full = mapView.full_cells;
    if (!Array.isArray(full) || !full.length) return [];
    const out = [];
    for (let i = 0; i < full.length; i++) {
      const c = full[i];
      if (!c || typeof c !== "object") continue;
      out.push({
        x: c.x,
        y: c.y,
        cell_kind: c.kind != null ? c.kind : c.cell_kind,
        transport_kind: c.transport != null ? c.transport : c.transport_kind,
        tile_type: c.tile_type != null ? String(c.tile_type) : "",
        sprite_identifier: c.sprite_identifier != null ? String(c.sprite_identifier) : (c.tile_type != null ? String(c.tile_type) : ""),
        rotation: c.rotation,
      });
    }
    return out;
  }

  function overlayCellsFromMapView(mapView) {
    if (!mapView || typeof mapView !== "object") return [];
    const ov = mapView.overlay_cells;
    if (!Array.isArray(ov) || !ov.length) return [];
    const out = [];
    for (let i = 0; i < ov.length; i++) {
      const c = ov[i];
      if (!c || typeof c !== "object") continue;
      out.push({
        x: c.x,
        y: c.y,
        cell_kind: c.kind != null ? c.kind : c.cell_kind,
        transport_kind: c.transport != null ? c.transport : c.transport_kind,
        tile_type: c.tile_type != null ? String(c.tile_type) : "",
        sprite_identifier: c.sprite_identifier != null ? String(c.sprite_identifier) : (c.tile_type != null ? String(c.tile_type) : ""),
        rotation: c.rotation,
      });
    }
    return out;
  }

  function cellDeltaCellsFromMapView(mapView) {
    if (!mapView || typeof mapView !== "object") return [];
    const delta = mapView.cell_delta;
    if (!Array.isArray(delta) || !delta.length) return [];
    const out = [];
    for (let i = 0; i < delta.length; i++) {
      const c = delta[i];
      if (!c || typeof c !== "object") continue;
      out.push({
        x: c.x,
        y: c.y,
        cell_kind: c.kind != null ? c.kind : c.cell_kind,
        transport_kind: c.transport != null ? c.transport : c.transport_kind,
        tile_type: c.tile_type != null ? String(c.tile_type) : "",
        sprite_identifier: c.sprite_identifier != null ? String(c.sprite_identifier) : (c.tile_type != null ? String(c.tile_type) : ""),
        rotation: c.rotation,
      });
    }
    return out;
  }

  function fullMapCellsFromFrame(frame) {
    if (!frame || typeof frame !== "object") return [];
    const fromMapView = labCellsFromMapView(frame.map_view);
    if (fromMapView.length) return fromMapView;
    const fromDelta = cellDeltaCellsFromMapView(frame.map_view);
    if (fromDelta.length) return fromDelta;
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
    const mapView = frame && frame.map_view;
    if (mapView && typeof mapView === "object") {
      pushCellList(out, overlayCellsFromMapView(mapView), "");
      pushCellList(out, cellDeltaCellsFromMapView(mapView), "");
    }
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
    /* Lab grid uses island-local ``cell.x`` / ``cell.y`` (visualCol); no dense server frame. */
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

  var ROUTE_OVERLAY_CELL_KINDS = {
    route_probe: true,
    route_probe_path: true,
    confirmed_route: true,
    route_goal: true,
  };

  function isRouteOverlayCellKind(cellKind) {
    return ROUTE_OVERLAY_CELL_KINDS[String(cellKind || "")] === true;
  }

  function toneForRouteOverlayKind(cellKind) {
    const ck = String(cellKind || "");
    if (ck === "route_goal") {
      return "lab-route-goal-tone ring-2 ring-inset ring-violet-400/90 bg-violet-500/35";
    }
    if (ck === "confirmed_route") {
      return "lab-route-confirmed-tone ring-2 ring-inset ring-lime-400/90 bg-lime-500/35";
    }
    if (ck === "route_probe" || ck === "route_probe_path") {
      return "lab-route-probe-tone ring-2 ring-inset ring-amber-400/85 bg-amber-500/30";
    }
    return "";
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
    const routeTone = toneForRouteOverlayKind(ck);
    if (routeTone) return routeTone;
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
    if (ck === "internal_void") {
      return "ring-1 ring-inset ring-fuchsia-400/55 bg-fuchsia-950/28";
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
      const ck = cell.cell_kind != null ? String(cell.cell_kind) : "";
      const hudRole =
        cell.overlay_role != null
          ? String(cell.overlay_role)
          : isRouteOverlayCellKind(ck)
            ? ck
            : "";
      applyLabCellHudAttributes(el, cell, hudRole);
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

  /** Solid bridge bars (paired with ``BUNDLE_EDGE_PALETTE`` / inset fill). */
  var BUNDLE_BRIDGE_HEX = [
    "#fde047",
    "#bef264",
    "#67e8f9",
    "#f0abfc",
    "#fdba74",
    "#7dd3fc",
  ];

  function clearLabCellBundleBridges(el) {
    if (!el || !el.querySelectorAll) return;
    var bridges = el.querySelectorAll("[data-lab-bundle-bridge]");
    for (var i = 0; i < bridges.length; i++) {
      bridges[i].remove();
    }
  }

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

  /** ``cell_overlay_json``: ``equipment_bundles[].cells_json`` with ``bundle_edges`` (hull) + ``bundle_links`` (gap bridges). */
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
        clearLabCellBundleBridges(el);
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
        var linkStr = cell.bundle_links != null ? String(cell.bundle_links) : "";
        if (linkStr) {
          var hex = BUNDLE_BRIDGE_HEX[pi % BUNDLE_BRIDGE_HEX.length];
          for (var li = 0; li < linkStr.length; li++) {
            var d = linkStr.charAt(li);
            var dir = LINK_KEY_TO_DIR[d];
            if (dir === undefined) continue;
            var suffix = DIR_TO_BRIDGE_SUFFIX[dir];
            var br = document.createElement("div");
            br.setAttribute("data-lab-bundle-bridge", "1");
            br.setAttribute("aria-hidden", "true");
            br.className = "lab-bundle-bridge lab-bundle-bridge-" + suffix;
            br.style.backgroundColor = hex;
            el.appendChild(br);
          }
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
      clearLabCellBundleBridges(domCells[i]);
      domCells[i].className = baseClasses[i] || "";
      domCells[i].style.boxShadow = "";
      domCells[i].removeAttribute("data-cell-kind");
      domCells[i].removeAttribute("data-overlay-role");
      domCells[i].removeAttribute("data-tile-type");
      clearLabCellSprite(domCells[i]);
    }
  }

  function frameHasRenderableMap(frame) {
    return fullMapCellsFromFrame(frame).length > 0;
  }

  function formatOptimizationMilestoneHint(frame) {
    if (!frame || typeof frame !== "object") {
      return "—";
    }
    const parts = [];
    if (frame.event_type) {
      parts.push(String(frame.event_type));
    }
    const m = frame.metrics;
    if (m && typeof m === "object") {
      if (m.normal_count != null) {
        parts.push("normal_count=" + String(m.normal_count));
      }
      if (m.rejected_count != null) {
        parts.push("rejected_count=" + String(m.rejected_count));
      }
      if (m.commit_order != null) {
        parts.push("commit_order=" + String(m.commit_order));
      }
      if (parts.length <= 1) {
        const keys = Object.keys(m).slice(0, 4);
        for (let ki = 0; ki < keys.length; ki++) {
          const k = keys[ki];
          parts.push(k + "=" + String(m[k]));
        }
      }
    }
    return parts.length ? parts.join(" · ") : "optimization milestone";
  }

  function renderFullMapReplayFrame(frame, baseClasses, domCells, resolveCellIndex) {
    const fm = fullMapCellsFromFrame(frame);
    if (!fm.length) return false;
    renderFullMapCells(baseClasses, domCells, fm, resolveCellIndex);
    const ovCells = overlayCellsFromMapView(frame.map_view);
    if (ovCells.length) {
      renderFullMapCells(baseClasses, domCells, ovCells, resolveCellIndex);
    }
    const deltaCells = cellDeltaCellsFromMapView(frame.map_view);
    if (deltaCells.length) {
      renderFullMapCells(baseClasses, domCells, deltaCells, resolveCellIndex);
    }
    renderDiffOverlays(baseClasses, domCells, frame, resolveCellIndex);
    applyEquipmentBundleStrokeClasses(frame, domCells, resolveCellIndex);
    return true;
  }

  function renderReplayFrame(frame, baseClasses, domCells, resolveCellIndex, allFrames) {
    if (!frame || typeof frame !== "object") {
      resetGridBase(domCells, baseClasses);
      return;
    }
    const fm = fullMapCellsFromFrame(frame);
    if (fm.length) {
      resetGridBase(domCells, baseClasses);
      renderFullMapReplayFrame(frame, baseClasses, domCells, resolveCellIndex);
      return;
    }
    const ov = frame.cell_overlay_json;
    if (ov && typeof ov === "object") {
      resetGridBase(domCells, baseClasses);
      renderCellOverlay(baseClasses, domCells, ov, resolveCellIndex);
      return;
    }
    resetGridBase(domCells, baseClasses);
  }

  function updateFrameInfo(frame, totalCount, phaseEl, frameEl, gridEl, timelineSlotIndex) {
    const dash = "—";
    const denom = Number.isFinite(totalCount) ? totalCount : 0;
    if (!frame || typeof frame !== "object") {
      if (phaseEl) phaseEl.textContent = dash;
      const et = document.getElementById("lab-replay-event-type");
      const ti = document.getElementById("lab-replay-title");
      const de = document.getElementById("lab-replay-description");
      if (et) et.textContent = dash;
      if (ti) ti.textContent = dash;
      if (de) de.textContent = dash;
      if (frameEl) frameEl.textContent = formatLabFrameCounter(0, denom);
      return;
    }
    if (phaseEl) phaseEl.textContent = frame.phase != null ? String(frame.phase) : dash;
    const et = document.getElementById("lab-replay-event-type");
    const ti = document.getElementById("lab-replay-title");
    const de = document.getElementById("lab-replay-description");
    if (et) et.textContent = frame.event_type ? String(frame.event_type) : dash;
    if (ti) ti.textContent = frame.title != null ? String(frame.title) : dash;
    if (de) de.textContent = frame.description != null ? String(frame.description) : dash;
    let slot = timelineSlotIndex;
    if (slot == null || !Number.isFinite(Number(slot))) {
      const fi = Number(frame.frame_index);
      slot = Number.isFinite(fi) ? fi : 0;
    }
    if (frameEl) frameEl.textContent = formatLabFrameCounter(slot, denom);
    if (gridEl) gridEl.dataset.overlay = frame.frame_key ? String(frame.frame_key) : "";
  }

  function updateReplayTruncationHud(frame, trackMetrics) {
    const hud = document.getElementById("lab-replay-truncation-hud");
    if (!hud) return;
    const dash = "—";
    const fm = frame && frame.metrics && typeof frame.metrics === "object" ? frame.metrics : {};
    const tm = trackMetrics && typeof trackMetrics === "object" ? trackMetrics : {};
    const parts = [];
    const diag =
      typeof tm.diagnostic_reason === "string" && tm.diagnostic_reason ? tm.diagnostic_reason : null;
    if (diag) {
      parts.push("diagnostic: " + diag);
    }
    const truncated = fm.replay_truncated === true || tm.replay_truncated === true;
    if (truncated) {
      const reason =
        typeof fm.truncation_reason === "string" && fm.truncation_reason
          ? fm.truncation_reason
          : typeof tm.truncation_reason === "string" && tm.truncation_reason
            ? tm.truncation_reason
            : "unknown";
      let text = "truncated: " + reason;
      const dropped = fm.dropped_frame_count != null ? fm.dropped_frame_count : tm.dropped_frame_count;
      if (dropped != null && Number.isFinite(Number(dropped))) {
        text += " · dropped " + String(dropped);
      }
      parts.push(text);
    }
    hud.textContent = parts.length ? parts.join(" · ") : dash;
  }

  function init() {
    const matrix = readJsonScript("lab-cell-overlay-matrix-data");
    let runs = readJsonScript("lab-runs-data");
    if (!Array.isArray(runs)) {
      runs = [];
    }
    const uiInitial = readJsonScript("lab-ui-initial-state");
    const replayFramesRaw = readJsonScript("lab-replay-frames-data");
    let replayFrames = Array.isArray(replayFramesRaw) ? replayFramesRaw : [];
    const trackMetricsRaw = readJsonScript("lab-replay-track-metrics-data");
    let replayTrackMetrics =
      trackMetricsRaw && typeof trackMetricsRaw === "object" ? trackMetricsRaw : {};
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
    const scrubEl = document.getElementById("lab-timeline-scrub");
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

    let labViewportTransform = { zoom: 1, tx: 0, ty: 0 };
    let labPanState = null;
    /** Fitted cell edge (px) at zoom 1 for runtime replay; from ``applyReplayGridSizing``. */
    let replayFitBasePx = 20;
    /** Measured cell edge (px) at zoom 1 for demo matrix grid. */
    let demoBaseCellPxAtZoom1 = 20;

    let domCells;
    let baseClasses;

    function labViewportContentOffset(clientX, clientY) {
      if (!gridViewport) {
        return { vx: 0, vy: 0 };
      }
      const vr = gridViewport.getBoundingClientRect();
      const cs = window.getComputedStyle(gridViewport);
      const pl = parseFloat(cs.paddingLeft) || 0;
      const pt = parseFloat(cs.paddingTop) || 0;
      return {
        vx: clientX - vr.left - pl,
        vy: clientY - vr.top - pt,
      };
    }

    function labBaseCellAndGapPx() {
      if (hasServerReplay && replayLayout) {
        const cellPx = Math.max(4, Math.round(Number(replayFitBasePx)));
        const gapPx = Math.max(0, Math.round(cellPx * 0.2));
        return { cellPx: cellPx, gapPx: gapPx, gw: replayLayout.gridW, gh: replayLayout.gridH };
      }
      if (domCells && domCells.length) {
        const cellPx = Math.max(4, Math.round(Number(demoBaseCellPxAtZoom1)));
        const gapPx = Math.max(0, Math.round(cellPx * 0.2));
        return { cellPx: cellPx, gapPx: gapPx, gw: GRID_W, gh: GRID_H };
      }
      return null;
    }

    function labWorldPointFromClient(clientX, clientY) {
      const o = labViewportContentOffset(clientX, clientY);
      const t = labViewportTransform;
      const z = Number(t.zoom);
      const zoom = Number.isFinite(z) && z > 0 ? z : 1;
      return {
        wx: (o.vx - t.tx) / zoom,
        wy: (o.vy - t.ty) / zoom,
      };
    }

    function syncLabReplayStageSizeFromGrid() {
      if (!gridStage || !gridEl) {
        return;
      }
      const w = gridEl.offsetWidth;
      const h = gridEl.offsetHeight;
      if (w > 0 && h > 0) {
        gridStage.style.width = w + "px";
        gridStage.style.height = h + "px";
      }
    }

    function applyLabViewportTransform() {
      if (!gridStage) {
        return;
      }
      const t = labViewportTransform;
      const tx = snapToDevicePixel(t.tx);
      const ty = snapToDevicePixel(t.ty);
      const z = Number(t.zoom);
      const zoom = Number.isFinite(z) && z > 0 ? z : 1;
      gridStage.style.transformOrigin = "0 0";
      gridStage.style.transform =
        "translate(" + tx + "px, " + ty + "px) scale(" + zoom + ")";
    }

    function applyLabGridLayoutForZoom() {
      let cellPx = null;
      if (hasServerReplay && replayLayout) {
        const gw = replayLayout.gridW;
        const gh = replayLayout.gridH;
        cellPx = Math.max(4, Math.round(Number(replayFitBasePx)));
        gridEl.style.gridTemplateColumns = "repeat(" + gw + ", minmax(0, " + cellPx + "px))";
        gridEl.style.gridTemplateRows = "repeat(" + gh + ", minmax(0, " + cellPx + "px))";
      } else if (domCells && domCells.length) {
        cellPx = Math.max(4, Math.round(Number(demoBaseCellPxAtZoom1)));
        gridEl.style.gridTemplateColumns = "repeat(" + GRID_W + ", minmax(0, " + cellPx + "px))";
        gridEl.style.gridTemplateRows = "repeat(" + GRID_H + ", minmax(0, " + cellPx + "px))";
      }
      if (cellPx != null) {
        /* ~0.25rem at ~20px cells in CSS; gap scales with stage ``scale()`` via world cell size. */
        const gapPx = Math.max(0, Math.round(cellPx * 0.2));
        gridEl.style.setProperty("--lab-cell-gap", gapPx + "px");
        const radiusPx = Math.max(2, Math.min(7, Math.round(cellPx * 0.14)));
        gridEl.style.setProperty("--lab-cell-radius", radiusPx + "px");
      }
      syncLabReplayStageSizeFromGrid();
      applyLabViewportTransform();
    }

    function resetLabViewportTransform() {
      labViewportTransform = { zoom: 1, tx: 0, ty: 0 };
      applyLabGridLayoutForZoom();
    }

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
      const maxCell = 36;

      function applyReplayGridSizing() {
        if (!gridViewport || !replayLayout) return;
        const cw = gridViewport.clientWidth - padPx * 2;
        const ch = gridViewport.clientHeight - padPx * 2;
        replayFitBasePx = Math.max(
          minCell,
          Math.min(maxCell, Math.floor(Math.min(cw / replayLayout.gridW, ch / replayLayout.gridH))),
        );
        applyLabGridLayoutForZoom();
      }

      function labReplayViewportOnWindowResize() {
        applyReplayGridSizing();
        resetLabViewportTransform();
      }

      applyReplayGridSizing();
      resizeObserver = null;
      replayResizeMode = null;
      if (gridViewport && typeof ResizeObserver !== "undefined") {
        /* Do not reset zoom/pan here: cell-pixel zoom changes inner layout and can
         * retrigger the observer; ``applyReplayGridSizing`` already calls
         * ``applyLabGridLayoutForZoom`` with the current ``labViewportTransform``. */
        resizeObserver = new ResizeObserver(function () {
          applyReplayGridSizing();
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
      requestAnimationFrame(function () {
        const first = domCells[0];
        if (first && first.offsetWidth > 0) {
          demoBaseCellPxAtZoom1 = Math.max(4, first.offsetWidth);
        }
        applyLabGridLayoutForZoom();
      });
    }

    const rootEl = document.getElementById("lab-root");
    function syncLabDebugRotationClass() {
      if (!gridEl) return;
      if (labRotationDebugEnabled(rootEl)) {
        gridEl.classList.add("lab-debug-rotation");
      } else {
        gridEl.classList.remove("lab-debug-rotation");
      }
    }
    syncLabDebugRotationClass();
    const idSpriteRaw = readJsonScript("lab-identifier-sprite-paths-data");
    labIdentifierSpriteRelpaths =
      idSpriteRaw && typeof idSpriteRaw === "object" && !Array.isArray(idSpriteRaw)
        ? idSpriteRaw
        : {};
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

    function getMaxTimelineIndex() {
      if (hasServerReplay) {
        return Math.max(0, replayFrames.length - 1);
      }
      return TOTAL_FRAMES;
    }

    function getCurrentTimelineIndex() {
      return hasServerReplay ? replayArrayIndex : frame;
    }

    function setTimelineIndex(nextIndex, options) {
      const opt = options || {};
      const pause = opt.pause !== false;
      const max = getMaxTimelineIndex();
      const parsed = parseInt(String(nextIndex), 10);
      const raw = Number.isFinite(parsed) ? parsed : 0;
      const clamped = clampNumber(raw, 0, max);
      if (hasServerReplay) {
        replayArrayIndex = clamped;
      } else {
        frame = clamped;
      }
      if (pause) {
        setPlaying(false);
      }
      applyFrame();
    }

    function syncLabTimelineScrub() {
      if (!scrubEl) {
        return;
      }
      const max = getMaxTimelineIndex();
      scrubEl.min = "0";
      scrubEl.max = String(max);
      const noFrames =
        (hasServerReplay && replayFrames.length === 0) || (!hasServerReplay && TOTAL_FRAMES <= 0);
      scrubEl.disabled = noFrames;
      if (!noFrames) {
        const cur = getCurrentTimelineIndex();
        scrubEl.value = String(clampNumber(cur, 0, max));
      }
    }

    function getCurrentReplayFrame() {
      if (!hasServerReplay) return null;
      return replayFrames[replayArrayIndex] || null;
    }

    function applyFrame() {
      if (hasServerReplay) {
        if (replayArrayIndex < 0) replayArrayIndex = 0;
        if (replayArrayIndex >= replayFrames.length) replayArrayIndex = replayFrames.length - 1;
        const fr = getCurrentReplayFrame();
        renderReplayFrame(fr, baseClasses, domCells, resolveCellIndex, replayFrames);
        updateFrameInfo(fr, replayFrames.length, phaseEl, frameEl, gridEl, replayArrayIndex);
        updateReplayTruncationHud(fr, replayTrackMetrics);
        const cycle = document.getElementById("lab-computation-cycle");
        if (cycle) {
          if (fr && fr.inspector && fr.inspector.source_frame_index != null) {
            cycle.textContent =
              "source_frame_index " + String(fr.inspector.source_frame_index);
          } else if (fr && fr.frame_key != null) {
            cycle.textContent = "frame_key " + String(fr.frame_key);
          } else {
            cycle.textContent = formatLabFrameCounter(replayArrayIndex, replayFrames.length);
          }
        }
        const hint = document.getElementById("lab-replay-footer-hint");
        if (hint) {
          if (fr && fr.description) {
            hint.textContent = String(fr.description);
          } else if (fr && fr.inspector) {
            const optEv = fr.inspector.optimization_event_type;
            const labEv = fr.inspector.lab_event_type;
            hint.textContent = optEv
              ? "optimization " + String(optEv)
              : labEv
                ? "lab " + String(labEv)
                : "replay frame";
          } else {
            hint.textContent =
              fr && fr.id != null
                ? "ReplayFrame id " + String(fr.id) + (fr.is_keyframe ? " · keyframe" : "")
                : "—";
          }
        }
        syncLabTimelineScrub();
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
      if (frameEl) frameEl.textContent = formatLabFrameCounter(frame, TOTAL_FRAMES);
      if (gridEl) gridEl.dataset.overlay = overlay;
      const cycle = document.getElementById("lab-computation-cycle");
      if (cycle) cycle.textContent = "computation_cycle #" + String(frame);
      syncLabTimelineScrub();
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

    function runDetailStatusLabel(run) {
      if (!run || typeof run !== "object") return "—";
      if (run.status === "failed" || run.validation_passed === false) {
        return "validation failed";
      }
      if (runCapacityFailed(run)) {
        return capacityFailedStatusText(run);
      }
      if (run.status === "completed" || run.run_success === true) {
        return "completed";
      }
      return run.status != null ? String(run.status) : "—";
    }

    function labUiDash() {
      return "—";
    }

    /** Map persisted issue_code enum values to gettext msgids (never show raw snake_case). */
    function formatLabIssueCodeLabel(code, run) {
      if (code == null || code === "") {
        return labUiDash();
      }
      const key = String(code);
      const tt =
        run && run.throughput_target && typeof run.throughput_target === "object"
          ? run.throughput_target
          : null;
      if (key === "throughput_target_shortfall" && tt) {
        const dash = labUiDash();
        const shortfall = tt.throughput_shortfall_per_min;
        if (shortfall != null && shortfall !== dash) {
          const perMinLabel = typeof shapezUiT === "function" ? shapezUiT("/min") : "/min";
          const shortLabel = typeof shapezUiT === "function" ? shapezUiT("Short by") : "Short by";
          return shortLabel + " " + formatCompactNumber(shortfall) + perMinLabel;
        }
      }
      const msgidByCode = {
        throughput_target_shortfall: "throughput target shortfall",
        rttp_validation_failed: "RTTP validation failed",
      };
      const msgid = msgidByCode[key] || key;
      return typeof shapezUiT === "function" ? shapezUiT(msgid) : msgid;
    }

    function formatCompactNumber(value) {
      const dash = labUiDash();
      if (value == null || value === "" || value === dash) return dash;
      const n = Number.parseFloat(String(value));
      if (!Number.isFinite(n)) return String(value);
      return Math.round(n).toLocaleString();
    }

    function formatOutputUnitShort(unit) {
      const dash = labUiDash();
      if (unit == null || unit === "" || unit === dash) return "";
      const u = String(unit);
      if (u === "shapes_per_min") return "shapes/min";
      if (u === "L_per_min") return "L/min";
      return u.replace(/_/g, "/");
    }

    function formatThroughputDetail(value, unit) {
      const dash = labUiDash();
      const num = formatCompactNumber(value);
      if (num === dash) return dash;
      const shortUnit = formatOutputUnitShort(unit);
      return shortUnit ? num + " " + shortUnit : num;
    }

    function buildRunListSubtitle(run) {
      const dash = labUiDash();
      if (!run || typeof run !== "object") return dash;
      const cap = run.capacity && typeof run.capacity === "object" ? run.capacity : {};
      const rec =
        run.reconstruction && typeof run.reconstruction === "object" ? run.reconstruction : {};
      const rttp = run.rttp && typeof run.rttp === "object" ? run.rttp : {};
      const primaryKind =
        cap.primary_resource_kind != null && cap.primary_resource_kind !== dash
          ? String(cap.primary_resource_kind)
          : "shape";
      const theor =
        primaryKind === "fluid"
          ? formatCompactNumber(cap.fluid_max_throughput_per_min)
          : formatCompactNumber(cap.shape_max_throughput_per_min);
      const committed = rttp.confirmed_count != null ? String(rttp.confirmed_count) : dash;
      const tier = rec.quality_tier_short != null ? String(rec.quality_tier_short) : dash;
      const theorPart =
        theor !== dash ? theor + "/min " + (typeof shapezUiT === "function" ? shapezUiT("theor.") : "theor.") : dash;
      const committedPart =
        committed !== dash
          ? committed + " " + (typeof shapezUiT === "function" ? shapezUiT("committed") : "committed")
          : dash;
      return theorPart + " | " + committedPart + " | " + (tier !== dash ? tier : dash);
    }

    function updateLabStatCards(run) {
      const dash = labUiDash();
      const set = function (id, text) {
        const el = document.getElementById(id);
        if (el) el.textContent = text != null ? String(text) : dash;
      };
      if (!run || typeof run !== "object") {
        set("lab-card-theoretical-max-value", dash);
        set("lab-card-resource-capacity-value", dash);
        set("lab-card-footprint-value", dash);
        set("lab-card-reconstruction-quality-value", dash);
        set("lab-card-rttp-committed-value", dash);
        set("lab-card-rttp-committed-sub", dash);
        return;
      }
      const cap = run.capacity && typeof run.capacity === "object" ? run.capacity : {};
      const rec =
        run.reconstruction && typeof run.reconstruction === "object" ? run.reconstruction : {};
      const rttp = run.rttp && typeof run.rttp === "object" ? run.rttp : {};
      const primary =
        cap.primary_resource_kind != null && cap.primary_resource_kind !== dash
          ? String(cap.primary_resource_kind)
          : rec.primary_resource_kind != null && rec.primary_resource_kind !== dash
            ? String(rec.primary_resource_kind)
            : "shape";
      const headline =
        primary === "fluid"
          ? formatCompactNumber(cap.fluid_max_throughput_per_min)
          : formatCompactNumber(cap.reconstruction_max_throughput_per_min);
      set("lab-card-theoretical-max-value", headline);
      const primaryLabel =
        primary === "fluid"
          ? typeof shapezUiT === "function"
            ? shapezUiT("terrain upper bound (fluid)")
            : "terrain upper bound (fluid)"
          : typeof shapezUiT === "function"
            ? shapezUiT("terrain upper bound (shape)")
            : "terrain upper bound (shape)";
      set("lab-card-theoretical-max-sub", primaryLabel);
      const shapeN = formatCompactNumber(cap.shape_max_throughput_per_min);
      const fluidN = formatCompactNumber(cap.fluid_max_throughput_per_min);
      const shapePlatforms = cap.shape_platform_count;
      const fluidPlatforms = cap.fluid_platform_count;
      const shapeLabel = typeof shapezUiT === "function" ? shapezUiT("Shape") : "Shape";
      const fluidLabel = typeof shapezUiT === "function" ? shapezUiT("Fluid") : "Fluid";
      const resourceLines = [];
      if (shapeN !== dash) {
        resourceLines.push(
          shapeLabel + " " + shapeN + " (" + String(shapePlatforms != null ? shapePlatforms : 0) + ")",
        );
      }
      if (fluidPlatforms === 0 || fluidPlatforms === "0") {
        resourceLines.push(fluidLabel + " 0");
      } else if (fluidN !== dash) {
        resourceLines.push(fluidLabel + " " + fluidN + " (" + String(fluidPlatforms) + ")");
      }
      set("lab-card-resource-capacity-value", resourceLines.length ? resourceLines.join(" · ") : dash);
      const confirmed = rec.confirmed_cell_count;
      const displayCells = rec.display_cell_count;
      set(
        "lab-card-footprint-value",
        confirmed !== dash && displayCells !== dash && confirmed != null && displayCells != null
          ? String(confirmed) + " / " + String(displayCells)
          : dash,
      );
      const tierShort = rec.quality_tier_short;
      const conf = rec.confidence_score;
      set(
        "lab-card-reconstruction-quality-value",
        tierShort != null && tierShort !== dash
          ? String(tierShort) + " · " + (conf != null ? String(conf) : dash)
          : dash,
      );
      const tt =
        run.throughput_target && typeof run.throughput_target === "object"
          ? run.throughput_target
          : {};
      const count = rttp.confirmed_count;
      const placementLabel =
        typeof shapezUiT === "function" ? shapezUiT("placement(s)") : "placement(s)";
      const perMinLabel = typeof shapezUiT === "function" ? shapezUiT("/min") : "/min";
      const actualAvailable =
        rttp.actual_output_status === "available" && rttp.actual_committed_output_per_min != null;
      const actualRate = actualAvailable
        ? formatCompactNumber(rttp.actual_committed_output_per_min)
        : dash;
      const budgetStatus =
        tt.budget_status != null && tt.budget_status !== dash ? String(tt.budget_status) : "";
      const hasBudgetChip = budgetStatus === "satisfied" || budgetStatus === "shortfall";
      if (actualAvailable) {
        set("lab-card-rttp-committed-value", actualRate + perMinLabel);
      } else {
        set(
          "lab-card-rttp-committed-value",
          count != null && count !== dash ? String(count) + " " + placementLabel : dash,
        );
      }
      if (hasBudgetChip) {
        const pct =
          tt.throughput_target_percent != null && tt.throughput_target_percent !== dash
            ? String(tt.throughput_target_percent)
            : dash;
        const targetTp =
          tt.target_throughput_per_min != null && tt.target_throughput_per_min !== dash
            ? formatCompactNumber(tt.target_throughput_per_min)
            : dash;
        const targetLabel =
          typeof shapezUiT === "function" ? shapezUiT("Target") : "Target";
        const subLine =
          targetLabel +
          " " +
          pct +
          "% · " +
          actualRate +
          " / " +
          targetTp +
          perMinLabel;
        set("lab-card-rttp-committed-sub", subLine);
      } else if (rttp.actual_output_status === "pending_pr_2b") {
        set(
          "lab-card-rttp-committed-sub",
          typeof shapezUiT === "function"
            ? shapezUiT("actual output pending")
            : "actual output pending",
        );
      } else if (actualAvailable) {
        set("lab-card-rttp-committed-sub", actualRate + perMinLabel);
      } else {
        const unavailableLabel =
          typeof shapezUiT === "function"
            ? shapezUiT("actual output unavailable")
            : "actual output unavailable";
        set("lab-card-rttp-committed-sub", unavailableLabel);
      }
      const chipEl = document.getElementById("lab-card-rttp-committed-chip");
      if (chipEl) {
        if (budgetStatus === "satisfied") {
          chipEl.textContent =
            typeof shapezUiT === "function" ? shapezUiT("Target satisfied") : "Target satisfied";
          chipEl.className = "mt-1 text-xs font-medium text-emerald-400";
          chipEl.classList.remove("hidden");
        } else if (budgetStatus === "shortfall") {
          const shortfall =
            tt.throughput_shortfall_per_min != null && tt.throughput_shortfall_per_min !== dash
              ? formatCompactNumber(tt.throughput_shortfall_per_min)
              : dash;
          const shortLabel =
            typeof shapezUiT === "function" ? shapezUiT("Short by") : "Short by";
          chipEl.textContent = shortLabel + " " + shortfall + perMinLabel;
          chipEl.className = "mt-1 text-xs font-medium text-amber-400";
          chipEl.classList.remove("hidden");
        } else {
          chipEl.textContent = "";
          chipEl.classList.add("hidden");
        }
      }
    }

    function updateLabDetailPanels(run) {
      const dash = labUiDash();
      const set = function (id, text) {
        const el = document.getElementById(id);
        if (el) el.textContent = text != null ? String(text) : dash;
      };
      if (!run || typeof run !== "object") {
        [
          "lab-detail-rec-quality",
          "lab-detail-rec-confidence",
          "lab-detail-rec-primary",
          "lab-detail-rec-display-cells",
          "lab-detail-rec-mineable",
          "lab-detail-rec-shape",
          "lab-detail-rec-fluid",
          "lab-detail-rec-confirmed",
          "lab-detail-rec-ambiguous",
          "lab-detail-rec-void",
          "lab-detail-cap-shape",
          "lab-detail-cap-fluid",
          "lab-detail-cap-platform",
          "lab-detail-cap-source",
          "lab-detail-cap-basis",
          "lab-detail-rttp-confirmed",
          "lab-detail-rttp-validation",
          "lab-detail-rttp-candidates",
          "lab-detail-rttp-commit-order",
          "lab-detail-rttp-output",
          "lab-detail-tt-percent",
          "lab-detail-tt-target",
          "lab-detail-tt-utilization",
          "lab-detail-tt-budget",
          "lab-detail-tt-shortfall",
          "lab-detail-first-issue",
          "lab-detail-issue-coord",
          "lab-detail-issue-candidate",
          "lab-detail-issue-reservation",
          "lab-detail-issue-message",
        ].forEach(function (id) {
          set(id, dash);
        });
        return;
      }
      const rec =
        run.reconstruction && typeof run.reconstruction === "object" ? run.reconstruction : {};
      const cap = run.capacity && typeof run.capacity === "object" ? run.capacity : {};
      const rttp = run.rttp && typeof run.rttp === "object" ? run.rttp : {};
      const tt =
        run.throughput_target && typeof run.throughput_target === "object"
          ? run.throughput_target
          : {};
      set("lab-detail-rec-quality", rec.quality_tier);
      set("lab-detail-rec-confidence", rec.confidence_score);
      set("lab-detail-rec-primary", rec.primary_resource_kind);
      set("lab-detail-rec-display-cells", rec.display_cell_count);
      set("lab-detail-rec-mineable", rec.mineable_cell_count);
      set("lab-detail-rec-shape", rec.shape_confirmed_cell_count);
      set("lab-detail-rec-fluid", rec.fluid_confirmed_cell_count);
      set("lab-detail-rec-confirmed", rec.confirmed_cell_count);
      set("lab-detail-rec-ambiguous", rec.ambiguous_cell_count);
      set("lab-detail-rec-void", rec.external_void_cell_count);
      set(
        "lab-detail-cap-shape",
        formatThroughputDetail(cap.shape_max_throughput_per_min, cap.shape_output_unit),
      );
      set(
        "lab-detail-cap-fluid",
        formatThroughputDetail(cap.fluid_max_throughput_per_min, cap.fluid_output_unit),
      );
      set(
        "lab-detail-cap-platform",
        (cap.shape_platform_count != null ? "shape " + cap.shape_platform_count : "") +
          (cap.fluid_platform_count != null
            ? " · fluid " + cap.fluid_platform_count
            : ""),
      );
      set("lab-detail-cap-source", cap.extraction_rule_source);
      set("lab-detail-cap-basis", cap.capacity_basis);
      set("lab-detail-rttp-confirmed", rttp.confirmed_count);
      set(
        "lab-detail-rttp-validation",
        rttp.validation_passed === true ? "passed" : rttp.validation_passed === false ? "failed" : dash,
      );
      set("lab-detail-rttp-candidates", rttp.candidate_count);
      set("lab-detail-rttp-commit-order", rttp.commit_order_preview);
      set(
        "lab-detail-rttp-output",
        rttp.actual_output_status === "pending_pr_2b"
          ? typeof shapezUiT === "function"
            ? shapezUiT("actual output pending")
            : "actual output pending"
          : rttp.actual_committed_output_per_min != null
            ? String(rttp.actual_committed_output_per_min)
            : dash,
      );
      const pctVal =
        tt.throughput_target_percent != null && tt.throughput_target_percent !== dash
          ? String(tt.throughput_target_percent) + "%"
          : dash;
      set("lab-detail-tt-percent", pctVal);
      set(
        "lab-detail-tt-target",
        tt.target_throughput_per_min != null && tt.target_throughput_per_min !== dash
          ? String(tt.target_throughput_per_min)
          : dash,
      );
      const actualUtil =
        tt.actual_utilization_ratio != null && tt.actual_utilization_ratio !== dash
          ? tt.actual_utilization_ratio
          : dash;
      const maxTp =
        tt.reconstruction_max_throughput_per_min != null &&
        tt.reconstruction_max_throughput_per_min !== dash
          ? tt.reconstruction_max_throughput_per_min
          : cap.reconstruction_max_throughput_per_min;
      const actualOut =
        tt.actual_committed_output_per_min != null && tt.actual_committed_output_per_min !== dash
          ? tt.actual_committed_output_per_min
          : rttp.actual_committed_output_per_min;
      if (actualOut != null && actualOut !== dash && maxTp != null && maxTp !== dash) {
        set(
          "lab-detail-tt-utilization",
          String(actualOut) + " / " + String(maxTp) + " (" + String(actualUtil) + ")",
        );
      } else {
        set("lab-detail-tt-utilization", dash);
      }
      const budgetStatus =
        tt.budget_status != null && tt.budget_status !== dash ? String(tt.budget_status) : dash;
      set("lab-detail-tt-budget", budgetStatus);
      if (budgetStatus === "shortfall") {
        set(
          "lab-detail-tt-shortfall",
          tt.throughput_shortfall_per_min != null && tt.throughput_shortfall_per_min !== dash
            ? String(tt.throughput_shortfall_per_min)
            : dash,
        );
      } else {
        set("lab-detail-tt-shortfall", dash);
      }
      const firstIssueRaw =
        run.first_issue_code != null && run.first_issue_code !== ""
          ? String(run.first_issue_code)
          : Array.isArray(run.issue_codes) && run.issue_codes.length
            ? String(run.issue_codes[0])
            : "";
      set(
        "lab-detail-first-issue",
        firstIssueRaw !== "" ? formatLabIssueCodeLabel(firstIssueRaw, run) : dash,
      );
      const detail = run.first_issue_detail;
      if (detail && typeof detail === "object") {
        set(
          "lab-detail-issue-coord",
          detail.coord != null && Array.isArray(detail.coord)
            ? "[" + detail.coord.join(", ") + "]"
            : dash,
        );
        set(
          "lab-detail-issue-candidate",
          detail.candidate_id != null && detail.candidate_id !== "" ? String(detail.candidate_id) : dash,
        );
        set(
          "lab-detail-issue-reservation",
          detail.route_reservation_id != null && detail.route_reservation_id !== ""
            ? String(detail.route_reservation_id)
            : dash,
        );
        set(
          "lab-detail-issue-message",
          detail.message != null && detail.message !== "" ? String(detail.message) : dash,
        );
      } else {
        set("lab-detail-issue-coord", dash);
        set("lab-detail-issue-candidate", dash);
        set("lab-detail-issue-reservation", dash);
        set("lab-detail-issue-message", dash);
      }
    }

    function setRunDetail(run) {
      const dash = labUiDash();
      if (!run) {
        const title = document.getElementById("lab-detail-run-id");
        if (title) title.textContent = dash;
        const statusEl = document.getElementById("lab-detail-status");
        if (statusEl) statusEl.textContent = dash;
        updateLabStatCards(null);
        updateLabDetailPanels(null);
        return;
      }
      const statusEl = document.getElementById("lab-detail-status");
      if (statusEl) statusEl.textContent = runDetailStatusLabel(run);
      const title = document.getElementById("lab-detail-run-id");
      if (title) {
        title.textContent = run.id != null ? "Run #" + String(run.id) : dash;
      }
      updateLabStatCards(run);
      updateLabDetailPanels(run);
    }

    function evolutionRunButtonClasses(run, selected) {
      const failed = run && (run.status === "failed" || run.validation_passed === false);
      const partial = run && !failed && runCapacityFailed(run);
      if (selected) {
        if (failed) {
          return "w-full rounded-xl border p-3 text-left transition border-rose-500/80 bg-rose-950/40";
        }
        if (partial) {
          return "w-full rounded-xl border p-3 text-left transition border-amber-500/80 bg-amber-950/40";
        }
        return "w-full rounded-xl border p-3 text-left transition border-cyan-500 bg-cyan-500/10";
      }
      if (failed) {
        return "w-full rounded-xl border p-3 text-left transition border-rose-800/80 bg-rose-950/20 hover:border-rose-700";
      }
      if (partial) {
        return "w-full rounded-xl border p-3 text-left transition border-amber-800/80 bg-amber-950/20 hover:border-amber-700";
      }
      return "w-full rounded-xl border p-3 text-left transition border-slate-800 bg-slate-900 hover:border-slate-700";
    }

    function renderEvolutionRunsList(selectedRunId) {
      const list = document.getElementById("lab-evolution-runs-list");
      if (!list) return;
      list.innerHTML = "";
      if (!runs.length) {
        const empty = document.createElement("p");
        empty.className = "text-sm text-slate-500";
        empty.textContent = "No runs";
        list.appendChild(empty);
        return;
      }
      const selected =
        selectedRunId != null ? String(selectedRunId) : runs[0] && runs[0].id ? String(runs[0].id) : null;
      runs.forEach(function (run) {
        if (!run || run.id == null) return;
        const rid = String(run.id);
        const failed = run.status === "failed" || run.validation_passed === false;
        const partial = !failed && runCapacityFailed(run);
        const btn = document.createElement("button");
        btn.type = "button";
        btn.setAttribute("data-lab-run-id", rid);
        btn.className = evolutionRunButtonClasses(run, selected === rid);
        const headlineLabel = failed
          ? "validation failed"
          : partial
            ? "capacity failed (" +
              String(run.rttp && run.rttp.confirmed_count != null ? run.rttp.confirmed_count : "—") +
              "/" +
              String(run.target_miner_bundle_count) +
              ")"
            : "Run #" + rid;
        btn.innerHTML =
          '<div class="flex items-center justify-between gap-2">' +
          '<div class="font-medium">Run #' +
          rid +
          "</div>" +
          '<div class="text-sm ' +
          (failed ? "text-rose-300" : partial ? "text-amber-300" : "text-cyan-300") +
          '">' +
          headlineLabel +
          "</div>" +
          "</div>" +
          '<div class="mt-2 text-xs text-slate-400 lab-run-list-subtitle">' +
          buildRunListSubtitle(run) +
          "</div>";
        if (run.first_issue_code) {
          const issue = document.createElement("p");
          issue.className = "mt-2 truncate text-xs text-rose-300/90";
          const issueLabel = formatLabIssueCodeLabel(run.first_issue_code, run);
          issue.title = issueLabel;
          issue.textContent = issueLabel;
          btn.appendChild(issue);
        }
        btn.addEventListener("click", function () {
          applyRunSelectionHighlight(rid);
          setRunDetail(run);
        });
        list.appendChild(btn);
      });
    }

    function upsertRunSummary(runSummary) {
      if (!runSummary || typeof runSummary !== "object" || runSummary.id == null) {
        return;
      }
      const id = String(runSummary.id);
      runs = [runSummary].concat(
        (runs || []).filter(function (r) {
          return r && String(r.id) !== id;
        }),
      );
      renderEvolutionRunsList(id);
      applyRunSelectionHighlight(id);
      setRunDetail(runSummary);
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

    const resetMapBtn = document.getElementById("lab-header-reset");
    resetMapBtn?.addEventListener("click", function () {
      const resetUrl =
        rootEl && rootEl.dataset && rootEl.dataset.labResetMapUrl
          ? String(rootEl.dataset.labResetMapUrl)
          : "";
      if (!resetUrl) {
        replayRunFeedback = { error_code: "save_project_first" };
        renderReplayRunStatus(replayRunFeedback);
        return;
      }
      if (resetMapBtn.disabled) {
        return;
      }
      const confirmed = window.confirm(
        "Reset map to inspection baseline? Runtime solver data in the database will be removed.",
      );
      if (!confirmed) {
        return;
      }
      resetMapBtn.disabled = true;
      replayRunFeedback = { running: true, reset: true };
      renderReplayRunStatus(replayRunFeedback);
      fetch(resetUrl, {
        method: "POST",
        credentials: "same-origin",
        headers: {
          Accept: "application/json",
          "X-CSRFToken": labCsrfToken(),
        },
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
          const data = bundle.data || {};
          if (!res.ok || data.ok === false || data.replay_ok === false) {
            replayRunFeedback = {
              error_code:
                typeof data.error_code === "string" ? data.error_code : "reset_failed",
            };
            renderReplayRunStatus(replayRunFeedback);
            return;
          }
          replayRunFeedback = null;
          renderReplayRunStatus(replayRunFeedback);
          window.location.assign(window.location.pathname);
        })
        .catch(function () {
          replayRunFeedback = { error_code: "network_error" };
          renderReplayRunStatus(replayRunFeedback);
        })
        .finally(function () {
          syncLabActionButtons();
        });
    });
    syncLabActionButtons();

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

    if (scrubEl) {
      scrubEl.addEventListener("pointerdown", function (event) {
        event.stopPropagation();
        setPlaying(false);
      });
      scrubEl.addEventListener("input", function () {
        setTimelineIndex(scrubEl.value, { pause: true });
      });
    }

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

    function labProjectSlugFromRedirect(redirectUrl) {
      if (!redirectUrl) {
        return "";
      }
      try {
        const u = new URL(redirectUrl, window.location.origin);
        const m = u.pathname.match(/\/asteroid-miner-layout\/p\/([^/]+)\/?/);
        return m ? decodeURIComponent(m[1]) : "";
      } catch {
        return "";
      }
    }

    function syncLabProjectEndpoints(payload) {
      if (!rootEl || !payload || typeof payload !== "object") {
        return;
      }
      let slug =
        typeof payload.project_slug === "string" ? payload.project_slug.trim() : "";
      let runUrl =
        typeof payload.run_solver_url === "string" ? payload.run_solver_url.trim() : "";
      if (!slug && typeof payload.redirect === "string") {
        slug = labProjectSlugFromRedirect(payload.redirect);
      }
      if (slug) {
        rootEl.dataset.labProjectSlug = slug;
      }
      if (runUrl) {
        rootEl.dataset.labRunSolverUrl = runUrl;
      }
      const resetUrl =
        typeof payload.reset_map_url === "string" ? payload.reset_map_url.trim() : "";
      if (resetUrl) {
        rootEl.dataset.labResetMapUrl = resetUrl;
      }
      syncLabActionButtons();
    }

    function syncLabActionButtons() {
      const runUrl =
        rootEl && rootEl.dataset && rootEl.dataset.labRunSolverUrl
          ? String(rootEl.dataset.labRunSolverUrl)
          : "";
      const resetUrl =
        rootEl && rootEl.dataset && rootEl.dataset.labResetMapUrl
          ? String(rootEl.dataset.labResetMapUrl)
          : "";
      const runBtn = document.getElementById("lab-header-run");
      const resetBtn = document.getElementById("lab-header-reset");
      if (runBtn) {
        runBtn.disabled = !runUrl;
        runBtn.classList.toggle("opacity-50", !runUrl);
        runBtn.classList.toggle("cursor-not-allowed", !runUrl);
      }
      if (resetBtn) {
        resetBtn.disabled = !resetUrl;
        resetBtn.classList.toggle("opacity-50", !resetUrl);
        resetBtn.classList.toggle("cursor-not-allowed", !resetUrl);
      }
    }

    function replaceLabReplayPayload(payload, opts) {
      if (!payload || typeof payload !== "object") return;
      syncLabProjectEndpoints(payload);
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
      if (payload.replay_track_metrics && typeof payload.replay_track_metrics === "object") {
        replayTrackMetrics = payload.replay_track_metrics;
      }
      hasServerReplay = replayFrames.length > 0;
      if (!hasServerReplay) {
        window.location.assign(redirectTo || window.location.href);
        return;
      }
      replayCleanup();
      replayCleanup = initializeServerReplaySurface(replayFrames);
      resetLabViewportTransform();
      const seekLast =
        opts && typeof opts === "object" && opts.seekLastFrame === true;
      replayArrayIndex = seekLast
        ? Math.max(0, replayFrames.length - 1)
        : replaySlotForServerInitialFrame();
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
            syncLabProjectEndpoints(data);
            if (data.in_place) {
              replaceLabReplayPayload(data);
              return;
            }
            if (data.redirect) {
              if (typeof history.pushState === "function") {
                try {
                  history.pushState(null, "", data.redirect);
                  syncProjectSlugHiddenFromRedirect(importForm, data.redirect);
                  syncLabProjectEndpoints(data);
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
      const w = labWorldPointFromClient(clientX, clientY);
      const dims = labBaseCellAndGapPx();
      if (!dims || !domCells || !domCells.length) {
        return null;
      }
      const cellPx = dims.cellPx;
      const gapPx = dims.gapPx;
      const gw = dims.gw;
      const gh = dims.gh;
      const stride = cellPx + gapPx;
      let x = 0;
      let col = -1;
      for (let c = 0; c < gw; c++) {
        if (w.wx >= x && w.wx < x + cellPx) {
          col = c;
          break;
        }
        x += stride;
      }
      if (col < 0) {
        return null;
      }
      let y = 0;
      let row = -1;
      for (let r = 0; r < gh; r++) {
        if (w.wy >= y && w.wy < y + cellPx) {
          row = r;
          break;
        }
        y += stride;
      }
      if (row < 0) {
        return null;
      }
      const idx = row * gw + col;
      if (idx < 0 || idx >= domCells.length) {
        return null;
      }
      return domCells[idx] || null;
    }

    function updateLabGridHudEmpty() {
      if (gridHudCoord) {
        gridHudCoord.textContent = "—";
      }
      if (gridHudRole) {
        gridHudRole.textContent = "—";
      }
    }

    function getLabCellDisplayIslandCoord(cellEl) {
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
        gridHudCoord.textContent = getLabCellDisplayIslandCoord(cellEl);
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
      const o = labViewportContentOffset(event.clientX, event.clientY);
      const vx = o.vx;
      const vy = o.vy;
      const oldZoom = labViewportTransform.zoom;
      const zoomFactor = event.deltaY < 0 ? 1.12 : 1 / 1.12;
      const nextZoom = clampNumber(oldZoom * zoomFactor, LAB_VIEWPORT_MIN_SCALE, LAB_VIEWPORT_MAX_SCALE);
      if (nextZoom === oldZoom) {
        updateLabGridHudFromPoint(event.clientX, event.clientY);
        return;
      }
      const z0 = oldZoom;
      const z1 = nextZoom;
      const tx0 = labViewportTransform.tx;
      const ty0 = labViewportTransform.ty;
      labViewportTransform.zoom = nextZoom;
      labViewportTransform.tx = vx - (z1 / z0) * (vx - tx0);
      labViewportTransform.ty = vy - (z1 / z0) * (vy - ty0);
      applyLabViewportTransform();
      updateLabGridHudFromPoint(event.clientX, event.clientY);
    }

    function labPointerShouldStartViewportPan(event) {
      if (!gridViewport || event.button !== 0) {
        return false;
      }
      const t = event.target;
      if (!(t instanceof Element)) {
        return false;
      }
      if (t.closest("#lab-timeline-controls, #lab-timeline-scrub")) {
        return false;
      }
      if (t.closest("input, button, select, textarea, a, label")) {
        return false;
      }
      return true;
    }

    function endLabViewportPan(event) {
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

    function handleLabViewportPointerDown(event) {
      if (!labPointerShouldStartViewportPan(event)) {
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
      endLabViewportPan(event);
    }

    function handleLabViewportPointerLeave(event) {
      updateLabGridHudEmpty();
      endLabViewportPan(event);
    }

    function bindLabViewportInteractions() {
      if (labViewportInteractionsBound || !gridViewport) {
        return;
      }
      labViewportInteractionsBound = true;
      function preventLabViewportSelectDrag(ev) {
        ev.preventDefault();
      }
      gridViewport.addEventListener("dragstart", preventLabViewportSelectDrag);
      gridViewport.addEventListener("selectstart", preventLabViewportSelectDrag);
      if (gridStage) {
        gridStage.addEventListener("dragstart", preventLabViewportSelectDrag);
        gridStage.addEventListener("selectstart", preventLabViewportSelectDrag);
      }
      if (gridEl) {
        gridEl.addEventListener("dragstart", preventLabViewportSelectDrag);
        gridEl.addEventListener("selectstart", preventLabViewportSelectDrag);
      }
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

    let replayRunFeedback = null;
    renderReplayRunStatus(replayRunFeedback);

    const runSolverBtn = document.getElementById("lab-header-run");
    runSolverBtn?.addEventListener("click", function () {
      const runUrl =
        rootEl && rootEl.dataset && rootEl.dataset.labRunSolverUrl
          ? String(rootEl.dataset.labRunSolverUrl)
          : "";
      if (!runUrl) {
        replayRunFeedback = { error_code: "save_project_first" };
        renderReplayRunStatus(replayRunFeedback);
        return;
      }
      if (runSolverBtn.disabled) {
        return;
      }
      runSolverBtn.disabled = true;
      replayRunFeedback = { running: true };
      renderReplayRunStatus(replayRunFeedback);
      const macroOnlyEl = document.getElementById("lab-macro-only-mode");
      const macroOnlyMode = Boolean(macroOnlyEl && macroOnlyEl.checked);
      const runSolverHeaders = {
        Accept: "application/json",
        "X-CSRFToken": labCsrfToken(),
      };
      const runSolverInit = {
        method: "POST",
        credentials: "same-origin",
        headers: runSolverHeaders,
      };
      const percentEl = document.getElementById("lab-throughput-target-percent");
      const postBody = {};
      if (percentEl) {
        const parsed = parseInt(String(percentEl.value), 10);
        if (!Number.isNaN(parsed)) {
          postBody.throughput_target_percent = parsed;
        }
      }
      if (macroOnlyMode) {
        postBody.macro_only_mode = true;
        postBody.rttp_record_replay = true;
      }
      if (Object.keys(postBody).length > 0) {
        runSolverHeaders["Content-Type"] = "application/json";
        runSolverInit.body = JSON.stringify(postBody);
      }
      fetch(runUrl, runSolverInit)
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
          const data = bundle.data || {};
          if (!res.ok || data.ok === false) {
            replayRunFeedback = {
              error_code:
                typeof data.error_code === "string" ? data.error_code : "request_failed",
            };
            if (data.solver_run_id != null) {
              replayRunFeedback.solver_run_id = data.solver_run_id;
              replayRunFeedback.validation_passed = data.validation_passed;
            }
            renderReplayRunStatus(replayRunFeedback);
            if (data.run_summary) {
              upsertRunSummary(data.run_summary);
            }
            if (Array.isArray(data.lab_replay_frames_json)) {
              replaceLabReplayPayload(data);
            }
            return;
          }
          replayRunFeedback = {
            solver_run_id: data.solver_run_id,
            validation_passed: data.validation_passed,
            run_summary: data.run_summary || null,
            gene_template_source: data.gene_template_source || null,
          };
          renderReplayRunStatus(replayRunFeedback);
          if (data.run_summary) {
            upsertRunSummary(data.run_summary);
          }
          replaceLabReplayPayload(data, { seekLastFrame: true });
        })
        .catch(function () {
          replayRunFeedback = { error_code: "network_error" };
          renderReplayRunStatus(replayRunFeedback);
        })
        .finally(function () {
          runSolverBtn.disabled = false;
        });
    });

    const throughputSlider = document.getElementById("lab-throughput-target-percent");
    const throughputSliderLabel = document.getElementById("lab-throughput-target-percent-label");
    function syncThroughputTargetLabel() {
      if (!throughputSlider || !throughputSliderLabel) {
        return;
      }
      throughputSliderLabel.textContent = String(throughputSlider.value) + "%";
    }
    throughputSlider?.addEventListener("input", syncThroughputTargetLabel);
    syncThroughputTargetLabel();

    function labReplayFrameOrmId(fr) {
      if (!fr || typeof fr !== "object") {
        return null;
      }
      if (fr.id != null && fr.id !== "") {
        const legacy = parseInt(String(fr.id), 10);
        if (Number.isFinite(legacy)) {
          return legacy;
        }
      }
      const insp = fr.inspector;
      if (insp && typeof insp === "object" && insp.replay_frame_id != null) {
        const fromInsp = parseInt(String(insp.replay_frame_id), 10);
        if (Number.isFinite(fromInsp)) {
          return fromInsp;
        }
      }
      return null;
    }

    function setLabCellDetailUnavailableHint(message) {
      const hint = document.getElementById("lab-replay-footer-hint");
      if (hint) {
        hint.textContent = message;
      }
    }

    function labCellMatchesWorldXY(cell, x, y) {
      if (!cell || typeof cell !== "object") {
        return false;
      }
      const cx = Number(cell.x);
      const cy = Number(cell.y);
      return Number.isFinite(cx) && Number.isFinite(cy) && cx === x && cy === y;
    }

    function labTimelineWireCellToDetail(cell) {
      if (!cell || typeof cell !== "object") {
        return null;
      }
      const out = {
        x: cell.x,
        y: cell.y,
        rotation: cell.rotation != null ? cell.rotation : 0,
        cell_kind: cell.kind != null ? cell.kind : cell.cell_kind != null ? cell.cell_kind : "",
        transport_kind:
          cell.transport != null ? cell.transport : cell.transport_kind != null ? cell.transport_kind : "",
        tile_type:
          cell.tile_type != null
            ? String(cell.tile_type)
            : cell.sprite_identifier != null
              ? String(cell.sprite_identifier)
              : "",
      };
      if (cell.layer != null) {
        out.layer = cell.layer;
      }
      return out;
    }

    function labCellDetailLookupInMapView(mapView, x, y) {
      if (!mapView || typeof mapView !== "object") {
        return { cell: null, sources: {} };
      }
      const sources = {};
      const layers = [];
      const full = mapView.full_cells;
      if (Array.isArray(full)) {
        for (let i = 0; i < full.length; i++) {
          const c = full[i];
          if (labCellMatchesWorldXY(c, x, y)) {
            sources.map_view_full_cells = c;
            const mapped = labTimelineWireCellToDetail(c);
            if (mapped) {
              layers.push(mapped);
            }
          }
        }
      }
      const delta = mapView.cell_delta;
      if (Array.isArray(delta)) {
        for (let j = 0; j < delta.length; j++) {
          const d = delta[j];
          if (labCellMatchesWorldXY(d, x, y)) {
            sources.map_view_cell_delta = d;
            const mapped = labTimelineWireCellToDetail(d);
            if (mapped) {
              layers.push(mapped);
            }
          }
        }
      }
      const overlay = mapView.overlay_cells;
      if (Array.isArray(overlay)) {
        const matches = [];
        for (let k = 0; k < overlay.length; k++) {
          const o = overlay[k];
          if (labCellMatchesWorldXY(o, x, y)) {
            matches.push(o);
            const mapped = labTimelineWireCellToDetail(o);
            if (mapped) {
              layers.push(mapped);
            }
          }
        }
        if (matches.length) {
          sources.map_view_overlay_cells = matches.length === 1 ? matches[0] : matches;
        }
      }
      if (!layers.length) {
        return { cell: null, sources: sources };
      }
      const merged = {};
      for (let m = 0; m < layers.length; m++) {
        Object.assign(merged, layers[m]);
      }
      return { cell: merged, sources: sources };
    }

    function labCellDetailFromTimelineFrame(fr, x, y) {
      const lookup = labCellDetailLookupInMapView(fr.map_view, x, y);
      const payload = {
        ok: true,
        cell: lookup.cell,
        sources: lookup.sources,
        message: lookup.cell ? "" : "no_cell_at_xy",
        frame_index: fr.frame_index != null ? fr.frame_index : null,
      };
      if (fr.event_type != null) {
        payload.event_type = String(fr.event_type);
      }
      const insp = fr.inspector;
      if (insp && insp.optimization_event_type != null) {
        payload.optimization_event_type = String(insp.optimization_event_type);
      }
      if (lookup.sources.map_view_full_cells || lookup.sources.map_view_cell_delta) {
        payload.detail_source = "map_view_client";
      } else if (Object.keys(lookup.sources).length) {
        payload.detail_source = "map_view_overlay_client";
      }
      return payload;
    }

    const LAB_CELL_DETAIL_KEY_ORDER = [
      "x",
      "y",
      "layer",
      "rotation",
      "cell_kind",
      "tile_type",
      "transport_kind",
    ];

    function labCellDetailIsSuppressedKey(key) {
      return String(key || "").startsWith("server_");
    }

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
          return !seen[k] && !labCellDetailIsSuppressedKey(k);
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
        let dd = labCellDetailFormatValue(obj[k]);
        if (k === "rotation") {
          dd +=
            ' <span class="whitespace-nowrap text-xs text-slate-500">(East=0, clockwise)</span>';
        }
        rows +=
          '<div class="grid grid-cols-[minmax(0,auto)_1fr] gap-x-3 border-b border-slate-800/80 py-2 last:border-b-0">' +
          '<dt class="shrink-0 font-mono text-xs text-slate-500">' +
          labCellDetailEscapeHtml(k) +
          "</dt>" +
          '<dd class="min-w-0 text-slate-200">' +
          dd +
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
          '<h3 class="text-xs font-semibold uppercase tracking-wide text-slate-400">Sources</h3>' +
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
        if (!fr) {
          setLabCellDetailUnavailableHint("cell detail unavailable (no replay frame)");
          return;
        }
        const frameOrmId = labReplayFrameOrmId(fr);
        const cellUrl = rootEl && rootEl.dataset ? rootEl.dataset.labReplayCellUrl || "" : "";
        const trackIdStr =
          rootEl && rootEl.dataset && rootEl.dataset.labReplayTrackId != null
            ? String(rootEl.dataset.labReplayTrackId)
            : "";
        if (!cellUrl || !trackIdStr) {
          setLabCellDetailUnavailableHint("cell detail unavailable (replay track not configured)");
          return;
        }
        if (frameOrmId == null) {
          openCellDetailModal();
          if (cellDetailBody) {
            labCellDetailRenderSuccess(cellDetailBody, labCellDetailFromTimelineFrame(fr, xy.x, xy.y));
          }
          setLabCellDetailUnavailableHint("cell detail from map_view (no persisted ReplayFrame)");
          return;
        }
        const projectSlug =
          rootEl && rootEl.dataset && rootEl.dataset.labProjectSlug != null
            ? String(rootEl.dataset.labProjectSlug)
            : "";
        const payload = {
          replay_frame_id: frameOrmId,
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
        renderReplayFrame(fr, baseClasses, domCells, resolveCellIndex, replayFrames);
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
        updateFrameInfo(
          fr,
          hasServerReplay ? replayFrames.length : 0,
          phaseEl,
          frameEl,
          gridEl,
          replayArrayIndex,
        );
      },
      collectOverlayPaintTargets: collectOverlayPaintTargets,
      visualCol: visualCol,
      rawXToDenseX: rawXToDenseX,
      replaceLabReplayPayload: replaceLabReplayPayload,
    };

    applyLabGridLayoutForZoom();
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
