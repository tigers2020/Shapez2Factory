import type { Connection, Edge, Node } from "@xyflow/react";

import { getOperationInputArity } from "./operationArity";

export type WireCarrier = "material" | "fluid";

type RecipeConnResult = { ok: true } | { ok: false; message: string };

function dataRecordFromUnknown(raw: unknown): Record<string, unknown> {
  if (raw && typeof raw === "object" && !Array.isArray(raw)) {
    return raw as Record<string, unknown>;
  }
  return {};
}

function operationKeyTrimmed(data: unknown): string {
  const d = dataRecordFromUnknown(data);
  const op = d.operation;
  return typeof op === "string" ? op.trim() : "";
}

function paintAndCrystalFromOpData(data: unknown): {
  paint: string | undefined;
  crystal: string | undefined;
} {
  const opData = dataRecordFromUnknown(data);
  return {
    paint: typeof opData.paint_color === "string" ? opData.paint_color : undefined,
    crystal:
      typeof opData.crystal_color === "string" ? opData.crystal_color : undefined,
  };
}

export function nodeDataIsFluidCarrier(data: unknown): boolean {
  return dataRecordFromUnknown(data).source_carrier === "fluid";
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
    source: c.source,
    target: c.target,
    sourceHandle: c.sourceHandle ?? undefined,
    targetHandle: c.targetHandle ?? undefined,
    type: "recipe",
    data,
  };
}

