/* GENERATED — do not edit by hand. Source: frontend/graph_layout/src/*.ts | Rebuild: npm run build:graph-layout */

// frontend/graph_layout/src/constants.ts
var ORDERING_PASSES = 4;
var POSITIONING_PASSES = 6;
var EDITOR_LAYOUT_CONSOLE_DEBUG_LS_KEY = "shapezDebugGraphLayout";

// frontend/graph_layout/src/graphLayoutDebug.ts
function isEditorGraphLayoutConsoleDebugEnabled() {
  if (typeof globalThis === "undefined") {
    return false;
  }
  const g = globalThis;
  if (g.__SHAPEZ_DEBUG_GRAPH_LAYOUT__ === true) {
    return true;
  }
  const storageMatch = (store) => {
    try {
      const v = store?.getItem(EDITOR_LAYOUT_CONSOLE_DEBUG_LS_KEY);
      return v === "1" || v === "true";
    } catch {
      return false;
    }
  };
  if (storageMatch(globalThis.localStorage) || storageMatch(globalThis.sessionStorage)) {
    return true;
  }
  try {
    const search = globalThis.location?.search;
    if (typeof search === "string" && search.length > 1) {
      const qs = new URLSearchParams(search);
      const q = qs.get("debugGraphLayout");
      if (q === "1" || q === "true") {
        return true;
      }
    }
  } catch {
  }
  return false;
}

// frontend/graph_layout/src/graphLayoutBounds.ts
function buildEmptyGraphLayout(metrics) {
  const p = metrics.graphPadding;
  return {
    positions: /* @__PURE__ */ new Map(),
    width: p * 2,
    height: p * 2,
    bounds: {
      minX: p,
      minY: p,
      maxX: p,
      maxY: p,
      width: 0,
      height: 0
    }
  };
}
function buildFinalGraphLayout(nodes, leftPositions, topPositions, metrics) {
  const rawMinLeft = Math.min(...leftPositions.values());
  const rawMinTop = Math.min(...topPositions.values());
  const xOffset = metrics.graphPadding - rawMinLeft;
  const yOffset = metrics.graphPadding - rawMinTop;
  const positions = /* @__PURE__ */ new Map();
  for (const node of nodes) {
    positions.set(node.id, {
      x: (leftPositions.get(node.id) || 0) + xOffset,
      y: (topPositions.get(node.id) || 0) + yOffset
    });
  }
  const positioned = [...positions.values()];
  const minX = Math.min(...positioned.map((position) => position.x));
  const minY = Math.min(...positioned.map((position) => position.y));
  const maxX = Math.max(...positioned.map((position) => position.x + metrics.nodeWidth));
  const maxY = Math.max(...positioned.map((position) => position.y + metrics.nodeHeight));
  return {
    positions,
    width: maxX + metrics.graphPadding,
    height: maxY + metrics.graphPadding,
    bounds: {
      minX,
      minY,
      maxX,
      maxY,
      width: maxX - minX,
      height: maxY - minY
    }
  };
}

// frontend/graph_layout/src/graphLayoutMath.ts
function average(values) {
  if (!values.length) {
    return 0;
  }
  return values.reduce((sum, value) => sum + value, 0) / values.length;
}
function compareNumbers(a, b) {
  return a - b;
}
function median(values) {
  if (!values.length) {
    return 0;
  }
  const sorted = [...values].sort(compareNumbers);
  const mid = Math.floor(sorted.length / 2);
  return sorted.length % 2 ? sorted[mid] : (sorted[mid - 1] + sorted[mid]) / 2;
}

// frontend/graph_layout/src/graphLayoutInput.ts
function getGraphNodes(graph) {
  return Array.isArray(graph?.nodes) ? graph.nodes : [];
}
function getGraphEdges(graph) {
  return Array.isArray(graph?.edges) ? graph.edges : [];
}
function buildNodeIndexMap(nodes) {
  return new Map(nodes.map((node, index) => [node.id, index]));
}
function computeNodeDepths(graph) {
  const nodes = getGraphNodes(graph);
  const edges = getGraphEdges(graph);
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
  return depths;
}
function groupNodeIdsByDepth(graph, depths) {
  const columns = /* @__PURE__ */ new Map();
  for (const node of getGraphNodes(graph)) {
    const depth = depths.get(node.id) || 0;
    const column = columns.get(depth) || [];
    column.push(node.id);
    columns.set(depth, column);
  }
  return new Map([...columns.entries()].sort((a, b) => compareNumbers(a[0], b[0])));
}

