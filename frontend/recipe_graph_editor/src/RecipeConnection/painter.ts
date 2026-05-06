import type { Connection, Edge, Node } from "@xyflow/react";

import {
  nodeDataIsFluidCarrier,
  requiredInputCountForCarrier,
} from "./carriers";
import { isMaterialToOperationConnection } from "./predicates";
import {
  dataRecordFromUnknown,
  edgeDomainKind,
  operationKeyTrimmed,
  paintAndCrystalFromOpData,
} from "./utils";

/**
 * XYFlow often snaps to the geometrically nearest handle; painter / crystal_generator 2-wire
 * still expects fluid on ``in-1`` and shape on ``in``. Derive the target handle from the source
 * wire carrier.
 */
export function normalizeMaterialToPainterConnection(nodes: Node[], c: Connection): Connection {
  if (!c.source || !c.target || !isMaterialToOperationConnection(nodes, c)) {
    return c;
  }
  const tn = nodes.find((n) => n.id === c.target);
  const sn = nodes.find((n) => n.id === c.source);
  if (!tn || !sn) {
    return c;
  }
  const opKey = operationKeyTrimmed(tn.data);
  if (opKey !== "painter" && opKey !== "crystal_generator") {
    return c;
  }
  const { paint, crystal } = paintAndCrystalFromOpData(tn.data);
  if (opKey === "painter" && String(paint ?? "").trim()) {
    return c;
  }
  if (opKey === "crystal_generator" && String(crystal ?? "").trim()) {
    return c;
  }
  const handle = nodeDataIsFluidCarrier(sn.data) ? "in-1" : "in";
  return { ...c, targetHandle: handle };
}

function painterTargetHandleWantOrSkip(e: Edge, tn: Node, sn: Node): "skip" | "in" | "in-1" {
  if (tn.type !== "operation") {
    return "skip";
  }
  if (sn.type !== "shape" && sn.type !== "intermediate") {
    return "skip";
  }
  const dk = edgeDomainKind(e);
  if (dk !== undefined && dk !== "input") {
    return "skip";
  }
  const opKey = operationKeyTrimmed(tn.data);
  if (opKey !== "painter" && opKey !== "crystal_generator") {
    return "skip";
  }
  const { paint, crystal } = paintAndCrystalFromOpData(tn.data);
  if (opKey === "painter" && String(paint ?? "").trim()) {
    return "skip";
  }
  if (opKey === "crystal_generator" && String(crystal ?? "").trim()) {
    return "skip";
  }
  if (requiredInputCountForCarrier(opKey, paint, crystal) < 2) {
    return "skip";
  }
  return nodeDataIsFluidCarrier(sn.data) ? "in-1" : "in";
}

function edgeWithAdjustedPainterTarget(e: Edge, want: "in" | "in-1"): Edge {
  const prev: Record<string, unknown> =
    e.data && typeof e.data === "object" && !Array.isArray(e.data)
      ? { ...dataRecordFromUnknown(e.data) }
      : { domainKind: "input" };
  if (typeof prev.domainKind !== "string") {
    prev.domainKind = "input";
  }
  if (want === "in-1") {
    prev.slot = "1";
  } else {
    delete prev.slot;
  }
  return { ...e, targetHandle: want, data: prev };
}

/**
 * RF 스냅샷에 ``targetHandle``이 빠지면 XYFlow가 첫 번째 소켓(페인터·크리스털은 ``in-1`` 상단)에 묶인다.
 * 부트스트랩·재계산 응답 직후 재료/유체에 맞게 고친다.
 */
export function ensurePainterTargetHandlesOnEdges(nodes: Node[], edges: Edge[]): Edge[] {
  return edges.map((e) => {
    const tn = nodes.find((n) => n.id === e.target);
    const sn = nodes.find((n) => n.id === e.source);
    if (!tn || !sn) {
      return e;
    }
    const want = painterTargetHandleWantOrSkip(e, tn, sn);
    if (want === "skip") {
      return e;
    }
    if (e.targetHandle === want) {
      return e;
    }
    return edgeWithAdjustedPainterTarget(e, want);
  });
}
