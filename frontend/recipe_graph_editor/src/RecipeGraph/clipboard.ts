import type { Edge, Node, NodeChange } from "@xyflow/react";
import { useEffect, type Dispatch, type SetStateAction } from "react";

import { ensurePainterTargetHandlesOnEdges } from "../RecipeConnection";
import { ensureOperationOutputArtifacts } from "../Operation/outputStaging";

/** Ref holder (avoids deprecated `MutableRefObject` in Sonar ruleset). */
type RefBox<T> = { current: T };

export const RECIPE_GRAPH_CLIPBOARD_PREFIX = "shapez2-recipe-graph/v1:";

export type RecipeGraphClipboardPayload = {
  version: 1;
  nodes: Node[];
  edges: Edge[];
};

function cloneGraphNode(n: Node): Node {
  const raw = structuredClone(n) as Node;
  return {
    ...raw,
    selected: false,
    dragging: false,
  };
}

function cloneGraphEdge(e: Edge): Edge {
  const raw = structuredClone(e) as Edge;
  return {
    ...raw,
    selected: false,
  };
}

export function buildSubgraphClipboardPayload(
  selectedIds: ReadonlySet<string>,
  nodes: Node[],
  edges: Edge[],
): RecipeGraphClipboardPayload | null {
  const picked = nodes.filter((n) => selectedIds.has(n.id));
  if (picked.length === 0) {
    return null;
  }
  const edgeList = edges.filter(
    (e) => selectedIds.has(e.source) && selectedIds.has(e.target),
  );
  return {
    version: 1,
    nodes: picked.map(cloneGraphNode),
    edges: edgeList.map(cloneGraphEdge),
  };
}

export function serializeRecipeGraphClipboard(payload: RecipeGraphClipboardPayload): string {
  return `${RECIPE_GRAPH_CLIPBOARD_PREFIX}${JSON.stringify(payload)}`;
}

export function tryParseRecipeGraphClipboard(text: string): RecipeGraphClipboardPayload | null {
  const t = text.trim();
  if (!t.startsWith(RECIPE_GRAPH_CLIPBOARD_PREFIX)) {
    return null;
  }
  try {
    const json = t.slice(RECIPE_GRAPH_CLIPBOARD_PREFIX.length);
    const v = JSON.parse(json) as RecipeGraphClipboardPayload;
    if (v?.version !== 1 || !Array.isArray(v.nodes) || !Array.isArray(v.edges)) {
      return null;
    }
    return v;
  } catch {
    return null;
  }
}

function idPrefixForNodeType(t: string | undefined): string {
  if (t === "shape") {
    return "src";
  }
  if (t === "operation") {
    return "op";
  }
  if (t === "intermediate") {
    return "im";
  }
  if (t === "output") {
    return "out";
  }
  return "node";
}

/**
 * 새 ID를 부여하고, 뷰포트 중심에 붙여넣기 위치를 맞춘다.
 */
export function remapClipboardPayloadForPaste(
  payload: RecipeGraphClipboardPayload,
  newGraphNodeId: (prefix: string) => string,
  translateNodes: (nodes: Node[]) => Node[],
): { nodes: Node[]; edges: Edge[] } {
  const idMap = new Map<string, string>();
  for (const n of payload.nodes) {
    idMap.set(n.id, newGraphNodeId(idPrefixForNodeType(n.type)));
  }

  const nodes = translateNodes(
    payload.nodes.map((n) => {
      const nid = idMap.get(n.id);
      if (!nid) {
        return n;
      }
      return {
        ...n,
        id: nid,
        selected: true,
      };
    }),
  );

  const edges: Edge[] = payload.edges.map((e) => {
    const ns = idMap.get(e.source);
    const nt = idMap.get(e.target);
    if (!ns || !nt) {
      return { ...e, id: newGraphNodeId("e") };
    }
    const sh = typeof e.sourceHandle === "string" ? e.sourceHandle : "";
    const th = typeof e.targetHandle === "string" ? e.targetHandle : "";
    const dk =
      e.data && typeof e.data === "object" && "domainKind" in e.data
        ? String((e.data as { domainKind?: string }).domainKind)
        : "";
    const nextId = `e-${ns}-${nt}-${dk || "edge"}-${sh}_${th}-${newGraphNodeId("x").slice(-6)}`;
    return {
      ...e,
      id: nextId,
      source: ns,
      target: nt,
      selected: false,
    };
  });

  return { nodes, edges };
}