// frontend/graph_layout/src/graphLayoutPorts.ts
function sourceHandleLaneOrder(h) {
  if (h == null || h === "") {
    return 0;
  }
  if (h === "out") {
    return 0;
  }
  const m = /^out-(\d+)$/.exec(h);
  if (m) {
    return Number.parseInt(m[1], 10);
  }
  return 0;
}
function targetHandleSlotOrder(h) {
  if (h == null || h === "") {
    return 0;
  }
  if (h === "in") {
    return 0;
  }
  const m = /^in-(\d+)$/.exec(h);
  if (m) {
    return Number.parseInt(m[1], 10);
  }
  return 0;
}
function edgeTargetPortRank(e) {
  const v = e.targetPortVisualRank;
  if (v != null && Number.isFinite(v)) {
    return v;
  }
  return targetHandleSlotOrder(e.targetHandle);
}

// frontend/graph_layout/src/graphLayoutAdjacency.ts
function buildAdjacency(graph, nodeIndexMap) {
  const predTags = /* @__PURE__ */ new Map();
  const succTags = /* @__PURE__ */ new Map();
  for (const nodeId of nodeIndexMap.keys()) {
    predTags.set(nodeId, []);
    succTags.set(nodeId, []);
  }
  for (const edge of getGraphEdges(graph)) {
    if (!nodeIndexMap.has(edge.from) || !nodeIndexMap.has(edge.to)) {
      continue;
    }
    predTags.get(edge.to)?.push({
      id: edge.from,
      portKey: edgeTargetPortRank(edge)
    });
    succTags.get(edge.from)?.push({
      id: edge.to,
      portKey: sourceHandleLaneOrder(edge.sourceHandle)
    });
  }
  const compareTagged = (left, right) => {
    if (left.portKey !== right.portKey) {
      return compareNumbers(left.portKey, right.portKey);
    }
    return compareNumbers(nodeIndexMap.get(left.id) || 0, nodeIndexMap.get(right.id) || 0);
  };
  const predecessors = /* @__PURE__ */ new Map();
  const successors = /* @__PURE__ */ new Map();
  for (const nodeId of nodeIndexMap.keys()) {
    predecessors.set(
      nodeId,
      [...predTags.get(nodeId) || []].sort(compareTagged).map((t) => t.id)
    );
    successors.set(
      nodeId,
      [...succTags.get(nodeId) || []].sort(compareTagged).map((t) => t.id)
    );
  }
  return { predecessors, successors };
}

// frontend/graph_layout/src/graphLayoutMergeOrdering.ts
function buildMergeTargetNodeIds(graph) {
  const counts = /* @__PURE__ */ new Map();
  for (const edge of getGraphEdges(graph)) {
    counts.set(edge.to, (counts.get(edge.to) ?? 0) + 1);
  }
  return new Set([...counts.entries()].filter(([, n]) => n >= 2).map(([id]) => id));
}
function outgoingPortRankToMergeTargets(nodeId, graph, mergeTargets) {
  const m = /* @__PURE__ */ new Map();
  for (const edge of getGraphEdges(graph)) {
    if (edge.from === nodeId && mergeTargets.has(edge.to)) {
      m.set(edge.to, edgeTargetPortRank(edge));
    }
  }
  return m;
}
function editorStableInitialY(node) {
  const y = node?.initialY;
  if (y == null || !Number.isFinite(y)) {
    return Number.POSITIVE_INFINITY;
  }
  return y;
}
function compareEditorColumnOrder(a, b, graph, mergeTargets, meta) {
  const oa = outgoingPortRankToMergeTargets(a, graph, mergeTargets);
  const ob = outgoingPortRankToMergeTargets(b, graph, mergeTargets);
  const shared = [...oa.keys()].filter((t) => ob.has(t)).sort((x, y) => x.localeCompare(y));
  for (const t of shared) {
    const ra = oa.get(t) ?? 0;
    const rb = ob.get(t) ?? 0;
    if (ra !== rb) {
      return compareNumbers(ra, rb);
    }
  }
  const ya = editorStableInitialY(meta.get(a));
  const yb = editorStableInitialY(meta.get(b));
  if (ya !== yb) {
    return compareNumbers(ya, yb);
  }
  const ka = meta.get(a)?.layerSortKey ?? 0;
  const kb = meta.get(b)?.layerSortKey ?? 0;
  if (ka !== kb) {
    return compareNumbers(ka, kb);
  }
  return a.localeCompare(b);
}
function orderEditorLayersBySortKey(groupedColumns, graph) {
  const meta = new Map(graph.nodes.map((n) => [n.id, n]));
  const mergeTargets = buildMergeTargetNodeIds(graph);
  const out = /* @__PURE__ */ new Map();
  for (const [depth, ids] of groupedColumns) {
    const sorted = [...ids].sort(
      (a, b) => compareEditorColumnOrder(a, b, graph, mergeTargets, meta)
    );
    out.set(depth, sorted);
  }
  return out;
}

