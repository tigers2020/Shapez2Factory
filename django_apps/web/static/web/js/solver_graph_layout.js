export const NODE_WIDTH = 190;
/** Must match rendered graph card height in graph_markup (shape + preview + labels). */
export const NODE_HEIGHT = 320;
export const COLUMN_GAP = 270;
/** Minimum vertical gap between node tops; must be >= NODE_HEIGHT to avoid overlap. */
export const ROW_GAP = 356;
export const GRAPH_PADDING = 40;
const COLUMN_STAGGER = 26;

const ORDERING_PASSES = 4;
const POSITIONING_PASSES = 6;
const EDGE_GAP = Math.max(40, COLUMN_GAP - NODE_WIDTH);
const SAME_RANK_GAP = EDGE_GAP;

function average(values) {
  if (!values.length) {
    return 0;
  }
  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function compareNumbers(a, b) {
  return a - b;
}

function getGraphNodes(graph) {
  return Array.isArray(graph?.nodes) ? graph.nodes : [];
}

function getGraphEdges(graph) {
  return Array.isArray(graph?.edges) ? graph.edges : [];
}

function buildNodeIndexMap(nodes) {
  return new Map(nodes.map((node, index) => [node.id, index]));
}

export function computeNodeDepths(graph) {
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

export function groupNodeIdsByDepth(graph, depths) {
  const columns = new Map();
  for (const node of getGraphNodes(graph)) {
    const depth = depths.get(node.id) || 0;
    const column = columns.get(depth) || [];
    column.push(node.id);
    columns.set(depth, column);
  }

  return new Map([...columns.entries()].sort((a, b) => compareNumbers(a[0], b[0])));
}

function buildAdjacency(graph, nodeIndexMap) {
  const predecessors = new Map();
  const successors = new Map();
  for (const nodeId of nodeIndexMap.keys()) {
    predecessors.set(nodeId, []);
    successors.set(nodeId, []);
  }

  for (const edge of getGraphEdges(graph)) {
    if (!nodeIndexMap.has(edge.from) || !nodeIndexMap.has(edge.to)) {
      continue;
    }
    predecessors.get(edge.to)?.push(edge.from);
    successors.get(edge.from)?.push(edge.to);
  }

  const sortByBaseOrder = (left, right) =>
    compareNumbers(nodeIndexMap.get(left) || 0, nodeIndexMap.get(right) || 0);
  for (const neighborIds of predecessors.values()) {
    neighborIds.sort(sortByBaseOrder);
  }
  for (const neighborIds of successors.values()) {
    neighborIds.sort(sortByBaseOrder);
  }

  return { predecessors, successors };
}

function buildOrderIndexMap(columns) {
  const orderIndex = new Map();
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
    const leftNeighbors = (neighborMap.get(left) || []).filter((nodeId) => orderIndex.has(nodeId));
    const rightNeighbors = (neighborMap.get(right) || []).filter((nodeId) => orderIndex.has(nodeId));
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
    if (Math.abs(leftScore - rightScore) > 0.0001) {
      return leftScore - rightScore;
    }

    const currentDelta = compareNumbers(
      currentOrder.get(left) || 0,
      currentOrder.get(right) || 0,
    );
    if (currentDelta !== 0) {
      return currentDelta;
    }
    return compareNumbers(baseOrder.get(left) || 0, baseOrder.get(right) || 0);
  });
}

export function orderNodeIdsByBarycenter(graph, columns, depths) {
  const sortedDepths = [...columns.keys()].sort(compareNumbers);
  const nodeIndexMap = buildNodeIndexMap(getGraphNodes(graph));
  const adjacency = buildAdjacency(graph, nodeIndexMap);
  const orderedColumns = new Map(
    sortedDepths.map((depth) => [depth, [...(columns.get(depth) || [])]]),
  );
  const baseOrder = new Map();
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
          baseOrder,
        ),
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
          baseOrder,
        ),
      );
    }
  }

  return orderedColumns;
}

function compactColumnTops(nodeIds, desiredTops) {
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
    placed.push(Math.max(desiredTop, placed[index - 1] + ROW_GAP));
  }

  for (let index = placed.length - 2; index >= 0; index -= 1) {
    placed[index] = Math.min(placed[index], placed[index + 1] - ROW_GAP);
  }

  return placed;
}

