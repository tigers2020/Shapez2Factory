import type { Connection, Edge, Node } from "@xyflow/react";

import {
  outputLaneFromSourceHandle,
  requiredInputCountForCarrier,
} from "./carriers";
import { evaluateRecipeConnection } from "./evaluate";
import {
  isIntermediateToOutputConnection,
  isMaterialToOperationConnection,
} from "./predicates";
import { edgeDomainKind, operationKeyTrimmed, paintAndCrystalFromOpData } from "./utils";

function addLastEdgeIdIfPresent(ids: Set<string>, list: Edge[]): void {
  const last = list.at(-1);
  if (last) {
    ids.add(last.id);
  }
}

function collectMaterialToOperationRemovalIds(
  ids: Set<string>,
  nodes: Node[],
  edges: Edge[],
  c: Connection,
  tn: Node,
): void {
  if (!isMaterialToOperationConnection(nodes, c)) {
    return;
  }
  const incoming = edges.filter((e) => e.target === c.target && edgeDomainKind(e) === "input");
  const th = c.targetHandle ?? "in";
  const samePort = incoming.filter((e) => (e.targetHandle ?? "in") === th);
  if (samePort.length > 0) {
    addLastEdgeIdIfPresent(ids, samePort);
    return;
  }
  const opKey = operationKeyTrimmed(tn.data);
  const { paint, crystal } = paintAndCrystalFromOpData(tn.data);
  const need = requiredInputCountForCarrier(opKey, paint, crystal);
  if (incoming.length >= need) {
    addLastEdgeIdIfPresent(ids, incoming);
  }
}

/**
 * 새 연결 ``c``를 넣기 전에 제거할 기존 엣지 id 목록(마지막 충돌 연결 우선).
 * ``isValidConnection`` / ``onConnect``에서 교체 연결을 허용할 때 사용한다.
 */
export function getRecipeConnectEdgeRemovals(
  nodes: Node[],
  edges: Edge[],
  c: Connection,
): string[] {
  if (!c.source || !c.target || c.source === c.target) {
    return [];
  }
  const sn = nodes.find((n) => n.id === c.source);
  const tn = nodes.find((n) => n.id === c.target);
  if (!sn || !tn) {
    return [];
  }
  const st = sn.type;
  if (st === "output") {
    return [];
  }

  const ids = new Set<string>();

  for (const e of edges) {
    if (e.source === c.source && e.target === c.target) {
      ids.add(e.id);
    }
  }

  if (isIntermediateToOutputConnection(nodes, c)) {
    for (const e of edges) {
      if (e.target === c.target && edgeDomainKind(e) === "delivery") {
        ids.add(e.id);
      }
    }
  }

  collectMaterialToOperationRemovalIds(ids, nodes, edges, c, tn);

  return [...ids];
}

export function wouldConnectAfterRemovals(
  nodes: Node[],
  edges: Edge[],
  c: Connection,
): boolean {
  const remove = new Set(getRecipeConnectEdgeRemovals(nodes, edges, c));
  const filtered = edges.filter((e) => !remove.has(e.id));
  return evaluateRecipeConnection(nodes, filtered, c).ok;
}

function connectionDomainKind(sn: Node, tn: Node): "delivery" | "input" | "output" {
  if (sn.type === "intermediate" && tn.type === "output") {
    return "delivery";
  }
  if (sn.type === "shape" || sn.type === "intermediate") {
    return "input";
  }
  return "output";
}

export function connectionToRecipeEdge(c: Connection, nodes: Node[]): Edge {
  const sn = nodes.find((n) => n.id === c.source);
  const tn = nodes.find((n) => n.id === c.target);
  if (!sn?.type || !tn?.type) {
    throw new Error("connectionToRecipeEdge: missing source or target node");
  }
  const domainKind = connectionDomainKind(sn, tn);
  const th = c.targetHandle ?? "";
  const slotPart =
    domainKind === "input" && typeof th === "string" && th.startsWith("in-") && th.length > 3
      ? th.slice(3)
      : "";
  const data: Record<string, unknown> = { domainKind };
  if (domainKind === "input" && slotPart && /^\d+$/.test(slotPart) && Number(slotPart) >= 1) {
    data.slot = slotPart;
  }
  if (domainKind === "output") {
    const sh = typeof c.sourceHandle === "string" ? c.sourceHandle : "out";
    data.slot = String(outputLaneFromSourceHandle(sh));
  }
  const handleKey = `${c.sourceHandle ?? ""}_${c.targetHandle ?? ""}`;
  const eid = `e-${c.source}-${c.target}-${domainKind}-${handleKey}`;
  return {
    id: eid,
    source: c.source,
    target: c.target,
    sourceHandle: c.sourceHandle ?? undefined,
    targetHandle: c.targetHandle ?? undefined,
    type: "recipe",
    data,
  };
}
