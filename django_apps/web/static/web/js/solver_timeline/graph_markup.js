import {
  NODE_HEIGHT,
  NODE_WIDTH,
  computeGraphLayout,
} from "../solver_graph_layout.js?v=20260502-graph-ui-2";

const PREVIEW_HEIGHT = 104;
const EDGE_ELBOW_PADDING = 44;
const EDGE_PORT_SPACING = 30;
const EDGE_LABEL_WIDTH = 90;
const EDGE_LABEL_HEIGHT = 22;
const EDGE_LANE_SPACING = 18;
const EDGE_LABEL_STAGGER = 18;

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function formatQuantityBadge(node) {
  const role = node.role || "intermediate";
  const quantity = Number(node.quantity ?? 1);
  if (role === "target") {
    return `<span class="mt-2 shrink-0 rounded-full bg-cyan-300/15 px-2 py-0.5 text-[10px] font-semibold text-cyan-100">OUTPUT x${escapeHtml(quantity)}</span>`;
  }
  if (role === "source") {
    return `<span class="mt-2 shrink-0 rounded-full bg-cyan-300/15 px-2 py-0.5 text-[10px] font-semibold text-cyan-100">QTY x${escapeHtml(quantity)}</span>`;
  }
  return `<span class="mt-2 shrink-0 rounded-full bg-slate-600/25 px-2 py-0.5 text-[10px] font-semibold text-slate-200">FLOW x${escapeHtml(quantity)}</span>`;
}

function renderShapePreview(node) {
  if (!node.preview_image_url) {
    return '<div class="flex h-full items-center justify-center text-[10px] uppercase tracking-wide text-slate-500">No preview</div>';
  }
  return `
    <div class="relative h-full w-full">
      <img
        src="${escapeHtml(node.preview_image_url)}"
        alt="${escapeHtml(node.preview_alt || node.shape_code || "Shape preview")}"
        class="h-full w-full object-contain"
        loading="lazy"
        data-graph-preview-image
      />
      <div class="hidden h-full w-full items-center justify-center text-[10px] uppercase tracking-wide text-slate-500" data-graph-preview-fallback>
        No preview
      </div>
    </div>
  `;
}

function renderShapeRoleBadge(role, isTarget) {
  return `
    <div class="mb-2 flex w-full shrink-0 items-center justify-between gap-2">
      <span class="rounded-full border border-slate-700 px-2 py-0.5 text-[10px] font-semibold uppercase tracking-wide text-slate-300">${escapeHtml(role)}</span>
      ${isTarget ? '<span class="rounded-full bg-emerald-300 px-2 py-0.5 text-[10px] font-bold text-emerald-950">TARGET</span>' : ""}
    </div>
  `;
}

function renderReusedBadge(reusedCount) {
  if (reusedCount <= 0) {
    return "";
  }
  return `<span class="mt-2 rounded-full bg-amber-300/15 px-2 py-0.5 text-[10px] font-semibold text-amber-100">REUSED x${escapeHtml(reusedCount + 1)}</span>`;
}

function renderReplicaBadge(node) {
  const batchTotal = Number(node.batch_total ?? 0);
  const batchIndex = Number(node.batch_index ?? 0);
  if (batchTotal <= 1 || batchIndex <= 0) {
    return "";
  }
  return `<span class="mt-2 rounded-full bg-fuchsia-300/15 px-2 py-0.5 text-[10px] font-semibold text-fuchsia-100">BATCH ${escapeHtml(batchIndex)}/${escapeHtml(batchTotal)}</span>`;
}

function renderProducedStateBadge(node) {
  if (node.produced_state === "unused") {
    return '<span class="mt-2 rounded-full bg-rose-300/15 px-2 py-0.5 text-[10px] font-semibold text-rose-100">UNUSED</span>';
  }
  if (node.produced_state === "consumed") {
    return '<span class="mt-2 rounded-full bg-emerald-300/15 px-2 py-0.5 text-[10px] font-semibold text-emerald-100">CONSUMED</span>';
  }
  return "";
}

function renderShapeGraphNode(node, position) {
  const role = node.role || "intermediate";
  const isTarget = role === "target";
  const reusedCount = Number(node.reused_count || 0);
  const isUnused = node.produced_state === "unused";
  return `
    <div
      role="button"
      tabindex="0"
      class="absolute z-10 flex flex-col items-center rounded-3xl border ${isTarget ? "border-emerald-300/60 bg-emerald-400/10" : isUnused ? "border-rose-400/30 bg-rose-950/20" : "border-cyan-400/20 bg-slate-950/90"} overflow-hidden p-3 pb-2 text-center shadow-md shadow-slate-950/30 transition hover:border-cyan-200/60"
      style="left:${position.x}px; top:${position.y}px; width:${NODE_WIDTH}px; height:${NODE_HEIGHT}px;"
      data-graph-node-id="${escapeHtml(node.id)}"
      data-graph-node-kind="shape"
    >
      <div class="flex h-full w-full min-w-0 flex-col">
      ${renderShapeRoleBadge(role, isTarget)}
      <div class="w-full rounded-2xl bg-black/30 p-2 ring-1 ring-cyan-400/15">
        <div
          class="overflow-hidden rounded-xl border border-slate-800 bg-slate-950"
          style="height: ${PREVIEW_HEIGHT}px;"
        >
          ${renderShapePreview(node)}
        </div>
      </div>
      <p class="mt-1 max-w-full shrink-0 truncate font-mono text-[11px] text-cyan-100" title="${escapeHtml(node.shape_code)}">${escapeHtml(node.shape_code)}</p>
      <p class="mt-0.5 shrink-0 text-[10px] leading-tight text-slate-500">${escapeHtml(node.label || "Shape")}</p>
      ${formatQuantityBadge(node)}
      ${renderProducedStateBadge(node)}
      ${renderReplicaBadge(node)}
      ${renderReusedBadge(reusedCount)}
      </div>
    </div>
  `;
}

