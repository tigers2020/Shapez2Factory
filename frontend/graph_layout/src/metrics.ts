import type { LayoutMetrics } from "./types";

/** Matches legacy `solver_graph_layout.js` / timeline graph cards. Single source for spacing. */
export const SOLVER_LAYOUT_METRICS: LayoutMetrics = {
  nodeWidth: 190,
  nodeHeight: 320,
  columnGap: 270,
  rowGap: 356,
  graphPadding: 40,
  columnStagger: 26,
  horizontalPlacement: "timeline",
};

/**
 * Recipe graph editor (React Flow): small tiles (~56px).
 * columnGap = horizontal gap between adjacent columns (edge-to-edge), not timeline card spacing.
 */
export const EDITOR_LAYOUT_METRICS: LayoutMetrics = {
  nodeWidth: 56,
  nodeHeight: 56,
  columnGap: 48,
  rowGap: 112,
  graphPadding: 40,
  columnStagger: 26,
  horizontalPlacement: "editor",
};