function buildInitialTopPositions(columns) {
  const positions = new Map();
  for (const nodeIds of columns.values()) {
    nodeIds.forEach((nodeId, index) => {
      positions.set(nodeId, index * ROW_GAP);
    });
  }
  return positions;
}

function computeDesiredTop(nodeId, neighborMap, topPositions) {
  const neighborTops = (neighborMap.get(nodeId) || [])
    .filter((neighborId) => topPositions.has(neighborId))
    .map((neighborId) => topPositions.get(neighborId) || 0);
  if (!neighborTops.length) {
    return topPositions.get(nodeId) || 0;
  }
  return average(neighborTops);
}

function buildNodeRankOrderMap(columns) {
  const rankOrder = new Map();
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
    if (Math.abs(topDelta) > 0.0001) {
      return topDelta;
    }
    return compareNumbers(rankOrder.get(left) || 0, rankOrder.get(right) || 0);
  });
}

export function computeHorizontalPositions(graph, columns, topPositions) {
  const nodes = getGraphNodes(graph);
  const nodeIndexMap = buildNodeIndexMap(nodes);
  const adjacency = buildAdjacency(graph, nodeIndexMap);
  const rankOrder = buildNodeRankOrderMap(columns);
  const sortedDepths = [...columns.keys()].sort(compareNumbers);
  const leftPositions = new Map();

  for (let depthIndex = sortedDepths.length - 1; depthIndex >= 0; depthIndex -= 1) {
    const depth = sortedDepths[depthIndex];
    const nodeIds = orderNodeIdsForHorizontalPlacement(
      columns.get(depth) || [],
      topPositions,
      rankOrder,
    );
    let nextRankLeft = Infinity;

    for (let nodeIndex = nodeIds.length - 1; nodeIndex >= 0; nodeIndex -= 1) {
      const nodeId = nodeIds[nodeIndex];
      const sameRankStagger = nodeIndex * COLUMN_STAGGER;
      const successorLefts = (adjacency.successors.get(nodeId) || [])
        .filter((successorId) => leftPositions.has(successorId))
        .map((successorId) => (leftPositions.get(successorId) || 0) - COLUMN_GAP - sameRankStagger);
      const sameRankConstraint = Number.isFinite(nextRankLeft)
        ? nextRankLeft - NODE_WIDTH - SAME_RANK_GAP
        : Infinity;
      const constrainedLeft = successorLefts.length
        ? Math.min(sameRankConstraint, ...successorLefts)
        : Number.isFinite(sameRankConstraint)
          ? sameRankConstraint - sameRankStagger
          : 0;

      leftPositions.set(nodeId, constrainedLeft);
      nextRankLeft = constrainedLeft;
    }
  }

  return leftPositions;
}

function buildEmptyGraphLayout() {
  return {
    positions: new Map(),
    width: GRAPH_PADDING * 2,
    height: GRAPH_PADDING * 2,
    bounds: {
      minX: GRAPH_PADDING,
      minY: GRAPH_PADDING,
      maxX: GRAPH_PADDING,
      maxY: GRAPH_PADDING,
      width: 0,
      height: 0,
    },
  };
}

function buildOrderedColumnLayout(graph, nodes) {
  const depths = computeNodeDepths(graph);
  const groupedColumns = groupNodeIdsByDepth(graph, depths);
  const orderedColumns = orderNodeIdsByBarycenter(graph, groupedColumns, depths);
  const nodeIndexMap = buildNodeIndexMap(nodes);
  return {
    orderedColumns,
    sortedDepths: [...orderedColumns.keys()].sort(compareNumbers),
    adjacency: buildAdjacency(graph, nodeIndexMap),
  };
}

function applyVerticalSweep(sortedDepths, orderedColumns, neighborMap, topPositions) {
  for (const depth of sortedDepths) {
    const nodeIds = orderedColumns.get(depth) || [];
    const desiredTops = nodeIds.map((nodeId) =>
      computeDesiredTop(nodeId, neighborMap, topPositions),
    );
    const compactedTops = compactColumnTops(nodeIds, desiredTops);
    nodeIds.forEach((nodeId, index) => {
      topPositions.set(nodeId, compactedTops[index]);
    });
  }
}

