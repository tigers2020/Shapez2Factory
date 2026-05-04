import { Handle, Position, type NodeProps } from "@xyflow/react";
import { useState } from "react";

import { getOperationInputArity } from "./operationArity";

type ShapeNodeData = {
  shape_code?: string;
  quantity?: number;
  role?: string;
  validationSeverity?: "error" | "warning";
  preview_image_url?: string;
  preview_alt?: string;
};

type OperationNodeData = {
  operation?: string;
  paint_color?: string;
  validationSeverity?: "error" | "warning";
};

/** 넓은 연결 히트 영역(카드 위에서도 잡히도록). */
const handleClass =
  "!flex !h-9 !w-9 !min-h-9 !min-w-9 !items-center !justify-center !border !border-neutral-500/70 !bg-neutral-800/90 !rounded-full";

function validationBadge(severity: "error" | "warning" | undefined) {
  if (severity === "error") {
    return (
      <span
        className="absolute -right-1 -top-1 rounded border border-rose-600/80 bg-rose-950/95 px-1 font-mono text-[8px] font-semibold uppercase tracking-wide text-rose-200"
        title="Validation error"
      >
        !
      </span>
    );
  }
  if (severity === "warning") {
    return (
      <span
        className="absolute -right-1 -top-1 rounded border border-amber-600/70 bg-amber-950/95 px-1 font-mono text-[8px] font-semibold uppercase tracking-wide text-amber-100"
        title="Validation warning"
      >
        ?
      </span>
    );
  }
  return null;
}

function MiniShapePreview({
  code,
  previewAlt,
  previewImageUrl,
}: {
  code: string;
  previewAlt?: string;
  previewImageUrl?: string;
}) {
  const [imgFailed, setImgFailed] = useState(false);
  const url = typeof previewImageUrl === "string" ? previewImageUrl.trim() : "";
  const short = code.trim().slice(0, 3) || "—";
  if (url && !imgFailed) {
    return (
      <div
        aria-hidden
        className="flex h-9 w-9 shrink-0 items-center justify-center overflow-hidden rounded border border-cyan-700/40 bg-neutral-950"
      >
        <img
          alt={previewAlt || code || "Shape preview"}
          className="h-full w-full object-contain p-0.5"
          loading="lazy"
          src={url}
          onError={() => {
            setImgFailed(true);
          }}
        />
      </div>
    );
  }
  return (
    <div
      aria-hidden
      className="flex h-9 w-9 shrink-0 items-center justify-center rounded border border-cyan-700/40 bg-gradient-to-br from-cyan-950/80 to-neutral-900 font-mono text-[10px] font-semibold text-cyan-100/90"
    >
      {short}
    </div>
  );
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
  cutter_full: "✂",
  half_destroyer: "½",
  splitter: "⫾",
  pin_pusher: "▣",
  swapper: "⇄",
  stacker: "⧈",
  painter: "◈",
  color_mixer: "◎",
};

function operationGlyph(op: string): string {
  return OP_ICON[op] ?? "◇";
}

const nodeShell = (selected: boolean, borderAccent: string) =>
  [
    "relative min-w-[112px] max-w-[180px] rounded-xl border bg-neutral-900/95 px-2.5 py-2 font-mono text-[10px] text-neutral-100 shadow-lg transition-shadow",
    borderAccent,
    selected ? "ring-2 ring-cyan-400/75 ring-offset-1 ring-offset-neutral-950" : "",
  ].join(" ");

export function ShapeNode(props: NodeProps) {
  const { data, id, selected } = props;
  const d = (data || {}) as ShapeNodeData;
  const code = String(d.shape_code ?? "");
  const qty = typeof d.quantity === "number" ? d.quantity : 1;
  return (
    <div className={nodeShell(selected, "border-cyan-700/45")}>
      {validationBadge(d.validationSeverity)}
      <div className="mb-1 flex items-start gap-2">
        <MiniShapePreview
          code={code}
          previewAlt={typeof d.preview_alt === "string" ? d.preview_alt : undefined}
          previewImageUrl={typeof d.preview_image_url === "string" ? d.preview_image_url : undefined}
        />
        <div className="min-w-0 flex-1">
          <p className="text-[9px] font-semibold uppercase tracking-[0.14em] text-cyan-400/90">
            Source
          </p>
          <p className="truncate text-[11px] text-neutral-100" title={code || "(empty)"}>
            {code || "—"}
          </p>
          <p className="mt-0.5 text-[9px] text-neutral-500">×{qty}</p>
        </div>
      </div>
      <p className="truncate border-t border-neutral-800/80 pt-1 text-[9px] text-neutral-500">{id}</p>
      <Handle className={handleClass} id="out" position={Position.Right} type="source" />
    </div>
  );
}

