import { disposeShapeGltfViewer, mountShapeGltfViewer } from "./shape_gltf_viewer.js";

const TIMELINE_DEBOUNCE_MS = 320;
const NODE_WIDTH = 190;
const NODE_HEIGHT = 232;
const COLUMN_GAP = 270;
const ROW_GAP = 276;
const GRAPH_PADDING = 40;
const MIN_GRAPH_SCALE = 0.18;
const MAX_GRAPH_SCALE = 2.2;
const GRAPH_ZOOM_STEP = 1.18;

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function setBanner(el, text, visible) {
  if (!el) {
    return;
  }
  el.textContent = text;
  el.classList.toggle("hidden", !visible);
}

function disposeTimelineViewers(host) {
  for (const el of host.querySelectorAll("[data-shape-gltf-viewer]")) {
    disposeShapeGltfViewer(el);
  }
}

function clearStepsHost(host) {
  disposeTimelineViewers(host);
  host.replaceChildren();
}

function setStepsHtml(host, html) {
  disposeTimelineViewers(host);
  host.innerHTML = html;
}

function renderShapeGraphNode(node, position) {
  const role = node.role || "intermediate";
  const isTarget = role === "target";
  const reusedCount = Number(node.reused_count || 0);
  return `
    <div
      role="button"
      tabindex="0"
      class="absolute flex flex-col items-center rounded-3xl border ${isTarget ? "border-emerald-300/60 bg-emerald-400/10" : "border-cyan-400/20 bg-slate-950/90"} p-3 text-center shadow-xl shadow-slate-950/40 transition hover:border-cyan-200/60"
      style="left:${position.x}px; top:${position.y}px; width:${NODE_WIDTH}px; min-height:${NODE_HEIGHT}px;"
      data-graph-node-id="${escapeHtml(node.id)}"
      data-graph-node-kind="shape"
    >
      <div class="mb-2 flex w-full items-center justify-between gap-2">
        <span class="rounded-full border border-slate-700 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-slate-300">${escapeHtml(role)}</span>
        ${isTarget ? '<span class="rounded-full bg-emerald-300 px-2 py-0.5 text-[10px] font-bold text-emerald-950">TARGET</span>' : ""}
      </div>
      <div
        class="w-full rounded-2xl bg-black/30 p-2 ring-1 ring-cyan-400/15"
        data-shape-gltf-viewer
        data-graph-shape-preview
        data-graph-preview-node-id="${escapeHtml(node.id)}"
        data-asset-base=""
      >
        <div
          class="h-32 overflow-hidden rounded-xl border border-slate-800 bg-slate-950"
          style="height: 8rem; min-height: 8rem;"
          data-shape-gltf-viewport
        ></div>
        <script type="application/json">{}</script>
      </div>
      <p class="mt-3 max-w-full truncate font-mono text-xs text-cyan-100" title="${escapeHtml(node.shape_code)}">${escapeHtml(node.shape_code)}</p>
      <p class="mt-1 text-[10px] text-slate-500">${escapeHtml(node.label || "Shape")}</p>
      ${reusedCount > 0 ? `<span class="mt-2 rounded-full bg-amber-300/15 px-2 py-0.5 text-[10px] font-semibold text-amber-100">REUSED x${escapeHtml(reusedCount + 1)}</span>` : ""}
    </div>
  `;
}

function renderOperationGraphNode(node, position) {
  const operation = node.operation || {};
  return `
    <button
      type="button"
      class="absolute flex flex-col items-center justify-center rounded-full border border-orange-300/50 bg-orange-400/10 p-4 text-center shadow-xl shadow-orange-950/30 transition hover:border-orange-100"
      style="left:${position.x}px; top:${position.y}px; width:${NODE_WIDTH}px; min-height:${NODE_HEIGHT}px;"
      data-graph-node-id="${escapeHtml(node.id)}"
      data-graph-node-kind="operation"
    >
      <div class="flex h-20 w-20 items-center justify-center rounded-full border border-slate-700 bg-slate-950/80">
        <img src="${escapeHtml(operation.icon)}" alt="${escapeHtml(operation.label)}" class="h-12 w-12 object-contain" loading="lazy" />
      </div>
      <p class="mt-2 text-xs font-bold uppercase tracking-wide text-orange-100">${escapeHtml(operation.label)}</p>
      <p class="mt-1 text-[10px] text-slate-400">${escapeHtml(operation.input_count)} in / ${escapeHtml(operation.output_count)} out</p>
    </button>
  `;
}

