import type { FluidPrimaryInk } from "../EditorFoundation/fluidSourceUi";
import { inkFromFluidShapeCode } from "../EditorFoundation/fluidSourceUi";
import { nodeDataIsFluidCarrier } from "../RecipeConnection";
import {
  paintOrCrystalToUiString,
  scalarQuantityToUiString,
  scalarToUiString,
} from "./scalars";

export type NodeEditFormFields = {
  carrierMode: "material" | "fluid";
  shapeCode: string;
  fluidInk: FluidPrimaryInk;
  quantity: string;
  operation: string;
  paintColor: string;
};

/** Snapshot of editable modal fields derived from `node.data`. */
export function formFieldsFromNodeData(d: Record<string, unknown>): NodeEditFormFields {
  return {
    carrierMode: nodeDataIsFluidCarrier(d) ? "fluid" : "material",
    shapeCode: scalarToUiString(d.shape_code, ""),
    fluidInk: nodeDataIsFluidCarrier(d)
      ? inkFromFluidShapeCode(scalarToUiString(d.shape_code, ""))
      : "r",
    quantity: scalarQuantityToUiString(d.quantity, 1),
    operation: scalarToUiString(d.operation, ""),
    paintColor: paintOrCrystalToUiString(d),
  };
}
