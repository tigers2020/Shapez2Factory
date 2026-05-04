import type { Edge, Node } from "@xyflow/react";

import { getOperationOutputCount } from "./operationArity";

function edgeDomainKind(e: Edge): string | undefined {
  const d = e.data;
  if (d && typeof d === "object" && "domainKind" in d) {
    return String((d as { domainKind?: string }).domainKind);
  }
  return undefined;
}

/**
 * 연산 노드에 대해 catalog ``output_count``만큼 ``operation → intermediate`` 출력 엣지가 없으면
 * 빈 intermediate 노드와 출력 엣지를 붙인다(재계산으로 shape_code 채움).
 */
export function ensureOperationOutputArtifacts(
  nodes: Node[],
  edges: Edge[],
  opId: string,
  newGraphNodeId: (prefix: string) => string,
): { nodes: Node[]; edges: Edge[] } {
  const op = nodes.find((n) => n.id === opId && n.type === "operation");
  if (!op) {
    return { nodes, edges };
  }
  const opKey = String((op.data as { operation?: string } | undefined)?.operation ?? "");
  const want = getOperationOutputCount(opKey);
  const outgoing = edges.filter((e) => e.source === opId && edgeDomainKind(e) === "output");
  if (outgoing.length >= want) {
    return { nodes, edges };
  }

  const nextNodes = [...nodes];
  const nextEdges = [...edges];
  const bx = typeof op.position?.x === "number" ? op.position.x : 0;
  const by = typeof op.position?.y === "number" ? op.position.y : 0;
  const dx = 260;
  const dy = want > 1 ? 100 : 0;

  for (let k = outgoing.length; k < want; k++) {
    const slotIndex = k;
    const imId = newGraphNodeId("im");
    const yOff = want > 1 ? (slotIndex - (want - 1) / 2) * dy : 0;
    nextNodes.push({
      id: imId,
      type: "intermediate",
      position: { x: bx + dx, y: by + yOff },
      data: { shape_code: "", quantity: 1, role: "intermediate" },
    });
    const data: Record<string, unknown> = { domainKind: "output" };
    if (want > 1) {
      data.slot = String(slotIndex + 1);
    }
    const handleKey = "out_in";
    nextEdges.push({
      id: `e-${opId}-${imId}-output-${handleKey}`,
      source: opId,
      target: imId,
      sourceHandle: "out",
      targetHandle: "in",
      type: "recipe",
      data,
    });
  }

  return { nodes: nextNodes, edges: nextEdges };
}
