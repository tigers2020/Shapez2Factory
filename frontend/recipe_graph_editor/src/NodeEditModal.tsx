import type { Node } from "@xyflow/react";
import { useCallback, useEffect, useId, useMemo, useState } from "react";

import type { CatalogOperationRow } from "./recipeNodeCatalogMerge";
import { RecipeShapePreview } from "./recipeShapePreview";
import { ru } from "./recipeUiStrings";

export type NodeEditAnchor = {
  /** `rf-editor-canvas` 기준 px — 카드 가로 중앙 */
  left: number;
  /** `rf-editor-canvas` 기준 px — 카드 상단 */
  top: number;
};

type NodeEditModalProps = {
  node: Node;
  anchor: NodeEditAnchor;
  catalogOperations: CatalogOperationRow[];
  engineOperationIds: readonly string[];
  onClose: () => void;
  onApply: (data: Record<string, unknown>) => void;
};

function coerceRecord(data: unknown): Record<string, unknown> {
  return data && typeof data === "object" && !Array.isArray(data)
    ? { ...(data as Record<string, unknown>) }
    : {};
}

export function NodeEditModal({
  anchor,
  catalogOperations,
  engineOperationIds,
  node,
  onApply,
  onClose,
}: NodeEditModalProps) {
  const titleId = useId();
  const base = useMemo(() => coerceRecord(node.data), [node.data]);
  const dataSig = useMemo(() => JSON.stringify(node.data ?? null), [node.data]);

  const [shapeCode, setShapeCode] = useState(String(base.shape_code ?? ""));
  const [quantity, setQuantity] = useState(String(base.quantity ?? 1));
  const [operation, setOperation] = useState(String(base.operation ?? ""));
  const [paintColor, setPaintColor] = useState(
    String(base.paint_color ?? base.crystal_color ?? ""),
  );

  const engineSet = useMemo(() => new Set(engineOperationIds), [engineOperationIds]);

  const catalogSorted = useMemo(() => {
    return [...catalogOperations].sort((a, b) =>
      (a.label || a.value).localeCompare(b.label || b.value, undefined, { sensitivity: "base" }),
    );
  }, [catalogOperations]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      }
    };
    window.addEventListener("keydown", onKey);
    return () => {
      window.removeEventListener("keydown", onKey);
    };
  }, [onClose]);

  useEffect(() => {
    const d = coerceRecord(node.data);
    setShapeCode(String(d.shape_code ?? ""));
    setQuantity(String(d.quantity ?? 1));
    setOperation(String(d.operation ?? ""));
    setPaintColor(String(d.paint_color ?? d.crystal_color ?? ""));
  }, [node.id, dataSig]);

  const opTrim = operation.trim();
  const opKnownInCatalog = catalogSorted.some((r) => r.value === opTrim);

  const apply = useCallback(() => {
    const t = node.type ?? "";
    if (t === "operation") {
      const next: Record<string, unknown> = { operation: operation.trim() };
      const op = operation.trim();
      if (op === "painter") {
        const pc = paintColor.trim().slice(0, 1);
        next.paint_color = pc || "r";
        next.crystal_color = undefined;
      } else if (op === "crystal_generator") {
        const cc = paintColor.trim().slice(0, 1);
        next.crystal_color = cc || "c";
        next.paint_color = undefined;
      } else {
        next.paint_color = undefined;
        next.crystal_color = undefined;
      }
      onApply(next);
      return;
    }
    const q = Number.parseInt(quantity, 10);
    onApply({
      shape_code: shapeCode.trim(),
      quantity: Number.isFinite(q) && q >= 1 ? q : 1,
    });
  }, [node.type, onApply, operation, paintColor, quantity, shapeCode]);

  const modalHeading =
    node.type === "operation"
      ? ru("modalHeadingOperation")
      : node.type === "output"
        ? ru("modalHeadingOutput")
        : node.type === "intermediate"
          ? ru("modalHeadingIntermediate")
          : ru("modalHeadingSource");

  const roleLabel =
    typeof base.role === "string"
      ? base.role
      : node.type === "output"
        ? "target"
        : node.type === "shape"
          ? "source"
          : "—";

  const shapeHint =
    node.type === "intermediate" && !String(base.shape_code ?? "").trim()
      ? ru("kindSummaryMidEmpty")
      : node.type === "output" && !String(base.shape_code ?? "").trim()
        ? ru("kindSummaryTargetEmpty")
        : "";

  return (
    <>
      <button
        aria-label={ru("ariaCloseEditor")}
        className="absolute inset-0 z-40 cursor-default bg-black/35"
        type="button"
        onClick={onClose}
      />
      <div
        aria-labelledby={titleId}
        className="absolute z-50 w-[min(92vw,320px)] rounded-lg border border-cyan-700/50 bg-slate-950/98 p-3 shadow-2xl shadow-black/60 backdrop-blur-sm"
        role="dialog"
        style={{
          left: anchor.left,
          top: Math.max(8, anchor.top),
          transform: "translate(-50%, calc(-100% - 12px))",
        }}
      >
        <div className="mb-2 flex items-start justify-between gap-2">
          <div className="min-w-0">
            <p className="font-mono text-[9px] font-semibold uppercase tracking-wider text-cyan-400/90">
              {modalHeading}
            </p>
            <h2 className="mt-0.5 truncate font-mono text-xs text-slate-100" id={titleId}>
              {node.id}
            </h2>
            {node.type !== "operation" ? (
              <p className="mt-1 font-mono text-[9px] text-slate-500">
                {ru("modalNodeMeta")}: <span className="text-slate-400">{roleLabel}</span>
              </p>
            ) : null}
          </div>
          <button
            className="shrink-0 rounded border border-slate-600 px-2 py-0.5 text-[11px] text-slate-300 hover:border-rose-600/50 hover:text-rose-200"
            type="button"
            onClick={onClose}
          >
            {ru("btnClose")}
          </button>
        </div>

        {node.type === "operation" ? (
          <div className="space-y-2">
            <label className="block">
              <span className="mb-0.5 block font-mono text-[10px] text-slate-500">
                {ru("modalOperationField")}
              </span>
              <select
                className="w-full rounded border border-slate-600 bg-slate-900 px-2 py-1.5 font-mono text-xs text-slate-100"
                value={opTrim}
                onChange={(e) => {
                  setOperation(e.target.value);
                }}
              >
                <option disabled value="">
                  —
                </option>
                {opTrim && !opKnownInCatalog ? (
                  <option value={opTrim}>
                    {opTrim} ({ru("modalUnknownOp")})
                  </option>
                ) : null}
                {catalogSorted.map((row) => {
                  const en = engineSet.has(row.value);
                  return (
                    <option key={row.value} disabled={!en} value={row.value}>
                      {row.label || row.value}
                      {!en ? " (engine off)" : ""}
                    </option>
                  );
                })}
              </select>
            </label>
            {(operation.trim() === "painter" || operation.trim() === "crystal_generator") ? (
              <label className="block">
                <span className="mb-0.5 block font-mono text-[10px] text-slate-500">
                  {operation.trim() === "crystal_generator"
                    ? ru("crystalColorHint")
                    : ru("paintColorHint")}
                </span>
                <input
                  className="w-full rounded border border-slate-600 bg-slate-900 px-2 py-1.5 font-mono text-xs text-slate-100"
                  maxLength={1}
                  onChange={(e) => {
                    setPaintColor(e.target.value);
                  }}
                  value={paintColor}
                />
              </label>
            ) : null}
          </div>
        ) : (
          <div className="space-y-2">
            <div>
              <p className="mb-1 font-mono text-[10px] text-slate-500">{ru("modalPreviewLabel")}</p>
              <div className="flex justify-center">
                <RecipeShapePreview
                  code={shapeCode}
                  previewAlt={typeof base.preview_alt === "string" ? base.preview_alt : undefined}
                  previewImageUrl={
                    typeof base.preview_image_url === "string" ? base.preview_image_url : undefined
                  }
                  variant="modal"
                />
              </div>
            </div>
            {shapeHint ? (
              <p className="text-center font-mono text-[10px] text-amber-200/85">{shapeHint}</p>
            ) : null}
            <label className="block">
              <span className="mb-0.5 block font-mono text-[10px] text-slate-500">shape_code</span>
              <input
                className="w-full rounded border border-slate-600 bg-slate-900 px-2 py-1.5 font-mono text-xs text-slate-100"
                onChange={(e) => {
                  setShapeCode(e.target.value);
                }}
                spellCheck={false}
                value={shapeCode}
              />
            </label>
            <label className="block">
              <span className="mb-0.5 block font-mono text-[10px] text-slate-500">quantity</span>
              <input
                className="w-full rounded border border-slate-600 bg-slate-900 px-2 py-1.5 font-mono text-xs text-slate-100"
                inputMode="numeric"
                min={1}
                onChange={(e) => {
                  setQuantity(e.target.value);
                }}
                type="number"
                value={quantity}
              />
            </label>
            {typeof base.role === "string" ? (
              <p className="font-mono text-[10px] text-slate-500">
                role: <span className="text-slate-400">{base.role}</span> {ru("roleReadonly")}
              </p>
            ) : null}
          </div>
        )}

        <div className="mt-3 flex justify-end gap-2">
          <button
            className="rounded border border-slate-600 px-3 py-1.5 text-xs text-slate-300 hover:border-slate-500"
            type="button"
            onClick={onClose}
          >
            {ru("btnCancel")}
          </button>
          <button
            className="rounded border border-cyan-600/60 bg-cyan-950/40 px-3 py-1.5 text-xs font-semibold text-cyan-100 hover:border-cyan-500"
            disabled={node.type === "operation" && !engineSet.has(opTrim)}
            type="button"
            onClick={apply}
          >
            {ru("btnApply")}
          </button>
        </div>
      </div>
    </>
  );
}
