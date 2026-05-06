import type { Connection, Edge, Node } from "@xyflow/react";

import {
  expectedInputCarriers,
  expectedOutputCarrier,
  nodeDataIsFluidCarrier,
  outputLaneFromSourceHandle,
  requiredInputCountForCarrier,
  type WireCarrier,
} from "./carriers";
import {
  pendingInputEdgeFromConnection,
  sortedInputEdgesToOperation,
} from "./inputSort";
import { normalizeMaterialToPainterConnection } from "./painter";
import {
  edgeToConnection,
  isIntermediateToOutputConnection,
  isMaterialToOperationConnection,
  isOperationMaterialOutputSourceHandle,
} from "./predicates";
import { edgeDomainKind, operationKeyTrimmed, paintAndCrystalFromOpData } from "./utils";

type RecipeConnResult = { ok: true } | { ok: false; message: string };

function recipeDuplicateLink(edges: Edge[], c: Connection): RecipeConnResult | undefined {
  if (edges.some((e) => e.source === c.source && e.target === c.target)) {
    return { ok: false, message: "That link already exists." };
  }
  return undefined;
}

function recipeEvaluateDelivery(
  nodes: Node[],
  edges: Edge[],
  c: Connection,
): RecipeConnResult | undefined {
  if (!isIntermediateToOutputConnection(nodes, c)) {
    return undefined;
  }
  const deliveriesToTarget = edges.filter(
    (e) => e.target === c.target && edgeDomainKind(e) === "delivery",
  );
  if (
    deliveriesToTarget.length >= 1 &&
    !deliveriesToTarget.some((e) => e.source === c.source)
  ) {
    return {
      ok: false,
      message: "This output already has a delivery link.",
    };
  }
  return { ok: true };
}

type MaterialCarrierCheckContext = {
  nodes: Node[];
  c: Connection;
  sn: Node;
  opKey: string;
  paint: string | undefined;
  crystal: string | undefined;
  need: number;
  incoming: Edge[];
  th: string;
};

function resolveMaterialInputWantCarrier(
  ctx: MaterialCarrierCheckContext,
  expected: WireCarrier[],
): { want: WireCarrier | undefined; twoWireFluidShape: boolean } {
  const k = ctx.opKey.trim();
  const twoWireFluidShape =
    (k === "painter" && !String(ctx.paint ?? "").trim() && expected.length === 2) ||
    (k === "crystal_generator" && !String(ctx.crystal ?? "").trim() && expected.length === 2);
  if (twoWireFluidShape) {
    return { want: ctx.th === "in-1" ? "fluid" : "material", twoWireFluidShape };
  }
  const pending = pendingInputEdgeFromConnection(ctx.c);
  const sorted = sortedInputEdgesToOperation(
    [...ctx.incoming, pending],
    ctx.nodes,
    ctx.c.target,
  );
  const idx = sorted.findIndex((e) => e.id === "__pending__");
  const want = idx >= 0 && idx < expected.length ? expected[idx] : undefined;
  return { want, twoWireFluidShape };
}

function materialCarrierMismatchMessage(
  opKey: string,
  th: string,
  want: WireCarrier,
  twoWireFluidShape: boolean,
): RecipeConnResult {
  const k = opKey.trim();
  if (!twoWireFluidShape) {
    return {
      ok: false,
      message: `This wire must be ${want} (operation ${opKey} handle ${th}).`,
    };
  }
  const here =
    th === "in-1"
      ? `port 1 (upper handle in-1) — fluid only`
      : `port 0 (lower handle in) — shape (material) only`;
  const opHint = k === "painter" ? "Painter" : "Crystal generator (same ports as painter)";
  return {
    ok: false,
    message: `This wire must be ${want} on ${here}. ${opHint}: shape on in (lower) · fluid on in-1 (upper).`,
  };
}

function materialOpCarrierMismatch(ctx: MaterialCarrierCheckContext): RecipeConnResult | undefined {
  const expected = expectedInputCarriers(ctx.opKey, ctx.paint, ctx.crystal);
  if (ctx.need <= 0 || expected.length <= 0) {
    return undefined;
  }
  const { want, twoWireFluidShape } = resolveMaterialInputWantCarrier(ctx, expected);
  if (want === undefined) {
    return undefined;
  }
  const got: WireCarrier = nodeDataIsFluidCarrier(ctx.sn.data) ? "fluid" : "material";
  if (got === want) {
    return undefined;
  }
  return materialCarrierMismatchMessage(ctx.opKey, ctx.th, want, twoWireFluidShape);
}