export function OperationNode(props: NodeProps) {
  const { data, id, selected } = props;
  const d = (data || {}) as OperationNodeData;
  const op = String(d.operation ?? "");
  const glyph = operationGlyph(op);
  const title = operationTitle(op);
  const arity = getOperationInputArity(op);
  return (
    <div className={nodeShell(selected, "border-purple-600/45")}>
      {validationBadge(d.validationSeverity)}
      <div className="mb-1 flex items-center gap-2">
        <span className="flex h-8 w-8 shrink-0 items-center justify-center rounded border border-purple-600/35 bg-purple-950/60 text-sm text-purple-100">
          {glyph}
        </span>
        <div className="min-w-0 flex-1">
          <p className="text-[9px] font-semibold uppercase tracking-[0.14em] text-purple-300/90">
            Operation
          </p>
          <p className="truncate text-[11px] text-neutral-100" title={op}>
            {title}
          </p>
          {d.paint_color ? (
            <p className="mt-0.5 text-[9px] text-amber-200/90">paint: {d.paint_color}</p>
          ) : null}
        </div>
      </div>
      <p className="truncate border-t border-neutral-800/80 pt-1 text-[9px] text-neutral-500">{id}</p>
      {arity >= 2 ? (
        <>
          <Handle
            className={handleClass}
            id="in"
            position={Position.Left}
            style={{ top: "32%" }}
            type="target"
          />
          <Handle
            className={handleClass}
            id="in-1"
            position={Position.Left}
            style={{ top: "68%" }}
            type="target"
          />
        </>
      ) : (
        <Handle
          className={handleClass}
          id="in"
          position={Position.Left}
          style={{ top: "50%", transform: "translateY(-50%)" }}
          type="target"
        />
      )}
      <Handle className={handleClass} id="out" position={Position.Right} type="source" />
    </div>
  );
}

export function IntermediateNode(props: NodeProps) {
  const { data, id, selected } = props;
  const d = (data || {}) as ShapeNodeData;
  const code = String(d.shape_code ?? "");
  return (
    <div className={nodeShell(selected, "border-teal-600/40")}>
      {validationBadge(d.validationSeverity)}
      <div className="mb-1 flex items-start gap-2">
        <MiniShapePreview
          code={code}
          previewAlt={typeof d.preview_alt === "string" ? d.preview_alt : undefined}
          previewImageUrl={typeof d.preview_image_url === "string" ? d.preview_image_url : undefined}
        />
        <div className="min-w-0 flex-1">
          <p className="text-[9px] font-semibold uppercase tracking-[0.14em] text-teal-400/90">
            Intermediate
          </p>
          <p className="text-[9px] text-neutral-500">Produced by upstream op</p>
          <p className="truncate text-[11px] text-neutral-100" title={code || "(pending)"}>
            {code || "—"}
          </p>
        </div>
      </div>
      <p className="truncate border-t border-neutral-800/80 pt-1 text-[9px] text-neutral-500">{id}</p>
      <Handle className={handleClass} id="in" position={Position.Left} type="target" />
      <Handle className={handleClass} id="out" position={Position.Right} type="source" />
    </div>
  );
}

export function OutputNode(props: NodeProps) {
  const { data, id, selected } = props;
  const d = (data || {}) as ShapeNodeData;
  const code = String(d.shape_code ?? "");
  return (
    <div className={nodeShell(selected, "border-orange-500/55")}>
      {validationBadge(d.validationSeverity)}
      <div className="mb-1">
        <p className="text-[9px] font-semibold uppercase tracking-[0.18em] text-orange-300/90">
          Output
        </p>
        <p className="mt-1 text-[9px] text-neutral-500">Target delivery</p>
        <div className="mt-1 flex items-start gap-2">
          <MiniShapePreview
            code={code}
            previewAlt={typeof d.preview_alt === "string" ? d.preview_alt : undefined}
            previewImageUrl={
              typeof d.preview_image_url === "string" ? d.preview_image_url : undefined
            }
          />
          <p className="min-w-0 flex-1 truncate text-[11px] text-neutral-100" title={code || "—"}>
            {code || "—"}
          </p>
        </div>
      </div>
      <p className="truncate border-t border-neutral-800/80 pt-1 text-[9px] text-neutral-500">{id}</p>
      <Handle className={handleClass} id="in" position={Position.Left} type="target" />
    </div>
  );
}

export const recipeNodeTypes = {
  shape: ShapeNode,
  operation: OperationNode,
  intermediate: IntermediateNode,
  output: OutputNode,
};
