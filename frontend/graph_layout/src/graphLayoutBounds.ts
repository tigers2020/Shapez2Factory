import type { GraphLayoutResult, LayoutMetrics, LayoutNode } from "./types";

export function buildEmptyGraphLayout(metrics: LayoutMetrics): GraphLayoutResult {
  const p = metrics.graphPadding;
  return {
    positions: new Map(),
    width: p * 2,
    height: p * 2,
    bounds: {
      minX: p,
      minY: p,
      maxX: p,
      maxY: p,
      width: 0,
      height: 0,
    },
  };
}

export function buildFinalGraphLayout(
  nodes: LayoutNode[],
  leftPositions: Map<string, number>,
  topPositions: Map<string, number>,
  metrics: LayoutMetrics,
): GraphLayoutResult {
  const rawMinLeft = Math.min(...leftPositions.values());
  const rawMinTop = Math.min(...topPositions.values());
  const xOffset = metrics.graphPadding - rawMinLeft;
  const yOffset = metrics.graphPadding - rawMinTop;
  const positions = new Map<string, { x: number; y: number }>();
  for (const node of nodes) {
    positions.set(node.id, {
      x: (leftPositions.get(node.id) || 0) + xOffset,
      y: (topPositions.get(node.id) || 0) + yOffset,
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
      height: maxY - minY,
    },
  };
}
