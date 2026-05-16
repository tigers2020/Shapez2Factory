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
    "lab-cell shrink-0 rounded-[5px] border bg-slate-950 border-slate-900";

  const rawTotal = window.__ASTEROID_LAB_TOTAL_FRAMES__;
  const TOTAL_FRAMES = Number.isFinite(rawTotal) ? rawTotal : 0;

  /** Extra empty cells beyond union bbox on each side (visual col / row), symmetric around (1,0). */
  const REPLAY_GRID_EDGE_PADDING = 5;

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

  /** World x to dense visual column; x === 0 is invalid (null). */
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
    const ov = frame.cell_overlay_json;
    if (ov && typeof ov === "object") {
      pushCellList(out, ov.issue_cells, "issue");
    }
    return out;
  }

  /** Collect drawable cells from tolerant overlay shapes (decode / existing_layout). */
  function collectOverlayPaintTargets(overlay) {
    const out = [];
    if (!overlay || typeof overlay !== "object") return out;

    pushCellList(out, overlay.cells, "");
    pushCellList(out, overlay.equipment_cells, "equipment");
    pushCellList(out, overlay.equipment, "equipment");
    pushCellList(out, overlay.issue_cells, "issue");
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
      "issue_cells",
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
    if (r === "issue" || (cell && cell.issue_code)) {
      return "ring-1 ring-inset ring-red-500/70 bg-red-950/30";
    }
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
    if (ck === "internal_void") {
      return "ring-1 ring-inset ring-zinc-500/50 bg-zinc-900/35";
    }
    if (ck === "space_pipe" || ck === "space_belt") {
      return "ring-1 ring-inset ring-cyan-400/40 bg-cyan-950/20";
    }
    if (ck === "fluid_miner" || ck === "shape_miner") {
      return "ring-1 ring-inset ring-amber-400/50 bg-amber-950/20";
    }
    if (ck === "fluid_miner_extension" || ck === "shape_miner_extension") {
      return "ring-1 ring-inset ring-amber-300/40 bg-amber-950/12";
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
      const idx = resolveCellIndex(cell.x, cell.y);
      if (idx == null || idx < 0 || idx >= domCells.length) continue;
      const base = baseClasses[idx] || "";
      const tone = toneForFullMapCell(cell);
      const el = domCells[idx];
      el.className = base + " " + tone;
      if (cell.cell_kind != null) el.setAttribute("data-cell-kind", String(cell.cell_kind));
    }
  }

  function renderDiffOverlays(baseClasses, domCells, frame, resolveCellIndex) {
    const targets = collectDiffPaintTargets(frame);
    for (let i = 0; i < targets.length; i++) {
      const cell = targets[i].cell;
      const role = targets[i].role;
      const idx = resolveCellIndex(cell.x, cell.y);
      if (idx == null || idx < 0 || idx >= domCells.length) continue;
      const tone = toneForDiffRole(role);
      if (!tone) continue;
      const base = baseClasses[idx] || "";
      const el = domCells[idx];
      el.className = base + " " + tone;
      el.setAttribute("data-overlay-role", role);
    }
  }

  function renderIssueOverlayOnly(baseClasses, domCells, overlay, resolveCellIndex) {
    const list = overlay && typeof overlay === "object" ? overlay.issue_cells : null;
    if (!Array.isArray(list)) return;
    for (let i = 0; i < list.length; i++) {
      const cell = list[i];
      if (!cell || typeof cell !== "object") continue;
      const idx = resolveCellIndex(cell.x, cell.y);
      if (idx == null || idx < 0 || idx >= domCells.length) continue;
      const base = baseClasses[idx] || "";
      const tone = overlayToneClasses("issue", cell);
      const el = domCells[idx];
      el.className = base + " " + tone;
      if (cell.cell_kind != null) el.setAttribute("data-cell-kind", String(cell.cell_kind));
      el.setAttribute("data-overlay-role", "issue");
    }
  }

  function renderDecodedCells(baseClasses, domCells, cells, resolveCellIndex) {
    if (!Array.isArray(cells)) return;
    const targets = [];
    pushCellList(targets, cells, "");
    for (let i = 0; i < targets.length; i++) {
      const cell = targets[i].cell;
      const idx = resolveCellIndex(cell.x, cell.y);
      if (idx == null || idx < 0 || idx >= domCells.length) continue;
      const base = baseClasses[idx] || "";
      const tone = overlayToneClasses("decode", cell);
      const el = domCells[idx];
      el.className = base + " " + tone;
      if (cell.cell_kind != null) el.setAttribute("data-cell-kind", String(cell.cell_kind));
    }
  }

  function renderExistingLayoutOverlay(baseClasses, domCells, overlay, resolveCellIndex) {
    const targets = collectOverlayPaintTargets(overlay);
    for (let i = 0; i < targets.length; i++) {
      const cell = targets[i].cell;
      const role = targets[i].role;
      const idx = resolveCellIndex(cell.x, cell.y);
      if (idx == null || idx < 0 || idx >= domCells.length) continue;
      const base = baseClasses[idx] || "";
      const tone = overlayToneClasses(role, cell);
      const el = domCells[idx];
      el.className = base + " " + tone;
      if (cell.cell_kind != null) el.setAttribute("data-cell-kind", String(cell.cell_kind));
      if (role) el.setAttribute("data-overlay-role", role);
    }
  }

  function renderCellOverlay(baseClasses, domCells, overlay, resolveCellIndex) {
    if (!overlay || typeof overlay !== "object") return;
    const cells = overlay.cells;
    if (Array.isArray(cells) && cells.length > 0) {
      renderDecodedCells(baseClasses, domCells, cells, resolveCellIndex);
      return;
    }
    renderExistingLayoutOverlay(baseClasses, domCells, overlay, resolveCellIndex);
  }

  function resetGridBase(domCells, baseClasses) {
    for (let i = 0; i < domCells.length; i++) {
      domCells[i].className = baseClasses[i] || "";
      domCells[i].removeAttribute("data-cell-kind");
      domCells[i].removeAttribute("data-overlay-role");
    }
  }

  function renderReplayFrame(frame, baseClasses, domCells, resolveCellIndex) {
    resetGridBase(domCells, baseClasses);
    if (!frame || typeof frame !== "object") return;
    const fm = fullMapCellsFromFrame(frame);
    if (fm.length) {
      renderFullMapCells(baseClasses, domCells, fm, resolveCellIndex);
      renderDiffOverlays(baseClasses, domCells, frame, resolveCellIndex);
      const ov = frame.cell_overlay_json;
      if (ov && typeof ov === "object" && Array.isArray(ov.issue_cells) && ov.issue_cells.length) {
        renderIssueOverlayOnly(baseClasses, domCells, ov, resolveCellIndex);
      }
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
    const bootStartedWithServerReplay = hasServerReplay;

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

    let domCells;
    let baseClasses;
    let resolveCellIndex = cellIndexDemo;
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

      resolveCellIndex = function (x, y) {
        const d = visualCol(x);
        if (d == null) return null;
        const yi = Number(y);
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

      applyReplayGridSizing();
      resizeObserver = null;
      replayResizeMode = null;
      if (gridViewport && typeof ResizeObserver !== "undefined") {
        resizeObserver = new ResizeObserver(function () {
          applyReplayGridSizing();
        });
        resizeObserver.observe(gridViewport);
        replayResizeMode = "observer";
      } else if (gridViewport) {
        window.addEventListener("resize", applyReplayGridSizing);
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
          window.removeEventListener("resize", applyReplayGridSizing);
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
    const parseFrame = function (v, fallback) {
      const n = parseInt(String(v), 10);
      return Number.isNaN(n) ? fallback : n;
    };
    const datasetFrame = parseFrame(rootEl?.dataset.labInitialFrame, 0);
    const baselineFrame = parseFrame(initialFromServer.frame, datasetFrame);
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
      const next = Array.isArray(payload.lab_replay_frames_json) ? payload.lab_replay_frames_json : [];
      replayFrames = next;
      hasServerReplay = replayFrames.length > 0;
      if (!hasServerReplay || !bootStartedWithServerReplay) {
        window.location.assign(redirectTo || window.location.href);
        return;
      }
      if (!payload.replay_ok && next.length === 0) {
        window.location.assign(redirectTo || window.location.href);
        return;
      }
      replayCleanup();
      replayCleanup = initializeServerReplaySurface(replayFrames);
      replayArrayIndex = replaySlotForServerInitialFrame();
      setPlaying(false);
      applyFrame();
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
            window.location.assign(data.redirect);
          })
          .catch(function () {
            importForm.submit();
          });
      });
    }

    window.AsteroidLabReplay = {
      getCurrentReplayFrame: getCurrentReplayFrame,
      renderReplayFrame: function (fr) {
        renderReplayFrame(fr, baseClasses, domCells, resolveCellIndex);
      },
      renderCellOverlay: function (ov) {
        resetGridBase(domCells, baseClasses);
        renderCellOverlay(baseClasses, domCells, ov, resolveCellIndex);
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
      replaceLabReplayPayload: replaceLabReplayPayload,
    };

    setRunDetail(baselineRun);
    applyFrame();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
