import type { Connection, Edge, Node } from "@xyflow/react";

import { dataRecordFromUnknown, edgeDomainKind } from "./utils";

function inputSlotKeyFromTargetHandle(th: string | null | undefined): string {
  if (typeof th === "string" && th.startsWith("in-") && th.length > 3) {
    const suf = th.slice(3);
    if (/^\d+$/.test(suf) && Number.parseInt(suf, 10) >= 1) {
      return suf;
    }
  }
  return "";
}

function pendingInputEdgeFromConnection(c: Connection): Edge {
  const slot = inputSlotKeyFromTargetHandle(c.targetHandle);
  const data: Record<string, unknown> = { domainKind: "input" };
  if (slot) {
    data.slot = slot;
  }
  return {
    id: "__pending__",
    source: c.source,
    target: c.target,
    sourceHandle: c.sourceHandle ?? undefined,
    targetHandle: c.targetHandle ?? undefined,
    type: "recipe",
    data,
  };
}

function inputEdgeSortKey(e: Edge): [boolean, string, string] {
  const d = dataRecordFromUnknown(e.data);
  const slotKey = typeof d.slot === "string" && d.slot.trim() ? d.slot.trim() : "";
  const hasSlot = Boolean(slotKey);
  return [!hasSlot, slotKey, e.source];
}

/** Exported for fixture-driven alignment tests (`tests/recipeConnection.fixture.test.ts`). */
export function sortedInputEdgesToOperation(edges: Edge[], nodes: Node[], opId: string): Edge[] {
  const list = edges.filter((e) => e.target === opId && edgeDomainKind(e) === "input");
  const rows = list
    .map((e) => ({ e, k: inputEdgeSortKey(e) }))
    .filter((row) => {
      const sn = nodes.find((n) => n.id === row.e.source);
      return Boolean(sn && (sn.type === "shape" || sn.type === "intermediate"));
    })
    .sort((a, b) => {
      if (a.k[0] !== b.k[0]) {
        return (a.k[0] ? 1 : 0) - (b.k[0] ? 1 : 0);
      }
      if (a.k[1] !== b.k[1]) {
        return a.k[1].localeCompare(b.k[1]);
      }
      return a.k[2].localeCompare(b.k[2]);
    });
  return rows.map((r) => r.e);
}

export { pendingInputEdgeFromConnection };