function renderOperationGraphNode(node, position) {
  const operation = node.operation || {};
  const inputs = Number(operation.input_count ?? 0);
  const outputs = Number(operation.output_count ?? 0);
  const wordLine = `${inputs} in / ${outputs} out`;
  const ratioLine = `${inputs}:${outputs}`;
  const arrowLine = `${inputs}\u2192${outputs}`;
  return `
    <button
      type="button"
      class="absolute z-10 flex flex-col items-center justify-center overflow-hidden rounded-full border border-orange-300/50 bg-orange-400/10 p-3 text-center shadow-md shadow-orange-950/25 transition hover:border-orange-100"
      style="left:${position.x}px; top:${position.y}px; width:${NODE_WIDTH}px; height:${NODE_HEIGHT}px;"
      data-graph-node-id="${escapeHtml(node.id)}"
      data-graph-node-kind="operation"
    >
      <div class="flex h-16 w-16 shrink-0 items-center justify-center rounded-full border border-slate-700 bg-slate-950/80">
        <img src="${escapeHtml(operation.icon)}" alt="${escapeHtml(operation.label)}" class="h-10 w-10 object-contain" loading="lazy" />
      </div>
      <p class="mt-1 max-w-full truncate px-1 text-[11px] font-bold uppercase leading-tight tracking-wide text-orange-100">${escapeHtml(operation.label)}</p>
      <div class="mt-1 w-full max-w-[${NODE_WIDTH - 16}px] px-1 text-[9px] leading-snug text-slate-300" title="Catalog operation ports (not factory throughput)">
        <span class="block truncate">${escapeHtml(wordLine)}</span>
        <span class="block truncate font-mono text-slate-400">${escapeHtml(ratioLine)} \xb7 ${escapeHtml(arrowLine)}</span>
      </div>
    </button>
  `;
}

