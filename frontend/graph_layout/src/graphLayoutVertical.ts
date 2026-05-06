import { POSITIONING_PASSES } from "./constants";
import type { AdjacencyResult } from "./graphLayoutAdjacency";
import type { LayoutMetrics } from "./types";
import { average, median, compareNumbers } from "./graphLayoutMath";

/** Editor: column nodeIds order is semantic (initialY / ports); neighbor averages must not invert it. */
function enforceNonDecreasingDesiredTopsForColumnOrder(desiredTops: number[]): number[] {
  if (!desiredTops.length) {
    return desiredTops;
  }
  const out = [...desiredTops];
  for (let i = 1; i < out.length; i += 1) {
    const prev = out[i - 1];
    const cur = out[i];
    if (prev !== undefined && cur !== undefined && cur < prev) {
      out[i] = prev;
    }
  }
  return out;
}

function compactColumnTops(nodeIds: string[], desiredTops: number[], rowGap: number): number[] {
  if (!nodeIds.length) {
    return [];
  }

  const placed: number[] = [];
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

function buildInitialTopPositions(columns: Map<number, string[]>, rowGap: number): Map<string, number> {
  const positions = new Map<string, number>();
  for (const nodeIds of columns.values()) {
    nodeIds.forEach((nodeId, index) => {
      positions.set(nodeId, index * rowGap);
    });
  }
  return positions;
}

function computeDesiredTop(
  nodeId: string,
  neighborMap: Map<string, string[]>,
  topPositions: Map<string, number>,
): number {
  const neighborTops = (neighborMap.get(nodeId) || [])
    .filter((neighborId) => topPositions.has(neighborId))
    .map((neighborId) => topPositions.get(neighborId) || 0);
  if (!neighborTops.length) {
    return topPositions.get(nodeId) || 0;
  }
  return average(neighborTops);
}

function applyVerticalSweep(
  sortedDepths: number[],
  orderedColumns: Map<number, string[]>,
  neighborMap: Map<string, string[]>,
  topPositions: Map<string, number>,
  rowGap: number,
  editorClampColumnOrder: boolean,
): void {
  for (const depth of sortedDepths) {
    const nodeIds = orderedColumns.get(depth) || [];
    let desiredTops = nodeIds.map((nodeId) =>
      computeDesiredTop(nodeId, neighborMap, topPositions),
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

export function computeVerticalTopPositions(
  orderedColumns: Map<number, string[]>,
  sortedDepths: number[],
  adjacency: AdjacencyResult,
  metrics: LayoutMetrics,
): Map<string, number> {
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
      editorClamp,
    );
    // Timeline: symmetric barycenter (also pulls sources toward downstream).
    // Editor: predecessor-only — successor pull collapses merge ops toward a single source row.
    if (metrics.horizontalPlacement !== "editor") {
      applyVerticalSweep(
        reverseDepths,
        orderedColumns,
        adjacency.successors,
        topPositions,
        metrics.rowGap,
        false,
      );
    }
  }

  return topPositions;
}

/**
 * Editor: remove linear trend of (depth vs column median top) so long pipelines do not "sink" right/down.
 */
export function flattenEditorDepthVerticalTrend(
  orderedColumns: Map<number, string[]>,
  topPositions: Map<string, number>,
): void {
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

export function editorReflowColumnVerticalGaps(
  orderedColumns: Map<number, string[]>,
  topPositions: Map<string, number>,
  rowGap: number,
): void {
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
