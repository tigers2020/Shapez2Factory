import type { GraphInput, LayoutNode } from "./types";
import { compareNumbers } from "./graphLayoutMath";

export function getGraphNodes(graph: GraphInput): LayoutNode[] {
  return Array.isArray(graph?.nodes) ? graph.nodes : [];
}

export function getGraphEdges(graph: GraphInput) {
  return Array.isArray(graph?.edges) ? graph.edges : [];
}

export function buildNodeIndexMap(nodes: LayoutNode[]): Map<string, number> {
  return new Map(nodes.map((node, index) => [node.id, index]));
}

export function computeNodeDepths(graph: GraphInput): Map<string, number> {
  const nodes = getGraphNodes(graph);
  const edges = getGraphEdges(graph);
  const nodeIds = new Set(nodes.map((node) => node.id));
  const depths = new Map(nodes.map((node) => [node.id, 0]));

  let remainingPasses = nodes.length;
  while (remainingPasses > 0) {
    remainingPasses -= 1;
    let changed = false;
    for (const edge of edges) {
      if (!nodeIds.has(edge.from) || !nodeIds.has(edge.to)) {
        continue;
      }
      const nextDepth = (depths.get(edge.from) || 0) + 1;
      if (nextDepth > (depths.get(edge.to) || 0)) {
        depths.set(edge.to, nextDepth);
        changed = true;
      }
    }
    if (!changed) {
      break;
    }
  }

  return depths;
}

export function groupNodeIdsByDepth(
  graph: GraphInput,
  depths: Map<string, number>,
): Map<number, string[]> {
  const columns = new Map<number, string[]>();
  for (const node of getGraphNodes(graph)) {
    const depth = depths.get(node.id) || 0;
    const column = columns.get(depth) || [];
    column.push(node.id);
    columns.set(depth, column);
  }

  return new Map([...columns.entries()].sort((a, b) => compareNumbers(a[0], b[0])));
}
