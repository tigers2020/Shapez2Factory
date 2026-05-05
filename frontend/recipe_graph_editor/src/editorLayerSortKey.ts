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

/** Lower key = higher on canvas (preferred reading order for recipe editor auto-arrange). */
export function editorLayerSortKey(node: Node, allNodes: Node[], edges: Edge[]): number {
  const t = node.type ?? "";
  const d = (node.data ?? {}) as Record<string, unknown>;

  if (t === "shape") {
    if (nodeDataIsFluidCarrier(d)) {
      return RANK_LOWER_BRANCH;
    }
    let rank = RANK_NEUTRAL;
    for (const e of edges) {
      if (e.source !== node.id) {
        continue;
      }
      const tgt = allNodes.find((n) => n.id === e.target);
      if (!tgt || tgt.type !== "operation") {
        continue;
      }
      const opData = tgt.data as Record<string, unknown>;
      const op = String(opData.operation ?? "").trim();
      const th = (e.targetHandle ?? "in") as string;

      if (op === "stacker" || op === "swapper") {
        if (th === "in" || th === "") {
          rank = Math.min(rank, RANK_STACKER_UPPER);
        } else if (th === "in-1") {
          rank = Math.min(rank, RANK_LOWER_BRANCH);
        }
      }

      if (op === "painter" || op === "crystal_generator") {
        const twoWire = getEffectiveOperationInputArity(op, opData) >= 2;
        if (twoWire) {
          rank = Math.min(
            rank,
            nodeDataIsFluidCarrier(d) ? RANK_LOWER_BRANCH : RANK_PAINTER_MATERIAL,
          );
        }
      }
    }
    return rank;
  }

  if (t === "intermediate") {
    let best = RANK_NEUTRAL;
    for (const e of edges) {
      if (e.source !== node.id) {
        continue;
      }
      const tgt = allNodes.find((n) => n.id === e.target);
      if (!tgt || tgt.type !== "operation") {
        continue;
      }
      const opData = tgt.data as Record<string, unknown>;
      const op = String(opData.operation ?? "").trim();
      const th = (e.targetHandle ?? "in") as string;

      if (op === "stacker" || op === "swapper") {
        if (th === "in" || th === "") {
          best = Math.min(best, RANK_STACKER_UPPER);
        } else if (th === "in-1") {
          best = Math.min(best, RANK_LOWER_BRANCH);
        }
      }

      if (op === "painter" || op === "crystal_generator") {
        const twoWire = getEffectiveOperationInputArity(op, opData) >= 2;
        if (twoWire) {
          best = Math.min(
            best,
            nodeDataIsFluidCarrier(d) ? RANK_LOWER_BRANCH : RANK_PAINTER_MATERIAL,
          );
        }
      }
    }
    return best;
  }

  return 200;
}
