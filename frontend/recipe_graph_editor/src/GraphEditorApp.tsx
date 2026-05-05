import {
  addEdge,
  applyNodeChanges,
  Background,
  BackgroundVariant,
  Controls,
  MiniMap,
  ReactFlow,
  ReactFlowProvider,
  useEdgesState,
  useNodesState,
  useReactFlow,
  type Connection,
  type Edge,
  type IsValidConnection,
  type Node,
  type NodeChange,
} from "@xyflow/react";
import {
  useCallback,
  useEffect,
  useLayoutEffect,
  useMemo,
  useRef,
  useState,
  type DragEvent,
  type MutableRefObject,
} from "react";

import { InspectorNodeProperties } from "./InspectorNodeProperties";
import { NodeEditModal } from "./NodeEditModal";
import { postRecipeGraphRecompute, type RecipeGraphRecomputeResponse } from "./recipeGraphApi";
import { ensureOperationOutputArtifacts } from "./operationOutputStaging";
import {
  catalogIconByValue,
  enrichNodesWithCatalogIcons,
  type CatalogOperationRow,
} from "./recipeNodeCatalogMerge";
import {
  connectionToRecipeEdge,
  evaluateRecipeConnection,
  getRecipeConnectEdgeRemovals,
  isMaterialToOperationConnection,
  wouldConnectAfterRemovals,
} from "./recipeConnection";
import { recipeEdgeTypes } from "./recipeFlowEdges";
import { recipeNodeTypes } from "./recipeFlowNodes";
import { PALETTE_CATEGORY_ORDER, paletteCategoryForOperation } from "./operationPaletteGroups";
import { buildReactFlowSnapshot } from "./reactFlowSnapshot";
import { layoutNodesInColumns } from "./recipeGraphAutoLayout";
import { cleanupAfterNodeRemovals } from "./recipeGraphNodeCleanup";
import { loadRecipeNotes, saveRecipeNotes } from "./recipeGraphNotesStorage";
import { applyValidationIssuesToNodes } from "./validationIssuesNodes";
import { ru } from "./recipeUiStrings";

/** 새 소스 자재 노드에 넣을 기본 shape 코드. */
const DEFAULT_NEW_SOURCE_SHAPE_CODE = "CuCuCuCu";

/** 순색 유체 자리표시자(균일 단색으로 편집). */
const DEFAULT_NEW_FLUID_SHAPE_CODE = "CuCuCuCu";

/** ``recipeFlowNodes`` 타일 ``h-14 w-14`` (56px) 절반 — 뷰포트 중앙에 노드 중심을 맞출 때 보정. */
const RECIPE_NODE_TILE_HALF_PX = 28;

/** 팔레트 → React Flow 캔버스 커스텀 DnD MIME (브라우저 호환용 짧은 타입). */
const RECIPE_PALETTE_DND_OP = "application/x-shapez-recipe-graph-op";
const RECIPE_PALETTE_DND_SRC = "application/x-shapez-recipe-graph-src";
const RECIPE_PALETTE_DND_FLUID = "application/x-shapez-recipe-graph-fluid";

export type ReactFlowInitialPayload = {
  version: number;
  nodes: Node[];
  edges: Edge[];
};

export type GraphBootstrap = {
  api_recipe_graph_recompute?: string;
  staff_catalog_url?: string;
  staff_recipe_edit_url?: string;
  react_flow_initial?: ReactFlowInitialPayload | null;
  react_flow_initial_status?: "ok" | "missing" | "invalid";
  macro_step_count?: number;
};

export type { CatalogOperationRow } from "./recipeNodeCatalogMerge";

type GraphEditorAppProps = {
  recipeId: number;
  recipeCode: string;
  recipeName: string;
  bootstrap: GraphBootstrap | null;
  initialNodes: Node[];
  initialEdges: Edge[];
  catalogOperations: CatalogOperationRow[];
  engineOperationIds: readonly string[];
};

function reactFlowEmptyHint(
  bootstrap: GraphBootstrap | null,
  nodeCount: number,
): string | null {
  if (nodeCount > 0) {
    return null;
  }
  const st = bootstrap?.react_flow_initial_status;
  if (st === "invalid") {
    return ru("rfInvalidDoc");
  }
  const steps = bootstrap?.macro_step_count;
  if (typeof steps === "number" && steps > 0) {
    return ru("rfEmptyWithSteps");
  }
  return ru("rfEmptyDefault");
}

function setGlobalStatus(msg: string, isError: boolean) {
  const el = document.getElementById("macro-graph-status");
  if (!el) {
    return;
  }
  el.textContent = msg;
  el.classList.toggle("text-rose-300", isError);
  el.classList.toggle("text-amber-200/90", !isError && Boolean(msg));
}

type OperationPalettePanelProps = {
  operations: CatalogOperationRow[];
  engineOperationIds: readonly string[];
  onAddOperation: (operation: string) => void;
  onAddSourceShape: () => void;
  onAddFluidSource: () => void;
};

function newGraphNodeId(prefix: string): string {
  return `${prefix}-${Date.now().toString(36)}-${Math.random().toString(36).slice(2, 7)}`;
}

function paletteGridPosition(index: number): { x: number; y: number } {
  const col = index % 4;
  const row = Math.floor(index / 4);
  return { x: 48 + col * 200, y: 52 + row * 120 };
}

