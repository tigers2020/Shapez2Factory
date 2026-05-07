import {
  addEdge,
  applyNodeChanges,
  useEdgesState,
  useNodesState,
  type Connection,
  type Edge,
  type Node,
  type NodeChange,
} from "@xyflow/react";
import { useCallback, useMemo, useRef } from "react";

import { GraphEditorCanvasPanel } from "./CanvasPanel";
import { GraphEditorFooterActions } from "./FooterActions";
import { GraphEditorInspectorStrip } from "./InspectorStrip";
import { GraphEditorOperationPalette } from "./OperationPalette";
import { GraphEditorOutputsColumn } from "./OutputsColumn";
import { setGlobalStatus } from "./globalStatus";
import { mergeNodeDataWithPatch, shallowRecordFromUnknown } from "./nodeData";
import { newGraphNodeId, paletteGridPosition } from "./placement";
import { ensureOperationOutputArtifacts } from "../Operation/outputStaging";
import {
  catalogIconByValue,
  enrichNodesWithCatalogIcons,
  type CatalogOperationRow,
} from "../Operation/nodeCatalogMerge";
import {
  connectionToRecipeEdge,
  ensurePainterTargetHandlesOnEdges,
  evaluateRecipeConnection,
  filterStaleRecipeEdges,
  getRecipeConnectEdgeRemovals,
  isMaterialToOperationConnection,
  normalizeMaterialToPainterConnection,
} from "../RecipeConnection";
import { layoutNodesFromGraph } from "../RecipeGraph/autoLayout";
import type { RecipeGraphClipboardPayload, RecipeGraphClipboardShortcutDepsNoScreen } from "../RecipeGraph/clipboard";
import { cleanupAfterNodeRemovals } from "../RecipeGraph/nodeCleanup";
import {
  DEFAULT_SOURCE_SHAPE_QUANTITY_MATERIAL,
  pickCycledBaseFullSourceShapeCode,
} from "../EditorFoundation/constants";
import { ru } from "../EditorFoundation/recipeUiStrings";
import { useRecipeGraphConnectionFeedback } from "../Hooks/useRecipeGraphConnectionFeedback";
import { useRecipeGraphNotes } from "../Hooks/useRecipeGraphNotes";
import { useRecipeGraphRecompute } from "../Hooks/useRecipeGraphRecompute";
import { useRecipeGraphSelection } from "../Hooks/useRecipeGraphSelection";

export type ReactFlowInitialPayload = {
  version: number;
  nodes: Node[];
  edges: Edge[];
};

export type GraphBootstrap = {
  api_recipe_graph_recompute?: string;
  /** Staff GET atomic part sprite manifest for Canvas2D tiles */
  api_shape_part_sprite_manifest?: string;
  csrf_token?: string;
  staff_catalog_url?: string;
  staff_recipe_edit_url?: string;
  react_flow_initial?: ReactFlowInitialPayload | null;
  react_flow_initial_status?: "ok" | "missing" | "invalid";
  macro_step_count?: number;
};

export type { CatalogOperationRow } from "../Operation/nodeCatalogMerge";