export function flowViewportCenterFlowCoords(
  paneSelector: string,
  screenToFlowPosition: (p: { x: number; y: number }) => { x: number; y: number },
): { x: number; y: number } | null {
  const pane = document.querySelector(paneSelector) as HTMLElement | null;
  if (!pane) {
    return null;
  }
  const r = pane.getBoundingClientRect();
  return screenToFlowPosition({
    x: r.left + r.width / 2,
    y: r.top + r.height / 2,
  });
}

export function translateNodesToFlowPoint(nodes: Node[], cx: number, cy: number): Node[] {
  if (nodes.length === 0) {
    return nodes;
  }
  let sx = 0;
  let sy = 0;
  for (const n of nodes) {
    const px = typeof n.position?.x === "number" ? n.position.x : 0;
    const py = typeof n.position?.y === "number" ? n.position.y : 0;
    sx += px;
    sy += py;
  }
  const n = nodes.length;
  const mx = sx / n;
  const my = sy / n;
  const dx = cx - mx;
  const dy = cy - my;
  return nodes.map((node) => {
    const px = typeof node.position?.x === "number" ? node.position.x : 0;
    const py = typeof node.position?.y === "number" ? node.position.y : 0;
    return {
      ...node,
      position: { x: px + dx, y: py + dy },
    };
  });
}

export function mergeEdgesWithPainterFix(nodes: Node[], edges: Edge[]): Edge[] {
  return ensurePainterTargetHandlesOnEdges(nodes, edges).map((e) => ({
    ...e,
    type: e.type ?? "recipe",
  }));
}

export type RecipeGraphClipboardShortcutDeps = Readonly<{
  selectedNodeIds: readonly string[];
  nodesRef: RefBox<Node[]>;
  edgesRef: RefBox<Edge[]>;
  lastPayloadRef: RefBox<RecipeGraphClipboardPayload | null>;
  setNodes: Dispatch<SetStateAction<Node[]>>;
  setEdges: Dispatch<SetStateAction<Edge[]>>;
  onNodesChange: (changes: NodeChange[]) => void;
  enrichNodesWithIcons: (nodes: Node[]) => Node[];
  silentDryRunFromGraph: (nodes: Node[], edges: Edge[]) => void;
  newGraphNodeId: (prefix: string) => string;
  screenToFlowPosition: (p: { x: number; y: number }) => { x: number; y: number };
}>;

export type RecipeGraphClipboardShortcutDepsNoScreen = Omit<
  RecipeGraphClipboardShortcutDeps,
  "screenToFlowPosition"
>;

const CANVAS_PANE = ".rf-editor-canvas .react-flow";

type PasteShortcutCtx = Pick<
  RecipeGraphClipboardShortcutDeps,
  | "lastPayloadRef"
  | "screenToFlowPosition"
  | "newGraphNodeId"
  | "setNodes"
  | "setEdges"
  | "edgesRef"
  | "enrichNodesWithIcons"
  | "silentDryRunFromGraph"
>;

function schedulePasteSideEffects(
  nextNodes: Node[],
  nextEdges: Edge[],
  setEdges: Dispatch<SetStateAction<Edge[]>>,
  silentDryRunFromGraph: (nodes: Node[], edges: Edge[]) => void,
): void {
  queueMicrotask(() => {
    setEdges(nextEdges);
    silentDryRunFromGraph(nextNodes, nextEdges);
  });
}

type MergePastedSubgraphParams = Readonly<{
  curr: Node[];
  pastedRaw: Node[];
  pastedEdges: Edge[];
  edgesRef: RefBox<Edge[]>;
  enrichNodesWithIcons: (nodes: Node[]) => Node[];
  newGraphNodeId: (prefix: string) => string;
  setEdges: Dispatch<SetStateAction<Edge[]>>;
  silentDryRunFromGraph: (nodes: Node[], edges: Edge[]) => void;
}>;

function mergePastedSubgraphIntoNodes(p: MergePastedSubgraphParams): Node[] {
  const {
    curr,
    pastedRaw,
    pastedEdges,
    edgesRef,
    enrichNodesWithIcons,
    newGraphNodeId,
    setEdges,
    silentDryRunFromGraph,
  } = p;
  const cleared = curr.map((n) => ({ ...n, selected: false }));
  let nextNodes: Node[] = [...cleared, ...pastedRaw];
  let nextEdges = [...edgesRef.current, ...pastedEdges];
  nextEdges = mergeEdgesWithPainterFix(nextNodes, nextEdges);

  for (const n of pastedRaw) {
    if (n.type === "operation") {
      const syn = ensureOperationOutputArtifacts(
        nextNodes,
        nextEdges,
        n.id,
        newGraphNodeId,
      );
      nextNodes = syn.nodes;
      nextEdges = syn.edges;
    }
  }

  nextNodes = enrichNodesWithIcons(nextNodes);
  schedulePasteSideEffects(nextNodes, nextEdges, setEdges, silentDryRunFromGraph);
  return nextNodes;
}

