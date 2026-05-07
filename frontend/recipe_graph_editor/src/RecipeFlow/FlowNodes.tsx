import { Handle, Position, useUpdateNodeInternals, type NodeProps } from "@xyflow/react";
import { useCallback } from "react";

import { defaultQuantityForShapeNodeData } from "../EditorFoundation/constants";
import { getEffectiveOperationInputArity, getOperationOutputCount } from "../Operation/arity";
import { RecipeShapePreview } from "../ShapeSprite/RecipeShapePreview";

type ShapeNodeData = {
  shape_code?: string;
  quantity?: number;
  role?: string;
  source_carrier?: string;
  validationSeverity?: "error" | "warning";
  preview_image_url?: string;
  preview_alt?: string;
  preview_scene?: Record<string, unknown>;
};

type OperationNodeData = {
  operation?: string;
  paint_color?: string;
  crystal_color?: string;
  icon?: string;
  validationSeverity?: "error" | "warning";
};

/** 타일 가장자리에 붙는 좁은 소켓; 히트는 connectionRadius에 의존 */
const socketHandleClass =
  "!h-5 !w-2 !min-h-0 !min-w-0 !rounded-sm !border !border-slate-400/85 !bg-slate-700/95 !shadow-none";

function validationBadge(severity: "error" | "warning" | undefined) {
  if (severity === "error") {
    return (
      <span
        className="absolute -right-0.5 -top-0.5 z-10 rounded border border-rose-600/80 bg-rose-950/95 px-0.5 font-mono text-[7px] font-semibold uppercase tracking-wide text-rose-200"
        title="Validation error"
      >
        !
      </span>
    );
  }
  if (severity === "warning") {
    return (
      <span
        className="absolute -right-0.5 -top-0.5 z-10 rounded border border-amber-600/70 bg-amber-950/95 px-0.5 font-mono text-[7px] font-semibold uppercase tracking-wide text-amber-100"
        title="Validation warning"
      >
        ?
      </span>
    );
  }
  return null;
}

function operationTitle(code: string): string {
  if (!code) {
    return "Operation";
  }
  return code
    .split("_")
    .map((p) => (p.length ? p[0].toUpperCase() + p.slice(1) : p))
    .join(" ");
}

const OP_ICON: Record<string, string> = {
  rotate_cw: "↻",
  rotate_ccw: "↺",
  rotate_180: "⟲",
  cutter: "✂",
  half_destroyer: "½",
  splitter: "⫾",
  pin_pusher: "▣",
  swapper: "⇄",
  stacker: "⧈",
  painter: "◈",
  color_mixer: "◎",
  crystal_generator: "✦",
};

function operationGlyph(op: string): string {
  return OP_ICON[op] ?? "◇";
}

const tileRing = (selected: boolean, borderAccent: string) =>
  [
    "relative flex h-16 w-16 shrink-0 items-center justify-center rounded-lg border bg-slate-900/95 shadow-md transition-shadow",
    borderAccent,
    selected ? "ring-2 ring-cyan-400/75 ring-offset-1 ring-offset-slate-950" : "",
  ].join(" ");

function shapeTooltip(code: string, qty: number, id: string, role?: string): string {
  const parts = [id, role ? `role: ${role}` : "", code || "—", `×${qty}`].filter(Boolean);
  return parts.join("\n");
}

export function ShapeNode(props: NodeProps) {
  const { data, id, selected } = props;
  const d = (data || {}) as ShapeNodeData;
  const code = String(d.shape_code ?? "");
  const qty =
    typeof d.quantity === "number" ? d.quantity : defaultQuantityForShapeNodeData(d);
  const role = typeof d.role === "string" ? d.role : "";
  const updateNodeInternals = useUpdateNodeInternals();
  const onPreviewDisplayReady = useCallback(() => {
    updateNodeInternals(id);
  }, [id, updateNodeInternals]);
  return (
    <div className={tileRing(selected, "border-cyan-600/50")} title={shapeTooltip(code, qty, id, role)}>
      {validationBadge(d.validationSeverity)}
      <RecipeShapePreview
        key={`pv-${id}-${typeof d.preview_image_url === "string" ? d.preview_image_url : ""}-${d.preview_scene ? "s" : "n"}`}
        code={code}
        previewAlt={typeof d.preview_alt === "string" ? d.preview_alt : undefined}
        previewImageUrl={typeof d.preview_image_url === "string" ? d.preview_image_url : undefined}
        previewScene={
          d.preview_scene !== null &&
          typeof d.preview_scene === "object" &&
          !Array.isArray(d.preview_scene)
            ? d.preview_scene
            : undefined
        }
        variant="tile"
        onPreviewDisplayReady={onPreviewDisplayReady}
      />
      <Handle className={socketHandleClass} id="out" position={Position.Right} type="source" />
    </div>
  );
}

function operationLeftTargetHandles(inArity: number, twoWireFluidUpperShapeLower: boolean) {
  if (inArity < 2) {
    return (
      <Handle
        className={socketHandleClass}
        id="in"
        position={Position.Left}
        style={{ top: "50%", transform: "translateY(-50%)" }}
        type="target"
      />
    );
  }
  if (twoWireFluidUpperShapeLower) {
    return (
      <>
        <Handle
          className={socketHandleClass}
          id="in-1"
          position={Position.Left}
          style={{ top: "32%" }}
          type="target"
        />
        <Handle
          className={socketHandleClass}
          id="in"
          position={Position.Left}
          style={{ top: "68%" }}
          type="target"
        />
      </>
    );
  }
  return (
    <>
      <Handle
        className={socketHandleClass}
        id="in"
        position={Position.Left}
        style={{ top: "32%" }}
        type="target"
      />
      <Handle
        className={socketHandleClass}
        id="in-1"
        position={Position.Left}
        style={{ top: "68%" }}
        type="target"
      />
    </>
  );
}

