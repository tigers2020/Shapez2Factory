/** 한 레이어 풀 소스(기본 광물 4종, 미채색 u). 빈 소스 삽입 시 순환. */
export const BASE_FULL_SOURCE_SHAPE_CODES = [
  "CuCuCuCu",
  "RuRuRuRu",
  "SuSuSuSu",
  "WuWuWuWu",
] as const;

/** 첫 번째 기본 광물; 하위 호환·힌트용. */
export const DEFAULT_NEW_SOURCE_SHAPE_CODE = BASE_FULL_SOURCE_SHAPE_CODES[0];

/** 매크로 그래프 shape 기본 수량 — 규약 고정. 백엔드 RECIPE_GRAPH_DEFAULT_* 와 동일 수식. */
export const DEFAULT_SOURCE_SHAPE_QUANTITY_MATERIAL = 480 * 12;
export const DEFAULT_SOURCE_SHAPE_QUANTITY_FLUID = 28000 * 12;

export function defaultQuantityForShapeNodeData(data: {
  role?: unknown;
  source_carrier?: unknown;
}): number {
  if (data.source_carrier === "fluid") {
    return DEFAULT_SOURCE_SHAPE_QUANTITY_FLUID;
  }
  if (String(data.role ?? "") === "source") {
    return DEFAULT_SOURCE_SHAPE_QUANTITY_MATERIAL;
  }
  return 1;
}

/** `insertIndex`마다 4종 풀 소스를 번갈아 돌린다. */
export function pickCycledBaseFullSourceShapeCode(
  insertIndex: number,
): (typeof BASE_FULL_SOURCE_SHAPE_CODES)[number] {
  return BASE_FULL_SOURCE_SHAPE_CODES[insertIndex % BASE_FULL_SOURCE_SHAPE_CODES.length];
}

/** ``recipeFlowNodes`` shape tile ring ``h-16 w-16`` (64px) 절반 — 뷰포트 중앙 정렬 보정. */
export const RECIPE_NODE_TILE_HALF_PX = 32;

/** 팔레트 → React Flow 캔버스 커스텀 DnD MIME. */
export const RECIPE_PALETTE_DND_OP = "application/x-shapez-recipe-graph-op";
export const RECIPE_PALETTE_DND_SRC = "application/x-shapez-recipe-graph-src";

/** 팔레트 그리드: 열 수 및 셀 간격(px). */
export const RECIPE_PALETTE_GRID_COLUMNS = 4;
export const RECIPE_PALETTE_GRID_ORIGIN_X = 48;
export const RECIPE_PALETTE_GRID_CELL_WIDTH = 200;
export const RECIPE_PALETTE_GRID_ORIGIN_Y = 52;
export const RECIPE_PALETTE_GRID_CELL_HEIGHT = 120;

/** 로컬 노트 자동 저장 디바운스 (ms). */
export const RECIPE_NOTES_SAVE_DEBOUNCE_MS = 400;

/** 잘못된 연결 경고를 전역 상태에 다시 올리기 전 최소 간격 (ms). */
export const RECIPE_CONNECTION_WARN_THROTTLE_MS = 1200;
