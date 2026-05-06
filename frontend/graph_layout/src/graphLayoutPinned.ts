import type { GraphInput, GraphLayoutResult, LayoutMetrics } from "./types";
import { getGraphNodes } from "./graphLayoutInput";

function rectsOverlap(
  ax: number,
  ay: number,
  bx: number,
  by: number,
  metrics: LayoutMetrics,
): boolean {
  return !(
    ax + metrics.nodeWidth <= bx ||
    bx + metrics.nodeWidth <= ax ||
    ay + metrics.nodeHeight <= by ||
    by + metrics.nodeHeight <= ay
  );
}

function resolvePinnedNodeOverlaps(
  positions: Map<string, { x: number; y: number }>,
  metrics: LayoutMetrics,
): void {
  const ids = [...positions.keys()].sort((a, b) => {
    const pa = positions.get(a);
    const pb = positions.get(b);
    if (!pa || !pb) {
      return 0;
    }
    if (pa.y !== pb.y) {
      return pa.y - pb.y;
    }
    if (pa.x !== pb.x) {
      return pa.x - pb.x;
    }
    return String(a).localeCompare(String(b));
  });
  const placed: { x: number; y: number }[] = [];
  for (const id of ids) {
    const start = positions.get(id);
    if (!start) {
      continue;
    }
    let p = { x: start.x, y: start.y };
    let tries = 0;
    while (tries < 400) {
      let overlap = false;
      for (const q of placed) {
        if (rectsOverlap(p.x, p.y, q.x, q.y, metrics)) {
          overlap = true;
          break;
        }
      }
      if (!overlap) {
        break;
      }
      p = { x: p.x, y: p.y + metrics.rowGap };
      tries += 1;
    }
    placed.push({ x: p.x, y: p.y });
    positions.set(id, p);
  }
}

export function graphUsesPinnedPositions(graph: GraphInput): boolean {
  const nodes = getGraphNodes(graph);
  if (!nodes.length) {
    return false;
  }
  const coords: { x: number; y: number }[] = [];
  for (const node of nodes) {
    const x = Number(node.x);
    const y = Number(node.y);
    if (!Number.isFinite(x) || !Number.isFinite(y)) {
      return false;
    }
    coords.push({ x, y });
  }
  if (coords.length === 1) {
    return true;
  }
  const minX = Math.min(...coords.map((c) => c.x));
  const maxX = Math.max(...coords.map((c) => c.x));
  const minY = Math.min(...coords.map((c) => c.y));
  const maxY = Math.max(...coords.map((c) => c.y));
  const spread = Math.max(maxX - minX, maxY - minY);
  return spread > 0.5;
}

export function computePinnedGraphLayout(graph: GraphInput, metrics: LayoutMetrics): GraphLayoutResult {
  const nodes = getGraphNodes(graph);
  const positions = new Map<string, { x: number; y: number }>();
  for (const node of nodes) {
    const x = Number(node.x);
    const y = Number(node.y);
    positions.set(node.id, {
      x: Number.isFinite(x) ? x : metrics.graphPadding,
      y: Number.isFinite(y) ? y : metrics.graphPadding,
    });
  }
  const posVals = [...positions.values()];
  const xOff = metrics.graphPadding - Math.min(...posVals.map((p) => p.x));
  const yOff = metrics.graphPadding - Math.min(...posVals.map((p) => p.y));
  const shifted = new Map<string, { x: number; y: number }>();
  for (const [id, p] of positions) {
    shifted.set(id, { x: p.x + xOff, y: p.y + yOff });
  }
  resolvePinnedNodeOverlaps(shifted, metrics);
  const positioned = [...shifted.values()];
  const minX = Math.min(...positioned.map((position) => position.x));
  const minY = Math.min(...positioned.map((position) => position.y));
  const maxX = Math.max(...positioned.map((position) => position.x + metrics.nodeWidth));
  const maxY = Math.max(...positioned.map((position) => position.y + metrics.nodeHeight));

  return {
    positions: shifted,
    width: maxX + metrics.graphPadding,
    height: maxY + metrics.graphPadding,
    bounds: {
      minX,
      minY,
      maxX,
      maxY,
      width: maxX - minX,
      height: maxY - minY,
    },
  };
}
