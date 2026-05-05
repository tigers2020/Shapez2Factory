/** Minimal graph shape shared by solver markup and recipe editor adapters. */
export type LayoutEdge = {
  from: string;
  to: string;
  /** Recipe editor: XYFlow source handle id (e.g. out, out-1). Drives neighbor ordering. */
  sourceHandle?: string | null;
  /** Recipe editor: XYFlow target handle id (e.g. in, in-1). Drives neighbor ordering. */
  targetHandle?: string | null;
  /**
   * Editor: vertical sort key for this wire into `to` (smaller = align toward top of column).
   * Painter 2-wire: in-1 above in — must match `recipeFlowNodes` handle `top` %.
   */
  targetPortVisualRank?: number;
};

export type LayoutNode = {
  id: string;
  x?: number;
  y?: number;
  /**
   * Auto-arrange 직전 캔버스 y (위쪽이 작은 값). Pinned 레이아웃 판별용 `y`와 별도.
   * 없으면 엔진이 기본값으로 정렬한다.
   */
  initialY?: number;
  /** Lower sorts above (smaller y). Editor-only; omitted in solver timeline graphs. */
  layerSortKey?: number;
  /** Recipe editor: React Flow node.type — drives vertical bias for multi-input operations. */
  reactFlowType?: string;
};

export type GraphInput = { nodes: LayoutNode[]; edges: LayoutEdge[] };

/** timeline: legacy stagger within a layer (solver markup). editor: same depth → same x, y only varies. */
export type HorizontalPlacementPolicy = "timeline" | "editor";

export type LayoutMetrics = {
  nodeWidth: number;
  nodeHeight: number;
  columnGap: number;
  rowGap: number;
  graphPadding: number;
  columnStagger: number;
  horizontalPlacement: HorizontalPlacementPolicy;
};

export type LayoutBounds = {
  minX: number;
  minY: number;
  maxX: number;
  maxY: number;
  width: number;
  height: number;
};

export type GraphLayoutResult = {
  positions: Map<string, { x: number; y: number }>;
  width: number;
  height: number;
  bounds: LayoutBounds;
};
