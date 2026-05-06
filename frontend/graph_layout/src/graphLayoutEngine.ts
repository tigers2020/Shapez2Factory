/**
 * 공개 그래프 레이아웃 API의 진입점.
 * 구현은 solver/editor/pinned 단계별 모듈로 분리되어 있다 (`graphLayout*.ts`).
 */
import type { GraphInput, GraphLayoutResult, LayoutMetrics } from "./types";
import { isEditorGraphLayoutConsoleDebugEnabled } from "./graphLayoutDebug";
import { computeGroupedGraphLayout } from "./graphLayoutGrouped";
import { computeHorizontalPositions } from "./graphLayoutHorizontal";
import { computeNodeDepths, groupNodeIdsByDepth } from "./graphLayoutInput";
import { computePinnedGraphLayout, graphUsesPinnedPositions } from "./graphLayoutPinned";
import { orderNodeIdsByBarycenter } from "./graphLayoutBarycenter";

export { isEditorGraphLayoutConsoleDebugEnabled };
export { computeNodeDepths, groupNodeIdsByDepth };
export { orderNodeIdsByBarycenter };
export { computeHorizontalPositions };
export { computeGroupedGraphLayout };

export function computeGraphLayout(graph: GraphInput, metrics: LayoutMetrics): GraphLayoutResult {
  if (graphUsesPinnedPositions(graph)) {
    return computePinnedGraphLayout(graph, metrics);
  }
  return computeGroupedGraphLayout(graph, metrics);
}
