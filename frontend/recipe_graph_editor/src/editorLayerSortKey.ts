import type { Edge, Node } from "@xyflow/react";

import { getEffectiveOperationInputArity } from "./operationArity";
import { nodeDataIsFluidCarrier } from "./recipeConnection";

/** Stacker/swapper upper material branch (visual top). */
const RANK_STACKER_UPPER = 0;
/** Painter material wire (below long stacker branch, above fluid). */
const RANK_PAINTER_MATERIAL = 40;
/** Fluid / lower stacker branch. */
const RANK_LOWER_BRANCH = 100;
/** Fallback when no classified edges. */
const RANK_NEUTRAL = 55;

function operationTypeString(data: unknown): string {
  if (data === null || typeof data !== "object" || Array.isArray(data)) {
    return "";
  }
  const op = (data as { operation?: unknown }).operation;
  return typeof op === "string" ? op.trim() : "";
}

function rankForStackerSwapperHandle(th: string): number | null {
  if (th === "in" || th === "") {
    return RANK_STACKER_UPPER;
  }
  if (th === "in-1") {
    return RANK_LOWER_BRANCH;
  }
  return null;
}

function candidateRankFromOperationEdge(
  e: Edge,
  tgt: Node,
  carrierData: unknown,
): number | null {
  const op = operationTypeString(tgt.data);
  const th = e.targetHandle ?? "in";

  if (op === "stacker" || op === "swapper") {
    return rankForStackerSwapperHandle(th);
  }

  if (op === "painter" || op === "crystal_generator") {
    const twoWire = getEffectiveOperationInputArity(op, tgt.data) >= 2;
    if (!twoWire) {
      return null;
    }
    return nodeDataIsFluidCarrier(carrierData) ? RANK_LOWER_BRANCH : RANK_PAINTER_MATERIAL;
  }

  return null;
}

function minRankFromOutgoingOperationEdges(
  node: Node,
  allNodes: Node[],
  edges: Edge[],
  carrierData: unknown,
  initial: number,
): number {
  let rank = initial;
  for (const e of edges) {
    if (e.source !== node.id) {
      continue;
    }
    const tgt = allNodes.find((n) => n.id === e.target);
    if (tgt?.type !== "operation") {
      continue;
    }
    const cand = candidateRankFromOperationEdge(e, tgt, carrierData);
    if (cand !== null) {
      rank = Math.min(rank, cand);
    }
  }
  return rank;
}

/** Lower key = higher on canvas (preferred reading order for recipe editor auto-arrange). */
export function editorLayerSortKey(node: Node, allNodes: Node[], edges: Edge[]): number {
  const t = node.type ?? "";
  const d = node.data ?? {};

  if (t === "shape") {
    if (nodeDataIsFluidCarrier(d)) {
      return RANK_LOWER_BRANCH;
    }
    return minRankFromOutgoingOperationEdges(node, allNodes, edges, d, RANK_NEUTRAL);
  }

  if (t === "intermediate") {
    return minRankFromOutgoingOperationEdges(node, allNodes, edges, d, RANK_NEUTRAL);
  }

  return 200;
}
