import type { Connection, Edge, Node } from "@xyflow/react";

import { getOperationInputArity } from "./operationArity";

function isOperationMaterialOutputSourceHandle(h: string | null | undefined): boolean {
  if (h == null || h === "") {
    return true;
  }
  if (h === "out") {
    return true;
  }
  return /^out-\d+$/.test(h);
}

function edgeDomainKind(e: Edge): string | undefined {
  const d = e.data;
  if (d && typeof d === "object" && "domainKind" in d) {
    return String((d as { domainKind?: string }).domainKind);
  }
  return undefined;
}

export function isMaterialToOperationConnection(nodes: Node[], c: Connection): boolean {
  if (!c.source || !c.target || c.source === c.target) {
    return false;
  }
  const sn = nodes.find((n) => n.id === c.source);
  const tn = nodes.find((n) => n.id === c.target);
  if (!sn || !tn) {
    return false;
  }
  const st = sn.type;
  const tt = tn.type;
  return (
    (st === "shape" || st === "intermediate") &&
    tt === "operation" &&
    c.sourceHandle === "out" &&
    (c.targetHandle === "in" ||
      c.targetHandle == null ||
      c.targetHandle === "in-1" ||
      (typeof c.targetHandle === "string" && c.targetHandle.startsWith("in-")))
  );
}

/** intermediate(shape) → output(target) 납품 연결(RF 타입 기준). */
export function isIntermediateToOutputConnection(nodes: Node[], c: Connection): boolean {
  if (!c.source || !c.target || c.source === c.target) {
    return false;
  }
  const sn = nodes.find((n) => n.id === c.source);
  const tn = nodes.find((n) => n.id === c.target);
  if (!sn || !tn) {
    return false;
  }
  return (
    sn.type === "intermediate" &&
    tn.type === "output" &&
    (c.sourceHandle === "out" || c.sourceHandle == null) &&
    (c.targetHandle === "in" || c.targetHandle == null)
  );
}

export function evaluateRecipeConnection(
  nodes: Node[],
  edges: Edge[],
  c: Connection,
): { ok: true } | { ok: false; message: string } {
  if (!c.source || !c.target) {
    return { ok: false, message: "Incomplete connection." };
  }
  if (c.source === c.target) {
    return { ok: false, message: "Cannot connect a node to itself." };
  }

  const sn = nodes.find((n) => n.id === c.source);
  const tn = nodes.find((n) => n.id === c.target);
  if (!sn || !tn) {
    return { ok: false, message: "Unknown node." };
  }

  const st = sn.type;
  const tt = tn.type;

  const intermediateToOutput = isIntermediateToOutputConnection(nodes, c);

  if (edges.some((e) => e.source === c.source && e.target === c.target)) {
    return { ok: false, message: "That link already exists." };
  }

  if (intermediateToOutput) {
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

  if (st === "output") {
    return { ok: false, message: "Output nodes have no outgoing wires." };
  }

  if (tt === "output") {
    return {
      ok: false,
      message: "Only intermediate shapes may connect to an output terminal.",
    };
  }

  if (isMaterialToOperationConnection(nodes, c)) {
    const opKey = String((tn.data as { operation?: string } | undefined)?.operation ?? "");
    const need = getOperationInputArity(opKey);
    const incoming = edges.filter((e) => e.target === c.target && edgeDomainKind(e) === "input");
    if (incoming.length >= need) {
      return { ok: false, message: "This operation already has all required inputs." };
    }
    const th = c.targetHandle ?? "in";
    if (incoming.some((e) => (e.targetHandle ?? "in") === th)) {
      return { ok: false, message: "That operation input port is already used." };
    }
    return { ok: true };
  }

  const opToIntermediate =
    st === "operation" &&
    tt === "intermediate" &&
    isOperationMaterialOutputSourceHandle(c.sourceHandle) &&
    (c.targetHandle === "in" || c.targetHandle == null);

  if (opToIntermediate) {
    return { ok: true };
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

  if (isMaterialToOperationConnection(nodes, c)) {
    const incoming = edges.filter((e) => e.target === c.target && edgeDomainKind(e) === "input");
    const th = c.targetHandle ?? "in";
    const samePort = incoming.filter((e) => (e.targetHandle ?? "in") === th);
    if (samePort.length > 0) {
      ids.add(samePort[samePort.length - 1].id);
    } else {
      const opKey = String((tn.data as { operation?: string } | undefined)?.operation ?? "");
      const need = getOperationInputArity(opKey);
      if (incoming.length >= need) {
        ids.add(incoming[incoming.length - 1].id);
      }
    }
  }

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

export function connectionToRecipeEdge(c: Connection, nodes: Node[]): Edge {
  const sn = nodes.find((n) => n.id === c.source);
  const tn = nodes.find((n) => n.id === c.target);
  if (!sn?.type || !tn?.type) {
    throw new Error("connectionToRecipeEdge: missing source or target node");
  }
  let domainKind: "delivery" | "input" | "output";
  if (sn.type === "intermediate" && tn.type === "output") {
    domainKind = "delivery";
  } else if (sn.type === "shape" || sn.type === "intermediate") {
    domainKind = "input";
  } else {
    domainKind = "output";
  }
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
    let lane = 0;
    if (sh === "out") {
      lane = 0;
    } else {
      const m = /^out-(\d+)$/.exec(sh);
      if (m) {
        lane = Number.parseInt(m[1], 10);
      }
    }
    data.slot = String(lane);
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