export function OperationNode(props: NodeProps) {
  const { data, id, selected } = props;
  const d = (data || {}) as OperationNodeData;
  const op = String(d.operation ?? "");
  const glyph = operationGlyph(op);
  const title = operationTitle(op);
  const inArity = getEffectiveOperationInputArity(op, d);
  const outCount = getOperationOutputCount(op);
  /** Painter / crystal 2-wire: fluid ``in-1`` above shape ``in`` (matches domain slot "1"). */
  const twoWireFluidUpperShapeLower =
    inArity >= 2 &&
    ((op.trim() === "painter" && !String(d.paint_color ?? "").trim()) ||
      (op.trim() === "crystal_generator" && !String(d.crystal_color ?? "").trim()));
  const iconUrl = typeof d.icon === "string" ? d.icon.trim() : "";
  const tip = [id, title, d.paint_color ? `paint: ${d.paint_color}` : "", d.crystal_color ? `crystal: ${d.crystal_color}` : ""]
    .filter(Boolean)
    .join("\n");
  return (
    <div className={tileRing(selected, "border-purple-500/55")} title={tip}>
      {validationBadge(d.validationSeverity)}
      {operationLeftTargetHandles(inArity, twoWireFluidUpperShapeLower)}
      <div className="flex h-10 w-10 items-center justify-center overflow-hidden rounded border border-purple-600/40 bg-purple-950/50">
        {iconUrl ? (
          <img alt="" className="h-full w-full object-contain p-0.5" height={40} src={iconUrl} width={40} />
        ) : (
          <span className="text-lg text-purple-100/95" aria-hidden>
            {glyph}
          </span>
        )}
      </div>
      {outCount >= 2 ? (
        <>
          <Handle
            className={socketHandleClass}
            id="out"
            position={Position.Right}
            style={{ top: "32%" }}
            type="source"
          />
          <Handle
            className={socketHandleClass}
            id="out-1"
            position={Position.Right}
            style={{ top: "68%" }}
            type="source"
          />
        </>
      ) : (
        <Handle
          className={socketHandleClass}
          id="out"
          position={Position.Right}
          style={{ top: "50%", transform: "translateY(-50%)" }}
          type="source"
        />
      )}
    </div>
  );
}

export function IntermediateNode(props: NodeProps) {
  const { data, id, selected } = props;
  const d = (data || {}) as ShapeNodeData;
  const code = String(d.shape_code ?? "");
  const qty =
    typeof d.quantity === "number" ? d.quantity : defaultQuantityForShapeNodeData(d);
  const role = typeof d.role === "string" ? d.role : "intermediate";
  const updateNodeInternals = useUpdateNodeInternals();
  const onPreviewDisplayReady = useCallback(() => {
    updateNodeInternals(id);
  }, [id, updateNodeInternals]);
  return (
    <div className={tileRing(selected, "border-teal-600/50")} title={shapeTooltip(code, qty, id, role)}>
      {validationBadge(d.validationSeverity)}
      <RecipeShapePreview
        key={`pv-${id}-${typeof d.preview_image_url === "string" ? d.preview_image_url : ""}-${d.preview_scene ? "s" : "n"}`}
        code={code}
        previewAlt={typeof d.preview_alt === "string" ? d.preview_alt : undefined}
        previewImageUrl={typeof d.preview_image_url === "string" ? d.preview_image_url : undefined}
        previewScene={
          d.preview_scene !== null &&
          typeof d.preview_scene === "object" &&
          !Array.isArray(d.preview_scene)
            ? d.preview_scene
            : undefined
        }
        variant="tile"
        onPreviewDisplayReady={onPreviewDisplayReady}
      />
      <Handle className={socketHandleClass} id="in" position={Position.Left} type="target" />
      <Handle className={socketHandleClass} id="out" position={Position.Right} type="source" />
    </div>
  );
}

export function OutputNode(props: NodeProps) {
  const { data, id, selected } = props;
  const d = (data || {}) as ShapeNodeData;
  const code = String(d.shape_code ?? "");
  const qty =
    typeof d.quantity === "number" ? d.quantity : defaultQuantityForShapeNodeData(d);
  const role = typeof d.role === "string" ? d.role : "target";
  const updateNodeInternals = useUpdateNodeInternals();
  const onPreviewDisplayReady = useCallback(() => {
    updateNodeInternals(id);
  }, [id, updateNodeInternals]);
  return (
    <div className={tileRing(selected, "border-orange-500/60")} title={shapeTooltip(code, qty, id, role)}>
      {validationBadge(d.validationSeverity)}
      <RecipeShapePreview
        key={`pv-${id}-${typeof d.preview_image_url === "string" ? d.preview_image_url : ""}-${d.preview_scene ? "s" : "n"}`}
        code={code}
        previewAlt={typeof d.preview_alt === "string" ? d.preview_alt : undefined}
        previewImageUrl={typeof d.preview_image_url === "string" ? d.preview_image_url : undefined}
        previewScene={
          d.preview_scene !== null &&
          typeof d.preview_scene === "object" &&
          !Array.isArray(d.preview_scene)
            ? d.preview_scene
            : undefined
        }
        variant="tile"
        onPreviewDisplayReady={onPreviewDisplayReady}
      />
      <Handle className={socketHandleClass} id="in" position={Position.Left} type="target" />
    </div>
  );
}

export const recipeNodeTypes = {
  shape: ShapeNode,
  operation: OperationNode,
  intermediate: IntermediateNode,
  output: OutputNode,
};
