import { defaultQuantityForShapeNodeData } from "../EditorFoundation/constants";
import type { FluidPrimaryInk } from "../EditorFoundation/fluidSourceUi";
import { fluidShapeCodeFromInk } from "../EditorFoundation/fluidSourceUi";

export function buildOperationApplyPayload(
  operation: string,
  paintColor: string,
): Record<string, unknown> {
  const next: Record<string, unknown> = { operation: operation.trim() };
  const op = operation.trim();
  if (op === "painter") {
    const pc = paintColor.trim().slice(0, 1);
    if (pc && "rgb".includes(pc)) {
      next.paint_color = pc;
    } else {
      next.paint_color = undefined;
    }
    next.crystal_color = undefined;
  } else if (op === "crystal_generator") {
    const cc = paintColor.trim().slice(0, 1);
    if (cc) {
      next.crystal_color = cc;
    } else {
      delete next.crystal_color;
    }
    next.paint_color = undefined;
  } else {
    next.paint_color = undefined;
    next.crystal_color = undefined;
  }
  return next;
}

export type NodeEditApplyInput = {
  nodeType: string | undefined;
  base: Record<string, unknown>;
  operation: string;
  paintColor: string;
  shapeCode: string;
  quantity: string;
  carrierMode: "material" | "fluid";
  fluidInk: FluidPrimaryInk;
};

/** `null` when the node type does not apply patches (e.g. intermediate). */
export function buildNodeEditApplyPayload(input: NodeEditApplyInput): Record<string, unknown> | null {
  const t = input.nodeType ?? "";
  if (t === "intermediate") {
    return null;
  }
  if (t === "operation") {
    return buildOperationApplyPayload(input.operation, input.paintColor);
  }
  const q = Number.parseInt(input.quantity, 10);
  const fallbackQty =
    input.nodeType === "shape" ? defaultQuantityForShapeNodeData(input.base) : 1;
  const qty = Number.isFinite(q) && q >= 1 ? q : fallbackQty;
  if (input.nodeType === "output") {
    return {
      shape_code: input.shapeCode.trim(),
      quantity: qty,
    };
  }
  if (input.nodeType !== "shape") {
    return null;
  }
  const patch: Record<string, unknown> = { quantity: qty };
  if (input.carrierMode === "fluid") {
    patch.source_carrier = "fluid";
    if (input.nodeType === "shape" && input.base.role === "source") {
      patch.shape_code = fluidShapeCodeFromInk(input.fluidInk);
    } else {
      patch.shape_code = input.shapeCode.trim();
    }
  } else {
    patch.source_carrier = undefined;
    patch.shape_code = input.shapeCode.trim();
  }
  return patch;
}
