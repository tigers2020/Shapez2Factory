import type { Edge, Node } from "@xyflow/react";

/** `django_apps.shapez_solver.services.recipe_graph_react_flow_adapter.REACT_FLOW_GRAPH_PAYLOAD_VERSION` */
export const REACT_FLOW_SNAPSHOT_VERSION = 1;

export type WireReactFlowSnapshot = {
  version: number;
  nodes: Array<{
    id: string;
    type?: string;
    position: { x: number; y: number };
    data: Record<string, unknown>;
  }>;
  edges: Array<{
    id: string;
    source: string;
    target: string;
    data: Record<string, unknown>;
  }>;
};

function nodeTypeForWire(n: Node): string {
  const t = n.type;
  if (t === "shape" || t === "operation" || t === "intermediate" || t === "output") {
    return t;
  }
  return "intermediate";
}

export function buildReactFlowSnapshot(nodes: Node[], edges: Edge[]): WireReactFlowSnapshot {
  return {
    version: REACT_FLOW_SNAPSHOT_VERSION,
    nodes: nodes.map((n) => ({
      id: n.id,
      type: nodeTypeForWire(n),
      position: {
        x: typeof n.position?.x === "number" ? n.position.x : 0,
        y: typeof n.position?.y === "number" ? n.position.y : 0,
      },
      data: n.data && typeof n.data === "object" && !Array.isArray(n.data) ? { ...n.data } : {},
    })),
    edges: edges.map((e) => ({
      id: String(e.id),
      source: e.source,
      target: e.target,
      type: e.type ?? "recipe",
      sourceHandle: typeof e.sourceHandle === "string" ? e.sourceHandle : undefined,
      targetHandle: typeof e.targetHandle === "string" ? e.targetHandle : undefined,
      data: e.data && typeof e.data === "object" && !Array.isArray(e.data) ? { ...e.data } : {},
    })),
  };
}
