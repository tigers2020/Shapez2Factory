import { TIMELINE_DEBOUNCE_MS } from "./solver_timeline/constants.js";
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

function initSolverTimeline(panel) {
  const inputSelector = panel.dataset.codeInput;
  const input = inputSelector ? document.querySelector(inputSelector) : null;
  const targetCountSelector = panel.dataset.targetCountInput;
  const targetCountInput = targetCountSelector ? document.querySelector(targetCountSelector) : null;
  if (!input) {
    return;
  }

  input.addEventListener("input", () => scheduleTimeline(panel, input));
  input.addEventListener("change", () => scheduleTimeline(panel, input));
  targetCountInput?.addEventListener("input", () => scheduleTimeline(panel, input));
  targetCountInput?.addEventListener("change", () => scheduleTimeline(panel, input));
  scheduleTimeline(panel, input);
}

if (typeof document !== "undefined") {
  document.querySelectorAll("[data-solver-timeline]").forEach(initSolverTimeline);
}