function OperationPalettePanel({
  engineOperationIds,
  onAddFluidSource,
  onAddOperation,
  onAddSourceShape,
  operations,
}: OperationPalettePanelProps) {
  const [query, setQuery] = useState("");
  const engineSet = useMemo(() => new Set(engineOperationIds), [engineOperationIds]);

  const grouped = useMemo(() => {
    const q = query.trim().toLowerCase();
    const filtered = q
      ? operations.filter(
          (o) =>
            o.value.toLowerCase().includes(q) ||
            (o.label && o.label.toLowerCase().includes(q)),
        )
      : operations;
    const map = new Map<string, CatalogOperationRow[]>();
    for (const cat of PALETTE_CATEGORY_ORDER) {
      if (cat !== "SHAPE") {
        map.set(cat, []);
      }
    }
    for (const o of filtered) {
      const cat = paletteCategoryForOperation(o.value);
      const list = map.get(cat);
      if (list) {
        list.push(o);
      }
    }
    return map;
  }, [operations, query]);

  return (
    <aside
      aria-label="Operation palette"
      className="flex min-h-0 flex-col gap-2 overflow-hidden rounded-lg border border-slate-700 bg-slate-950/90"
    >
      <div className="shrink-0 border-b border-slate-800 p-2">
        <label className="sr-only" htmlFor="op-search">
          Search operations
        </label>
        <input
          className="w-full rounded border border-slate-600 bg-slate-900 px-2 py-1.5 font-mono text-xs text-slate-100 placeholder:text-slate-500"
          id="op-search"
          onChange={(e) => {
            setQuery(e.target.value);
          }}
          placeholder={ru("paletteSearchPh")}
          type="search"
          value={query}
        />
      </div>
      <div className="min-h-0 flex-1 space-y-3 overflow-y-auto p-2">
        <div>
          <p className="mb-1.5 font-mono text-[10px] font-semibold uppercase tracking-wider text-cyan-400/90">
            SHAPE
          </p>
          <ul className="space-y-1">
            <li>
              <button
                className="w-full rounded border border-cyan-800/50 bg-slate-900/80 px-2 py-1.5 text-left text-xs text-cyan-100/90 hover:border-cyan-500/50"
                draggable
                type="button"
                onClick={onAddSourceShape}
                onDragStart={(e) => {
                  e.dataTransfer.setData(RECIPE_PALETTE_DND_SRC, "1");
                  e.dataTransfer.effectAllowed = "copy";
                }}
              >
                <span className="font-mono text-slate-500">◇</span> {ru("emptySourceRow")}
                <span className="mt-0.5 block text-[10px] text-slate-500">
                  {ru("emptySourceHint", { code: DEFAULT_NEW_SOURCE_SHAPE_CODE })}
                </span>
              </button>
            </li>
            <li>
              <button
                className="w-full rounded border border-cyan-800/50 bg-slate-900/80 px-2 py-1.5 text-left text-xs text-cyan-100/90 hover:border-cyan-500/50"
                draggable
                type="button"
                onClick={onAddFluidSource}
                onDragStart={(e) => {
                  e.dataTransfer.setData(RECIPE_PALETTE_DND_FLUID, "1");
                  e.dataTransfer.effectAllowed = "copy";
                }}
              >
                <span className="font-mono text-slate-500">◇</span> {ru("emptyFluidRow")}
                <span className="mt-0.5 block text-[10px] text-slate-500">
                  {ru("emptyFluidHint", { code: DEFAULT_NEW_FLUID_SHAPE_CODE })}
                </span>
              </button>
            </li>
          </ul>
        </div>
        {PALETTE_CATEGORY_ORDER.filter((c) => c !== "SHAPE").map((cat) => {
          const rows = grouped.get(cat) ?? [];
          return (
            <div key={cat}>
              <p className="mb-1.5 font-mono text-[10px] font-semibold uppercase tracking-wider text-cyan-400/90">
                {cat}
              </p>
              {rows.length === 0 ? (
                <p className="text-[10px] text-slate-600">—</p>
              ) : (
                <ul className="space-y-1">
                  {rows.map((o) => {
                    const enabled = engineSet.has(o.value);
                    return (
                      <li key={o.value}>
                        <button
                          className={[
                            "flex w-full items-center gap-2 rounded border px-2 py-1.5 text-left text-xs",
                            enabled
                              ? "border-slate-700 bg-slate-900/80 text-slate-200 hover:border-cyan-600/40"
                              : "cursor-not-allowed border-slate-800/80 bg-slate-950/50 text-slate-600",
                          ].join(" ")}
                          disabled={!enabled}
                          title={
                            enabled
                              ? ru("opRowHintGridDrag", { value: o.value })
                              : ru("opNotInEngine")
                          }
                          type="button"
                          draggable={enabled}
                          onClick={() => {
                            if (enabled) {
                              onAddOperation(o.value);
                            }
                          }}
                          onDragStart={(e) => {
                            if (!enabled) {
                              e.preventDefault();
                              return;
                            }
                            e.dataTransfer.setData(RECIPE_PALETTE_DND_OP, o.value);
                            e.dataTransfer.effectAllowed = "copy";
                          }}
                        >
                          {o.icon ? (
                            <img
                              alt=""
                              className="h-6 w-6 shrink-0 rounded border border-slate-700 bg-slate-900 object-contain"
                              height={24}
                              src={o.icon}
                              width={24}
                            />
                          ) : (
                            <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded border border-slate-700 font-mono text-[10px] text-slate-500">
                              ◇
                            </span>
                          )}
                          <span className="min-w-0 flex-1 truncate font-mono text-[11px]">{o.label}</span>
                        </button>
                      </li>
                    );
                  })}
                </ul>
              )}
            </div>
          );
        })}
        {operations.length === 0 ? (
          <p className="text-[11px] leading-snug text-amber-200/80">
            {ru("catalogLoadError")}
          </p>
        ) : null}
      </div>
      <div className="shrink-0 border-t border-dashed border-slate-700 p-2">
        <p className="font-mono text-[10px] uppercase tracking-wider text-amber-300/80">
          Quick access
        </p>
        <p className="mt-1 text-[11px] leading-snug text-slate-500">{ru("paletteHelpP1")}</p>
      </div>
    </aside>
  );
}

function OutputsColumn() {
  return (
    <aside
      aria-label="Outputs"
      className="flex min-h-0 flex-col gap-2 overflow-hidden rounded-lg border border-slate-700 bg-slate-950/90 p-2"
    >
      <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.2em] text-purple-300/90">
        Outputs
      </p>
      <div className="flex-1 space-y-2 overflow-y-auto rounded border border-slate-800 bg-slate-900/50 p-2">
        <div className="rounded border border-orange-500/40 bg-slate-900 px-2 py-2 text-xs text-slate-200">
          <span className="font-mono text-[10px] text-orange-300/90">Output 1</span>
          <p className="mt-1 text-[11px] text-slate-500">Terminal (placeholder)</p>
        </div>
      </div>
    </aside>
  );
}