// frontend/graph_layout/src/graphLayoutBarycenter.ts
function buildOrderIndexMap(columns) {
  const orderIndex = /* @__PURE__ */ new Map();
  for (const nodeIds of columns.values()) {
    nodeIds.forEach((nodeId, index) => {
      orderIndex.set(nodeId, index);
    });
  }
  return orderIndex;
}
function reorderColumnByBarycenter(nodeIds, neighborMap, orderIndex, baseOrder) {
  const currentOrder = new Map(nodeIds.map((nodeId, index) => [nodeId, index]));
  return [...nodeIds].sort((left, right) => {
    const leftNeighbors = (neighborMap.get(left) || []).filter(
      (nodeId) => orderIndex.has(nodeId)
    );
    const rightNeighbors = (neighborMap.get(right) || []).filter(
      (nodeId) => orderIndex.has(nodeId)
    );
    const leftHasScore = leftNeighbors.length > 0;
    const rightHasScore = rightNeighbors.length > 0;
    if (!leftHasScore && !rightHasScore) {
      return compareNumbers(currentOrder.get(left) || 0, currentOrder.get(right) || 0);
    }
    if (!leftHasScore || !rightHasScore) {
      return leftHasScore ? -1 : 1;
    }
    const leftScore = average(leftNeighbors.map((nodeId) => orderIndex.get(nodeId) || 0));
    const rightScore = average(rightNeighbors.map((nodeId) => orderIndex.get(nodeId) || 0));
    if (Math.abs(leftScore - rightScore) > 1e-4) {
      return leftScore - rightScore;
    }
    const currentDelta = compareNumbers(
      currentOrder.get(left) || 0,
      currentOrder.get(right) || 0
    );
    if (currentDelta !== 0) {
      return currentDelta;
    }
    return compareNumbers(baseOrder.get(left) || 0, baseOrder.get(right) || 0);
  });
}
function orderNodeIdsByBarycenter(graph, columns, _depths) {
  const sortedDepths = [...columns.keys()].sort(compareNumbers);
  const nodeIndexMap = buildNodeIndexMap(getGraphNodes(graph));
  const adjacency = buildAdjacency(graph, nodeIndexMap);
  const orderedColumns = new Map(
    sortedDepths.map((depth) => [depth, [...columns.get(depth) || []]])
  );
  const baseOrder = /* @__PURE__ */ new Map();
  for (const nodeIds of orderedColumns.values()) {
    nodeIds.forEach((nodeId, index) => {
      baseOrder.set(nodeId, index);
    });
  }
  for (let pass = 0; pass < ORDERING_PASSES; pass += 1) {
    for (let index = 1; index < sortedDepths.length; index += 1) {
      const depth = sortedDepths[index];
      const orderIndex = buildOrderIndexMap(orderedColumns);
      orderedColumns.set(
        depth,
        reorderColumnByBarycenter(
          orderedColumns.get(depth) || [],
          adjacency.predecessors,
          orderIndex,
          baseOrder
        )
      );
    }
    for (let index = sortedDepths.length - 2; index >= 0; index -= 1) {
      const depth = sortedDepths[index];
      const orderIndex = buildOrderIndexMap(orderedColumns);
      orderedColumns.set(
        depth,
        reorderColumnByBarycenter(
          orderedColumns.get(depth) || [],
          adjacency.successors,
          orderIndex,
          baseOrder
        )
      );
    }
  }
  return orderedColumns;
}

