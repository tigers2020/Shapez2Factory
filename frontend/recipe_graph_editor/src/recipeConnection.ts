import type { Connection, Edge, Node } from "@xyflow/react";

import { getOperationInputArity } from "./operationArity";

export type WireCarrier = "material" | "fluid";

export function nodeDataIsFluidCarrier(data: unknown): boolean {
  const d =
    data && typeof data === "object" && !Array.isArray(data)
      ? (data as Record<string, unknown>)
      : {};
  return d.source_carrier === "fluid";
}

function inputSlotKeyFromTargetHandle(th: string | null | undefined): string {
  if (typeof th === "string" && th.startsWith("in-") && th.length > 3) {
    const suf = th.slice(3);
    if (/^\d+$/.test(suf) && Number.parseInt(suf, 10) >= 1) {
      return suf;
    }
  }
  return "";
}

function pendingInputEdgeFromConnection(c: Connection): Edge {
  const slot = inputSlotKeyFromTargetHandle(c.targetHandle);
  const data: Record<string, unknown> = { domainKind: "input" };
  if (slot) {
    data.slot = slot;
  }
  return {
    id: "__pending__",
    source: c.source!,
    target: c.target!,
    sourceHandle: c.sourceHandle ?? undefined,
    targetHandle: c.targetHandle ?? undefined,
    type: "recipe",
    data,
  };
}

function inputEdgeSortKey(e: Edge): [boolean, string, string] {
  const raw = e.data;
  const d =
    raw && typeof raw === "object" && !Array.isArray(raw)
      ? (raw as Record<string, unknown>)
      : {};
  const slotKey = typeof d.slot === "string" && d.slot.trim() ? d.slot.trim() : "";
  const hasSlot = Boolean(slotKey);
  return [!hasSlot, slotKey, e.source];
}

function sortedInputEdgesToOperation(edges: Edge[], nodes: Node[], opId: string): Edge[] {
  const list = edges.filter((e) => e.target === opId && edgeDomainKind(e) === "input");
  const rows = list
    .map((e) => ({ e, k: inputEdgeSortKey(e) }))
    .filter((row) => {
      const sn = nodes.find((n) => n.id === row.e.source);
      return Boolean(sn && (sn.type === "shape" || sn.type === "intermediate"));
    })
    .sort((a, b) => {
      if (a.k[0] !== b.k[0]) {
        return (a.k[0] ? 1 : 0) - (b.k[0] ? 1 : 0);
      }
      if (a.k[1] !== b.k[1]) {
        return a.k[1].localeCompare(b.k[1]);
      }
      return a.k[2].localeCompare(b.k[2]);
    });
  return rows.map((r) => r.e);
}

function requiredInputCountForCarrier(
  opKey: string,
  paintColor: string | undefined,
  crystalColor?: string,
): number {
  const k = opKey.trim();
  if (k === "painter" && String(paintColor ?? "").trim()) {
    return 1;
  }
  if (k === "crystal_generator" && String(crystalColor ?? "").trim()) {
    return 1;
  }
  return getOperationInputArity(k);
}

/** Port carrier order must match ``recipe_graph_input_carrier.expected_input_carriers`` (Python). */
function expectedInputCarriers(
  opKey: string,
  paintColor: string | undefined,
  crystalColor?: string,
): WireCarrier[] {
  const k = opKey.trim();
  if (k === "painter") {
    if (String(paintColor ?? "").trim()) {
      return ["material"];
    }
    return ["fluid", "material"];
  }
  if (k === "color_mixer") {
    return ["fluid", "fluid"];
  }
  if (k === "crystal_generator") {
    if (String(crystalColor ?? "").trim()) {
      return ["material"];
    }
    return ["fluid", "material"];
  }
  if (k === "swapper" || k === "stacker") {
    return ["material", "material"];
  }
  return ["material"];
}

function outputLaneFromSourceHandle(sh: string | null | undefined): number {
  if (typeof sh === "string") {
    const m = /^out-(\d+)$/.exec(sh);
    if (m) {
      return Number.parseInt(m[1], 10);
    }
  }
  return 0;
}