function recipeEvaluateMaterialToOperation(
  nodes: Node[],
  edges: Edge[],
  c: Connection,
  sn: Node,
  tn: Node,
): RecipeConnResult | undefined {
  if (!isMaterialToOperationConnection(nodes, c)) {
    return undefined;
  }
  const opKey = operationKeyTrimmed(tn.data);
  const { paint, crystal } = paintAndCrystalFromOpData(tn.data);
  const need = requiredInputCountForCarrier(opKey, paint, crystal);
  const incoming = edges.filter((e) => e.target === c.target && edgeDomainKind(e) === "input");
  if (incoming.length >= need) {
    return { ok: false, message: "This operation already has all required inputs." };
  }
  const th = c.targetHandle ?? "in";
  if (incoming.some((e) => (e.targetHandle ?? "in") === th)) {
    return { ok: false, message: "That operation input port is already used." };
  }
  const carrier = materialOpCarrierMismatch({
    nodes,
    c,
    sn,
    opKey,
    paint,
    crystal,
    need,
    incoming,
    th,
  });
  if (carrier) {
    return carrier;
  }
  return { ok: true };
}

function recipeEvaluateOpToIntermediate(
  c: Connection,
  sn: Node,
  tn: Node,
  st: string | undefined,
  tt: string | undefined,
): RecipeConnResult | undefined {
  const opToIntermediate =
    st === "operation" &&
    tt === "intermediate" &&
    isOperationMaterialOutputSourceHandle(c.sourceHandle) &&
    (c.targetHandle === "in" || c.targetHandle == null);
  if (!opToIntermediate) {
    return undefined;
  }
  const opKey = operationKeyTrimmed(sn.data);
  const lane = outputLaneFromSourceHandle(c.sourceHandle);
  const want = expectedOutputCarrier(opKey, lane);
  const got: WireCarrier = nodeDataIsFluidCarrier(tn.data) ? "fluid" : "material";
  if (want !== got) {
    return {
      ok: false,
      message: `Operation output is ${want}; intermediate node must match (got ${got}).`,
    };
  }
  return { ok: true };
}

export function evaluateRecipeConnection(
  nodes: Node[],
  edges: Edge[],
  cIn: Connection,
): RecipeConnResult {
  if (!cIn.source || !cIn.target) {
    return { ok: false, message: "Incomplete connection." };
  }
  if (cIn.source === cIn.target) {
    return { ok: false, message: "Cannot connect a node to itself." };
  }

  const sn = nodes.find((n) => n.id === cIn.source);
  const tn = nodes.find((n) => n.id === cIn.target);
  if (!sn || !tn) {
    return { ok: false, message: "Unknown node." };
  }

  const c = normalizeMaterialToPainterConnection(nodes, {
    source: cIn.source,
    target: cIn.target,
    sourceHandle: cIn.sourceHandle ?? null,
    targetHandle: cIn.targetHandle ?? null,
  });

  const st = sn.type;
  const tt = tn.type;

  const dup = recipeDuplicateLink(edges, c);
  if (dup) {
    return dup;
  }

  const delivery = recipeEvaluateDelivery(nodes, edges, c);
  if (delivery !== undefined) {
    return delivery;
  }

  if (st === "output") {
    return { ok: false, message: "Output nodes have no outgoing wires." };
  }

  if (tt === "output") {
    return {
      ok: false,
      message: "Only intermediate shapes may connect to an output terminal.",
    };
  }

  const material = recipeEvaluateMaterialToOperation(nodes, edges, c, sn, tn);
  if (material !== undefined) {
    return material;
  }

  const opToMid = recipeEvaluateOpToIntermediate(c, sn, tn, st, tt);
  if (opToMid !== undefined) {
    return opToMid;
  }

  if (st === "operation" && tt === "shape") {
    return { ok: false, message: "Operations cannot wire into source material nodes." };
  }

  if (st === "operation" && tt === "operation") {
    return { ok: false, message: "Operation-to-operation links are not allowed." };
  }

  if ((st === "shape" || st === "intermediate") && (tt === "shape" || tt === "intermediate")) {
    return { ok: false, message: "Shape-to-shape links are not allowed." };
  }

  return { ok: false, message: "Not a valid recipe wire (see staff graph rules)." };
}

/** Drop edges that are no longer valid after node data (e.g. carrier) changes. */
export function filterStaleRecipeEdges(nodes: Node[], edges: Edge[]): Edge[] {
  return edges.filter((e) => {
    const c = edgeToConnection(e);
    if (!c) {
      return false;
    }
    const rest = edges.filter((x) => x.id !== e.id);
    return evaluateRecipeConnection(nodes, rest, c).ok;
  });
}
