import { ReactFlowProvider, useEdgesState, useNodesState, type Connection, type Edge, type IsValidConnection, type Node } from "@xyflow/react";
import { useCallback, useMemo, useRef, useState } from "react";

import { NodeEditModal } from "../NodeEditModal/NodeEditModal";
import type { FlowViewportCenterRef } from "./flowViewport";
import { GraphEditorRecipeFlowBoard } from "./RecipeFlowBoard";
import type { CatalogOperationRow } from "../Operation/nodeCatalogMerge";
import type { RecipeGraphClipboardShortcutDepsNoScreen } from "../RecipeGraph/clipboard";

function escapeNodeIdForCssAttribute(nodeId: string): string {
  if (typeof CSS !== "undefined" && typeof CSS.escape === "function") {
    return CSS.escape(nodeId);
  }
  return nodeId.replaceAll("\\", String.raw`\\`).replaceAll('"', "\u005c" + '"');
}

export type GraphEditorCanvasPanelProps = Readonly<{
  clipboardShortcutDeps: RecipeGraphClipboardShortcutDepsNoScreen;
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
  onAutoArrange: () => void;
  catalogOperations: CatalogOperationRow[];
  engineOperationIds: readonly string[];
  getViewportCenterFlowRef: FlowViewportCenterRef;
}>;

export function GraphEditorCanvasPanel({
  catalogOperations,
  clipboardShortcutDeps,
  edges,
  emptyHint,
  engineOperationIds,
  getViewportCenterFlowRef,
  isValidConnection,
  nodes,
  onConnect,
  onDropOperationFromPalette,
  onDropSourceFromPalette,
  onAutoArrange,
  onEdgesChange,
  onNodesChange,
  onPatchNodeData,
  onSelectionChange,
}: GraphEditorCanvasPanelProps) {
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
      const escaped = escapeNodeIdForCssAttribute(node.id);
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
          <GraphEditorRecipeFlowBoard
            clipboardShortcutDeps={clipboardShortcutDeps}
            edges={edges}
            getViewportCenterFlowRef={getViewportCenterFlowRef}
            isValidConnection={isValidConnection}
            nodes={nodes}
            onConnect={onConnect}
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