function computeVerticalTopPositions(orderedColumns, sortedDepths, adjacency) {
  const topPositions = buildInitialTopPositions(orderedColumns);
  const reverseDepths = [...sortedDepths].reverse();

  for (let pass = 0; pass < POSITIONING_PASSES; pass += 1) {
    applyVerticalSweep(
      sortedDepths,
      orderedColumns,
      adjacency.predecessors,
      topPositions,
    );
    applyVerticalSweep(
      reverseDepths,
      orderedColumns,
      adjacency.successors,
      topPositions,
    );
  }

  return topPositions;
}

function buildFinalGraphLayout(nodes, leftPositions, topPositions) {
  const rawMinLeft = Math.min(...leftPositions.values());
  const rawMinTop = Math.min(...topPositions.values());
  const xOffset = GRAPH_PADDING - rawMinLeft;
  const yOffset = GRAPH_PADDING - rawMinTop;
  const positions = new Map();
  for (const node of nodes) {
    positions.set(node.id, {
      x: (leftPositions.get(node.id) || 0) + xOffset,
      y: (topPositions.get(node.id) || 0) + yOffset,
    });
  }

  const positioned = [...positions.values()];
  const minX = Math.min(...positioned.map((position) => position.x));
  const minY = Math.min(...positioned.map((position) => position.y));
  const maxX = Math.max(...positioned.map((position) => position.x + NODE_WIDTH));
  const maxY = Math.max(...positioned.map((position) => position.y + NODE_HEIGHT));

  return {
    positions,
    width: maxX + GRAPH_PADDING,
    height: maxY + GRAPH_PADDING,
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

export function computeGroupedGraphLayout(graph) {
  const nodes = getGraphNodes(graph);
  if (!nodes.length) {
    return buildEmptyGraphLayout();
  }

  const { orderedColumns, sortedDepths, adjacency } = buildOrderedColumnLayout(graph, nodes);
  const topPositions = computeVerticalTopPositions(
    orderedColumns,
    sortedDepths,
    adjacency,
  );
  const leftPositions = computeHorizontalPositions(graph, orderedColumns, topPositions);

  return buildFinalGraphLayout(nodes, leftPositions, topPositions);
}

function rectsOverlap(ax, ay, bx, by) {
  return !(
    ax + NODE_WIDTH <= bx ||
    bx + NODE_WIDTH <= ax ||
    ay + NODE_HEIGHT <= by ||
    by + NODE_HEIGHT <= ay
  );
}

/** Pinned 좌표가 서로 겹치면(예: 예전 자동 생성 간격) 세로로 벌린다. */
function resolvePinnedNodeOverlaps(positions) {
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
        if (rectsOverlap(p.x, p.y, q.x, q.y)) {
          overlap = true;
          break;
        }
      }
      if (!overlap) {
        break;
      }
      p = { x: p.x, y: p.y + ROW_GAP };
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

function computePinnedGraphLayout(graph) {
  const nodes = getGraphNodes(graph);
  const positions = new Map();
  for (const node of nodes) {
    const x = Number(node.x);
    const y = Number(node.y);
    positions.set(node.id, {
      x: Number.isFinite(x) ? x : GRAPH_PADDING,
      y: Number.isFinite(y) ? y : GRAPH_PADDING,
    });
  }
  const posVals = [...positions.values()];
  const xOff = GRAPH_PADDING - Math.min(...posVals.map((p) => p.x));
  const yOff = GRAPH_PADDING - Math.min(...posVals.map((p) => p.y));
  const shifted = new Map();
  for (const [id, p] of positions) {
    shifted.set(id, { x: p.x + xOff, y: p.y + yOff });
  }
  resolvePinnedNodeOverlaps(shifted);
  const positioned = [...shifted.values()];
  const minX = Math.min(...positioned.map((position) => position.x));
  const minY = Math.min(...positioned.map((position) => position.y));
  const maxX = Math.max(...positioned.map((position) => position.x + NODE_WIDTH));
  const maxY = Math.max(...positioned.map((position) => position.y + NODE_HEIGHT));

  return {
    positions: shifted,
    width: maxX + GRAPH_PADDING,
    height: maxY + GRAPH_PADDING,
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

export function computeGraphLayout(graph) {
  if (graphUsesPinnedPositions(graph)) {
    return computePinnedGraphLayout(graph);
  }
  return computeGroupedGraphLayout(graph);
}
