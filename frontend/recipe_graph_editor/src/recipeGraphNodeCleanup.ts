import type { Edge, Node } from "@xyflow/react";

function edgeDomainKind(e: Edge): string | undefined {
  const d = e.data;
  if (d && typeof d === "object" && "domainKind" in d) {
    return String((d as { domainKind?: string }).domainKind);
  }
  return undefined;
}

/**
 * 노드 삭제(`applyNodeChanges`로 반영된 직후 그래프) 뒤에 정리한다.
 *
 * - 삭제된 노드에 닿던 엣지는 제거한다.
 * - **연산** 노드가 제거되면, 그 연산의 `domainKind: "output"` 대상이던
 *   **intermediate** 스테이징 노드도 함께 제거한다(`ensureOperationOutputArtifacts` 대칭).
 */
export function cleanupAfterNodeRemovals(
  prevNodes: Node[],
  afterExplicitRemove: Node[],
  edges: Edge[],
): { nodes: Node[]; edges: Edge[] } {
  const explicitlyRemovedIds = new Set(
    prevNodes.filter((n) => !afterExplicitRemove.some((m) => m.id === n.id)).map((n) => n.id),
  );
  if (explicitlyRemovedIds.size === 0) {
    return { nodes: afterExplicitRemove, edges };
  }

  const stagingIntermediateIds = new Set<string>();
  for (const rid of explicitlyRemovedIds) {
    const n = prevNodes.find((x) => x.id === rid);
    if (n?.type !== "operation") {
      continue;
    }
    for (const e of edges) {
      if (e.source === rid && edgeDomainKind(e) === "output") {
        const target = prevNodes.find((x) => x.id === e.target);
        if (target?.type === "intermediate") {
          stagingIntermediateIds.add(e.target);
        }
      }
    }
  }

  const allRemovedNodeIds = new Set<string>([...explicitlyRemovedIds, ...stagingIntermediateIds]);
  const nextNodes = afterExplicitRemove.filter((n) => !stagingIntermediateIds.has(n.id));
  const nextEdges = edges.filter(
    (e) => !allRemovedNodeIds.has(e.source) && !allRemovedNodeIds.has(e.target),
  );

  return { nodes: nextNodes, edges: nextEdges };
}
