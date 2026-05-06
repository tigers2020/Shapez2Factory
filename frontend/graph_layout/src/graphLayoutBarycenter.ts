import { ORDERING_PASSES } from "./constants";
import type { GraphInput } from "./types";
import { buildAdjacency } from "./graphLayoutAdjacency";
import { buildNodeIndexMap, getGraphNodes } from "./graphLayoutInput";
import { average, compareNumbers } from "./graphLayoutMath";

function buildOrderIndexMap(columns: Map<number, string[]>): Map<string, number> {
  const orderIndex = new Map<string, number>();
  for (const nodeIds of columns.values()) {
    nodeIds.forEach((nodeId, index) => {
      orderIndex.set(nodeId, index);
    });
  }
  return orderIndex;
}

function reorderColumnByBarycenter(
  nodeIds: string[],
  neighborMap: Map<string, string[]>,
  orderIndex: Map<string, number>,
  baseOrder: Map<string, number>,
): string[] {
  const currentOrder = new Map(nodeIds.map((nodeId, index) => [nodeId, index]));
  return [...nodeIds].sort((left, right) => {
    const leftNeighbors = (neighborMap.get(left) || []).filter((nodeId) =>
      orderIndex.has(nodeId),
    );
    const rightNeighbors = (neighborMap.get(right) || []).filter((nodeId) =>
      orderIndex.has(nodeId),
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

export function orderNodeIdsByBarycenter(
  graph: GraphInput,
  columns: Map<number, string[]>,
  _depths: Map<string, number>,
): Map<number, string[]> {
  const sortedDepths = [...columns.keys()].sort(compareNumbers);
  const nodeIndexMap = buildNodeIndexMap(getGraphNodes(graph));
  const adjacency = buildAdjacency(graph, nodeIndexMap);
  const orderedColumns = new Map(
    sortedDepths.map((depth) => [depth, [...(columns.get(depth) || [])]]),
  );
  const baseOrder = new Map<string, number>();
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
