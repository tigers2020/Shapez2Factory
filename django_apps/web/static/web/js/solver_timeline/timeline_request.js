import { clearStepsHost, setBanner, setStepsHtml } from "./dom_utils.js";
import { mountGraph } from "./graph_mount.js";
import { updateThroughputSummary } from "./throughput_summary.js";

export async function requestTimeline(panel, code, seq) {
  const graphCanvas = panel.querySelector("[data-solver-graph-canvas]");
  const emptyEl = panel.querySelector("[data-solver-graph-empty]");
  const errorEl = panel.querySelector("[data-solver-timeline-error]");
  const warningsEl = panel.querySelector("[data-solver-timeline-warnings]");
  const apiUrl = panel.dataset.solverApi;
  const targetCountInputSelector = panel.dataset.targetCountInput;
  const targetCountInput = targetCountInputSelector
    ? document.querySelector(targetCountInputSelector)
    : null;
  const detailHost = panel.querySelector("[data-solver-node-detail]");
  const targetCount = Number.parseInt(targetCountInput?.value || "1", 10);

  if (!graphCanvas || !apiUrl) {
    return;
  }

  if (!code) {
    clearStepsHost(graphCanvas);
    if (detailHost) {
      clearStepsHost(detailHost);
    }
    updateThroughputSummary(panel, {}, false);
    setBanner(errorEl, "", false);
    setBanner(warningsEl, "", false);
    emptyEl?.classList.remove("hidden");
    return;
  }

  emptyEl?.classList.add("hidden");
  setStepsHtml(graphCanvas, '<p class="text-xs text-slate-500">Solving target shape...</p>');

  let data;
  try {
    const res = await fetch(apiUrl, {
      method: "POST",
      headers: {
        Accept: "application/json",
        "Content-Type": "application/json",
        "X-CSRFToken": panel.dataset.csrfToken || "",
      },
      body: JSON.stringify({
        code,
        target_count: Number.isFinite(targetCount) && targetCount > 0 ? targetCount : 1,
      }),
    });
    data = await res.json();
  } catch {
    if (seq !== panel._timelineSeq) {
      return;
    }
    clearStepsHost(graphCanvas);
    updateThroughputSummary(panel, {}, false);
    setBanner(errorEl, "Could not reach solver service.", true);
    setBanner(warningsEl, "", false);
    return;
  }

  if (seq !== panel._timelineSeq) {
    return;
  }

  if (!data.ok) {
    clearStepsHost(graphCanvas);
    updateThroughputSummary(panel, {}, false);
    const errorText =
      typeof data.error === "string"
        ? data.error
        : data.error?.message || "Could not solve this shape code.";
    setBanner(errorEl, errorText, true);
    setBanner(warningsEl, "", false);
    return;
  }

  setBanner(errorEl, "", false);
  const warnings = data.warnings || [];
  setBanner(warningsEl, warnings.join(" "), warnings.length > 0);
  updateThroughputSummary(panel, data, true);

  const graph = data.graph;
  if (!graph?.nodes?.length) {
    clearStepsHost(graphCanvas);
    emptyEl?.classList.remove("hidden");
    return;
  }

  await mountGraph(panel, graph);
}
