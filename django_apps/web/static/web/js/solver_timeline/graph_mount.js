import { initGraphViewport } from "./graph_viewport.js?v=20260502-graph-ui-2";
import { renderSelectedNodeDetail } from "./graph_detail.js?v=20260502-graph-ui-2";
import { renderSolverGraph } from "./graph_markup.js?v=20260502-graph-ui-2";
import { setStepsHtml } from "./dom_utils.js?v=20260502-graph-ui-2";

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

export async function mountGraph(panel, graph) {
  const canvas = panel.querySelector("[data-solver-graph-canvas]");
  if (!canvas) {
    return;
  }
  panel._displayedGraph = graph;

  setStepsHtml(canvas, renderSolverGraph(graph));
  initGraphPreviewFallbacks(canvas);
  initGraphViewport(canvas);

  const selectNode = (nodeId) => {
    panel._selectedGraphNodeId = nodeId;
    for (const el of canvas.querySelectorAll("[data-graph-node-id]")) {
      const on = el.dataset.graphNodeId === nodeId;
      el.classList.toggle("ring-2", on);
      el.classList.toggle("ring-inset", on);
      el.classList.toggle("ring-cyan-200", on);
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

  const selectedNodeId = resolveSelectedNodeId(graph, panel._selectedGraphNodeId);
  const targetNode = (graph.nodes || []).find(
    (node) => node.kind === "shape" && node.role === "target",
  );
  const firstNode = selectedNodeId
    ? (graph.nodes || []).find((node) => node.id === selectedNodeId)
    : targetNode || (graph.nodes || [])[0];
  if (firstNode) {
    selectNode(firstNode.id);
  }
}

function resolveSelectedNodeId(graph, selectedNodeId) {
  if (!selectedNodeId) {
    return null;
  }
  const exact = (graph.nodes || []).find(
    (node) => node.id === selectedNodeId,
  );
  if (exact) {
    return exact.id;
  }
  return null;
}