function inputEdgeSortKey(e: Edge): [boolean, string, string] {
  const d = dataRecordFromUnknown(e.data);
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
  const opKey = operationKeyTrimmed(tn.data);
  if (opKey !== "painter" && opKey !== "crystal_generator") {
    return c;
  }
  const { paint, crystal } = paintAndCrystalFromOpData(tn.data);
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
function painterTargetHandleWantOrSkip(e: Edge, tn: Node, sn: Node): "skip" | "in" | "in-1" {
  if (tn.type !== "operation") {
    return "skip";
  }
  if (sn.type !== "shape" && sn.type !== "intermediate") {
    return "skip";
  }
  const dk = edgeDomainKind(e);
  if (dk !== undefined && dk !== "input") {
    return "skip";
  }
  const opKey = operationKeyTrimmed(tn.data);
  if (opKey !== "painter" && opKey !== "crystal_generator") {
    return "skip";
  }
  const { paint, crystal } = paintAndCrystalFromOpData(tn.data);
  if (opKey === "painter" && String(paint ?? "").trim()) {
    return "skip";
  }
  if (opKey === "crystal_generator" && String(crystal ?? "").trim()) {
    return "skip";
  }
  if (requiredInputCountForCarrier(opKey, paint, crystal) < 2) {
    return "skip";
  }
  return nodeDataIsFluidCarrier(sn.data) ? "in-1" : "in";
}

function edgeWithAdjustedPainterTarget(e: Edge, want: "in" | "in-1"): Edge {
  const prev: Record<string, unknown> =
    e.data && typeof e.data === "object" && !Array.isArray(e.data)
      ? { ...dataRecordFromUnknown(e.data) }
      : { domainKind: "input" };
  if (typeof prev.domainKind !== "string") {
    prev.domainKind = "input";
  }
  if (want === "in-1") {
    prev.slot = "1";
  } else {
    delete prev.slot;
  }
  return { ...e, targetHandle: want, data: prev };
}

export function ensurePainterTargetHandlesOnEdges(nodes: Node[], edges: Edge[]): Edge[] {
  return edges.map((e) => {
    const tn = nodes.find((n) => n.id === e.target);
    const sn = nodes.find((n) => n.id === e.source);
    if (!tn || !sn) {
      return e;
    }
    const want = painterTargetHandleWantOrSkip(e, tn, sn);
    if (want === "skip") {
      return e;
    }
    if (e.targetHandle === want) {
      return e;
    }
    return edgeWithAdjustedPainterTarget(e, want);
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

function recipeDuplicateLink(edges: Edge[], c: Connection): RecipeConnResult | undefined {
  if (edges.some((e) => e.source === c.source && e.target === c.target)) {
    return { ok: false, message: "That link already exists." };
  }
  return undefined;
}

function recipeEvaluateDelivery(
  nodes: Node[],
  edges: Edge[],
  c: Connection,
): RecipeConnResult | undefined {
  if (!isIntermediateToOutputConnection(nodes, c)) {
    return undefined;
  }
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

type MaterialCarrierCheckContext = {
  nodes: Node[];
  c: Connection;
  sn: Node;
  opKey: string;
  paint: string | undefined;
  crystal: string | undefined;
  need: number;
  incoming: Edge[];
  th: string;
};

function resolveMaterialInputWantCarrier(
  ctx: MaterialCarrierCheckContext,
  expected: WireCarrier[],
): { want: WireCarrier | undefined; twoWireFluidShape: boolean } {
  const k = ctx.opKey.trim();
  const twoWireFluidShape =
    (k === "painter" && !String(ctx.paint ?? "").trim() && expected.length === 2) ||
    (k === "crystal_generator" && !String(ctx.crystal ?? "").trim() && expected.length === 2);
  if (twoWireFluidShape) {
    return { want: ctx.th === "in-1" ? "fluid" : "material", twoWireFluidShape };
  }
  const pending = pendingInputEdgeFromConnection(ctx.c);
  const sorted = sortedInputEdgesToOperation(
    [...ctx.incoming, pending],
    ctx.nodes,
    ctx.c.target,
  );
  const idx = sorted.findIndex((e) => e.id === "__pending__");
  const want = idx >= 0 && idx < expected.length ? expected[idx] : undefined;
  return { want, twoWireFluidShape };
}

function materialCarrierMismatchMessage(
  opKey: string,
  th: string,
  want: WireCarrier,
  twoWireFluidShape: boolean,
): RecipeConnResult {
  const k = opKey.trim();
  if (!twoWireFluidShape) {
    return {
      ok: false,
      message: `This wire must be ${want} (operation ${opKey} handle ${th}).`,
    };
  }
  const here =
    th === "in-1"
      ? `port 1 (upper handle in-1) — fluid only`
      : `port 0 (lower handle in) — shape (material) only`;
  const opHint = k === "painter" ? "Painter" : "Crystal generator (same ports as painter)";
  return {
    ok: false,
    message: `This wire must be ${want} on ${here}. ${opHint}: shape on in (lower) · fluid on in-1 (upper).`,
  };
}

function materialOpCarrierMismatch(ctx: MaterialCarrierCheckContext): RecipeConnResult | undefined {
  const expected = expectedInputCarriers(ctx.opKey, ctx.paint, ctx.crystal);
  if (ctx.need <= 0 || expected.length <= 0) {
    return undefined;
  }
  const { want, twoWireFluidShape } = resolveMaterialInputWantCarrier(ctx, expected);
  if (want === undefined) {
    return undefined;
  }
  const got: WireCarrier = nodeDataIsFluidCarrier(ctx.sn.data) ? "fluid" : "material";
  if (got === want) {
    return undefined;
  }
  return materialCarrierMismatchMessage(ctx.opKey, ctx.th, want, twoWireFluidShape);
}

function recipeEvaluateMaterialToOperation(
  nodes: Node[],
  edges: Edge[],
  c: Connection,
  sn: Node,
  tn: Node,
): RecipeConnResult | undefined {
  if (!isMaterialToOperationConnection(nodes, c)) {
    return undefined;
  }
  const opKey = operationKeyTrimmed(tn.data);
  const { paint, crystal } = paintAndCrystalFromOpData(tn.data);
  const need = requiredInputCountForCarrier(opKey, paint, crystal);
  const incoming = edges.filter((e) => e.target === c.target && edgeDomainKind(e) === "input");
  if (incoming.length >= need) {
    return { ok: false, message: "This operation already has all required inputs." };
  }
  const th = c.targetHandle ?? "in";
  if (incoming.some((e) => (e.targetHandle ?? "in") === th)) {
    return { ok: false, message: "That operation input port is already used." };
  }
  const carrier = materialOpCarrierMismatch({
    nodes,
    c,
    sn,
    opKey,
    paint,
    crystal,
    need,
    incoming,
    th,
  });
  if (carrier) {
    return carrier;
  }
  return { ok: true };
}

function recipeEvaluateOpToIntermediate(
  c: Connection,
  sn: Node,
  tn: Node,
  st: string | undefined,
  tt: string | undefined,
): RecipeConnResult | undefined {
  const opToIntermediate =
    st === "operation" &&
    tt === "intermediate" &&
    isOperationMaterialOutputSourceHandle(c.sourceHandle) &&
    (c.targetHandle === "in" || c.targetHandle == null);
  if (!opToIntermediate) {
    return undefined;
  }
  const opKey = operationKeyTrimmed(sn.data);
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

export function evaluateRecipeConnection(
  nodes: Node[],
  edges: Edge[],
  cIn: Connection,
): RecipeConnResult {
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

  const dup = recipeDuplicateLink(edges, c);
  if (dup) {
    return dup;
  }

  const delivery = recipeEvaluateDelivery(nodes, edges, c);
  if (delivery !== undefined) {
    return delivery;
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

  const material = recipeEvaluateMaterialToOperation(nodes, edges, c, sn, tn);
  if (material !== undefined) {
    return material;
  }

  const opToMid = recipeEvaluateOpToIntermediate(c, sn, tn, st, tt);
  if (opToMid !== undefined) {
    return opToMid;
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

function addLastEdgeIdIfPresent(ids: Set<string>, list: Edge[]): void {
  const last = list.at(-1);
  if (last) {
    ids.add(last.id);
  }
}

function collectMaterialToOperationRemovalIds(
  ids: Set<string>,
  nodes: Node[],
  edges: Edge[],
  c: Connection,
  tn: Node,
): void {
  if (!isMaterialToOperationConnection(nodes, c)) {
    return;
  }
  const incoming = edges.filter((e) => e.target === c.target && edgeDomainKind(e) === "input");
  const th = c.targetHandle ?? "in";
  const samePort = incoming.filter((e) => (e.targetHandle ?? "in") === th);
  if (samePort.length > 0) {
    addLastEdgeIdIfPresent(ids, samePort);
    return;
  }
  const opKey = operationKeyTrimmed(tn.data);
  const { paint, crystal } = paintAndCrystalFromOpData(tn.data);
  const need = requiredInputCountForCarrier(opKey, paint, crystal);
  if (incoming.length >= need) {
    addLastEdgeIdIfPresent(ids, incoming);
  }
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

  collectMaterialToOperationRemovalIds(ids, nodes, edges, c, tn);

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

function connectionDomainKind(sn: Node, tn: Node): "delivery" | "input" | "output" {
  if (sn.type === "intermediate" && tn.type === "output") {
    return "delivery";
  }
  if (sn.type === "shape" || sn.type === "intermediate") {
    return "input";
  }
  return "output";
}

export function connectionToRecipeEdge(c: Connection, nodes: Node[]): Edge {
  const sn = nodes.find((n) => n.id === c.source);
  const tn = nodes.find((n) => n.id === c.target);
  if (!sn?.type || !tn?.type) {
    throw new Error("connectionToRecipeEdge: missing source or target node");
  }
  const domainKind = connectionDomainKind(sn, tn);
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
    data.slot = String(outputLaneFromSourceHandle(sh));
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
