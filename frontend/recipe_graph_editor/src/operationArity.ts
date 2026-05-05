/** Mirrors ``recipe_graph_recompute.recompute_graph_document`` input counts (unary vs binary). */

/** Mirrors ``recipe_graph_recompute`` / catalog output lanes. */
const OUTPUT_2 = new Set(["cutter", "splitter", "swapper"]);

export function getOperationOutputCount(operation: string): number {
  const op = operation.trim();
  if (!op) {
    return 1;
  }
  return OUTPUT_2.has(op) ? 2 : 1;
}

const ARITY_2 = new Set(["swapper", "stacker", "color_mixer", "crystal_generator", "painter"]);

/** Max input handles when node ``data`` is unknown (e.g. connection rules default). */
export function getOperationInputArity(operation: string): number {
  const op = operation.trim();
  if (!op) {
    return 1;
  }
  return ARITY_2.has(op) ? 2 : 1;
}

/**
 * Painter / crystal_generator: 1 wire when preset color on the node, else 2 (fluid + shape).
 * Must stay aligned with ``recipe_graph_input_carrier.required_input_count`` (Python).
 */
export function getEffectiveOperationInputArity(
  operation: string,
  data: Record<string, unknown> | null | undefined,
): number {
  const op = operation.trim();
  if (!op) {
    return 1;
  }
  const d = data && typeof data === "object" && !Array.isArray(data) ? data : {};
  if (op === "painter") {
    return String(d.paint_color ?? "").trim() ? 1 : 2;
  }
  if (op === "crystal_generator") {
    return String(d.crystal_color ?? "").trim() ? 1 : 2;
  }
  return ARITY_2.has(op) ? 2 : 1;
}
