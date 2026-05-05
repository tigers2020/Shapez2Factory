import type { Edge, Node } from "@xyflow/react";

import {
  computeGroupedGraphLayout,
  EDITOR_LAYOUT_METRICS,
  type GraphInput,
} from "../../graph_layout/src/index";
import { editorLayerSortKey } from "./editorLayerSortKey";
import { getEffectiveOperationInputArity } from "./operationArity";

/** XYFlow는 보통 node.type을 채우지만, 비어 있으면 data.operation으로 연산 노드를 구분한다. */
function editorReactFlowKind(n: Node): string {
  const raw = n.type;
  const t = typeof raw === "string" ? raw.trim() : "";
  if (t.length > 0) {
    return t;
  }
  const d = n.data;
  if (d && typeof d === "object" && !Array.isArray(d)) {
    const op = String((d as Record<string, unknown>).operation ?? "").trim();
    if (op.length > 0) {
      return "operation";
    }
  }
  return "";
}

/** Matches `recipeFlowNodes` left inputs: painter / crystal 2-wire has in-1 above in. */
function targetPortVisualRankForRecipeEdge(
  nodes: Node[],
  targetNodeId: string,
  targetHandle: string | null | undefined,
): number {
  const th = targetHandle ?? "in";
  const tgt = nodes.find((n) => n.id === targetNodeId);
  if (!tgt || tgt.type !== "operation") {
    if (th === "in") {
      return 0;
    }
    const m = /^in-(\d+)$/.exec(th);
    if (m) {
      return Number.parseInt(m[1], 10);
    }
    return 0;
  }
  const d = (tgt.data ?? {}) as Record<string, unknown>;
  const op = String(d.operation ?? "").trim();
  const inArity = getEffectiveOperationInputArity(op, d);
  const twoWireFluidUpperShapeLower =
    inArity >= 2 &&
    ((op === "painter" && !String(d.paint_color ?? "").trim()) ||
      (op === "crystal_generator" && !String(d.crystal_color ?? "").trim()));

  if (inArity < 2) {
    return 0;
  }
  if (twoWireFluidUpperShapeLower) {
    if (th === "in-1") {
      return 0;
    }
    if (th === "in" || th === "") {
      return 1;
    }
    const m = /^in-(\d+)$/.exec(th);
    if (m) {
      return Number.parseInt(m[1], 10);
    }
    return 1;
  }
  if (th === "in" || th === "") {
    return 0;
  }
  if (th === "in-1") {
    return 1;
  }
  const m = /^in-(\d+)$/.exec(th);
  if (m) {
    return Number.parseInt(m[1], 10);
  }
  return 0;
}

function reactFlowToGraph(nodes: Node[], edges: Edge[]): GraphInput {
  return {
    nodes: nodes.map((n) => ({
      id: n.id,
      initialY: n.position.y,
      layerSortKey: editorLayerSortKey(n, nodes, edges),
      reactFlowType: editorReactFlowKind(n),
    })),
    edges: edges
      .filter((e) => e.source && e.target)
      .map((e) => {
        const to = String(e.target);
        return {
          from: String(e.source),
          to,
          sourceHandle: e.sourceHandle ?? null,
          targetHandle: e.targetHandle ?? null,
          targetPortVisualRank: targetPortVisualRankForRecipeEdge(nodes, to, e.targetHandle),
        };
      }),
  };
}

/** Snap flow coordinates to whole pixels (avoids float drift from pan/zoom). */
function snapPx(x: number, y: number): { x: number; y: number } {
  return { x: Math.round(x), y: Math.round(y) };
}

/**
 * DAG 기반 자동 배치 (공통 graph_layout 엔진 + 에디터 간격 프로필).
 * 엣지가 없으면 모든 노드가 depth 0으로 같은 열에 쌓입니다.
 *
 * 자동 배치마다 이동한 노드 목록을 `console.log`(JSON 문자열)로 남긴다. 이동이 없으면 `[]`.
 * 적용 좌표는 정수 픽셀로 반올림한다(뷰포트 부동소수 제거).
 * 엔진 내부 스냅샷(`[shapez graph-layout]`)은 `isEditorGraphLayoutConsoleDebugEnabled()`일 때만.
 */
export function layoutNodesFromGraph(nodes: Node[], edges: Edge[]): Node[] {
  if (nodes.length === 0) {
    return nodes;
  }
  const moveLogs: Array<{
    id: string;
    from: { x: number; y: number };
    to: { x: number; y: number };
  }> = [];

  const graph = reactFlowToGraph(nodes, edges);
  const layout = computeGroupedGraphLayout(graph, EDITOR_LAYOUT_METRICS);
  const next = nodes.map((n) => {
    const p = layout.positions.get(n.id);
    if (!p) {
      return n;
    }
    const from = snapPx(n.position.x, n.position.y);
    const to = snapPx(p.x, p.y);
    if (from.x !== to.x || from.y !== to.y) {
      moveLogs.push({ id: n.id, from, to });
    }
    return { ...n, position: to };
  });

  const payload = JSON.stringify(moveLogs, null, 2);
  console.log(`[AutoLayout] moved nodes (${moveLogs.length}) | edges=${edges.length}\n${payload}`);
  if (moveLogs.length > 0) {
    const g = globalThis as unknown as { copy?: (text: string) => void };
    if (typeof g.copy === "function") {
      try {
        g.copy(payload);
      } catch {
        /* DevTools `copy` unavailable */
      }
    }
  }

  return next;
}