// frontend/graph_layout/src/graphLayoutColumnPlan.ts
function buildOrderedColumnLayout(graph, nodes, metrics) {
  const depths = computeNodeDepths(graph);
  const groupedColumns = groupNodeIdsByDepth(graph, depths);
  const orderedColumns = metrics.horizontalPlacement === "editor" ? orderEditorLayersBySortKey(groupedColumns, graph) : orderNodeIdsByBarycenter(graph, groupedColumns, depths);
  const nodeIndexMap = buildNodeIndexMap(nodes);
  return {
    orderedColumns,
    sortedDepths: [...orderedColumns.keys()].sort(compareNumbers),
    adjacency: buildAdjacency(graph, nodeIndexMap)
  };
}

// frontend/graph_layout/src/graphLayoutHorizontal.ts
function buildNodeRankOrderMap(columns) {
  const rankOrder = /* @__PURE__ */ new Map();
  for (const nodeIds of columns.values()) {
    nodeIds.forEach((nodeId, index) => {
      rankOrder.set(nodeId, index);
    });
  }
  return rankOrder;
}
function orderNodeIdsForHorizontalPlacement(nodeIds, topPositions, rankOrder) {
  return [...nodeIds].sort((left, right) => {
    const topDelta = compareNumbers(topPositions.get(left) || 0, topPositions.get(right) || 0);
    if (Math.abs(topDelta) > 1e-4) {
      return topDelta;
    }
    return compareNumbers(rankOrder.get(left) || 0, rankOrder.get(right) || 0);
  });
}
function computeHorizontalPositions(graph, columns, topPositions, metrics) {
  const edgeGap = Math.max(40, metrics.columnGap - metrics.nodeWidth);
  const sameRankGap = edgeGap;
  const nodes = getGraphNodes(graph);
  const nodeIndexMap = buildNodeIndexMap(nodes);
  const adjacency = buildAdjacency(graph, nodeIndexMap);
  const rankOrder = buildNodeRankOrderMap(columns);
  const sortedDepths = [...columns.keys()].sort(compareNumbers);
  const leftPositions = /* @__PURE__ */ new Map();
  for (let depthIndex = sortedDepths.length - 1; depthIndex >= 0; depthIndex -= 1) {
    const depth = sortedDepths[depthIndex];
    const nodeIds = orderNodeIdsForHorizontalPlacement(
      columns.get(depth) || [],
      topPositions,
      rankOrder
    );
    let nextRankLeft = Infinity;
    for (let nodeIndex = nodeIds.length - 1; nodeIndex >= 0; nodeIndex -= 1) {
      const nodeId = nodeIds[nodeIndex];
      const sameRankStagger = nodeIndex * metrics.columnStagger;
      const successorLefts = (adjacency.successors.get(nodeId) || []).filter((successorId) => leftPositions.has(successorId)).map(
        (successorId) => (leftPositions.get(successorId) || 0) - metrics.columnGap - sameRankStagger
      );
      const sameRankConstraint = Number.isFinite(nextRankLeft) ? nextRankLeft - metrics.nodeWidth - sameRankGap : Infinity;
      let constrainedLeft;
      if (successorLefts.length) {
        constrainedLeft = Math.min(sameRankConstraint, ...successorLefts);
      } else if (Number.isFinite(sameRankConstraint)) {
        constrainedLeft = sameRankConstraint - sameRankStagger;
      } else {
        constrainedLeft = 0;
      }
      leftPositions.set(nodeId, constrainedLeft);
      nextRankLeft = constrainedLeft;
    }
  }
  return leftPositions;
}
function computeHorizontalPositionsEditor(columns, metrics) {
  const leftPositions = /* @__PURE__ */ new Map();
  const sortedDepths = [...columns.keys()].sort(compareNumbers);
  const step = metrics.nodeWidth + metrics.columnGap;
  for (const depth of sortedDepths) {
    const left = metrics.graphPadding + depth * step;
    for (const nodeId of columns.get(depth) || []) {
      leftPositions.set(nodeId, left);
    }
  }
  return leftPositions;
}