function parsePortIndex(value) {
  const text = String(value || "");
  const match = text.match(/\b([A-Z])(?:\b|\s*\()/);
  if (!match) {
    return 0;
  }
  return Math.max(0, match[1].charCodeAt(0) - "A".charCodeAt(0));
}

function computePortOffset(index, count) {
  if (!Number.isFinite(count) || count <= 1) {
    return 0;
  }
  return (index - (count - 1) / 2) * EDGE_PORT_SPACING;
}

function resolveEdgeAnchor(node, edge, side) {
  const baseY = node.position.y + NODE_HEIGHT / 2;

  if (node.kind === "operation") {
    if (side === "to" && edge.kind === "input") {
      const inputCount = Number(node.operation?.input_count ?? 0);
      return {
        x: node.position.x,
        y: baseY + computePortOffset(parsePortIndex(edge.slot || edge.label), inputCount),
      };
    }
    if (side === "from" && edge.kind === "output") {
      const outputCount = Number(node.operation?.output_count ?? 0);
      return {
        x: node.position.x + NODE_WIDTH,
        y: baseY + computePortOffset(parsePortIndex(edge.slot || edge.label), outputCount),
      };
    }
  }

  return {
    x: side === "from" ? node.position.x + NODE_WIDTH : node.position.x,
    y: baseY,
  };
}

export function computeEdgeGeometry(edge, fromNode, toNode, edgeIndex = 0) {
  const fromAnchor = resolveEdgeAnchor(fromNode, edge, "from");
  const toAnchor = resolveEdgeAnchor(toNode, edge, "to");
  const laneDirection = edgeIndex % 2 === 0 ? 1 : -1;
  const laneOffset = (Math.floor(edgeIndex / 2) + 1) * EDGE_LANE_SPACING * laneDirection;
  const elbowX = Math.max(
    fromAnchor.x + EDGE_ELBOW_PADDING + Math.max(laneOffset, 0),
    toAnchor.x - EDGE_ELBOW_PADDING + Math.min(laneOffset, 0),
  );
  const labelCenterX = elbowX + (toAnchor.x - elbowX) / 2;
  const labelOffsetDirection = parsePortIndex(edge.slot || edge.label) % 2 === 0 ? -1 : 1;

  return {
    x1: fromAnchor.x,
    y1: fromAnchor.y,
    x2: toAnchor.x,
    y2: toAnchor.y,
    elbowX,
    labelX: labelCenterX - EDGE_LABEL_WIDTH / 2,
    labelY:
      toAnchor.y -
      EDGE_LABEL_HEIGHT -
      6 +
      labelOffsetDirection * (Math.floor(edgeIndex / 2) * EDGE_LABEL_STAGGER),
  };
}

function renderEdgePath(geometry) {
  return `<path d="M ${geometry.x1} ${geometry.y1} L ${geometry.elbowX} ${geometry.y1} L ${geometry.elbowX} ${geometry.y2} L ${geometry.x2} ${geometry.y2}" fill="none" stroke="rgba(34,211,238,0.45)" stroke-width="2" marker-end="url(#arrowhead)" />`;
}

function renderEdgeLabel(edge, geometry) {
  return `
    <foreignObject x="${geometry.labelX}" y="${geometry.labelY}" width="${EDGE_LABEL_WIDTH}" height="${EDGE_LABEL_HEIGHT}" data-graph-edge-label>
      <div xmlns="http://www.w3.org/1999/xhtml" class="rounded-full border border-slate-700 bg-slate-950/90 px-2 py-0.5 text-center text-[10px] text-slate-300">
        ${escapeHtml(edge.label || edge.slot || edge.kind)}
      </div>
    </foreignObject>
  `;
}

function renderGraphEdges(graph, positions) {
  const nodeMap = new Map(
    (graph.nodes || []).map((node) => [
      node.id,
      {
        ...node,
        position: positions.get(node.id) || { x: 0, y: 0 },
      },
    ]),
  );
  return (graph.edges || [])
    .map((edge, edgeIndex) => {
      const fromNode = nodeMap.get(edge.from);
      const toNode = nodeMap.get(edge.to);
      if (!fromNode || !toNode) {
        return "";
      }
      const geometry = computeEdgeGeometry(edge, fromNode, toNode, edgeIndex);
      return `
        ${renderEdgePath(geometry)}
        ${renderEdgeLabel(edge, geometry)}
      `;
    })
    .join("");
}

function renderGraphControls() {
  return `
    <div class="absolute left-3 top-3 z-30 flex overflow-hidden rounded-full border border-slate-700 bg-slate-950/90 shadow-xl shadow-slate-950/40">
      <button type="button" class="px-3 py-2 text-sm font-semibold text-slate-200 hover:bg-slate-800" data-graph-zoom-in aria-label="Zoom in">+</button>
      <button type="button" class="border-x border-slate-700 px-3 py-2 text-sm font-semibold text-slate-200 hover:bg-slate-800" data-graph-zoom-out aria-label="Zoom out">-</button>
      <button type="button" class="px-3 py-2 text-xs font-semibold uppercase tracking-wide text-slate-300 hover:bg-slate-800" data-graph-reset>Reset</button>
    </div>
  `;
}

function renderGraphHint() {
  return `
    <p class="pointer-events-none absolute bottom-3 left-3 z-30 rounded-full border border-slate-700 bg-slate-950/80 px-3 py-1 text-[10px] uppercase tracking-wide text-slate-500">
      Drag to pan - wheel to zoom
    </p>
  `;
}

function renderGraphStage(graph, layout) {
  return `
    <div
      class="absolute left-0 top-0 isolate"
      style="width:${layout.width}px; height:${layout.height}px; transform-origin: 0 0;"
      data-graph-stage
      data-content-min-x="${layout.bounds.minX}"
      data-content-min-y="${layout.bounds.minY}"
      data-content-width="${layout.bounds.width}"
      data-content-height="${layout.bounds.height}"
    >
      ${(graph.nodes || [])
        .map((node) => {
          const position = layout.positions.get(node.id) || { x: 0, y: 0 };
          return node.kind === "shape"
            ? renderShapeGraphNode(node, position)
            : renderOperationGraphNode(node, position);
        })
        .join("")}
      <svg
        class="pointer-events-none absolute inset-0 z-30 h-full w-full"
        viewBox="0 0 ${layout.width} ${layout.height}"
        aria-hidden="true"
      >
        <defs>
          <marker id="arrowhead" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">
            <path d="M 0 0 L 8 4 L 0 8 z" fill="rgba(34,211,238,0.65)"></path>
          </marker>
        </defs>
        ${renderGraphEdges(graph, layout.positions)}
      </svg>
    </div>
  `;
}

export function renderSolverGraph(graph) {
  const layout = computeGraphLayout(graph);
  return `
    <div
      class="relative overflow-hidden rounded-3xl border border-slate-800 bg-slate-950/80 select-none"
      style="height: 34rem; touch-action: none; cursor: grab; user-select: none; -webkit-user-select: none;"
      data-graph-viewport
    >
      ${renderGraphControls()}
      ${renderGraphHint()}
      ${renderGraphStage(graph, layout)}
    </div>
  `;
}

export { GRAPH_PADDING, NODE_HEIGHT, NODE_WIDTH } from "../solver_graph_layout.js";
