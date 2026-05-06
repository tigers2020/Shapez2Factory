import type { GraphInput, GraphLayoutResult, LayoutMetrics } from "./types";
import { buildEmptyGraphLayout, buildFinalGraphLayout } from "./graphLayoutBounds";
import { buildOrderedColumnLayout } from "./graphLayoutColumnPlan";
import { isEditorGraphLayoutConsoleDebugEnabled } from "./graphLayoutDebug";
import {
  computeHorizontalPositions,
  computeHorizontalPositionsEditor,
} from "./graphLayoutHorizontal";
import { getGraphNodes } from "./graphLayoutInput";
import { compareNumbers } from "./graphLayoutMath";
import {
  computeVerticalTopPositions,
  editorReflowColumnVerticalGaps,
  flattenEditorDepthVerticalTrend,
} from "./graphLayoutVertical";

export function computeGroupedGraphLayout(graph: GraphInput, metrics: LayoutMetrics): GraphLayoutResult {
  const nodes = getGraphNodes(graph);
  if (!nodes.length) {
    return buildEmptyGraphLayout(metrics);
  }

  const { orderedColumns, sortedDepths, adjacency } = buildOrderedColumnLayout(graph, nodes, metrics);
  const topPositions = computeVerticalTopPositions(
    orderedColumns,
    sortedDepths,
    adjacency,
    metrics,
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
      avgTopSlopeVsDepth,
    };
    console.log(`[shapez graph-layout]\n${JSON.stringify(snapshot, null, 2)}`);
  }

  const leftPositions =
    metrics.horizontalPlacement === "editor"
      ? computeHorizontalPositionsEditor(orderedColumns, metrics)
      : computeHorizontalPositions(graph, orderedColumns, topPositions, metrics);

  return buildFinalGraphLayout(nodes, leftPositions, topPositions, metrics);
}
