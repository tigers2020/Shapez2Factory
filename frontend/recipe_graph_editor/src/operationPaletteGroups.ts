/** Staff catalog `operations[].value` → 팔레트 섹션(UI 전용).
 *
 * LOGIC·UTILITY 등 비표시 계열은 **카탈로그에 넣지 않거나**, 엔진 `engineOperationIds`에 없으면
 * `GraphEditorApp` 팔레트에서 비활성 처리한다.
 */

export const PALETTE_CATEGORY_ORDER = ["SHAPE", "COLOR", "ROTATE", "CUT", "FLOW"] as const;

export type PaletteCategoryId = (typeof PALETTE_CATEGORY_ORDER)[number];

export type OperationChangeGroup = Exclude<PaletteCategoryId, "SHAPE">;

/** 엔진에 정의된 연산만. 알 수 없는 값은 `null`(모달에서는 전체 카탈로그 표시). */
export function operationChangeGroupId(value: string): OperationChangeGroup | null {
  const v = value.trim().toLowerCase();
  if (!v) {
    return null;
  }
  if (["rotate_cw", "rotate_ccw", "rotate_180"].includes(v)) {
    return "ROTATE";
  }
  if (["cutter", "half_destroyer", "splitter"].includes(v)) {
    return "CUT";
  }
  if (["painter", "color_mixer", "crystal_generator"].includes(v)) {
    return "COLOR";
  }
  if (["stacker", "swapper", "merge", "pin_pusher"].includes(v)) {
    return "FLOW";
  }
  return null;
}

export function paletteCategoryForOperation(value: string): Exclude<PaletteCategoryId, "SHAPE"> {
  return operationChangeGroupId(value) ?? "FLOW";
}
