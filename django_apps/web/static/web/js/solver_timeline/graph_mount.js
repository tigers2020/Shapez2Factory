import { initGraphViewport } from "./graph_viewport.js";
import { renderSelectedNodeDetail } from "./graph_detail.js";
import { renderSolverGraph } from "./graph_markup.js";
import { setStepsHtml } from "./dom_utils.js";

function initGraphPreviewFallbacks(canvas) {
  canvas.querySelectorAll("[data-graph-preview-image]").forEach((img) => {
    const fallback = img.parentElement?.querySelector("[data-graph-preview-fallback]");
    if (!fallback) {
      return;
    }

    const showFallback = () => {
      img.classList.add("hidden");
      fallback.classList.remove("hidden");
    };

    img.addEventListener("error", showFallback, { once: true });
    if (img.complete && typeof img.naturalWidth === "number" && img.naturalWidth === 0) {
      showFallback();
    }
  });
}

async function mountGraphShapePreviews(panel, graph, canvas) {
  void panel;
  void graph;
  void canvas;
}

export async function mountGraph(panel, graph) {
  const canvas = panel.querySelector("[data-solver-graph-canvas]");
  if (!canvas) {
    return;
  }
  setStepsHtml(canvas, renderSolverGraph(graph));
  initGraphPreviewFallbacks(canvas);
  initGraphViewport(canvas);

  const selectNode = (nodeId) => {
    for (const el of canvas.querySelectorAll("[data-graph-node-id]")) {
      el.classList.toggle("ring-2", el.dataset.graphNodeId === nodeId);
      el.classList.toggle("ring-cyan-200", el.dataset.graphNodeId === nodeId);
    }
    renderSelectedNodeDetail(panel, graph, nodeId);
  };

  canvas.querySelectorAll("[data-graph-node-id]").forEach((nodeEl) => {
    nodeEl.addEventListener("click", () => selectNode(nodeEl.dataset.graphNodeId));
    nodeEl.addEventListener("keydown", (event) => {
      if (event.key === "Enter" || event.key === " ") {
        event.preventDefault();
        selectNode(nodeEl.dataset.graphNodeId);
      }
    });
  });

  await mountGraphShapePreviews(panel, graph, canvas);

  const targetNode = (graph.nodes || []).find((node) => node.kind === "shape" && node.role === "target");
  const firstNode = targetNode || (graph.nodes || [])[0];
  if (firstNode) {
    selectNode(firstNode.id);
  }
}
