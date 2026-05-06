import { getOperationInputArity } from "../Operation/arity";
import { dataRecordFromUnknown } from "./utils";

export type WireCarrier = "material" | "fluid";

export function nodeDataIsFluidCarrier(data: unknown): boolean {
  return dataRecordFromUnknown(data).source_carrier === "fluid";
}

export function requiredInputCountForCarrier(
  opKey: string,
  paintColor: string | undefined,
  crystalColor?: string,
): number {
  const k = opKey.trim();
  if (k === "painter" && String(paintColor ?? "").trim()) {
    return 1;
  }
  if (k === "crystal_generator" && String(crystalColor ?? "").trim()) {
    return 1;
  }
  return getOperationInputArity(k);
}

/**
 * Port carrier order must match ``recipe_graph_input_carrier.expected_input_carriers`` (Python).
 * Exported for fixture-driven alignment tests (`tests/recipeConnection.fixture.test.ts`).
 */
export function expectedInputCarriers(
  opKey: string,
  paintColor: string | undefined,
  crystalColor?: string,
): WireCarrier[] {
  const k = opKey.trim();
  if (k === "painter") {
    if (String(paintColor ?? "").trim()) {
      return ["material", "material"];
    }
    return ["fluid", "material"];
  }
  if (k === "color_mixer") {
    return ["fluid", "fluid"];
  }
  if (k === "crystal_generator") {
    if (String(crystalColor ?? "").trim()) {
      return ["material", "material"];
    }
    return ["fluid", "material"];
  }
  if (k === "swapper" || k === "stacker" || k === "merge") {
    return ["material", "material"];
  }
  return ["material", "material"];
}

export function outputLaneFromSourceHandle(sh: string | null | undefined): number {
  if (typeof sh === "string") {
    const m = /^out-(\d+)$/.exec(sh);
    if (m) {
      return Number.parseInt(m[1], 10);
    }
  }
  return 0;
}

export function expectedOutputCarrier(opKey: string, lane: number): WireCarrier {
  if (opKey.trim() === "color_mixer" && lane === 0) {
    return "fluid";
  }
  return "material";
}