function expectedOutputCarrier(opKey: string, lane: number): WireCarrier {
  if (opKey.trim() === "color_mixer" && lane === 0) {
    return "fluid";
  }
  return "material";
}

export function edgeToConnection(e: Edge): Connection | null {
  if (!e.source || !e.target) {
    return null;
  }
  return {
    source: e.source,
    target: e.target,
    sourceHandle: e.sourceHandle ?? null,
    targetHandle: e.targetHandle ?? null,
  };
}

/** Drop edges that are no longer valid after node data (e.g. carrier) changes. */
export function filterStaleRecipeEdges(nodes: Node[], edges: Edge[]): Edge[] {
  return edges.filter((e) => {
    const c = edgeToConnection(e);
    if (!c) {
      return false;
    }
    const rest = edges.filter((x) => x.id !== e.id);
    return evaluateRecipeConnection(nodes, rest, c).ok;
  });
}

function isOperationMaterialOutputSourceHandle(h: string | null | undefined): boolean {
  if (h == null || h === "") {
    return true;
  }
  if (h === "out") {
    return true;
  }
  return /^out-\d+$/.test(h);
}

function edgeDomainKind(e: Edge): string | undefined {
  const d = e.data;
  if (d && typeof d === "object" && "domainKind" in d) {
    return String((d as { domainKind?: string }).domainKind);
  }
  return undefined;
}

export function isMaterialToOperationConnection(nodes: Node[], c: Connection): boolean {
  if (!c.source || !c.target || c.source === c.target) {
    return false;
  }
  const sn = nodes.find((n) => n.id === c.source);
  const tn = nodes.find((n) => n.id === c.target);
  if (!sn || !tn) {
    return false;
  }
  const st = sn.type;
  const tt = tn.type;
  return (
    (st === "shape" || st === "intermediate") &&
    tt === "operation" &&
    (c.sourceHandle === "out" || c.sourceHandle == null || c.sourceHandle === "") &&
    (c.targetHandle === "in" ||
      c.targetHandle == null ||
      c.targetHandle === "in-1" ||
      (typeof c.targetHandle === "string" && c.targetHandle.startsWith("in-")))
  );
}

/**
 * XYFlow often snaps to the geometrically nearest handle; painter / crystal_generator 2-wire
 * still expects fluid on ``in-1`` and shape on ``in``. Derive the target handle from the source
 * wire carrier.
 */
export function normalizeMaterialToPainterConnection(nodes: Node[], c: Connection): Connection {
  if (!c.source || !c.target || !isMaterialToOperationConnection(nodes, c)) {
    return c;
  }
  const tn = nodes.find((n) => n.id === c.target);
  const sn = nodes.find((n) => n.id === c.source);
  if (!tn || !sn) {
    return c;
  }
  const opKey = String((tn.data as { operation?: string } | undefined)?.operation ?? "").trim();
  if (opKey !== "painter" && opKey !== "crystal_generator") {
    return c;
  }
  const opData = (tn.data as Record<string, unknown>) ?? {};
  const paint = typeof opData.paint_color === "string" ? opData.paint_color : undefined;
  const crystal =
    typeof opData.crystal_color === "string" ? opData.crystal_color : undefined;
  if (opKey === "painter" && String(paint ?? "").trim()) {
    return c;
  }
  if (opKey === "crystal_generator" && String(crystal ?? "").trim()) {
    return c;
  }
  const handle = nodeDataIsFluidCarrier(sn.data) ? "in-1" : "in";
  return { ...c, targetHandle: handle };
}

/**
 * RF 스냅샷에 ``targetHandle``이 빠지면 XYFlow가 첫 번째 소켓(페인터·크리스털은 ``in-1`` 상단)에 묶인다.
 * 부트스트랩·재계산 응답 직후 재료/유체에 맞게 고친다.
 */
