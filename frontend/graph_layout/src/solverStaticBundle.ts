/**
 * Entry used by esbuild to emit `django_apps/web/static/web/js/solver_graph_layout.js`.
 * Exports match the legacy hand-written module (pytest + timeline markup).
 */
import {
  computeGroupedGraphLayout as computeGroupedGraphLayoutCore,
  computeGraphLayout as computeGraphLayoutCore,
  computeHorizontalPositions as computeHorizontalPositionsCore,
} from "./graphLayoutEngine";
import type { GraphInput } from "./types";
import { SOLVER_LAYOUT_METRICS } from "./metrics";

const M = SOLVER_LAYOUT_METRICS;

export const NODE_WIDTH = M.nodeWidth;
export const NODE_HEIGHT = M.nodeHeight;
export const COLUMN_GAP = M.columnGap;
export const ROW_GAP = M.rowGap;
export const GRAPH_PADDING = M.graphPadding;

export {
  computeNodeDepths,
  groupNodeIdsByDepth,
  orderNodeIdsByBarycenter,
} from "./graphLayoutEngine";

export function computeHorizontalPositions(
  graph: GraphInput,
  columns: Map<number, string[]>,
  topPositions: Map<string, number>,
): Map<string, number> {
  return computeHorizontalPositionsCore(graph, columns, topPositions, M);
}

export function computeGroupedGraphLayout(graph: GraphInput) {
  return computeGroupedGraphLayoutCore(graph, M);
}

export function computeGraphLayout(graph: GraphInput) {
  return computeGraphLayoutCore(graph, M);
}
