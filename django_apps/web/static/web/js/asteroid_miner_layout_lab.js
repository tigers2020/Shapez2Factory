/**
 * Client-side replay controls for the asteroid mining lab page (shell UI).
 */
(function () {
  "use strict";

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

  function init() {
    const matrix = readJsonScript("lab-cell-overlay-matrix-data");
    const runs = readJsonScript("lab-runs-data");
    const uiInitial = readJsonScript("lab-ui-initial-state");
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

    function applyFrame() {
      if (frame < 0) frame = 0;
      if (frame > TOTAL_FRAMES) frame = TOTAL_FRAMES;
      const overlay = TOTAL_FRAMES <= 0 ? "candidates" : replayOverlayForFrame(frame);
      const oi = overlayIndex(overlay);
      for (let i = 0; i < cells.length; i++) {
        const row = matrix[i];
        if (row && row[oi]) {
          cells[i].className = row[oi];
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
      if (wantPlay && TOTAL_FRAMES <= 0) {
        wantPlay = false;
      }
      isPlaying = wantPlay;
      if (timerId !== null) {
        window.clearInterval(timerId);
        timerId = null;
      }
      if (isPlaying && TOTAL_FRAMES > 0) {
        timerId = window.setInterval(function () {
          frame += 1;
          if (frame >= TOTAL_FRAMES) frame = 0;
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
      frame = baselineFrame;
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
      frame = Math.max(0, frame - 1);
      applyFrame();
    });

    playBtn?.addEventListener("click", function () {
      if (TOTAL_FRAMES <= 0) return;
      setPlaying(!isPlaying);
      applyFrame();
    });

    document.getElementById("lab-timeline-next")?.addEventListener("click", function () {
      frame = Math.min(TOTAL_FRAMES, frame + 1);
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

    setRunDetail(baselineRun);
    applyFrame();
  }

  if (document.readyState === "loading") {
    document.addEventListener("DOMContentLoaded", init);
  } else {
    init();
  }
})();