export function ensurePainterTargetHandlesOnEdges(nodes: Node[], edges: Edge[]): Edge[] {
  return edges.map((e) => {
    const tn = nodes.find((n) => n.id === e.target);
    const sn = nodes.find((n) => n.id === e.source);
    if (!tn || !sn || tn.type !== "operation") {
      return e;
    }
    if (sn.type !== "shape" && sn.type !== "intermediate") {
      return e;
    }
    const dk = edgeDomainKind(e);
    if (dk !== undefined && dk !== "input") {
      return e;
    }
    const opKey = String((tn.data as { operation?: string } | undefined)?.operation ?? "").trim();
    if (opKey !== "painter" && opKey !== "crystal_generator") {
      return e;
    }
    const opData = (tn.data as Record<string, unknown>) ?? {};
    const paint = typeof opData.paint_color === "string" ? opData.paint_color : undefined;
    const crystal =
      typeof opData.crystal_color === "string" ? opData.crystal_color : undefined;
    if (opKey === "painter" && String(paint ?? "").trim()) {
      return e;
    }
    if (opKey === "crystal_generator" && String(crystal ?? "").trim()) {
      return e;
    }
    if (requiredInputCountForCarrier(opKey, paint, crystal) < 2) {
      return e;
    }
    const want = nodeDataIsFluidCarrier(sn.data) ? "in-1" : "in";
    if (e.targetHandle === want) {
      return e;
    }
    const prev =
      e.data && typeof e.data === "object" && !Array.isArray(e.data)
        ? ({ ...(e.data as Record<string, unknown>) } as Record<string, unknown>)
        : ({ domainKind: "input" } as Record<string, unknown>);
    if (typeof prev.domainKind !== "string") {
      prev.domainKind = "input";
    }
    if (want === "in-1") {
      prev.slot = "1";
    } else {
      delete prev.slot;
    }
    return { ...e, targetHandle: want, data: prev };
  });
}

/** intermediate(shape) → output(target) 납품 연결(RF 타입 기준). */
export function isIntermediateToOutputConnection(nodes: Node[], c: Connection): boolean {
  if (!c.source || !c.target || c.source === c.target) {
    return false;
  }
  const sn = nodes.find((n) => n.id === c.source);
  const tn = nodes.find((n) => n.id === c.target);
  if (!sn || !tn) {
    return false;
  }
  return (
    sn.type === "intermediate" &&
    tn.type === "output" &&
    (c.sourceHandle === "out" || c.sourceHandle == null) &&
    (c.targetHandle === "in" || c.targetHandle == null)
  );
}

