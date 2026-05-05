import type { Node } from "@xyflow/react";

function normalizeSeverity(raw: unknown): string {
  return typeof raw === "string" ? raw : "";
}

function applyIssueToBest(
  issue: unknown,
  rank: Record<string, number>,
  best: Map<string, number>,
): void {
  if (!issue || typeof issue !== "object") {
    return;
  }
  const raw = issue as Record<string, unknown>;
  const sev = normalizeSeverity(raw.severity);
  const r = rank[sev];
  if (!r) {
    return;
  }
  const ids = raw.node_ids;
  if (!Array.isArray(ids)) {
    return;
  }
  for (const nid of ids) {
    if (typeof nid !== "string") {
      continue;
    }
    const prev = best.get(nid) ?? 0;
    if (r > prev) {
      best.set(nid, r);
    }
  }
}

/** 서버 `validation.issues`와 동일한 우선순위 규칙 (`annotate_visual_graph_with_issues`). */
export function applyValidationIssuesToNodes(nodes: Node[], issues: unknown): Node[] {
  const rank: Record<string, number> = { error: 3, warning: 2 };
  const best = new Map<string, number>();
  if (Array.isArray(issues)) {
    for (const issue of issues) {
      applyIssueToBest(issue, rank, best);
    }
  }
  const inv: Record<number, "error" | "warning"> = { 3: "error", 2: "warning" };
  return nodes.map((n) => {
    const br = best.get(n.id);
    const sev = br != null && inv[br] ? inv[br] : undefined;
    const prev: Record<string, unknown> =
      n.data && typeof n.data === "object" && !Array.isArray(n.data)
        ? { ...n.data }
        : {};
    if (sev) {
      prev.validationSeverity = sev;
    } else {
      delete prev.validationSeverity;
    }
    return { ...n, data: prev };
  });
}
