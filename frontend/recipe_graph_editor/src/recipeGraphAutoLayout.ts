import type { Node } from "@xyflow/react";

const COL_WIDTH = 280;
const ROW_HEIGHT = 112;
const PAD_X = 40;
const PAD_Y = 44;

function columnForNode(n: Node): 0 | 1 | 2 | 3 {
  const t = n.type ?? "";
  if (t === "shape") {
    return 0;
  }
  if (t === "operation") {
    return 1;
  }
  if (t === "intermediate") {
    return 2;
  }
  if (t === "output") {
    return 3;
  }
  return 1;
}

function stackSortKey(n: Node): number {
  const p = n.position ?? { x: 0, y: 0 };
  const y = typeof p.y === "number" ? p.y : 0;
  const x = typeof p.x === "number" ? p.x : 0;
  return y * 10_000 + x;
}

/**
 * 1차 자동 배치: 소스 → 연산 → intermediate → 출력 순 좌→우 컬럼, 열 내에서는 기존 y·x 순으로 스택.
 */
export function layoutNodesInColumns(nodes: Node[]): Node[] {
  if (nodes.length === 0) {
    return nodes;
  }
  const buckets: Node[][] = [[], [], [], []];
  for (const n of nodes) {
    buckets[columnForNode(n)].push(n);
  }
  for (const b of buckets) {
    b.sort((a, c) => stackSortKey(a) - stackSortKey(c));
  }
  const idToPos = new Map<string, { x: number; y: number }>();
  buckets.forEach((col, ci) => {
    col.forEach((n, row) => {
      idToPos.set(n.id, { x: PAD_X + ci * COL_WIDTH, y: PAD_Y + row * ROW_HEIGHT });
    });
  });
  return nodes.map((n) => {
    const p = idToPos.get(n.id);
    if (!p) {
      return n;
    }
    return { ...n, position: { x: p.x, y: p.y } };
  });
}
