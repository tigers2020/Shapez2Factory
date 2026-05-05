/** Staff catalog `operations[].value` → 팔레트 섹션(UI 전용).
 *
 * LOGIC·UTILITY 등 비표시 계열은 **카탈로그에 넣지 않거나**, 엔진 `engineOperationIds`에 없으면
 * `GraphEditorApp` 팔레트에서 비활성 처리한다.
 */

export const PALETTE_CATEGORY_ORDER = ["SHAPE", "COLOR", "ROTATE", "CUT", "FLOW"] as const;

export type PaletteCategoryId = (typeof PALETTE_CATEGORY_ORDER)[number];

export function paletteCategoryForOperation(value: string): Exclude<PaletteCategoryId, "SHAPE"> {
  const v = value.trim();
  if (["rotate_cw", "rotate_ccw", "rotate_180"].includes(v)) {
    return "ROTATE";
  }
  if (["cutter", "half_destroyer", "splitter"].includes(v)) {
    return "CUT";
  }
  if (["painter", "color_mixer"].includes(v)) {
    return "COLOR";
  }
  return "FLOW";
}
