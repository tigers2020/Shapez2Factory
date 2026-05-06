import {
  Background,
  BackgroundVariant,
  Controls,
  MiniMap,
  ReactFlow,
  useEdgesState,
  useNodesState,
  useReactFlow,
  type Connection,
  type Edge,
  type IsValidConnection,
  type Node,
} from "@xyflow/react";
import { useCallback, useLayoutEffect, useMemo, type DragEvent } from "react";

import {
  RECIPE_NODE_TILE_HALF_PX,
  RECIPE_PALETTE_DND_OP,
  RECIPE_PALETTE_DND_SRC,
} from "../EditorFoundation/constants";
import type { FlowViewportCenterRef } from "./flowViewport";
import { recipeEdgeTypes } from "../RecipeFlow/FlowEdges";
import { recipeNodeTypes } from "../RecipeFlow/FlowNodes";
import {
  useRecipeGraphClipboardShortcuts,
  type RecipeGraphClipboardShortcutDepsNoScreen,
} from "../RecipeGraph/clipboard";

export type GraphEditorRecipeFlowBoardProps = Readonly<{
  clipboardShortcutDeps: RecipeGraphClipboardShortcutDepsNoScreen;
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
  getViewportCenterFlowRef: FlowViewportCenterRef;
}>;

export function GraphEditorRecipeFlowBoard({
  clipboardShortcutDeps,
  edges,
  getViewportCenterFlowRef,
  isValidConnection,
  nodes,
  onConnect,
  onDropOperationFromPalette,
  onDropSourceFromPalette,
  onEdgesChange,
  onNodeDoubleClick,
  onNodesChange,
  onSelectionChange,
}: GraphEditorRecipeFlowBoardProps) {
  const nodeTypes = useMemo(() => recipeNodeTypes, []);
  const edgeTypes = useMemo(() => recipeEdgeTypes, []);
  const { screenToFlowPosition } = useReactFlow();

  useRecipeGraphClipboardShortcuts({ ...clipboardShortcutDeps, screenToFlowPosition });

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
      }
    },
    [onDropOperationFromPalette, onDropSourceFromPalette, screenToFlowPosition],
  );

  return (
    <ReactFlow
      connectionRadius={56}
      defaultEdgeOptions={{ type: "recipe", style: { strokeWidth: 1.6 } }}
      defaultViewport={{ x: 0, y: 0, zoom: 1 }}
      deleteKeyCode={["Backspace", "Delete"]}
      edgeTypes={edgeTypes}
      multiSelectionKeyCode="Shift"
      edges={edges}
      fitView
      isValidConnection={isValidConnection}
      maxZoom={3.5}
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
