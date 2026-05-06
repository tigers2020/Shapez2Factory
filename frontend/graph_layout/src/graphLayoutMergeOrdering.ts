import type { GraphInput, LayoutNode } from "./types";
import { getGraphEdges } from "./graphLayoutInput";
import { compareNumbers } from "./graphLayoutMath";
import { edgeTargetPortRank } from "./graphLayoutPorts";

function buildMergeTargetNodeIds(graph: GraphInput): Set<string> {
  const counts = new Map<string, number>();
  for (const edge of getGraphEdges(graph)) {
    counts.set(edge.to, (counts.get(edge.to) ?? 0) + 1);
  }
  return new Set([...counts.entries()].filter(([, n]) => n >= 2).map(([id]) => id));
}

function outgoingPortRankToMergeTargets(
  nodeId: string,
  graph: GraphInput,
  mergeTargets: Set<string>,
): Map<string, number> {
  const m = new Map<string, number>();
  for (const edge of getGraphEdges(graph)) {
    if (edge.from === nodeId && mergeTargets.has(edge.to)) {
      m.set(edge.to, edgeTargetPortRank(edge));
    }
  }
  return m;
}

function editorStableInitialY(node: LayoutNode | undefined): number {
  const y = node?.initialY;
  if (y == null || !Number.isFinite(y)) {
    return Number.POSITIVE_INFINITY;
  }
  return y;
}

function compareEditorColumnOrder(
  a: string,
  b: string,
  graph: GraphInput,
  mergeTargets: Set<string>,
  meta: Map<string, LayoutNode>,
): number {
  const oa = outgoingPortRankToMergeTargets(a, graph, mergeTargets);
  const ob = outgoingPortRankToMergeTargets(b, graph, mergeTargets);
  const shared = [...oa.keys()].filter((t) => ob.has(t)).sort((x, y) => x.localeCompare(y));
  for (const t of shared) {
    const ra = oa.get(t) ?? 0;
    const rb = ob.get(t) ?? 0;
    if (ra !== rb) {
      return compareNumbers(ra, rb);
    }
  }

  const ya = editorStableInitialY(meta.get(a));
  const yb = editorStableInitialY(meta.get(b));
  if (ya !== yb) {
    return compareNumbers(ya, yb);
  }
  const ka = meta.get(a)?.layerSortKey ?? 0;
  const kb = meta.get(b)?.layerSortKey ?? 0;
  if (ka !== kb) {
    return compareNumbers(ka, kb);
  }
  return a.localeCompare(b);
}

export function orderEditorLayersBySortKey(
  groupedColumns: Map<number, string[]>,
  graph: GraphInput,
): Map<number, string[]> {
  const meta = new Map(graph.nodes.map((n) => [n.id, n]));
  const mergeTargets = buildMergeTargetNodeIds(graph);
  const out = new Map<number, string[]>();
  for (const [depth, ids] of groupedColumns) {
    const sorted = [...ids].sort((a, b) =>
      compareEditorColumnOrder(a, b, graph, mergeTargets, meta),
    );
    out.set(depth, sorted);
  }
  return out;
}
