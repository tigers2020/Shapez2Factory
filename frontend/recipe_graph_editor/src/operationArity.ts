/** Mirrors ``recipe_graph_recompute.recompute_graph_document`` input counts (unary vs binary). */

/** Mirrors ``recipe_graph_recompute`` / catalog output lanes. */
const OUTPUT_2 = new Set(["cutter", "cutter_full", "splitter", "swapper"]);

export function getOperationOutputCount(operation: string): number {
  const op = operation.trim();
  if (!op) {
    return 1;
  }
  return OUTPUT_2.has(op) ? 2 : 1;
}

const ARITY_2 = new Set(["swapper", "stacker", "color_mixer"]);

export function getOperationInputArity(operation: string): number {
  const op = operation.trim();
  if (!op) {
    return 1;
  }
  return ARITY_2.has(op) ? 2 : 1;
}