type RecipeFlowBoardProps = {
  nodes: Node[];
  edges: Edge[];
  onNodesChange: ReturnType<typeof useNodesState>[2];
  onEdgesChange: ReturnType<typeof useEdgesState>[2];
  isValidConnection: IsValidConnection;
  onConnect: (c: Connection) => void;
  onNodeDoubleClick: (_event: unknown, node: Node) => void;
  onSelectionChange: (p: { nodes: Node[]; edges: Edge[] }) => void;
  onDropOperationFromPalette: (operation: string, position: { x: number; y: number }) => void;
  onDropSourceFromPalette: (position: { x: number; y: number }) => void;
  onDropFluidFromPalette: (position: { x: number; y: number }) => void;
  getViewportCenterFlowRef: MutableRefObject<(() => { x: number; y: number }) | null>;
};

function RecipeFlowBoard({
  edges,
  getViewportCenterFlowRef,
  isValidConnection,
  nodes,
  onConnect,
  onDropFluidFromPalette,
  onDropOperationFromPalette,
  onDropSourceFromPalette,
  onEdgesChange,
  onNodeDoubleClick,
  onNodesChange,
  onSelectionChange,
}: RecipeFlowBoardProps) {
  const nodeTypes = useMemo(() => recipeNodeTypes, []);
  const edgeTypes = useMemo(() => recipeEdgeTypes, []);
  const { screenToFlowPosition } = useReactFlow();

  useLayoutEffect(() => {
    getViewportCenterFlowRef.current = () => {
      const pane = document.querySelector(".rf-editor-canvas .react-flow") as HTMLElement | null;
      if (!pane) {
        return { x: 200, y: 160 };
      }
      const r = pane.getBoundingClientRect();
      const p = screenToFlowPosition({
        x: r.left + r.width / 2,
        y: r.top + r.height / 2,
      });
      return {
        x: p.x - RECIPE_NODE_TILE_HALF_PX,
        y: p.y - RECIPE_NODE_TILE_HALF_PX,
      };
    };
    return () => {
      getViewportCenterFlowRef.current = null;
    };
  }, [getViewportCenterFlowRef, screenToFlowPosition]);

  const onDragOver = useCallback((e: DragEvent) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = "copy";
  }, []);

  const onDrop = useCallback(
    (e: DragEvent) => {
      e.preventDefault();
      const op = e.dataTransfer.getData(RECIPE_PALETTE_DND_OP);
      if (op) {
        onDropOperationFromPalette(op, screenToFlowPosition({ x: e.clientX, y: e.clientY }));
        return;
      }
      if (e.dataTransfer.getData(RECIPE_PALETTE_DND_SRC) === "1") {
        onDropSourceFromPalette(screenToFlowPosition({ x: e.clientX, y: e.clientY }));
        return;
      }
      if (e.dataTransfer.getData(RECIPE_PALETTE_DND_FLUID) === "1") {
        onDropFluidFromPalette(screenToFlowPosition({ x: e.clientX, y: e.clientY }));
      }
    },
    [onDropFluidFromPalette, onDropOperationFromPalette, onDropSourceFromPalette, screenToFlowPosition],
  );

  return (
    <ReactFlow
      connectionRadius={56}
      defaultEdgeOptions={{ type: "recipe", style: { strokeWidth: 1.6 } }}
      defaultViewport={{ x: 0, y: 0, zoom: 1 }}
      deleteKeyCode={["Backspace", "Delete"]}
      edgeTypes={edgeTypes}
      edges={edges}
      fitView
      isValidConnection={isValidConnection}
      maxZoom={1.8}
      minZoom={0.2}
      nodeTypes={nodeTypes}
      nodes={nodes}
      onConnect={onConnect}
      onDragOver={onDragOver}
      onDrop={onDrop}
      onEdgesChange={onEdgesChange}
      onNodeDoubleClick={onNodeDoubleClick}
      onNodesChange={onNodesChange}
      onSelectionChange={onSelectionChange}
      proOptions={{ hideAttribution: true }}
    >
      <Background color="#444" gap={16} variant={BackgroundVariant.Dots} />
      <Controls className="m-2! border-slate-600! bg-slate-900/95! shadow-lg!" />
      <MiniMap
        className="m-2! border-slate-600! bg-slate-900/90!"
        maskColor="rgb(15 15 15 / 0.7)"
        pannable
        zoomable
      />
    </ReactFlow>
  );
}

type GraphCanvasPanelProps = {
  nodes: Node[];
  edges: Edge[];
  onNodesChange: ReturnType<typeof useNodesState>[2];
  onEdgesChange: ReturnType<typeof useEdgesState>[2];
  isValidConnection: IsValidConnection;
  onConnect: (c: Connection) => void;
  emptyHint: string | null;
  onPatchNodeData: (nodeId: string, patch: Record<string, unknown>) => void;
  onSelectionChange: (params: { nodes: Node[] }) => void;
  onDropOperationFromPalette: (operation: string, position: { x: number; y: number }) => void;
  onDropSourceFromPalette: (position: { x: number; y: number }) => void;
  onDropFluidFromPalette: (position: { x: number; y: number }) => void;
  onAutoArrange: () => void;
  catalogOperations: CatalogOperationRow[];
  engineOperationIds: readonly string[];
  getViewportCenterFlowRef: MutableRefObject<(() => { x: number; y: number }) | null>;
};