async function runRecipeGraphPaste(ctx: PasteShortcutCtx): Promise<void> {
  let raw = "";
  try {
    raw = await navigator.clipboard.readText();
  } catch {
    raw = "";
  }
  const parsed = tryParseRecipeGraphClipboard(raw) ?? ctx.lastPayloadRef.current;
  if (!parsed) {
    return;
  }

  const center = flowViewportCenterFlowCoords(CANVAS_PANE, ctx.screenToFlowPosition);
  const cx = center?.x ?? 200;
  const cy = center?.y ?? 160;

  const { nodes: pastedRaw, edges: pastedEdges } = remapClipboardPayloadForPaste(
    parsed,
    ctx.newGraphNodeId,
    (nodes) => translateNodesToFlowPoint(nodes, cx, cy),
  );

  ctx.setNodes((curr) =>
    mergePastedSubgraphIntoNodes({
      curr,
      pastedRaw,
      pastedEdges,
      edgesRef: ctx.edgesRef,
      enrichNodesWithIcons: ctx.enrichNodesWithIcons,
      newGraphNodeId: ctx.newGraphNodeId,
      setEdges: ctx.setEdges,
      silentDryRunFromGraph: ctx.silentDryRunFromGraph,
    }),
  );
}

function targetIsEditable(elt: EventTarget | null): boolean {
  const el = elt as HTMLElement | null;
  if (!el) {
    return false;
  }
  if (el.isContentEditable) {
    return true;
  }
  const tag = el.tagName;
  if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") {
    return true;
  }
  return Boolean(el.closest("[contenteditable='true']"));
}

export function useRecipeGraphClipboardShortcuts(deps: RecipeGraphClipboardShortcutDeps): void {
  const {
    selectedNodeIds,
    nodesRef,
    edgesRef,
    lastPayloadRef,
    setNodes,
    setEdges,
    onNodesChange,
    enrichNodesWithIcons,
    silentDryRunFromGraph,
    newGraphNodeId,
    screenToFlowPosition,
  } = deps;

  useEffect(() => {
    const copyOrCut = (cut: boolean) => {
      const sel = new Set(selectedNodeIds);
      const payload = buildSubgraphClipboardPayload(sel, nodesRef.current, edgesRef.current);
      if (!payload) {
        return;
      }
      lastPayloadRef.current = payload;
      const text = serializeRecipeGraphClipboard(payload);
      navigator.clipboard.writeText(text).catch(() => {});
      if (cut) {
        const removeChanges: NodeChange[] = selectedNodeIds.map((id) => ({ type: "remove", id }));
        onNodesChange(removeChanges);
      }
    };

    const paste = () => {
      runRecipeGraphPaste({
        lastPayloadRef,
        screenToFlowPosition,
        newGraphNodeId,
        setNodes,
        setEdges,
        edgesRef,
        enrichNodesWithIcons,
        silentDryRunFromGraph,
      }).catch(() => {});
    };

    const onKeyDown = (e: KeyboardEvent) => {
      if (!e.ctrlKey && !e.metaKey) {
        return;
      }
      if (targetIsEditable(e.target)) {
        return;
      }
      const code = e.code;
      if (code === "KeyX") {
        e.preventDefault();
        copyOrCut(true);
        return;
      }
      if (code === "KeyC") {
        e.preventDefault();
        copyOrCut(false);
        return;
      }
      if (code === "KeyV") {
        e.preventDefault();
        paste();
      }
    };

    globalThis.addEventListener("keydown", onKeyDown);
    return () => {
      globalThis.removeEventListener("keydown", onKeyDown);
    };
  }, [
    enrichNodesWithIcons,
    lastPayloadRef,
    newGraphNodeId,
    nodesRef,
    edgesRef,
    onNodesChange,
    screenToFlowPosition,
    selectedNodeIds,
    setEdges,
    setNodes,
    silentDryRunFromGraph,
  ]);
}
