import type { Edge } from "@xyflow/react";

export function dataRecordFromUnknown(raw: unknown): Record<string, unknown> {
  if (raw && typeof raw === "object" && !Array.isArray(raw)) {
    return raw as Record<string, unknown>;
  }
  return {};
}

export function operationKeyTrimmed(data: unknown): string {
  const d = dataRecordFromUnknown(data);
  const op = d.operation;
  return typeof op === "string" ? op.trim() : "";
}

export function paintAndCrystalFromOpData(data: unknown): {
  paint: string | undefined;
  crystal: string | undefined;
} {
  const opData = dataRecordFromUnknown(data);
  return {
    paint: typeof opData.paint_color === "string" ? opData.paint_color : undefined,
    crystal:
      typeof opData.crystal_color === "string" ? opData.crystal_color : undefined,
  };
}

export function edgeDomainKind(e: Edge): string | undefined {
  const d = e.data;
  if (d && typeof d === "object" && "domainKind" in d) {
    return String((d as { domainKind?: string }).domainKind);
  }
  return undefined;
}
