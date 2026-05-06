/** Pure helpers for reading/writing scalar-ish fields on node `data`. */

export function coerceRecord(data: unknown): Record<string, unknown> {
  return data && typeof data === "object" && !Array.isArray(data)
    ? { ...(data as Record<string, unknown>) }
    : {};
}

/** Avoid `[object Object]` when node fields are accidentally non-scalars. */
export function scalarToUiString(value: unknown, fallback = ""): string {
  if (value === null || value === undefined) {
    return fallback;
  }
  if (typeof value === "string") {
    return value;
  }
  if (typeof value === "number" || typeof value === "boolean" || typeof value === "bigint") {
    return String(value);
  }
  return fallback;
}

export function scalarQuantityToUiString(value: unknown, fallback: number): string {
  if (typeof value === "number" && Number.isFinite(value)) {
    return String(value);
  }
  if (typeof value === "string") {
    return value;
  }
  return String(fallback);
}

export function previewSceneFromBase(base: Record<string, unknown>): Record<string, unknown> | undefined {
  const v = base.preview_scene;
  if (v !== null && typeof v === "object" && !Array.isArray(v)) {
    return v as Record<string, unknown>;
  }
  return undefined;
}

export function paintOrCrystalToUiString(base: Record<string, unknown>): string {
  const chosen = base.paint_color ?? base.crystal_color;
  return scalarToUiString(chosen, "");
}
