export function unknownScalarToString(value: unknown, fallback: string): string {
  if (typeof value === "string" || typeof value === "number" || typeof value === "boolean") {
    return String(value);
  }
  return fallback;
}

export function shallowRecordFromUnknown(value: unknown): Record<string, unknown> {
  if (value === null || typeof value !== "object" || Array.isArray(value)) {
    return {};
  }
  return { ...value };
}

export function mergeNodeDataWithPatch(
  prev: Record<string, unknown>,
  patch: Record<string, unknown>,
  iconByOperation: Map<string, string>,
): Record<string, unknown> {
  const next = { ...prev, ...patch };
  if ("paint_color" in patch && patch.paint_color === undefined) {
    delete next.paint_color;
  }
  if ("crystal_color" in patch && patch.crystal_color === undefined) {
    delete next.crystal_color;
  }
  if ("source_carrier" in patch && patch.source_carrier === undefined) {
    delete next.source_carrier;
  }
  if ("operation" in patch) {
    const op = unknownScalarToString(patch.operation, "").trim();
    const ic = iconByOperation.get(op);
    if (ic) {
      next.icon = ic;
    } else {
      delete next.icon;
    }
  }
  if (
    "shape_code" in patch ||
    "operation" in patch ||
    "paint_color" in patch ||
    "crystal_color" in patch ||
    "source_carrier" in patch
  ) {
    delete next.preview_image_url;
    delete next.preview_alt;
    delete next.preview_scene;
  }
  return next;
}
