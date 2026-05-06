import { ru } from "../EditorFoundation/recipeUiStrings";
import { scalarToUiString } from "./scalars";

export function modalHeadingForType(nodeType: string | undefined): string {
  if (nodeType === "operation") {
    return ru("modalHeadingOperation");
  }
  if (nodeType === "output") {
    return ru("modalHeadingOutput");
  }
  if (nodeType === "intermediate") {
    return ru("modalHeadingIntermediate");
  }
  return ru("modalHeadingSource");
}

export function roleLabelFromBase(base: Record<string, unknown>, nodeType: string | undefined): string {
  if (typeof base.role === "string") {
    return base.role;
  }
  if (nodeType === "output") {
    return "target";
  }
  if (nodeType === "shape") {
    return "source";
  }
  return "—";
}

export function shapeHintFromBase(nodeType: string | undefined, base: Record<string, unknown>): string {
  const codeStr = scalarToUiString(base.shape_code, "");
  const empty = !codeStr.trim();
  if (nodeType === "intermediate" && empty) {
    return ru("kindSummaryMidEmpty");
  }
  if (nodeType === "output" && empty) {
    return ru("kindSummaryTargetEmpty");
  }
  return "";
}