// frontend/graph_layout/src/graphLayoutVertical.ts
function enforceNonDecreasingDesiredTopsForColumnOrder(desiredTops) {
  if (!desiredTops.length) {
    return desiredTops;
  }
  const out = [...desiredTops];
  for (let i = 1; i < out.length; i += 1) {
    const prev = out[i - 1];
    const cur = out[i];
    if (prev !== void 0 && cur !== void 0 && cur < prev) {
      out[i] = prev;
    }
  }
  return out;
}
function compactColumnTops(nodeIds, desiredTops, rowGap) {
  if (!nodeIds.length) {
    return [];
  }
  const placed = [];
  for (let index = 0; index < nodeIds.length; index += 1) {
    const desiredTop = desiredTops[index];
    if (index === 0) {
      placed.push(desiredTop);
      continue;
    }
    placed.push(Math.max(desiredTop, placed[index - 1] + rowGap));
  }
  for (let index = placed.length - 2; index >= 0; index -= 1) {
    placed[index] = Math.min(placed[index], placed[index + 1] - rowGap);
  }
  return placed;
}
function buildInitialTopPositions(columns, rowGap) {
  const positions = /* @__PURE__ */ new Map();
  for (const nodeIds of columns.values()) {
    nodeIds.forEach((nodeId, index) => {
      positions.set(nodeId, index * rowGap);
    });
  }
  return positions;
}
function computeDesiredTop(nodeId, neighborMap, topPositions) {
  const neighborTops = (neighborMap.get(nodeId) || []).filter((neighborId) => topPositions.has(neighborId)).map((neighborId) => topPositions.get(neighborId) || 0);
  if (!neighborTops.length) {
    return topPositions.get(nodeId) || 0;
  }
  return average(neighborTops);
}
function applyVerticalSweep(sortedDepths, orderedColumns, neighborMap, topPositions, rowGap, editorClampColumnOrder) {
  for (const depth of sortedDepths) {
    const nodeIds = orderedColumns.get(depth) || [];
    let desiredTops = nodeIds.map(
      (nodeId) => computeDesiredTop(nodeId, neighborMap, topPositions)
    );
    if (editorClampColumnOrder) {
      desiredTops = enforceNonDecreasingDesiredTopsForColumnOrder(desiredTops);
    }
    const compactedTops = compactColumnTops(nodeIds, desiredTops, rowGap);
    nodeIds.forEach((nodeId, index) => {
      topPositions.set(nodeId, compactedTops[index]);
    });
  }
}
function computeVerticalTopPositions(orderedColumns, sortedDepths, adjacency, metrics) {
  const topPositions = buildInitialTopPositions(orderedColumns, metrics.rowGap);
  const reverseDepths = [...sortedDepths].reverse();
  const editorClamp = metrics.horizontalPlacement === "editor";
  for (let pass = 0; pass < POSITIONING_PASSES; pass += 1) {
    applyVerticalSweep(
      sortedDepths,
      orderedColumns,
      adjacency.predecessors,
      topPositions,
      metrics.rowGap,
      editorClamp
    );
    if (metrics.horizontalPlacement !== "editor") {
      applyVerticalSweep(
        reverseDepths,
        orderedColumns,
        adjacency.successors,
        topPositions,
        metrics.rowGap,
        false
      );
    }
  }
  return topPositions;
}
function flattenEditorDepthVerticalTrend(orderedColumns, topPositions) {
  const sortedDepths = [...orderedColumns.keys()].sort(compareNumbers);
  if (sortedDepths.length < 2) {
    return;
  }
  const depthMedianTop = sortedDepths.map((d) => {
    const ids = orderedColumns.get(d) || [];
    const tops = ids.map((id) => topPositions.get(id) ?? 0);
    return { depth: d, medianTop: median(tops) };
  });
  const xs = depthMedianTop.map((r) => r.depth);
  const ys = depthMedianTop.map((r) => r.medianTop);
  const mx = xs.reduce((a, b) => a + b, 0) / xs.length;
  const my = ys.reduce((a, b) => a + b, 0) / ys.length;
  let num = 0;
  let den = 0;
  for (let i = 0; i < xs.length; i += 1) {
    num += (xs[i] - mx) * (ys[i] - my);
    den += (xs[i] - mx) ** 2;
  }
  const slope = den > 1e-9 ? num / den : 0;
  if (Math.abs(slope) < 1e-6) {
    return;
  }
  for (const d of sortedDepths) {
    for (const id of orderedColumns.get(d) || []) {
      const t = topPositions.get(id) ?? 0;
      topPositions.set(id, t - slope * d);
    }
  }
}
function editorReflowColumnVerticalGaps(orderedColumns, topPositions, rowGap) {
  const sortedDepths = [...orderedColumns.keys()].sort(compareNumbers);
  for (const depth of sortedDepths) {
    const nodeIds = orderedColumns.get(depth) || [];
    const desiredTops = nodeIds.map((id) => topPositions.get(id) ?? 0);
    const compacted = compactColumnTops(nodeIds, desiredTops, rowGap);
    nodeIds.forEach((id, index) => {
      topPositions.set(id, compacted[index]);
    });
  }
}