function computeGraphLayout(graph) {
  const nodes = graph.nodes || [];
  const edges = graph.edges || [];
  const nodeIds = new Set(nodes.map((node) => node.id));
  const depths = new Map(nodes.map((node) => [node.id, 0]));

  let remainingPasses = nodes.length;
  while (remainingPasses > 0) {
    remainingPasses -= 1;
    let changed = false;
    for (const edge of edges) {
      if (!nodeIds.has(edge.from) || !nodeIds.has(edge.to)) {
        continue;
      }
      const nextDepth = (depths.get(edge.from) || 0) + 1;
      if (nextDepth > (depths.get(edge.to) || 0)) {
        depths.set(edge.to, nextDepth);
        changed = true;
      }
    }
    if (!changed) {
      break;
    }
  }

  const columns = new Map();
  for (const node of nodes) {
    const depth = depths.get(node.id) || 0;
    columns.set(depth, [...(columns.get(depth) || []), node]);
  }

  const positions = new Map();
  for (const [depth, columnNodes] of columns) {
    columnNodes.forEach((node, index) => {
      positions.set(node.id, {
        x: GRAPH_PADDING + depth * COLUMN_GAP,
        y: GRAPH_PADDING + index * ROW_GAP,
      });
    });
  }

  const maxDepth = Math.max(0, ...depths.values());
  const maxColumnSize = Math.max(1, ...[...columns.values()].map((column) => column.length));
  const positioned = [...positions.values()];
  const minX = Math.min(...positioned.map((position) => position.x));
  const minY = Math.min(...positioned.map((position) => position.y));
  const maxX = Math.max(...positioned.map((position) => position.x + NODE_WIDTH));
  const maxY = Math.max(...positioned.map((position) => position.y + NODE_HEIGHT));
  return {
    positions,
    width: GRAPH_PADDING * 2 + (maxDepth + 1) * COLUMN_GAP,
    height: GRAPH_PADDING * 2 + maxColumnSize * ROW_GAP,
    bounds: {
      minX,
      minY,
      maxX,
      maxY,
      width: maxX - minX,
      height: maxY - minY,
    },
  };
}

function renderGraphEdges(graph, positions) {
  return (graph.edges || [])
    .map((edge) => {
      const from = positions.get(edge.from);
      const to = positions.get(edge.to);
      if (!from || !to) {
        return "";
      }
      const x1 = from.x + NODE_WIDTH;
      const y1 = from.y + NODE_HEIGHT / 2;
      const x2 = to.x;
      const y2 = to.y + NODE_HEIGHT / 2;
      const midX = x1 + Math.max(40, (x2 - x1) / 2);
      const labelX = (x1 + x2) / 2;
      const labelY = (y1 + y2) / 2 - 8;
      return `
        <path d="M ${x1} ${y1} C ${midX} ${y1}, ${midX} ${y2}, ${x2} ${y2}" fill="none" stroke="rgba(34,211,238,0.45)" stroke-width="2" marker-end="url(#arrowhead)" />
        <foreignObject x="${labelX - 42}" y="${labelY}" width="84" height="22">
          <div xmlns="http://www.w3.org/1999/xhtml" class="rounded-full border border-slate-700 bg-slate-950/90 px-2 py-0.5 text-center text-[10px] text-slate-300">
            ${escapeHtml(edge.label || edge.slot || edge.kind)}
          </div>
        </foreignObject>
      `;
    })
    .join("");
}

