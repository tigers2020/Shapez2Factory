import {
  NODE_HEIGHT,
  NODE_WIDTH,
  computeGraphLayout,
} from "../solver_graph_layout.js?v=20260504-pinned-overlap";

import {
  GRAPH_MARKUP_EDGE_ELBOW_PADDING,
  GRAPH_MARKUP_EDGE_LABEL_HEIGHT,
  GRAPH_MARKUP_EDGE_LABEL_STAGGER,
  GRAPH_MARKUP_EDGE_LABEL_WIDTH,
  GRAPH_MARKUP_EDGE_LANE_SPACING,
  GRAPH_MARKUP_EDGE_PORT_SPACING,
  GRAPH_MARKUP_PREVIEW_HEIGHT,
} from "./constants.js?v=20260502-graph-ui-2";

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

function escapeAttr(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll('"', "&quot;")
    .replaceAll("<", "&lt;");
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
  const vErr = node.validation_severity === "error";
  const vWarn = node.validation_severity === "warning";
  const borderClass = vErr
    ? "border-rose-500/70 bg-rose-950/30 ring-2 ring-rose-400/50"
    : vWarn
      ? "border-amber-400/60 bg-amber-950/25 ring-2 ring-amber-300/40"
      : isTarget
        ? "border-emerald-300/60 bg-emerald-400/10"
        : isUnused
          ? "border-rose-400/30 bg-rose-950/20"
          : "border-cyan-400/20 bg-slate-950/90";
  return `
    <div
      class="absolute z-10 flex flex-col items-center rounded-3xl border ${borderClass} overflow-hidden p-3 pb-2 text-center shadow-md shadow-slate-950/30 transition hover:border-cyan-200/60"
      style="left:${position.x}px; top:${position.y}px; width:${NODE_WIDTH}px; height:${NODE_HEIGHT}px;"
      data-graph-node-id="${escapeHtml(node.id)}"
      data-graph-node-kind="shape"
      data-graph-validation="${escapeHtml(node.validation_severity || "")}"
    >
      <button type="button" class="absolute left-0 top-1/2 z-30 h-6 w-6 -translate-x-1/2 -translate-y-1/2 cursor-crosshair rounded-full border border-cyan-300/50 bg-cyan-500/80 shadow-md ring-2 ring-slate-950 hover:scale-105" title="Shape input — drag from operation output" aria-label="Shape input port" data-graph-port data-graph-port-flow="in" data-graph-port-owner="${escapeHtml(node.id)}"></button>
      <button type="button" class="absolute right-0 top-1/2 z-30 h-6 w-6 translate-x-1/2 -translate-y-1/2 cursor-crosshair rounded-full border border-amber-300/50 bg-amber-500/80 shadow-md ring-2 ring-slate-950 hover:scale-105" title="Shape output — drag to operation input" aria-label="Shape output port" data-graph-port data-graph-port-flow="out" data-graph-port-owner="${escapeHtml(node.id)}"></button>
      <div
        role="button"
        tabindex="0"
        data-graph-node-body
        class="relative z-10 flex h-full w-full min-w-0 flex-col items-center"
      >
      ${renderShapeRoleBadge(role, isTarget)}
      <div class="w-full rounded-2xl bg-black/30 p-2 ring-1 ring-cyan-400/15">
        <div
          class="overflow-hidden rounded-xl border border-slate-800 bg-slate-950"
          style="height: ${GRAPH_MARKUP_PREVIEW_HEIGHT}px;"
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
      ${vErr ? '<span class="mt-2 rounded-full bg-rose-400/20 px-2 py-0.5 text-[10px] font-semibold text-rose-100">GRAPH INVALID</span>' : ""}
      ${vWarn && !vErr ? '<span class="mt-2 rounded-full bg-amber-400/20 px-2 py-0.5 text-[10px] font-semibold text-amber-100">CHECK</span>' : ""}
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
    <div
      class="absolute z-10"
      style="left:${position.x}px; top:${position.y}px; width:${NODE_WIDTH}px; height:${NODE_HEIGHT}px;"
      data-graph-node-id="${escapeHtml(node.id)}"
      data-graph-node-kind="operation"
    >
      ${renderOperationPortDots(inputs, outputs, node.id)}
      <button
        type="button"
        tabindex="0"
        data-graph-node-body
        class="absolute inset-0 z-10 flex flex-col items-center justify-center overflow-hidden rounded-full border border-orange-300/50 bg-orange-400/10 p-3 text-center shadow-md shadow-orange-950/25 transition hover:border-orange-100"
      >
        <div class="flex h-16 w-16 shrink-0 items-center justify-center rounded-full border border-slate-700 bg-slate-950/80">
          <img src="${escapeHtml(operation.icon)}" alt="${escapeHtml(operation.label)}" class="h-10 w-10 object-contain" loading="lazy" />
        </div>
        <p class="mt-1 max-w-full truncate px-1 text-[11px] font-bold uppercase leading-tight tracking-wide text-orange-100">${escapeHtml(operation.label)}</p>
        <div class="mt-1 w-full max-w-[${NODE_WIDTH - 16}px] px-1 text-[9px] leading-snug text-slate-300" title="Catalog operation ports (edges attach to cyan=left, amber=right)">
          <span class="block truncate">${escapeHtml(wordLine)}</span>
          <span class="block truncate font-mono text-slate-400">${escapeHtml(ratioLine)} \xb7 ${escapeHtml(arrowLine)}</span>
        </div>
      </button>
    </div>
  `;
}

