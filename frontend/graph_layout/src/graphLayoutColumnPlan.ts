import type { GraphInput, LayoutMetrics, LayoutNode } from "./types";
import { buildAdjacency } from "./graphLayoutAdjacency";
import { buildNodeIndexMap, computeNodeDepths, groupNodeIdsByDepth } from "./graphLayoutInput";
import { compareNumbers } from "./graphLayoutMath";
import { orderEditorLayersBySortKey } from "./graphLayoutMergeOrdering";
import { orderNodeIdsByBarycenter } from "./graphLayoutBarycenter";

export function buildOrderedColumnLayout(graph: GraphInput, nodes: LayoutNode[], metrics: LayoutMetrics) {
  const depths = computeNodeDepths(graph);
  const groupedColumns = groupNodeIdsByDepth(graph, depths);
  const orderedColumns =
    metrics.horizontalPlacement === "editor"
      ? orderEditorLayersBySortKey(groupedColumns, graph)
      : orderNodeIdsByBarycenter(graph, groupedColumns, depths);
  const nodeIndexMap = buildNodeIndexMap(nodes);
  return {
    orderedColumns,
    sortedDepths: [...orderedColumns.keys()].sort(compareNumbers),
    adjacency: buildAdjacency(graph, nodeIndexMap),
  };
}
