import type { Connection, Edge, Node } from "@xyflow/react";

export function edgeToConnection(e: Edge): Connection | null {
  if (!e.source || !e.target) {
    return null;
  }
  return {
    source: e.source,
    target: e.target,
    sourceHandle: e.sourceHandle ?? null,
    targetHandle: e.targetHandle ?? null,
  };
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
    (c.sourceHandle === "out" || c.sourceHandle == null || c.sourceHandle === "") &&
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

export function isOperationMaterialOutputSourceHandle(h: string | null | undefined): boolean {
  if (h == null || h === "") {
    return true;
  }
  if (h === "out") {
    return true;
  }
  return /^out-\d+$/.test(h);
}