export function evaluateRecipeConnection(
  nodes: Node[],
  edges: Edge[],
  cIn: Connection,
): { ok: true } | { ok: false; message: string } {
  if (!cIn.source || !cIn.target) {
    return { ok: false, message: "Incomplete connection." };
  }
  if (cIn.source === cIn.target) {
    return { ok: false, message: "Cannot connect a node to itself." };
  }

  const sn = nodes.find((n) => n.id === cIn.source);
  const tn = nodes.find((n) => n.id === cIn.target);
  if (!sn || !tn) {
    return { ok: false, message: "Unknown node." };
  }

  const c = normalizeMaterialToPainterConnection(nodes, {
    source: cIn.source,
    target: cIn.target,
    sourceHandle: cIn.sourceHandle ?? null,
    targetHandle: cIn.targetHandle ?? null,
  });

  const st = sn.type;
  const tt = tn.type;

  const intermediateToOutput = isIntermediateToOutputConnection(nodes, c);

  if (edges.some((e) => e.source === c.source && e.target === c.target)) {
    return { ok: false, message: "That link already exists." };
  }

  if (intermediateToOutput) {
    const deliveriesToTarget = edges.filter(
      (e) => e.target === c.target && edgeDomainKind(e) === "delivery",
    );
    if (
      deliveriesToTarget.length >= 1 &&
      !deliveriesToTarget.some((e) => e.source === c.source)
    ) {
      return {
        ok: false,
        message: "This output already has a delivery link.",
      };
    }
    return { ok: true };
  }

  if (st === "output") {
    return { ok: false, message: "Output nodes have no outgoing wires." };
  }

  if (tt === "output") {
    return {
      ok: false,
      message: "Only intermediate shapes may connect to an output terminal.",
    };
  }

  if (isMaterialToOperationConnection(nodes, c)) {
    const opKey = String((tn.data as { operation?: string } | undefined)?.operation ?? "");
    const opData = (tn.data as Record<string, unknown>) ?? {};
    const paint = typeof opData.paint_color === "string" ? opData.paint_color : undefined;
    const crystal =
      typeof opData.crystal_color === "string" ? opData.crystal_color : undefined;
    const need = requiredInputCountForCarrier(opKey, paint, crystal);
    const incoming = edges.filter((e) => e.target === c.target && edgeDomainKind(e) === "input");
    if (incoming.length >= need) {
      return { ok: false, message: "This operation already has all required inputs." };
    }
    const th = c.targetHandle ?? "in";
    if (incoming.some((e) => (e.targetHandle ?? "in") === th)) {
      return { ok: false, message: "That operation input port is already used." };
    }
    const expected = expectedInputCarriers(opKey, paint, crystal);
    if (need > 0 && expected.length > 0) {
      const k = opKey.trim();
      let want: WireCarrier | undefined;
      const twoWireFluidShape =
        (k === "painter" && !String(paint ?? "").trim() && expected.length === 2) ||
        (k === "crystal_generator" && !String(crystal ?? "").trim() && expected.length === 2);
      if (twoWireFluidShape) {
        want = th === "in-1" ? "fluid" : "material";
      } else {
        const pending = pendingInputEdgeFromConnection(c);
        const sorted = sortedInputEdgesToOperation([...incoming, pending], nodes, c.target);
        const idx = sorted.findIndex((e) => e.id === "__pending__");
        if (idx >= 0 && idx < expected.length) {
          want = expected[idx];
        }
      }
      if (want !== undefined) {
        const got: WireCarrier = nodeDataIsFluidCarrier(sn.data) ? "fluid" : "material";
        if (got !== want) {
          if (twoWireFluidShape) {
            const here =
              th === "in-1"
                ? `port 1 (upper handle in-1) — fluid only`
                : `port 0 (lower handle in) — shape (material) only`;
            const opHint =
              k === "painter"
                ? "Painter"
                : "Crystal generator (same ports as painter)";
            return {
              ok: false,
              message: `This wire must be ${want} on ${here}. ${opHint}: shape on in (lower) · fluid on in-1 (upper).`,
            };
          }
          return {
            ok: false,
            message: `This wire must be ${want} (operation ${opKey} handle ${th}).`,
          };
        }
      }
    }
    return { ok: true };
  }

  const opToIntermediate =
    st === "operation" &&
    tt === "intermediate" &&
    isOperationMaterialOutputSourceHandle(c.sourceHandle) &&
    (c.targetHandle === "in" || c.targetHandle == null);

  if (opToIntermediate) {
    const opKey = String((sn.data as { operation?: string } | undefined)?.operation ?? "");
    const lane = outputLaneFromSourceHandle(c.sourceHandle);
    const want = expectedOutputCarrier(opKey, lane);
    const got: WireCarrier = nodeDataIsFluidCarrier(tn.data) ? "fluid" : "material";
    if (want !== got) {
      return {
        ok: false,
        message: `Operation output is ${want}; intermediate node must match (got ${got}).`,
      };
    }
    return { ok: true };
  }

  if (st === "operation" && tt === "shape") {
    return { ok: false, message: "Operations cannot wire into source material nodes." };
  }

  if (st === "operation" && tt === "operation") {
    return { ok: false, message: "Operation-to-operation links are not allowed." };
  }

  if ((st === "shape" || st === "intermediate") && (tt === "shape" || tt === "intermediate")) {
    return { ok: false, message: "Shape-to-shape links are not allowed." };
  }

  return { ok: false, message: "Not a valid recipe wire (see staff graph rules)." };
}

/**
 * 새 연결 ``c``를 넣기 전에 제거할 기존 엣지 id 목록(마지막 충돌 연결 우선).
 * ``isValidConnection`` / ``onConnect``에서 교체 연결을 허용할 때 사용한다.
 */
