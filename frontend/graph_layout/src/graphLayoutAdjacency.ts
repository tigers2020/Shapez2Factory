import type { GraphInput } from "./types";
import { getGraphEdges } from "./graphLayoutInput";
import { edgeTargetPortRank, sourceHandleLaneOrder } from "./graphLayoutPorts";
import { compareNumbers } from "./graphLayoutMath";

export type TaggedNeighbor = { id: string; portKey: number };

export function buildAdjacency(graph: GraphInput, nodeIndexMap: Map<string, number>) {
  const predTags = new Map<string, TaggedNeighbor[]>();
  const succTags = new Map<string, TaggedNeighbor[]>();
  for (const nodeId of nodeIndexMap.keys()) {
    predTags.set(nodeId, []);
    succTags.set(nodeId, []);
  }

  for (const edge of getGraphEdges(graph)) {
    if (!nodeIndexMap.has(edge.from) || !nodeIndexMap.has(edge.to)) {
      continue;
    }
    predTags.get(edge.to)?.push({
      id: edge.from,
      portKey: edgeTargetPortRank(edge),
    });
    succTags.get(edge.from)?.push({
      id: edge.to,
      portKey: sourceHandleLaneOrder(edge.sourceHandle),
    });
  }

  const compareTagged = (left: TaggedNeighbor, right: TaggedNeighbor): number => {
    if (left.portKey !== right.portKey) {
      return compareNumbers(left.portKey, right.portKey);
    }
    return compareNumbers(nodeIndexMap.get(left.id) || 0, nodeIndexMap.get(right.id) || 0);
  };

  const predecessors = new Map<string, string[]>();
  const successors = new Map<string, string[]>();
  for (const nodeId of nodeIndexMap.keys()) {
    predecessors.set(
      nodeId,
      [...(predTags.get(nodeId) || [])].sort(compareTagged).map((t) => t.id),
    );
    successors.set(
      nodeId,
      [...(succTags.get(nodeId) || [])].sort(compareTagged).map((t) => t.id),
    );
  }

  return { predecessors, successors };
}

export type AdjacencyResult = ReturnType<typeof buildAdjacency>;