// frontend/graph_layout/src/graphLayoutGrouped.ts
function computeGroupedGraphLayout(graph, metrics) {
  const nodes = getGraphNodes(graph);
  if (!nodes.length) {
    return buildEmptyGraphLayout(metrics);
  }
  const { orderedColumns, sortedDepths, adjacency } = buildOrderedColumnLayout(graph, nodes, metrics);
  const topPositions = computeVerticalTopPositions(
    orderedColumns,
    sortedDepths,
    adjacency,
    metrics
  );
  if (metrics.horizontalPlacement === "editor") {
    for (let pass = 0; pass < 2; pass += 1) {
      flattenEditorDepthVerticalTrend(orderedColumns, topPositions);
      editorReflowColumnVerticalGaps(orderedColumns, topPositions, metrics.rowGap);
    }
  }
  if (metrics.horizontalPlacement === "editor" && isEditorGraphLayoutConsoleDebugEnabled()) {
    const sortedDepthKeys = [...orderedColumns.keys()].sort(compareNumbers);
    const depthAvgTop = sortedDepthKeys.map((d) => {
      const ids = orderedColumns.get(d) || [];
      const tops = ids.map((id) => topPositions.get(id) ?? 0);
      const avgTop = tops.length ? tops.reduce((a, b) => a + b, 0) / tops.length : 0;
      return { depth: d, n: ids.length, avgTop };
    });
    let avgTopSlopeVsDepth = 0;
    if (depthAvgTop.length >= 2) {
      const xs = depthAvgTop.map((r) => r.depth);
      const ys = depthAvgTop.map((r) => r.avgTop);
      const mx = xs.reduce((a, b) => a + b, 0) / xs.length;
      const my = ys.reduce((a, b) => a + b, 0) / ys.length;
      let num = 0;
      let den = 0;
      for (let i = 0; i < xs.length; i += 1) {
        num += (xs[i] - mx) * (ys[i] - my);
        den += (xs[i] - mx) ** 2;
      }
      avgTopSlopeVsDepth = den > 1e-9 ? num / den : 0;
    }
    const snapshot = {
      nodeCount: nodes.length,
      nodeWidth: metrics.nodeWidth,
      columnGap: metrics.columnGap,
      rowGap: metrics.rowGap,
      horizontalStep: metrics.nodeWidth + metrics.columnGap,
      editorFlattenDepthTrend: true,
      mergeBiasPxCap: 0,
      depthAvgTop,
      avgTopSlopeVsDepth
    };
    console.log(`[shapez graph-layout]
${JSON.stringify(snapshot, null, 2)}`);
  }
  const leftPositions = metrics.horizontalPlacement === "editor" ? computeHorizontalPositionsEditor(orderedColumns, metrics) : computeHorizontalPositions(graph, orderedColumns, topPositions, metrics);
  return buildFinalGraphLayout(nodes, leftPositions, topPositions, metrics);
}