export function getRecipeConnectEdgeRemovals(
  nodes: Node[],
  edges: Edge[],
  c: Connection,
): string[] {
  if (!c.source || !c.target || c.source === c.target) {
    return [];
  }
  const sn = nodes.find((n) => n.id === c.source);
  const tn = nodes.find((n) => n.id === c.target);
  if (!sn || !tn) {
    return [];
  }
  const st = sn.type;
  if (st === "output") {
    return [];
  }

  const ids = new Set<string>();

  for (const e of edges) {
    if (e.source === c.source && e.target === c.target) {
      ids.add(e.id);
    }
  }

  if (isIntermediateToOutputConnection(nodes, c)) {
    for (const e of edges) {
      if (e.target === c.target && edgeDomainKind(e) === "delivery") {
        ids.add(e.id);
      }
    }
  }

  if (isMaterialToOperationConnection(nodes, c)) {
    const incoming = edges.filter((e) => e.target === c.target && edgeDomainKind(e) === "input");
    const th = c.targetHandle ?? "in";
    const samePort = incoming.filter((e) => (e.targetHandle ?? "in") === th);
    if (samePort.length > 0) {
      ids.add(samePort[samePort.length - 1].id);
    } else {
      const opKey = String((tn.data as { operation?: string } | undefined)?.operation ?? "");
      const opData = (tn.data as Record<string, unknown>) ?? {};
      const paint = typeof opData.paint_color === "string" ? opData.paint_color : undefined;
      const crystal =
        typeof opData.crystal_color === "string" ? opData.crystal_color : undefined;
      const need = requiredInputCountForCarrier(opKey, paint, crystal);
      if (incoming.length >= need) {
        ids.add(incoming[incoming.length - 1].id);
      }
    }
  }

  return [...ids];
}

export function wouldConnectAfterRemovals(
  nodes: Node[],
  edges: Edge[],
  c: Connection,
): boolean {
  const remove = new Set(getRecipeConnectEdgeRemovals(nodes, edges, c));
  const filtered = edges.filter((e) => !remove.has(e.id));
  return evaluateRecipeConnection(nodes, filtered, c).ok;
}

export function connectionToRecipeEdge(c: Connection, nodes: Node[]): Edge {
  const sn = nodes.find((n) => n.id === c.source);
  const tn = nodes.find((n) => n.id === c.target);
  if (!sn?.type || !tn?.type) {
    throw new Error("connectionToRecipeEdge: missing source or target node");
  }
  let domainKind: "delivery" | "input" | "output";
  if (sn.type === "intermediate" && tn.type === "output") {
    domainKind = "delivery";
  } else if (sn.type === "shape" || sn.type === "intermediate") {
    domainKind = "input";
  } else {
    domainKind = "output";
  }
  const th = c.targetHandle ?? "";
  const slotPart =
    domainKind === "input" && typeof th === "string" && th.startsWith("in-") && th.length > 3
      ? th.slice(3)
      : "";
  const data: Record<string, unknown> = { domainKind };
  if (domainKind === "input" && slotPart && /^\d+$/.test(slotPart) && Number(slotPart) >= 1) {
    data.slot = slotPart;
  }
  if (domainKind === "output") {
    const sh = typeof c.sourceHandle === "string" ? c.sourceHandle : "out";
    let lane = 0;
    if (sh === "out") {
      lane = 0;
    } else {
      const m = /^out-(\d+)$/.exec(sh);
      if (m) {
        lane = Number.parseInt(m[1], 10);
      }
    }
    data.slot = String(lane);
  }
  const handleKey = `${c.sourceHandle ?? ""}_${c.targetHandle ?? ""}`;
  const eid = `e-${c.source}-${c.target}-${domainKind}-${handleKey}`;
  return {
    id: eid,
    source: c.source,
    target: c.target,
    sourceHandle: c.sourceHandle ?? undefined,
    targetHandle: c.targetHandle ?? undefined,
    type: "recipe",
    data,
  };
}
