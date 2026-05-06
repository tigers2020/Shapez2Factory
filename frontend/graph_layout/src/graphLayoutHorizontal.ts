import type { GraphInput, LayoutMetrics } from "./types";
import { buildAdjacency } from "./graphLayoutAdjacency";
import { buildNodeIndexMap, getGraphNodes } from "./graphLayoutInput";
import { compareNumbers } from "./graphLayoutMath";

function buildNodeRankOrderMap(columns: Map<number, string[]>): Map<string, number> {
  const rankOrder = new Map<string, number>();
  for (const nodeIds of columns.values()) {
    nodeIds.forEach((nodeId, index) => {
      rankOrder.set(nodeId, index);
    });
  }
  return rankOrder;
}

function orderNodeIdsForHorizontalPlacement(
  nodeIds: string[],
  topPositions: Map<string, number>,
  rankOrder: Map<string, number>,
): string[] {
  return [...nodeIds].sort((left, right) => {
    const topDelta = compareNumbers(topPositions.get(left) || 0, topPositions.get(right) || 0);
    if (Math.abs(topDelta) > 0.0001) {
      return topDelta;
    }
    return compareNumbers(rankOrder.get(left) || 0, rankOrder.get(right) || 0);
  });
}

export function computeHorizontalPositions(
  graph: GraphInput,
  columns: Map<number, string[]>,
  topPositions: Map<string, number>,
  metrics: LayoutMetrics,
): Map<string, number> {
  const edgeGap = Math.max(40, metrics.columnGap - metrics.nodeWidth);
  const sameRankGap = edgeGap;

  const nodes = getGraphNodes(graph);
  const nodeIndexMap = buildNodeIndexMap(nodes);
  const adjacency = buildAdjacency(graph, nodeIndexMap);
  const rankOrder = buildNodeRankOrderMap(columns);
  const sortedDepths = [...columns.keys()].sort(compareNumbers);
  const leftPositions = new Map<string, number>();

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
      const sameRankStagger = nodeIndex * metrics.columnStagger;
      const successorLefts = (adjacency.successors.get(nodeId) || [])
        .filter((successorId) => leftPositions.has(successorId))
        .map(
          (successorId) =>
            (leftPositions.get(successorId) || 0) - metrics.columnGap - sameRankStagger,
        );
      const sameRankConstraint = Number.isFinite(nextRankLeft)
        ? nextRankLeft - metrics.nodeWidth - sameRankGap
        : Infinity;
      let constrainedLeft: number;
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

/** Editor policy: x encodes dependency depth only; parallel nodes at one depth share the same left. */
export function computeHorizontalPositionsEditor(
  columns: Map<number, string[]>,
  metrics: LayoutMetrics,
): Map<string, number> {
  const leftPositions = new Map<string, number>();
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