function renderSolverGraph(graph) {
  const layout = computeGraphLayout(graph);
  return `
    <div
      class="relative overflow-hidden rounded-3xl border border-slate-800 bg-slate-950/80"
      style="height: 34rem; touch-action: none; cursor: grab;"
      data-graph-viewport
    >
      <div class="absolute left-3 top-3 z-30 flex overflow-hidden rounded-full border border-slate-700 bg-slate-950/90 shadow-xl shadow-slate-950/40">
        <button type="button" class="px-3 py-2 text-sm font-semibold text-slate-200 hover:bg-slate-800" data-graph-zoom-in aria-label="Zoom in">+</button>
        <button type="button" class="border-x border-slate-700 px-3 py-2 text-sm font-semibold text-slate-200 hover:bg-slate-800" data-graph-zoom-out aria-label="Zoom out">-</button>
        <button type="button" class="px-3 py-2 text-xs font-semibold uppercase tracking-wide text-slate-300 hover:bg-slate-800" data-graph-reset>Reset</button>
      </div>
      <p class="pointer-events-none absolute bottom-3 left-3 z-30 rounded-full border border-slate-700 bg-slate-950/80 px-3 py-1 text-[10px] uppercase tracking-wide text-slate-500">
        Drag to pan · wheel to zoom
      </p>
      <div
        class="absolute left-0 top-0"
        style="width:${layout.width}px; height:${layout.height}px; transform-origin: 0 0;"
        data-graph-stage
        data-content-min-x="${layout.bounds.minX}"
        data-content-min-y="${layout.bounds.minY}"
        data-content-width="${layout.bounds.width}"
        data-content-height="${layout.bounds.height}"
      >
        <svg class="absolute inset-0 h-full w-full" viewBox="0 0 ${layout.width} ${layout.height}" aria-hidden="true">
          <defs>
            <marker id="arrowhead" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">
              <path d="M 0 0 L 8 4 L 0 8 z" fill="rgba(34,211,238,0.65)"></path>
            </marker>
          </defs>
          ${renderGraphEdges(graph, layout.positions)}
        </svg>
        ${(graph.nodes || [])
          .map((node) => {
            const position = layout.positions.get(node.id) || { x: 0, y: 0 };
            return node.kind === "shape"
              ? renderShapeGraphNode(node, position)
              : renderOperationGraphNode(node, position);
          })
          .join("")}
      </div>
    </div>
  `;
}

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function applyGraphTransform(viewport) {
  const stage = viewport.querySelector("[data-graph-stage]");
  const state = viewport._graphTransform;
  if (!stage || !state) {
    return;
  }
  stage.style.transform = `translate(${state.x}px, ${state.y}px) scale(${state.scale})`;
}

function resetGraphViewport(viewport) {
  const stage = viewport.querySelector("[data-graph-stage]");
  if (!stage) {
    return;
  }

  const viewportWidth = Math.max(1, viewport.clientWidth);
  const viewportHeight = Math.max(1, viewport.clientHeight);
  const contentMinX = Number(stage.dataset.contentMinX || 0);
  const contentMinY = Number(stage.dataset.contentMinY || 0);
  const contentWidth = Number(stage.dataset.contentWidth || stage.offsetWidth);
  const contentHeight = Number(stage.dataset.contentHeight || stage.offsetHeight);
  const fitWidthScale = (viewportWidth - GRAPH_PADDING * 2) / contentWidth;
  const fitHeightScale = (viewportHeight - GRAPH_PADDING * 2) / contentHeight;
  const scale = clamp(
    Math.min(1, fitWidthScale, fitHeightScale),
    MIN_GRAPH_SCALE,
    MAX_GRAPH_SCALE,
  );
  const scaledWidth = contentWidth * scale;
  const scaledHeight = contentHeight * scale;
  viewport._graphTransform = {
    scale,
    x: (viewportWidth - scaledWidth) / 2 - contentMinX * scale,
    y: (viewportHeight - scaledHeight) / 2 - contentMinY * scale,
    dragging: false,
    startX: 0,
    startY: 0,
    originX: 0,
    originY: 0,
  };
  applyGraphTransform(viewport);
}

function zoomGraphViewport(viewport, nextScale, anchorX, anchorY) {
  const state = viewport._graphTransform;
  if (!state) {
    return;
  }
  const scale = clamp(nextScale, MIN_GRAPH_SCALE, MAX_GRAPH_SCALE);
  const ratio = scale / state.scale;
  state.x = anchorX - (anchorX - state.x) * ratio;
  state.y = anchorY - (anchorY - state.y) * ratio;
  state.scale = scale;
  applyGraphTransform(viewport);
}

