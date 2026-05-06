/** Matches recipe editor: `out` = lane 0, `out-1` = lane 1, … */
export function sourceHandleLaneOrder(h: string | null | undefined): number {
  if (h == null || h === "") {
    return 0;
  }
  if (h === "out") {
    return 0;
  }
  const m = /^out-(\d+)$/.exec(h);
  if (m) {
    return Number.parseInt(m[1], 10);
  }
  return 0;
}

/** Target port: `in` = 0, `in-1` = 1, … */
export function targetHandleSlotOrder(h: string | null | undefined): number {
  if (h == null || h === "") {
    return 0;
  }
  if (h === "in") {
    return 0;
  }
  const m = /^in-(\d+)$/.exec(h);
  if (m) {
    return Number.parseInt(m[1], 10);
  }
  return 0;
}

/** Target-side port order for adjacency; prefers explicit `targetPortVisualRank`. */
export function edgeTargetPortRank(e: {
  targetPortVisualRank?: number;
  targetHandle?: string | null;
}): number {
  const v = e.targetPortVisualRank;
  if (v != null && Number.isFinite(v)) {
    return v;
  }
  return targetHandleSlotOrder(e.targetHandle);
}
