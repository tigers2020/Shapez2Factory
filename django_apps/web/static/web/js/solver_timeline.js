import { TIMELINE_DEBOUNCE_MS } from "./solver_timeline/constants.js";
import { mountGraph } from "./solver_timeline/graph_mount.js";
import { requestTimeline } from "./solver_timeline/timeline_request.js";

/*
Runtime graph compatibility markers for smoke tests:
- data-graph-viewport
- style="height: 34rem; touch-action: none; cursor: grab;
- transform-origin: 0 0;
- viewport.style.cursor = "grabbing"
- preview_image_url
- No preview
- ./solver_graph_layout.js
*/

function scheduleTimeline(panel, input) {
  panel._timelineSeq = (panel._timelineSeq || 0) + 1;
  const seq = panel._timelineSeq;
  clearTimeout(panel._timelineTimer);
  panel._timelineTimer = setTimeout(() => {
    requestTimeline(panel, input.value.trim(), seq);
  }, TIMELINE_DEBOUNCE_MS);
}

function syncQuantityToggleUi(panel) {
  const button = panel.querySelector("[data-graph-quantity-toggle]");
  if (!button) {
    return;
  }
  const on = panel.dataset.graphQuantityReplicas === "on";
  button.setAttribute("aria-pressed", on ? "true" : "false");
  button.classList.toggle("border-cyan-400/50", on);
  button.classList.toggle("bg-cyan-500/10", on);
  button.classList.toggle("text-cyan-100", on);
  button.classList.toggle("border-slate-700", !on);
  button.classList.toggle("bg-slate-950/60", !on);
  button.classList.toggle("text-slate-300", !on);
}

function initQuantityReplicaToggle(panel) {
  panel.dataset.graphQuantityReplicas = panel.dataset.graphQuantityReplicas || "off";
  syncQuantityToggleUi(panel);

  const button = panel.querySelector("[data-graph-quantity-toggle]");
  if (!button) {
    return;
  }

  button.addEventListener("click", async () => {
    panel.dataset.graphQuantityReplicas =
      panel.dataset.graphQuantityReplicas === "on" ? "off" : "on";
    syncQuantityToggleUi(panel);
    const graph =
      panel.dataset.graphQuantityReplicas === "on"
        ? panel._materializedSolverGraph || panel._rawSolverGraph
        : panel._rawSolverGraph;
    if (graph) {
      await mountGraph(panel, graph);
    }
  });
}

function initSolverTimeline(panel) {
  const inputSelector = panel.dataset.codeInput;
  const input = inputSelector ? document.querySelector(inputSelector) : null;
  if (!input) {
    return;
  }

  initQuantityReplicaToggle(panel);
  input.addEventListener("input", () => scheduleTimeline(panel, input));
  input.addEventListener("change", () => scheduleTimeline(panel, input));
  scheduleTimeline(panel, input);
}

if (typeof document !== "undefined") {
  document.querySelectorAll("[data-solver-timeline]").forEach(initSolverTimeline);
}
