/**
 * ESM bundle entry for Node/pytest: editor metrics + grouped layout (recipe graph editor).
 */
import { computeGroupedGraphLayout } from "./graphLayoutEngine";
import { EDITOR_LAYOUT_METRICS } from "./metrics";
import type { GraphInput } from "./types";

export function computeEditorGraphLayout(graph: GraphInput) {
  return computeGroupedGraphLayout(graph, EDITOR_LAYOUT_METRICS);
}

export const EDITOR_ROW_GAP = EDITOR_LAYOUT_METRICS.rowGap;