function parsePortIndex(value) {
  const raw = String(value ?? "").trim();
  if (raw === "") {
    return 0;
  }
  if (/^\d+$/.test(raw)) {
    return Math.max(0, parseInt(raw, 10));
  }
  const letterMatch = raw.match(/\b([A-Z])(?:\b|\s*\()/);
  if (letterMatch) {
    return Math.max(0, letterMatch[1].charCodeAt(0) - "A".charCodeAt(0));
  }
  const digitMatch = raw.match(/(\d+)/);
  if (digitMatch) {
    return Math.max(0, parseInt(digitMatch[1], 10));
  }
  return 0;
}

function computePortOffset(index, count) {
  if (!Number.isFinite(count) || count <= 1) {
    return 0;
  }
  return (index - (count - 1) / 2) * GRAPH_MARKUP_EDGE_PORT_SPACING;
}

function renderOperationPortDots(inputCount, outputCount, nodeId) {
  const nid = escapeHtml(nodeId);
  const ic = Math.max(0, Math.floor(Number(inputCount ?? 0)));
  const oc = Math.max(0, Math.floor(Number(outputCount ?? 0)));
  let html = "";
  for (let i = 0; i < ic; i += 1) {
    const topPx = NODE_HEIGHT / 2 + computePortOffset(i, ic) - 5;
    html += `<button type="button" class="absolute z-30 h-5 w-5 -translate-x-1/2 -translate-y-1/2 cursor-crosshair rounded-full border border-cyan-300/60 bg-cyan-400/90 shadow-md ring-2 ring-slate-950 hover:scale-110" style="left:0;top:${topPx}px" title="Input port ${i} — drag wire" aria-label="Input port ${i}" data-graph-port data-graph-port-flow="in" data-graph-port-owner="${nid}" data-graph-port-index="${i}"></button>`;
  }
  for (let j = 0; j < oc; j += 1) {
    const topPx = NODE_HEIGHT / 2 + computePortOffset(j, oc) - 5;
    html += `<button type="button" class="absolute z-30 h-5 w-5 -translate-x-1/2 -translate-y-1/2 cursor-crosshair rounded-full border border-amber-300/60 bg-amber-400/90 shadow-md ring-2 ring-slate-950 hover:scale-110" style="left:${NODE_WIDTH}px;top:${topPx}px" title="Output port ${j} — drag wire" aria-label="Output port ${j}" data-graph-port data-graph-port-flow="out" data-graph-port-owner="${nid}" data-graph-port-index="${j}"></button>`;
  }
  return html;
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
  const laneOffset = (Math.floor(edgeIndex / 2) + 1) * GRAPH_MARKUP_EDGE_LANE_SPACING * laneDirection;
  const elbowX = Math.max(
    fromAnchor.x + GRAPH_MARKUP_EDGE_ELBOW_PADDING + Math.max(laneOffset, 0),
    toAnchor.x - GRAPH_MARKUP_EDGE_ELBOW_PADDING + Math.min(laneOffset, 0),
  );
  const labelCenterX = elbowX + (toAnchor.x - elbowX) / 2;
  const labelOffsetDirection = parsePortIndex(edge.slot || edge.label) % 2 === 0 ? -1 : 1;

  return {
    x1: fromAnchor.x,
    y1: fromAnchor.y,
    x2: toAnchor.x,
    y2: toAnchor.y,
    elbowX,
    labelX: labelCenterX - GRAPH_MARKUP_EDGE_LABEL_WIDTH / 2,
    labelY:
      toAnchor.y -
      GRAPH_MARKUP_EDGE_LABEL_HEIGHT -
      6 +
      labelOffsetDirection * (Math.floor(edgeIndex / 2) * GRAPH_MARKUP_EDGE_LABEL_STAGGER),
  };
}

function edgePathD(geometry) {
  return `M ${geometry.x1} ${geometry.y1} L ${geometry.elbowX} ${geometry.y1} L ${geometry.elbowX} ${geometry.y2} L ${geometry.x2} ${geometry.y2}`;
}

function renderEdgePathVisible(geometry) {
  const d = edgePathD(geometry);
  return `<path d="${d}" fill="none" stroke="rgba(34,211,238,0.45)" stroke-width="2" pointer-events="none" marker-end="url(#arrowhead)" />`;
}

function renderEdgeHitPath(geometry, edge) {
  const d = edgePathD(geometry);
  const from = escapeAttr(edge.from);
  const to = escapeAttr(edge.to);
  const kind = escapeAttr(edge.kind);
  const slotRaw = edge.slot != null && String(edge.slot) !== "" ? String(edge.slot) : "";
  const slotAttr =
    slotRaw !== ""
      ? ` data-graph-edge-slot="${escapeAttr(slotRaw)}"`
      : "";
  return `<path d="${d}" fill="none" stroke="transparent" stroke-width="18" pointer-events="stroke" vector-effect="non-scaling-stroke" data-graph-edge-hit="1" data-graph-edge-from="${from}" data-graph-edge-to="${to}" data-graph-edge-kind="${kind}"${slotAttr} style="cursor:pointer" title="Remove wire (staff)" />`;
}

function renderEdgeLabel(edge, geometry) {
  return `
    <foreignObject x="${geometry.labelX}" y="${geometry.labelY}" width="${GRAPH_MARKUP_EDGE_LABEL_WIDTH}" height="${GRAPH_MARKUP_EDGE_LABEL_HEIGHT}" pointer-events="none" data-graph-edge-label>
      <div xmlns="http://www.w3.org/1999/xhtml" class="pointer-events-none rounded-full border border-slate-700 bg-slate-950/90 px-2 py-0.5 text-center text-[10px] text-slate-300">
        ${escapeHtml(edge.label || edge.slot || edge.kind)}
      </div>
    </foreignObject>
  `;
}

function renderGraphEdgesVisible(graph, positions) {
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
        ${renderEdgePathVisible(geometry)}
        ${renderEdgeLabel(edge, geometry)}
      `;
    })
    .join("");
}

function renderGraphEdgeHits(graph, positions) {
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
      return renderEdgeHitPath(geometry, edge);
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

/**
 * @param {{ includeEdgeHitForDelete?: boolean }} [stageOptions]
 */
function renderGraphStage(graph, layout, stageOptions) {
  const includeHit = Boolean(stageOptions?.includeEdgeHitForDelete);
  const edgeLayers = includeHit
    ? `<svg
        class="absolute inset-0 z-[28] h-full w-full overflow-visible"
        viewBox="0 0 ${layout.width} ${layout.height}"
        aria-hidden="true"
      >
        <rect width="100%" height="100%" fill="transparent" style="pointer-events: none" />
        ${renderGraphEdgeHits(graph, layout.positions)}
      </svg>
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
        ${renderGraphEdgesVisible(graph, layout.positions)}
      </svg>`
    : `<svg
        class="pointer-events-none absolute inset-0 z-30 h-full w-full"
        viewBox="0 0 ${layout.width} ${layout.height}"
        aria-hidden="true"
      >
        <defs>
          <marker id="arrowhead" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto">
            <path d="M 0 0 L 8 4 L 0 8 z" fill="rgba(34,211,238,0.65)"></path>
          </marker>
        </defs>
        ${renderGraphEdgesVisible(graph, layout.positions)}
      </svg>`;
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
      ${edgeLayers}
    </div>
  `;
}

/**
 * @param {{ nodes?: unknown[], edges?: unknown[] }} graph
 * @param {{ includeEdgeHitForDelete?: boolean }} [options]
 */
export function renderSolverGraph(graph, options) {
  const layout = computeGraphLayout(graph);
  const stageOptions =
    options && options.includeEdgeHitForDelete ? { includeEdgeHitForDelete: true } : undefined;
  return `
    <div
      class="relative overflow-hidden rounded-3xl border border-slate-800 bg-slate-950/80 select-none"
      style="height: 34rem; touch-action: none; cursor: grab; user-select: none; -webkit-user-select: none;"
      data-graph-viewport
    >
      ${renderGraphControls()}
      ${renderGraphHint()}
      ${renderGraphStage(graph, layout, stageOptions)}
    </div>
  `;
}

export { GRAPH_PADDING, NODE_HEIGHT, NODE_WIDTH } from "../solver_graph_layout.js";
