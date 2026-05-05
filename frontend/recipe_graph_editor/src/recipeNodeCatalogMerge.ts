import type { Node } from "@xyflow/react";

export type CatalogOperationRow = { value: string; label: string; icon: string };

export function catalogIconByValue(rows: readonly CatalogOperationRow[]): Map<string, string> {
  const m = new Map<string, string>();
  for (const r of rows) {
    const v = String(r.value ?? "").trim();
    const icon = typeof r.icon === "string" ? r.icon.trim() : "";
    if (v && icon) {
      m.set(v, icon);
    }
  }
  return m;
}

/** 연산 노드 `data.icon`이 비어 있으면 카탈로그 URL을 채운다(불변 입력은 얕은 복사만). */
export function enrichNodesWithCatalogIcons(
  nodes: Node[],
  iconByValue: ReadonlyMap<string, string>,
): Node[] {
  return nodes.map((n) => {
    if (n.type !== "operation") {
      return n;
    }
    const raw = n.data;
    const d =
      raw && typeof raw === "object" && !Array.isArray(raw)
        ? (raw as Record<string, unknown>)
        : {};
    const op = String(d.operation ?? "").trim();
    if (!op) {
      return n;
    }
    const icon = iconByValue.get(op);
    if (!icon || d.icon === icon) {
      return n;
    }
    return { ...n, data: { ...d, icon } };
  });
}