// frontend/graph_layout/src/graphLayoutPinned.ts
function rectsOverlap(ax, ay, bx, by, metrics) {
  return !(ax + metrics.nodeWidth <= bx || bx + metrics.nodeWidth <= ax || ay + metrics.nodeHeight <= by || by + metrics.nodeHeight <= ay);
}
function resolvePinnedNodeOverlaps(positions, metrics) {
  const ids = [...positions.keys()].sort((a, b) => {
    const pa = positions.get(a);
    const pb = positions.get(b);
    if (!pa || !pb) {
      return 0;
    }
    if (pa.y !== pb.y) {
      return pa.y - pb.y;
    }
    if (pa.x !== pb.x) {
      return pa.x - pb.x;
    }
    return String(a).localeCompare(String(b));
  });
  const placed = [];
  for (const id of ids) {
    const start = positions.get(id);
    if (!start) {
      continue;
    }
    let p = { x: start.x, y: start.y };
    let tries = 0;
    while (tries < 400) {
      let overlap = false;
      for (const q of placed) {
        if (rectsOverlap(p.x, p.y, q.x, q.y, metrics)) {
          overlap = true;
          break;
        }
      }
      if (!overlap) {
        break;
      }
      p = { x: p.x, y: p.y + metrics.rowGap };
      tries += 1;
    }
    placed.push({ x: p.x, y: p.y });
    positions.set(id, p);
  }
}
function graphUsesPinnedPositions(graph) {
  const nodes = getGraphNodes(graph);
  if (!nodes.length) {
    return false;
  }
  const coords = [];
  for (const node of nodes) {
    const x = Number(node.x);
    const y = Number(node.y);
    if (!Number.isFinite(x) || !Number.isFinite(y)) {
      return false;
    }
    coords.push({ x, y });
  }
  if (coords.length === 1) {
    return true;
  }
  const minX = Math.min(...coords.map((c) => c.x));
  const maxX = Math.max(...coords.map((c) => c.x));
  const minY = Math.min(...coords.map((c) => c.y));
  const maxY = Math.max(...coords.map((c) => c.y));
  const spread = Math.max(maxX - minX, maxY - minY);
  return spread > 0.5;
}
function computePinnedGraphLayout(graph, metrics) {
  const nodes = getGraphNodes(graph);
  const positions = /* @__PURE__ */ new Map();
  for (const node of nodes) {
    const x = Number(node.x);
    const y = Number(node.y);
    positions.set(node.id, {
      x: Number.isFinite(x) ? x : metrics.graphPadding,
      y: Number.isFinite(y) ? y : metrics.graphPadding
    });
  }
  const posVals = [...positions.values()];
  const xOff = metrics.graphPadding - Math.min(...posVals.map((p) => p.x));
  const yOff = metrics.graphPadding - Math.min(...posVals.map((p) => p.y));
  const shifted = /* @__PURE__ */ new Map();
  for (const [id, p] of positions) {
    shifted.set(id, { x: p.x + xOff, y: p.y + yOff });
  }
  resolvePinnedNodeOverlaps(shifted, metrics);
  const positioned = [...shifted.values()];
  const minX = Math.min(...positioned.map((position) => position.x));
  const minY = Math.min(...positioned.map((position) => position.y));
  const maxX = Math.max(...positioned.map((position) => position.x + metrics.nodeWidth));
  const maxY = Math.max(...positioned.map((position) => position.y + metrics.nodeHeight));
  return {
    positions: shifted,
    width: maxX + metrics.graphPadding,
    height: maxY + metrics.graphPadding,
    bounds: {
      minX,
      minY,
      maxX,
      maxY,
      width: maxX - minX,
      height: maxY - minY
    }
  };
}

// frontend/graph_layout/src/graphLayoutEngine.ts
function computeGraphLayout(graph, metrics) {
  if (graphUsesPinnedPositions(graph)) {
    return computePinnedGraphLayout(graph, metrics);
  }
  return computeGroupedGraphLayout(graph, metrics);
}

// frontend/graph_layout/src/metrics.ts
var SOLVER_LAYOUT_METRICS = {
  nodeWidth: 190,
  nodeHeight: 320,
  columnGap: 270,
  rowGap: 356,
  graphPadding: 40,
  columnStagger: 26,
  horizontalPlacement: "timeline"
};

// frontend/graph_layout/src/solverStaticBundle.ts
var M = SOLVER_LAYOUT_METRICS;
var NODE_WIDTH = M.nodeWidth;
var NODE_HEIGHT = M.nodeHeight;
var COLUMN_GAP = M.columnGap;
var ROW_GAP = M.rowGap;
var GRAPH_PADDING = M.graphPadding;
function computeHorizontalPositions2(graph, columns, topPositions) {
  return computeHorizontalPositions(graph, columns, topPositions, M);
}
function computeGroupedGraphLayout2(graph) {
  return computeGroupedGraphLayout(graph, M);
}
function computeGraphLayout2(graph) {
  return computeGraphLayout(graph, M);
}
export {
  COLUMN_GAP,
  GRAPH_PADDING,
  NODE_HEIGHT,
  NODE_WIDTH,
  ROW_GAP,
  computeGraphLayout2 as computeGraphLayout,
  computeGroupedGraphLayout2 as computeGroupedGraphLayout,
  computeHorizontalPositions2 as computeHorizontalPositions,
  computeNodeDepths,
  groupNodeIdsByDepth,
  orderNodeIdsByBarycenter
};