function initGraphViewport(canvas) {
  const viewport = canvas.querySelector("[data-graph-viewport]");
  if (!viewport) {
    return;
  }
  resetGraphViewport(viewport);

  viewport.querySelector("[data-graph-zoom-in]")?.addEventListener("click", () => {
    zoomGraphViewport(
      viewport,
      viewport._graphTransform.scale * GRAPH_ZOOM_STEP,
      viewport.clientWidth / 2,
      viewport.clientHeight / 2,
    );
  });
  viewport.querySelector("[data-graph-zoom-out]")?.addEventListener("click", () => {
    zoomGraphViewport(
      viewport,
      viewport._graphTransform.scale / GRAPH_ZOOM_STEP,
      viewport.clientWidth / 2,
      viewport.clientHeight / 2,
    );
  });
  viewport.querySelector("[data-graph-reset]")?.addEventListener("click", () => {
    resetGraphViewport(viewport);
  });

  viewport.addEventListener(
    "wheel",
    (event) => {
      event.preventDefault();
      const rect = viewport.getBoundingClientRect();
      const anchorX = event.clientX - rect.left;
      const anchorY = event.clientY - rect.top;
      const factor = event.deltaY < 0 ? GRAPH_ZOOM_STEP : 1 / GRAPH_ZOOM_STEP;
      zoomGraphViewport(viewport, viewport._graphTransform.scale * factor, anchorX, anchorY);
    },
    { passive: false },
  );

  viewport.addEventListener("pointerdown", (event) => {
    if (event.target.closest("[data-graph-node-id], button")) {
      return;
    }
    const state = viewport._graphTransform;
    state.dragging = true;
    state.startX = event.clientX;
    state.startY = event.clientY;
    state.originX = state.x;
    state.originY = state.y;
    viewport.setPointerCapture(event.pointerId);
    viewport.style.cursor = "grabbing";
  });

  viewport.addEventListener("pointermove", (event) => {
    const state = viewport._graphTransform;
    if (!state?.dragging) {
      return;
    }
    state.x = state.originX + event.clientX - state.startX;
    state.y = state.originY + event.clientY - state.startY;
    applyGraphTransform(viewport);
  });

  const stopDragging = (event) => {
    const state = viewport._graphTransform;
    if (!state?.dragging) {
      return;
    }
    state.dragging = false;
    viewport.releasePointerCapture?.(event.pointerId);
    viewport.style.cursor = "grab";
  };

  viewport.addEventListener("pointerup", stopDragging);
  viewport.addEventListener("pointercancel", stopDragging);
}

function connectedEdges(graph, nodeId) {
  return (graph.edges || []).filter((edge) => edge.from === nodeId || edge.to === nodeId);
}

async function mountGraphShapePreviews(panel, graph, canvas) {
  const assetBase = panel.dataset.assetBase || "";
  const nodesById = new Map((graph.nodes || []).map((node) => [node.id, node]));

  for (const viewer of canvas.querySelectorAll("[data-graph-shape-preview]")) {
    const node = nodesById.get(viewer.dataset.graphPreviewNodeId);
    const script = viewer.querySelector('script[type="application/json"]');
    if (!node?.preview_scene || !script) {
      continue;
    }
    viewer.dataset.assetBase = assetBase;
    script.textContent = JSON.stringify(node.preview_scene);
    await mountShapeGltfViewer(viewer);
  }
}