function GraphCanvasPanel({
  catalogOperations,
  edges,
  emptyHint,
  engineOperationIds,
  getViewportCenterFlowRef,
  isValidConnection,
  nodes,
  onConnect,
  onDropFluidFromPalette,
  onDropOperationFromPalette,
  onDropSourceFromPalette,
  onAutoArrange,
  onEdgesChange,
  onNodesChange,
  onPatchNodeData,
  onSelectionChange,
}: GraphCanvasPanelProps) {
  const canvasRef = useRef<HTMLDivElement>(null);
  const [editModal, setEditModal] = useState<{ nodeId: string; left: number; top: number } | null>(
    null,
  );

  const editingNode = useMemo(
    () => (editModal ? nodes.find((n) => n.id === editModal.nodeId) : undefined),
    [editModal, nodes],
  );

  const closeModal = useCallback(() => {
    setEditModal(null);
  }, []);

  const handleApplyPatch = useCallback(
    (patch: Record<string, unknown>) => {
      if (!editModal) {
        return;
      }
      onPatchNodeData(editModal.nodeId, patch);
      setEditModal(null);
    },
    [editModal, onPatchNodeData],
  );

  const relaySelectionChange = useCallback(
    (p: { nodes: Node[]; edges: Edge[] }) => {
      onSelectionChange({ nodes: p.nodes });
    },
    [onSelectionChange],
  );

  const onNodeDoubleClick = useCallback(
    (_event: unknown, node: Node) => {
      const root = canvasRef.current;
      if (!root) {
        return;
      }
      const escaped =
        typeof CSS !== "undefined" && typeof CSS.escape === "function"
          ? CSS.escape(node.id)
          : node.id.replace(/\\/g, "\\\\").replace(/"/g, '\\"');
      const target = root.querySelector(
        `.react-flow__node[data-id="${escaped}"]`,
      ) as HTMLElement | null;
      if (!target) {
        return;
      }
      const cr = root.getBoundingClientRect();
      const nr = target.getBoundingClientRect();
      const left = nr.left - cr.left + nr.width / 2;
      const top = nr.top - cr.top;
      setEditModal({ nodeId: node.id, left, top });
    },
    [],
  );

  return (
    <section
      aria-label="Recipe graph canvas"
      className="relative flex min-h-0 min-w-0 flex-col overflow-hidden rounded-lg border border-slate-700 bg-slate-950"
    >
      <div className="z-10 flex shrink-0 flex-wrap items-center gap-2 border-b border-slate-800 bg-slate-900/95 px-2 py-1.5 font-mono text-[11px] text-slate-400">
        <span className="text-slate-500">Wire shapes into operations; outputs on the right.</span>
        <span className="grow" />
        <label className="flex cursor-pointer items-center gap-1">
          <input className="accent-cyan-500" defaultChecked type="checkbox" /> Grid
        </label>
        <label className="flex cursor-pointer items-center gap-1">
          <input className="accent-cyan-500" defaultChecked type="checkbox" /> Snap
        </label>
        <span className="text-cyan-400/90">100%</span>
        <button
          className="rounded border border-cyan-700/50 px-2 py-0.5 text-cyan-100/95 hover:border-cyan-500/60"
          type="button"
          onClick={onAutoArrange}
        >
          Auto arrange
        </button>
      </div>
      <div className="rf-editor-canvas relative min-h-0 flex-1" ref={canvasRef}>
        {emptyHint ? (
          <div
            aria-live="polite"
            className="pointer-events-none absolute inset-0 z-6 flex items-center justify-center p-6"
          >
            <div className="max-w-md rounded-lg border border-amber-600/40 bg-slate-950/90 px-4 py-3 text-center text-sm leading-relaxed text-amber-100/95 shadow-xl backdrop-blur-sm">
              {emptyHint}
            </div>
          </div>
        ) : null}
        <ReactFlowProvider>
          <RecipeFlowBoard
            edges={edges}
            getViewportCenterFlowRef={getViewportCenterFlowRef}
            isValidConnection={isValidConnection}
            nodes={nodes}
            onConnect={onConnect}
            onDropFluidFromPalette={onDropFluidFromPalette}
            onDropOperationFromPalette={onDropOperationFromPalette}
            onDropSourceFromPalette={onDropSourceFromPalette}
            onEdgesChange={onEdgesChange}
            onNodeDoubleClick={onNodeDoubleClick}
            onNodesChange={onNodesChange}
            onSelectionChange={relaySelectionChange}
          />
        </ReactFlowProvider>
        {editingNode && editModal ? (
          <NodeEditModal
            anchor={{ left: editModal.left, top: editModal.top }}
            catalogOperations={catalogOperations}
            engineOperationIds={engineOperationIds}
            node={editingNode}
            onApply={handleApplyPatch}
            onClose={closeModal}
          />
        ) : null}
      </div>
      <div className="pointer-events-none absolute left-3 top-12 z-5 max-w-[55%] rounded border border-purple-500/30 bg-purple-950/40 px-2 py-1 font-mono text-[10px] text-purple-200/90">
        Stage track (visual group) — placeholder
      </div>
    </section>
  );
}

type InspectorStripProps = {
  validationOk: boolean | null;
  footerHint: string;
  connectionFeedback: string;
  nodeCount: number;
  edgeCount: number;
  outputCount: number;
  selectedNodeIds: string[];
  nodes: Node[];
  onPatchNodeData: (nodeId: string, patch: Record<string, unknown>) => void;
  notes: string;
  onNotesChange: (text: string) => void;
};

function InspectorStrip({
  connectionFeedback,
  edgeCount,
  footerHint,
  nodeCount,
  nodes,
  notes,
  onNotesChange,
  onPatchNodeData,
  outputCount,
  selectedNodeIds,
  validationOk,
}: InspectorStripProps) {
  const firstSel = useMemo(() => {
    const id = selectedNodeIds[0];
    return id ? nodes.find((n) => n.id === id) : undefined;
  }, [nodes, selectedNodeIds]);

  const selectedSummary =
    selectedNodeIds.length === 0
      ? ru("selNone")
      : selectedNodeIds.length === 1
        ? ru("selOne", { id: selectedNodeIds[0] })
        : ru("selMulti", { n: selectedNodeIds.length });

  const propertiesSummary = useMemo(() => {
    if (selectedNodeIds.length === 0) {
      return ru("summaryPickNode");
    }
    if (selectedNodeIds.length > 1) {
      return ru("summaryMultiEdit");
    }
    const n = firstSel;
    if (!n) {
      return "—";
    }
    const t = n.type ?? "?";
    const d =
      n.data && typeof n.data === "object" && !Array.isArray(n.data)
        ? (n.data as Record<string, unknown>)
        : {};
    if (t === "operation") {
      return ru("kindSummaryOp", { op: String(d.operation ?? "?") });
    }
    if (t === "shape") {
      return ru("kindSummarySource", { role: String(d.role ?? "?") });
    }
    if (t === "intermediate") {
      const code = String(d.shape_code ?? "");
      return code
        ? ru("kindSummaryMidCode", { code: code.slice(0, 36) })
        : ru("kindSummaryMidEmpty");
    }
    if (t === "output") {
      const code = String(d.shape_code ?? "");
      return code
        ? ru("kindSummaryTargetCode", { code: code.slice(0, 36) })
        : ru("kindSummaryTargetEmpty");
    }
    return ru("kindUnknown", { t });
  }, [firstSel, selectedNodeIds.length]);

  const validationSummary =
    validationOk === null
      ? ru("validationPrompt")
      : validationOk
        ? ru("validationOk")
        : ru("validationIssues");

  const validationClass =
    validationOk === null
      ? "text-slate-500"
      : validationOk
        ? "text-emerald-300/85"
        : "text-rose-300/90";

  return (
    <div
      aria-label="Inspector"
      className="grid shrink-0 grid-cols-5 gap-2 border-t border-slate-800 pt-2"
    >
      <div className="min-h-[72px] rounded border border-slate-700 bg-slate-950/80 p-2">
        <p className="font-mono text-[10px] font-semibold uppercase tracking-wider text-slate-500">
          Selected
        </p>
        <p className="mt-1 text-[11px] leading-snug text-slate-300">{selectedSummary}</p>
      </div>
      <div className="max-h-44 min-h-[72px] overflow-y-auto rounded border border-slate-700 bg-slate-950/80 p-2">
        <p className="font-mono text-[10px] font-semibold uppercase tracking-wider text-slate-500">
          Properties
        </p>
        {selectedNodeIds.length === 1 && firstSel ? (
          <InspectorNodeProperties node={firstSel} onPatch={onPatchNodeData} />
        ) : (
          <p className="mt-1 text-[11px] leading-snug text-slate-400">{propertiesSummary}</p>
        )}
      </div>
      <div className="min-h-[72px] rounded border border-slate-700 bg-slate-950/80 p-2">
        <p className="font-mono text-[10px] font-semibold uppercase tracking-wider text-slate-500">
          Validation
        </p>
        <p className={`mt-1 text-[11px] leading-snug ${validationClass}`}>{validationSummary}</p>
        {connectionFeedback ? (
          <p className="mt-1 border-t border-slate-800 pt-1 text-[11px] leading-snug text-amber-200/90">
            {ru("connFeedback")} {connectionFeedback}
          </p>
        ) : footerHint ? (
          <p className="mt-1 text-[10px] leading-snug text-slate-500">{footerHint}</p>
        ) : null}
      </div>
      <div className="min-h-[72px] rounded border border-slate-700 bg-slate-950/80 p-2">
        <p className="font-mono text-[10px] font-semibold uppercase tracking-wider text-slate-500">
          Stats
        </p>
        <p className="mt-1 font-mono text-[11px] leading-snug text-slate-400">
          {ru("statsLine", { nodeCount, edgeCount, outputCount })}
        </p>
      </div>
      <div className="flex min-h-[72px] flex-col rounded border border-slate-700 bg-slate-950/80 p-2">
        <label className="font-mono text-[10px] font-semibold uppercase tracking-wider text-slate-500" htmlFor="inspector-notes">
          Notes
        </label>
        <textarea
          className="mt-1 min-h-[52px] w-full flex-1 resize-y rounded border border-slate-700 bg-slate-900 px-1.5 py-1 font-mono text-[10px] leading-snug text-slate-300 placeholder:text-slate-600"
          id="inspector-notes"
          onChange={(e) => {
            onNotesChange(e.target.value);
          }}
          placeholder={ru("notesPlaceholder")}
          spellCheck={true}
          value={notes}
        />
        <p className="mt-0.5 text-[9px] text-slate-600">
          {ru("notesFooter")}
        </p>
      </div>
    </div>
  );
}

type FooterActionsProps = {
  busy: boolean;
  validationOk: boolean | null;
  footerHint: string;
  onDryRun: () => void;
  onSave: () => void;
};

function FooterActions({ busy, footerHint, onDryRun, onSave, validationOk }: FooterActionsProps) {
  const validLabel =
    validationOk === null ? "—" : validationOk ? "Graph is valid" : "Graph has issues";
  const validClass =
    validationOk === null
      ? "text-slate-500"
      : validationOk
        ? "text-emerald-400/90"
        : "text-rose-300/90";

  return (
    <footer className="flex shrink-0 flex-wrap items-center justify-between gap-2 border-t border-slate-800 pt-2 font-mono text-xs">
      <div className="flex flex-wrap gap-2">
        <button
          className="rounded border border-slate-600 px-3 py-1.5 text-slate-200 hover:border-slate-500 disabled:opacity-40"
          disabled={busy}
          onClick={onDryRun}
          type="button"
        >
          Recompute (dry-run)
        </button>
        <button
          className="rounded border border-amber-600/50 bg-amber-950/40 px-3 py-1.5 font-semibold text-amber-100 hover:border-amber-500/70 disabled:opacity-40"
          disabled={busy}
          onClick={onSave}
          type="button"
        >
          Recompute &amp; save graph
        </button>
      </div>
      <div className="max-w-[42%] text-center text-[11px] text-slate-500">
        <span className={validClass}>{validLabel}</span>
        {footerHint ? (
          <>
            <span className="mx-2 text-slate-600">·</span>
            <span className="text-slate-400">{footerHint}</span>
          </>
        ) : null}
      </div>
      <div className="flex flex-wrap gap-2">
        <button
          className="rounded border border-cyan-700/50 px-3 py-1.5 text-cyan-100 hover:border-cyan-500/60 disabled:opacity-40"
          disabled
          type="button"
        >
          + Add output
        </button>
        <button
          className="rounded border border-red-900/50 px-3 py-1.5 text-red-200/90 hover:border-red-700/60 disabled:opacity-40"
          disabled
          type="button"
        >
          Clear canvas
        </button>
      </div>
    </footer>
  );
}

export function GraphEditorApp({
  recipeId,
  recipeCode,
  recipeName,
  bootstrap,
  initialEdges,
  initialNodes,
  catalogOperations,
  engineOperationIds,
}: GraphEditorAppProps) {
  const catalogHref = bootstrap?.staff_catalog_url ?? "#";
  const editHref = bootstrap?.staff_recipe_edit_url ?? "#";
  const recomputeUrl = bootstrap?.api_recipe_graph_recompute ?? "";

  const catalogIconByOp = useMemo(
    () => catalogIconByValue(catalogOperations),
    [catalogOperations],
  );
  const catalogIconByOpRef = useRef(catalogIconByOp);
  catalogIconByOpRef.current = catalogIconByOp;

  const getViewportCenterFlowRef = useRef<(() => { x: number; y: number }) | null>(null);

  const seededNodes = useMemo(
    () => enrichNodesWithCatalogIcons(initialNodes, catalogIconByOp),
    [initialNodes, catalogIconByOp],
  );

  const [nodes, setNodes, rfOnNodesChange] = useNodesState(seededNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const nodesRef = useRef(nodes);
  const edgesRef = useRef(edges);
  nodesRef.current = nodes;
  edgesRef.current = edges;
  const [busy, setBusy] = useState(false);
  const [validationOk, setValidationOk] = useState<boolean | null>(null);
  const [footerHint, setFooterHint] = useState("");
  const [connectionFeedback, setConnectionFeedback] = useState("");
  const [selectedNodeIds, setSelectedNodeIds] = useState<string[]>([]);
  const [notes, setNotes] = useState("");
  const notesSaveTimerRef = useRef<ReturnType<typeof setTimeout> | undefined>(undefined);
  const connInspectorMsgRef = useRef("");
  const warnConnAtMs = useRef(0);
  const emptyHint = useMemo(
    () => reactFlowEmptyHint(bootstrap, nodes.length),
    [bootstrap, nodes.length],
  );

  useEffect(() => {
    if (notesSaveTimerRef.current !== undefined) {
      clearTimeout(notesSaveTimerRef.current);
      notesSaveTimerRef.current = undefined;
    }
    setNotes(loadRecipeNotes(recipeId));
  }, [recipeId]);

  const handleNotesChange = useCallback((text: string) => {
    setNotes(text);
    if (notesSaveTimerRef.current !== undefined) {
      clearTimeout(notesSaveTimerRef.current);
    }
    notesSaveTimerRef.current = setTimeout(() => {
      saveRecipeNotes(recipeId, text);
    }, 400);
  }, [recipeId]);

  const outputCount = useMemo(() => nodes.filter((n) => n.type === "output").length, [nodes]);

  const handleSelectionChange = useCallback((params: { nodes: Node[] }) => {
    setSelectedNodeIds(params.nodes.map((n) => n.id));
  }, []);

  const clearConnectionInspectorFeedback = useCallback(() => {
    connInspectorMsgRef.current = "";
    setConnectionFeedback("");
  }, []);

  const isValidConnection = useCallback<IsValidConnection>(
    (edge) => {
      if (!edge.source || !edge.target) {
        return false;
      }
      const c: Connection = {
        source: edge.source,
        target: edge.target,
        sourceHandle: edge.sourceHandle ?? null,
        targetHandle: edge.targetHandle ?? null,
      };
      const res = evaluateRecipeConnection(nodes, edges, c);
      if (res.ok) {
        clearConnectionInspectorFeedback();
        return true;
      }
      if (wouldConnectAfterRemovals(nodes, edges, c)) {
        clearConnectionInspectorFeedback();
        return true;
      }
      if (res.message !== connInspectorMsgRef.current) {
        connInspectorMsgRef.current = res.message;
        setConnectionFeedback(res.message);
      }
      const now = Date.now();
      if (now - warnConnAtMs.current > 1200) {
        warnConnAtMs.current = now;
        setGlobalStatus(res.message, true);
      }
      return false;
    },
    [clearConnectionInspectorFeedback, edges, nodes],
  );

  const applyRecomputeJson = useCallback(
    (json: RecipeGraphRecomputeResponse, meta: { commit: boolean; silent?: boolean }) => {
      if (json.react_flow?.nodes && Array.isArray(json.react_flow.edges)) {
        const withVal = applyValidationIssuesToNodes(
          json.react_flow.nodes as Node[],
          json.validation?.issues,
        );
        setNodes(enrichNodesWithCatalogIcons(withVal, catalogIconByOpRef.current));
        const nextEdges = json.react_flow.edges as Edge[];
        setEdges(
          nextEdges.map((e) => ({
            ...e,
            type: e.type ?? "recipe",
          })),
        );
      }
      const vok = json.validation?.ok;
      setValidationOk(typeof vok === "boolean" ? vok : null);
      if (meta.silent) {
        return;
      }
      const issues = json.validation?.issues;
      const issueCount = Array.isArray(issues) ? issues.length : 0;
      setFooterHint(
        meta.commit
          ? json.steps_synced
            ? "Saved · steps synced"
            : "Saved (steps not synced)"
          : `Dry-run · ${issueCount} validation note(s)`,
      );
      setGlobalStatus(
        meta.commit ? "Recompute & save complete." : "Dry-run complete. Review validation.",
        false,
      );
    },
    [setEdges, setNodes],
  );

  const silentDryRunFromGraph = useCallback(
    async (nodeList: Node[], edgeList: Edge[]) => {
      if (!recomputeUrl || !recipeId) {
        return;
      }
      try {
        const rf = buildReactFlowSnapshot(nodeList, edgeList);
        const json = await postRecipeGraphRecompute(recomputeUrl, { react_flow: rf });
        applyRecomputeJson(json, { commit: false, silent: true });
      } catch {
        // Keep local wiring; user can use Dry-run for an error message.
      }
    },
    [applyRecomputeJson, recipeId, recomputeUrl],
  );

  const onNodesChange = useCallback(
    (changes: NodeChange[]) => {
      if (!changes.some((c) => c.type === "remove")) {
        rfOnNodesChange(changes);
        return;
      }
      setNodes((current) => {
        const after = applyNodeChanges(changes, current);
        const { nodes: cleanedNodes, edges: cleanedEdges } = cleanupAfterNodeRemovals(
          current,
          after,
          edgesRef.current,
        );
        queueMicrotask(() => {
          setEdges(cleanedEdges);
          void silentDryRunFromGraph(cleanedNodes, cleanedEdges);
        });
        return cleanedNodes;
      });
    },
    [rfOnNodesChange, setEdges, setNodes, silentDryRunFromGraph],
  );

  const onConnect = useCallback(
    (c: Connection) => {
      clearConnectionInspectorFeedback();
      const currentNodes = nodesRef.current;
      const currentEdges = edgesRef.current;
      const remove = new Set(getRecipeConnectEdgeRemovals(currentNodes, currentEdges, c));
      const filtered = currentEdges.filter((e) => !remove.has(e.id));
      if (!evaluateRecipeConnection(currentNodes, filtered, c).ok) {
        return;
      }
      const nextEdges = addEdge(connectionToRecipeEdge(c, currentNodes), filtered);
      let graphNodes = currentNodes;
      let graphEdges = nextEdges;
      if (isMaterialToOperationConnection(currentNodes, c) && c.target) {
        const syn = ensureOperationOutputArtifacts(
          currentNodes,
          nextEdges,
          c.target,
          newGraphNodeId,
        );
        graphNodes = syn.nodes;
        graphEdges = syn.edges;
        if (syn.nodes !== currentNodes) {
          setNodes(syn.nodes);
        }
        setEdges(syn.edges);
      } else {
        setEdges(nextEdges);
      }
      void silentDryRunFromGraph(graphNodes, graphEdges);
    },
    [clearConnectionInspectorFeedback, setEdges, setNodes, silentDryRunFromGraph],
  );

  const addOperationNode = useCallback(
    (operation: string) => {
      setNodes((nds) => {
        const pos = getViewportCenterFlowRef.current?.() ?? paletteGridPosition(nds.length);
        const id = newGraphNodeId("op");
        const icon = catalogIconByOp.get(operation);
        const data: Record<string, unknown> = { operation, ...(icon ? { icon } : {}) };
        if (operation === "crystal_generator") {
          data.crystal_color = "c";
        }
        return [...nds, { id, type: "operation", position: pos, data }];
      });
    },
    [catalogIconByOp, setNodes],
  );

  const addSourceShapeNode = useCallback(() => {
    setNodes((nds) => {
      const pos = getViewportCenterFlowRef.current?.() ?? paletteGridPosition(nds.length);
      const id = newGraphNodeId("src");
      return [
        ...nds,
        {
          id,
          type: "shape",
          position: pos,
          data: { shape_code: DEFAULT_NEW_SOURCE_SHAPE_CODE, quantity: 1, role: "source" },
        },
      ];
    });
  }, [setNodes]);

  const dropOperationAtPosition = useCallback(
    (operation: string, position: { x: number; y: number }) => {
      const engineSet = new Set(engineOperationIds);
      if (!engineSet.has(operation)) {
        setGlobalStatus(ru("opDropRejected"), true);
        return;
      }
      const id = newGraphNodeId("op");
      const icon = catalogIconByOp.get(operation);
      const data: Record<string, unknown> = { operation, ...(icon ? { icon } : {}) };
      if (operation === "crystal_generator") {
        data.crystal_color = "c";
      }
      setNodes((nds) => {
        const opNode: Node = {
          id,
          type: "operation",
          position: { x: position.x, y: position.y },
          data,
        };
        const next = [...nds, opNode];
        const syn = ensureOperationOutputArtifacts(next, edgesRef.current, id, newGraphNodeId);
        queueMicrotask(() => {
          setEdges(syn.edges);
          void silentDryRunFromGraph(syn.nodes, syn.edges);
        });
        return syn.nodes;
      });
    },
    [catalogIconByOp, engineOperationIds, setEdges, setNodes, silentDryRunFromGraph],
  );

  const dropSourceShapeAtPosition = useCallback(
    (position: { x: number; y: number }) => {
      setNodes((nds) => {
        const id = newGraphNodeId("src");
        const next: Node[] = [
          ...nds,
          {
            id,
            type: "shape",
            position: { x: position.x, y: position.y },
            data: { shape_code: DEFAULT_NEW_SOURCE_SHAPE_CODE, quantity: 1, role: "source" },
          },
        ];
        queueMicrotask(() => {
          void silentDryRunFromGraph(next, edgesRef.current);
        });
        return next;
      });
    },
    [setNodes, silentDryRunFromGraph],
  );

  const addFluidSourceNode = useCallback(() => {
    setNodes((nds) => {
      const pos = getViewportCenterFlowRef.current?.() ?? paletteGridPosition(nds.length);
      const id = newGraphNodeId("fluid");
      return [
        ...nds,
        {
          id,
          type: "shape",
          position: pos,
          data: { shape_code: DEFAULT_NEW_FLUID_SHAPE_CODE, quantity: 1, role: "source" },
        },
      ];
    });
  }, [setNodes]);

  const dropFluidSourceAtPosition = useCallback(
    (position: { x: number; y: number }) => {
      setNodes((nds) => {
        const id = newGraphNodeId("fluid");
        const next: Node[] = [
          ...nds,
          {
            id,
            type: "shape",
            position: { x: position.x, y: position.y },
            data: { shape_code: DEFAULT_NEW_FLUID_SHAPE_CODE, quantity: 1, role: "source" },
          },
        ];
        queueMicrotask(() => {
          void silentDryRunFromGraph(next, edgesRef.current);
        });
        return next;
      });
    },
    [setNodes, silentDryRunFromGraph],
  );

  const autoArrangeNodes = useCallback(() => {
    setNodes((nds) => {
      if (nds.length === 0) {
        return nds;
      }
      const next = layoutNodesInColumns(nds);
      queueMicrotask(() => {
        void silentDryRunFromGraph(next, edgesRef.current);
      });
      return next;
    });
  }, [setNodes, silentDryRunFromGraph]);

  const patchNodeData = useCallback(
    (nodeId: string, patch: Record<string, unknown>) => {
      const edgesSnapshot = edgesRef.current;
      setNodes((nds) => {
        const n = nds.find((x) => x.id === nodeId);
        if (!n) {
          return nds;
        }
        const prev =
          n.data && typeof n.data === "object" && !Array.isArray(n.data)
            ? { ...(n.data as Record<string, unknown>) }
            : {};
        const next = { ...prev, ...patch };
        if ("paint_color" in patch && patch.paint_color === undefined) {
          delete next.paint_color;
        }
        if ("crystal_color" in patch && patch.crystal_color === undefined) {
          delete next.crystal_color;
        }
        if ("operation" in patch) {
          const op = String(patch.operation ?? "").trim();
          const ic = catalogIconByOpRef.current.get(op);
          if (ic) {
            next.icon = ic;
          } else {
            delete next.icon;
          }
        }
        if (
          "shape_code" in patch ||
          "operation" in patch ||
          "paint_color" in patch ||
          "crystal_color" in patch
        ) {
          delete next.preview_image_url;
          delete next.preview_alt;
        }
        const pos = n.position ?? { x: 0, y: 0 };
        const newNode: Node = {
          ...n,
          position: {
            x: typeof pos.x === "number" ? pos.x : 0,
            y: typeof pos.y === "number" ? pos.y : 0,
          },
          data: next,
        };
        const change: NodeChange = { type: "replace", id: nodeId, item: newNode };
        const updated = applyNodeChanges([change], nds);
        queueMicrotask(() => {
          void silentDryRunFromGraph(updated, edgesSnapshot);
        });
        return updated;
      });
    },
    [setNodes, silentDryRunFromGraph],
  );

  const runRecompute = useCallback(
    async (commit: boolean) => {
      if (!recomputeUrl) {
        setGlobalStatus("Missing recompute API URL in bootstrap.", true);
        return;
      }
      if (!recipeId) {
        setGlobalStatus("Missing recipe id.", true);
        return;
      }
      setBusy(true);
      setGlobalStatus(commit ? "Saving…" : "Recomputing…", false);
      try {
        const rf = buildReactFlowSnapshot(nodes, edges);
        const payload: Record<string, unknown> = { react_flow: rf };
        if (commit) {
          payload.commit = true;
        }
        const json = await postRecipeGraphRecompute(recomputeUrl, payload);
        applyRecomputeJson(json, { commit });
      } catch (e) {
        const msg = e instanceof Error ? e.message : "Request failed";
        setGlobalStatus(msg, true);
        setFooterHint("");
      } finally {
        setBusy(false);
      }
    },
    [applyRecomputeJson, edges, nodes, recipeId, recomputeUrl],
  );

  const onDryRun = useCallback(() => {
    void runRecompute(false);
  }, [runRecompute]);

  const onSave = useCallback(() => {
    void runRecompute(true);
  }, [runRecompute]);

  return (
    <div className="flex min-h-[min(85vh,920px)] flex-col gap-2 text-slate-100">
      <header className="flex shrink-0 flex-wrap items-start justify-between gap-3 rounded-lg border border-slate-700 bg-slate-900/60 px-3 py-2">
        <div>
          <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.28em] text-cyan-400/90">
            Recipe graph editor
          </p>
          <h2 className="mt-0.5 font-mono text-lg text-white">RECIPE GRAPH EDITOR</h2>
          <p className="mt-0.5 text-xs text-slate-400">
            Create, preview and optimize shape recipes.
          </p>
          <p className="mt-1 font-mono text-sm text-amber-200/90">
            {recipeCode}
            {recipeName ? <span className="text-slate-400"> · {recipeName}</span> : null}
          </p>
        </div>
        <div className="flex flex-wrap gap-2 text-xs">
          <a
            className="rounded-lg border border-slate-600 px-3 py-2 font-semibold text-slate-200 hover:border-cyan-600/50"
            href={catalogHref}
          >
            Catalog
          </a>
          <a
            className="rounded-lg border border-amber-600/40 px-3 py-2 font-semibold text-amber-100 hover:border-amber-500/60"
            href={editHref}
          >
            Edit metadata
          </a>
        </div>
      </header>

      <div className="grid min-h-0 flex-1 grid-cols-1 gap-2 md:grid-cols-[220px_minmax(0,1fr)_168px]">
        <OperationPalettePanel
          engineOperationIds={engineOperationIds}
          onAddFluidSource={addFluidSourceNode}
          onAddOperation={addOperationNode}
          onAddSourceShape={addSourceShapeNode}
          operations={catalogOperations}
        />
        <GraphCanvasPanel
          catalogOperations={catalogOperations}
          edges={edges}
          emptyHint={emptyHint}
          engineOperationIds={engineOperationIds}
          getViewportCenterFlowRef={getViewportCenterFlowRef}
          isValidConnection={isValidConnection}
          nodes={nodes}
          onConnect={onConnect}
          onAutoArrange={autoArrangeNodes}
          onDropFluidFromPalette={dropFluidSourceAtPosition}
          onDropOperationFromPalette={dropOperationAtPosition}
          onDropSourceFromPalette={dropSourceShapeAtPosition}
          onEdgesChange={onEdgesChange}
          onNodesChange={onNodesChange}
          onPatchNodeData={patchNodeData}
          onSelectionChange={handleSelectionChange}
        />
        <OutputsColumn />
      </div>

      <InspectorStrip
        connectionFeedback={connectionFeedback}
        edgeCount={edges.length}
        footerHint={footerHint}
        nodeCount={nodes.length}
        nodes={nodes}
        notes={notes}
        onNotesChange={handleNotesChange}
        onPatchNodeData={patchNodeData}
        outputCount={outputCount}
        selectedNodeIds={selectedNodeIds}
        validationOk={validationOk}
      />
      <FooterActions
        busy={busy}
        footerHint={footerHint}
        onDryRun={onDryRun}
        onSave={onSave}
        validationOk={validationOk}
      />
    </div>
  );
}
