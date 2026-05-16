/**
 * Client-side replay controls for the asteroid mining lab page (shell UI).
 */
(function () {
  "use strict";

  const GRID_W = 23;
  const GRID_H = 15;

  const rawTotal = window.__ASTEROID_LAB_TOTAL_FRAMES__;
  const TOTAL_FRAMES = Number.isFinite(rawTotal) ? rawTotal : 0;

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

  function cellIndex(x, y) {
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
    return "ring-1 ring-inset ring-violet-400/35 bg-violet-950/15";
  }

  function renderDecodedCells(baseClasses, domCells, cells) {
    if (!Array.isArray(cells)) return;
    const targets = [];
    pushCellList(targets, cells, "");
    for (let i = 0; i < targets.length; i++) {
      const cell = targets[i].cell;
      const idx = cellIndex(cell.x, cell.y);
      if (idx == null || idx < 0 || idx >= domCells.length) continue;
      const base = baseClasses[idx] || "";
      const tone = overlayToneClasses("decode", cell);
      const el = domCells[idx];
      el.className = base + " " + tone;
      if (cell.cell_kind != null) el.setAttribute("data-cell-kind", String(cell.cell_kind));
    }
  }

  function renderExistingLayoutOverlay(baseClasses, domCells, overlay) {
    const targets = collectOverlayPaintTargets(overlay);
    for (let i = 0; i < targets.length; i++) {
      const cell = targets[i].cell;
      const role = targets[i].role;
      const idx = cellIndex(cell.x, cell.y);
      if (idx == null || idx < 0 || idx >= domCells.length) continue;
      const base = baseClasses[idx] || "";
      const tone = overlayToneClasses(role, cell);
      const el = domCells[idx];
      el.className = base + " " + tone;
      if (cell.cell_kind != null) el.setAttribute("data-cell-kind", String(cell.cell_kind));
      if (role) el.setAttribute("data-overlay-role", role);
    }
  }

  function renderCellOverlay(baseClasses, domCells, overlay) {
    if (!overlay || typeof overlay !== "object") return;
    const cells = overlay.cells;
    if (Array.isArray(cells) && cells.length > 0) {
      renderDecodedCells(baseClasses, domCells, cells);
      return;
    }
    renderExistingLayoutOverlay(baseClasses, domCells, overlay);
  }

  function resetGridBase(domCells, baseClasses) {
    for (let i = 0; i < domCells.length; i++) {
      domCells[i].className = baseClasses[i] || "";
      domCells[i].removeAttribute("data-cell-kind");
      domCells[i].removeAttribute("data-overlay-role");
    }
  }

  function renderReplayFrame(frame, baseClasses, domCells) {
    resetGridBase(domCells, baseClasses);
    if (!frame || typeof frame !== "object") return;
    const ov = frame.cell_overlay_json;
    if (ov && typeof ov === "object") {
      renderCellOverlay(baseClasses, domCells, ov);
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
    const replayFrames = Array.isArray(replayFramesRaw) ? replayFramesRaw : [];
    const hasServerReplay = replayFrames.length > 0;

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

    if (!matrix || !Array.isArray(matrix) || cells.length !== matrix.length) {
      return;
    }

    const domCells = Array.prototype.slice.call(cells);
    const baseClasses = domCells.map(function (el) {
      return String(el.className || "");
    });

    const rootEl = document.getElementById("lab-root");
    const parseFrame = function (v, fallback) {
      const n = parseInt(String(v), 10);
      return Number.isNaN(n) ? fallback : n;
    };
    const datasetFrame = parseFrame(rootEl?.dataset.labInitialFrame, 0);
    const initialFromServer = uiInitial && typeof uiInitial === "object" ? uiInitial : {};
    const baselineFrame = parseFrame(initialFromServer.frame, datasetFrame);
    const baselineBlueprint =
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

    let frame = baselineFrame;
    let isPlaying = false;
    let timerId = null;

    let replayArrayIndex = 0;

    function getCurrentReplayFrame() {
      if (!hasServerReplay) return null;
      return replayFrames[replayArrayIndex] || null;
    }

    function applyFrame() {
      if (hasServerReplay) {
        if (replayArrayIndex < 0) replayArrayIndex = 0;
        if (replayArrayIndex >= replayFrames.length) replayArrayIndex = replayFrames.length - 1;
        const fr = getCurrentReplayFrame();
        renderReplayFrame(fr, baseClasses, domCells);
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
        replayArrayIndex = 0;
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

    window.AsteroidLabReplay = {
      getCurrentReplayFrame: getCurrentReplayFrame,
      renderReplayFrame: function (fr) {
        renderReplayFrame(fr, baseClasses, domCells);
      },
      renderCellOverlay: function (ov) {
        resetGridBase(domCells, baseClasses);
        renderCellOverlay(baseClasses, domCells, ov);
      },
      renderDecodedCells: function (list) {
        resetGridBase(domCells, baseClasses);
        renderDecodedCells(baseClasses, domCells, list);
      },
      renderExistingLayoutOverlay: function (ov) {
        resetGridBase(domCells, baseClasses);
        renderExistingLayoutOverlay(baseClasses, domCells, ov);
      },
      updateFrameInfo: function (fr) {
        updateFrameInfo(fr, hasServerReplay ? replayFrames.length : 0, phaseEl, frameEl, gridEl);
      },
      collectOverlayPaintTargets: collectOverlayPaintTargets,
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