async function renderSelectedNodeDetail(panel, graph, nodeId) {
  const detailHost = panel.querySelector("[data-solver-node-detail]");
  const assetBase = panel.dataset.assetBase || "";
  if (!detailHost) {
    return;
  }
  disposeTimelineViewers(detailHost);

  const node = (graph.nodes || []).find((candidate) => candidate.id === nodeId);
  if (!node) {
    detailHost.innerHTML = '<p class="text-xs text-slate-500">Select a graph node.</p>';
    return;
  }

  const edges = connectedEdges(graph, node.id);
  if (node.kind === "operation") {
    const operation = node.operation || {};
    detailHost.innerHTML = `
      <div class="rounded-3xl border border-slate-800 bg-slate-950/70 p-5">
        <p class="text-xs font-semibold uppercase tracking-[0.2em] text-orange-200">Selected operation</p>
        <div class="mt-4 flex flex-wrap items-center gap-4">
          <div class="flex h-20 w-20 items-center justify-center rounded-full border border-orange-300/40 bg-orange-400/10">
            <img src="${escapeHtml(operation.icon)}" alt="${escapeHtml(operation.label)}" class="h-12 w-12 object-contain" />
          </div>
          <div>
            <h3 class="text-lg font-semibold text-slate-100">${escapeHtml(operation.label)}</h3>
            <p class="mt-1 text-sm text-slate-400">${escapeHtml(operation.description || "")}</p>
            <p class="mt-2 text-xs text-slate-500">${escapeHtml(operation.input_count)} inputs / ${escapeHtml(operation.output_count)} outputs</p>
          </div>
        </div>
        <p class="mt-4 text-xs text-slate-500">${escapeHtml(edges.map((edge) => edge.label || edge.kind).join(" · "))}</p>
      </div>
    `;
    return;
  }

  detailHost.innerHTML = `
    <div class="rounded-3xl border border-cyan-400/20 bg-slate-950/70 p-5">
      <div class="mb-4 flex flex-wrap items-start justify-between gap-3">
        <div>
          <p class="text-xs font-semibold uppercase tracking-[0.2em] text-cyan-200">Selected shape</p>
          <h3 class="mt-1 font-mono text-lg text-slate-100">${escapeHtml(node.shape_code)}</h3>
          <p class="mt-1 text-xs uppercase tracking-wide text-slate-500">${escapeHtml(node.role)} · ${escapeHtml(node.label)}</p>
        </div>
        ${node.role === "target" ? '<span class="rounded-full bg-emerald-300 px-3 py-1 text-[11px] font-bold text-emerald-950">TARGET</span>' : ""}
      </div>
      <div class="rounded-3xl bg-black/30 p-3 ring-1 ring-cyan-400/20" data-shape-gltf-viewer data-asset-base="">
        <div class="h-64 overflow-hidden rounded-2xl border border-slate-800 bg-slate-950" style="height: 16rem; min-height: 16rem;" data-shape-gltf-viewport></div>
        <script type="application/json">{}</script>
      </div>
      <p class="mt-4 text-xs text-slate-500">${escapeHtml(edges.map((edge) => edge.label || edge.kind).join(" · "))}</p>
    </div>
  `;

  const viewer = detailHost.querySelector("[data-shape-gltf-viewer]");
  const script = viewer?.querySelector('script[type="application/json"]');
  if (viewer && script && node.preview_scene) {
    viewer.dataset.assetBase = assetBase;
    script.textContent = JSON.stringify(node.preview_scene);
    await mountShapeGltfViewer(viewer);
  }
}

async function mountGraph(panel, graph) {
  const canvas = panel.querySelector("[data-solver-graph-canvas]");
  if (!canvas) {
    return;
  }
  setStepsHtml(canvas, renderSolverGraph(graph));
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

async function requestTimeline(panel, code, seq) {
  const graphCanvas = panel.querySelector("[data-solver-graph-canvas]");
  const emptyEl = panel.querySelector("[data-solver-graph-empty]");
  const errorEl = panel.querySelector("[data-solver-timeline-error]");
  const warningsEl = panel.querySelector("[data-solver-timeline-warnings]");
  const apiUrl = panel.dataset.solverApi;
  const detailHost = panel.querySelector("[data-solver-node-detail]");

  if (!graphCanvas || !apiUrl) {
    return;
  }

  if (!code) {
    clearStepsHost(graphCanvas);
    if (detailHost) {
      clearStepsHost(detailHost);
    }
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
      body: JSON.stringify({ code }),
    });
    data = await res.json();
  } catch {
    if (seq !== panel._timelineSeq) {
      return;
    }
    clearStepsHost(graphCanvas);
    setBanner(errorEl, "Could not reach solver service.", true);
    setBanner(warningsEl, "", false);
    return;
  }

  if (seq !== panel._timelineSeq) {
    return;
  }

  if (!data.ok) {
    clearStepsHost(graphCanvas);
    setBanner(errorEl, data.error || "Could not solve this shape code.", true);
    setBanner(warningsEl, "", false);
    return;
  }

  setBanner(errorEl, "", false);
  const warnings = data.warnings || [];
  setBanner(warningsEl, warnings.join(" "), warnings.length > 0);

  const graph = data.graph;
  if (!graph?.nodes?.length) {
    clearStepsHost(graphCanvas);
    emptyEl?.classList.remove("hidden");
    return;
  }

  await mountGraph(panel, graph);
}

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
  if (!input) {
    return;
  }

  input.addEventListener("input", () => scheduleTimeline(panel, input));
  input.addEventListener("change", () => scheduleTimeline(panel, input));
  scheduleTimeline(panel, input);
}

document.querySelectorAll("[data-solver-timeline]").forEach(initSolverTimeline);
