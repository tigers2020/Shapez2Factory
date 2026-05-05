import type { Node } from "@xyflow/react";

function coerceRecord(data: unknown): Record<string, unknown> | null {
  if (!data || typeof data !== "object" || Array.isArray(data)) {
    return null;
  }
  return { ...(data as Record<string, unknown>) };
}

function pickTrimmedString(srv: Record<string, unknown>, key: string): string | undefined {
  if (!(key in srv)) {
    return undefined;
  }
  const v = srv[key];
  if (typeof v !== "string") {
    return undefined;
  }
  return v;
}

function applyOptionalPreviewStringField(
  prev: Record<string, unknown>,
  srv: Record<string, unknown>,
  key: "preview_image_url" | "preview_alt",
): void {
  if (!(key in srv)) {
    return;
  }
  const v = srv[key];
  if (typeof v === "string") {
    const t = v.trim();
    if (t) {
      prev[key] = t;
    } else {
      delete prev[key];
    }
  } else if (v === null) {
    delete prev[key];
  }
}

function applyPreviewOverlay(prev: Record<string, unknown>, srv: Record<string, unknown>): void {
  applyOptionalPreviewStringField(prev, srv, "preview_image_url");
  applyOptionalPreviewStringField(prev, srv, "preview_alt");
}

function quantityFromServerValue(q: unknown): number {
  if (typeof q === "number") {
    return q;
  }
  if (typeof q === "string") {
    return Number.parseInt(q, 10);
  }
  return Number.NaN;
}

/** shape / intermediate / output 타일 — 서버 재계산 결과로 덮어쓴다. */
function applyShapeLikeSemanticOverlay(prev: Record<string, unknown>, srv: Record<string, unknown>): void {
  const code = pickTrimmedString(srv, "shape_code");
  if (code !== undefined) {
    prev.shape_code = code;
  }
  if ("quantity" in srv) {
    const n = quantityFromServerValue(srv.quantity);
    if (Number.isFinite(n) && n >= 1) {
      prev.quantity = Math.floor(n);
    }
  }
  const role = pickTrimmedString(srv, "role");
  if (role !== undefined && role.length > 0) {
    prev.role = role;
  }
  const scRaw = srv.source_carrier;
  if (typeof scRaw === "string" && scRaw.trim() === "fluid") {
    prev.source_carrier = "fluid";
  } else {
    delete prev.source_carrier;
  }
}

function applyOperationSemanticOverlay(prev: Record<string, unknown>, srv: Record<string, unknown>): void {
  const op = pickTrimmedString(srv, "operation");
  if (op !== undefined) {
    prev.operation = op;
  }
  if ("paint_color" in srv) {
    const v = srv.paint_color;
    if (typeof v === "string" && v.trim()) {
      const c = v.trim().slice(0, 1).toLowerCase();
      if ("rgb".includes(c)) {
        prev.paint_color = c;
      } else {
        delete prev.paint_color;
      }
    } else {
      delete prev.paint_color;
    }
  }
  if ("crystal_color" in srv) {
    const v = srv.crystal_color;
    if (typeof v === "string" && v.trim()) {
      prev.crystal_color = v.trim().slice(0, 1);
    } else {
      delete prev.crystal_color;
    }
  }
}

/**
 * Silent 재계산 응답에서 위치·엣지는 유지하고, 서버가 권위 있는 노드 `data`만 id 기준으로 반영한다.
 * (중간·타깃 도형의 `shape_code` / 수량 / 캐리어, 연산 속성, 프리뷰 URL 등)
 */
export function mergeSilentPreviewFromServer(nodes: Node[], serverNodes: Node[] | undefined): Node[] {
  if (!Array.isArray(serverNodes) || serverNodes.length === 0) {
    return nodes;
  }
  const byId = new Map<string, Record<string, unknown>>();
  for (const sn of serverNodes) {
    const id = String(sn.id ?? "");
    if (!id) {
      continue;
    }
    const srv = coerceRecord(sn.data);
    if (!srv) {
      continue;
    }
    byId.set(id, srv);
  }
  if (byId.size === 0) {
    return nodes;
  }
  return nodes.map((n) => {
    const srv = byId.get(n.id);
    if (!srv) {
      return n;
    }
    const prev = coerceRecord(n.data) ?? {};
    const t = String(n.type ?? "");
    if (t === "intermediate" || t === "output" || t === "shape") {
      applyShapeLikeSemanticOverlay(prev, srv);
    } else if (t === "operation") {
      applyOperationSemanticOverlay(prev, srv);
    }
    applyPreviewOverlay(prev, srv);
    return { ...n, data: prev };
  });
}