type GraphEditorAppProps = Readonly<{
  recipeId: number;
  recipeCode: string;
  recipeName: string;
  bootstrap: GraphBootstrap | null;
  initialNodes: Node[];
  initialEdges: Edge[];
  catalogOperations: CatalogOperationRow[];
  engineOperationIds: readonly string[];
}>;

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

  const seededEdges = useMemo(
    () => ensurePainterTargetHandlesOnEdges(seededNodes, initialEdges),
    [seededNodes, initialEdges],
  );

  const [nodes, setNodes, rfOnNodesChange] = useNodesState(seededNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(seededEdges);
  const nodesRef = useRef(nodes);
  const edgesRef = useRef(edges);
  nodesRef.current = nodes;
  edgesRef.current = edges;

  const { notes, handleNotesChange } = useRecipeGraphNotes(recipeId);
  const { selectedNodeIds, handleSelectionChange } = useRecipeGraphSelection();
  const {
    connectionFeedback,
    clearConnectionInspectorFeedback,
    isValidConnection,
  } = useRecipeGraphConnectionFeedback(nodes, edges);

  const {
    busy,
    validationOk,
    footerHint,
    silentDryRunFromGraph,
    onDryRun,
    onSave,
  } = useRecipeGraphRecompute({
    recipeId,
    recomputeUrl,
    nodesRef,
    edgesRef,
    setNodes,
    setEdges,
    catalogIconByOpRef,
  });

  const lastClipboardPayloadRef = useRef<RecipeGraphClipboardPayload | null>(null);
  const enrichNodesWithIcons = useCallback(
    (nds: Node[]) => enrichNodesWithCatalogIcons(nds, catalogIconByOpRef.current),
    [],
  );
  const newSourceShapeSeqRef = useRef(0);
  const emptyHint = useMemo(
    () => reactFlowEmptyHint(bootstrap, nodes.length),
    [bootstrap, nodes.length],
  );

  const outputCount = useMemo(() => nodes.filter((n) => n.type === "output").length, [nodes]);

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

  const clipboardShortcutDeps = useMemo(
    (): RecipeGraphClipboardShortcutDepsNoScreen => ({
      selectedNodeIds,
      nodesRef,
      edgesRef,
      lastPayloadRef: lastClipboardPayloadRef,
      setNodes,
      setEdges,
      onNodesChange,
      enrichNodesWithIcons,
      silentDryRunFromGraph,
      newGraphNodeId,
    }),
    [enrichNodesWithIcons, onNodesChange, selectedNodeIds, silentDryRunFromGraph],
  );

  const onConnect = useCallback(
    (conn: Connection) => {
      clearConnectionInspectorFeedback();
      const currentNodes = nodesRef.current;
      const currentEdges = edgesRef.current;
      const raw: Connection = {
        source: conn.source,
        target: conn.target,
        sourceHandle: conn.sourceHandle ?? null,
        targetHandle: conn.targetHandle ?? null,
      };
      const c = normalizeMaterialToPainterConnection(currentNodes, raw);
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
        return [...nds, { id, type: "operation", position: pos, data }];
      });
    },
    [catalogIconByOp, setNodes],
  );

  const addSourceShapeNode = useCallback(() => {
    const seq = newSourceShapeSeqRef.current;
    newSourceShapeSeqRef.current = seq + 1;
    const shapeCode = pickCycledBaseFullSourceShapeCode(seq);
    setNodes((nds) => {
      const pos = getViewportCenterFlowRef.current?.() ?? paletteGridPosition(nds.length);
      const id = newGraphNodeId("src");
      return [
        ...nds,
        {
          id,
          type: "shape",
          position: pos,
          data: { shape_code: shapeCode, quantity: DEFAULT_SOURCE_SHAPE_QUANTITY_MATERIAL, role: "source" },
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
      const seq = newSourceShapeSeqRef.current;
      newSourceShapeSeqRef.current = seq + 1;
      const shapeCode = pickCycledBaseFullSourceShapeCode(seq);
      setNodes((nds) => {
        const id = newGraphNodeId("src");
        const next: Node[] = [
          ...nds,
          {
            id,
            type: "shape",
            position: { x: position.x, y: position.y },
            data: { shape_code: shapeCode, quantity: DEFAULT_SOURCE_SHAPE_QUANTITY_MATERIAL, role: "source" },
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
      const next = layoutNodesFromGraph(nds, edgesRef.current);
      queueMicrotask(() => {
        void silentDryRunFromGraph(next, edgesRef.current);
      });
      return next;
    });
  }, [setNodes, silentDryRunFromGraph]);

  const patchNodeData = useCallback(
    (nodeId: string, patch: Record<string, unknown>) => {
      const targetPre = nodesRef.current.find((x) => x.id === nodeId);
      if (targetPre?.type === "intermediate") {
        return;
      }
      const edgesSnapshot = edgesRef.current;
      setNodes((nds) => {
        const n = nds.find((x) => x.id === nodeId);
        if (!n) {
          return nds;
        }
        const prev = shallowRecordFromUnknown(n.data);
        const next = mergeNodeDataWithPatch(prev, patch, catalogIconByOpRef.current);
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
        const stripStaleEdges =
          (n.type === "shape" || n.type === "intermediate") &&
          ("source_carrier" in patch || "shape_code" in patch);
        const nextEdges = stripStaleEdges
          ? filterStaleRecipeEdges(updated, edgesSnapshot)
          : edgesSnapshot;
        queueMicrotask(() => {
          if (stripStaleEdges) {
            setEdges(nextEdges);
          }
          void silentDryRunFromGraph(updated, nextEdges);
        });
        return updated;
      });
    },
    [setEdges, setNodes, silentDryRunFromGraph],
  );

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
        <GraphEditorOperationPalette
          engineOperationIds={engineOperationIds}
          onAddOperation={addOperationNode}
          onAddSourceShape={addSourceShapeNode}
          operations={catalogOperations}
        />
        <GraphEditorCanvasPanel
          catalogOperations={catalogOperations}
          clipboardShortcutDeps={clipboardShortcutDeps}
          edges={edges}
          emptyHint={emptyHint}
          engineOperationIds={engineOperationIds}
          getViewportCenterFlowRef={getViewportCenterFlowRef}
          isValidConnection={isValidConnection}
          nodes={nodes}
          onConnect={onConnect}
          onAutoArrange={autoArrangeNodes}
          onDropOperationFromPalette={dropOperationAtPosition}
          onDropSourceFromPalette={dropSourceShapeAtPosition}
          onEdgesChange={onEdgesChange}
          onNodesChange={onNodesChange}
          onPatchNodeData={patchNodeData}
          onSelectionChange={handleSelectionChange}
        />
        <GraphEditorOutputsColumn />
      </div>

      <GraphEditorInspectorStrip
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
      <GraphEditorFooterActions
        busy={busy}
        footerHint={footerHint}
        onDryRun={onDryRun}
        onSave={onSave}
        validationOk={validationOk}
      />
    </div>
  );
}
