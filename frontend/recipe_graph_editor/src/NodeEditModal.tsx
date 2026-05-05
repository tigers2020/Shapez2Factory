import type { Node } from "@xyflow/react";
import { useCallback, useEffect, useId, useMemo, useState } from "react";

export type NodeEditAnchor = {
  /** `rf-editor-canvas` 기준 px — 카드 가로 중앙 */
  left: number;
  /** `rf-editor-canvas` 기준 px — 카드 상단 */
  top: number;
};

type NodeEditModalProps = {
  node: Node;
  anchor: NodeEditAnchor;
  onClose: () => void;
  onApply: (data: Record<string, unknown>) => void;
};

function coerceRecord(data: unknown): Record<string, unknown> {
  return data && typeof data === "object" && !Array.isArray(data)
    ? { ...(data as Record<string, unknown>) }
    : {};
}

export function NodeEditModal({ anchor, node, onApply, onClose }: NodeEditModalProps) {
  const titleId = useId();
  const base = useMemo(() => coerceRecord(node.data), [node.data]);
  const [shapeCode, setShapeCode] = useState(String(base.shape_code ?? ""));
  const [quantity, setQuantity] = useState(String(base.quantity ?? 1));
  const [operation, setOperation] = useState(String(base.operation ?? ""));
  const [paintColor, setPaintColor] = useState(String(base.paint_color ?? ""));

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

  const apply = useCallback(() => {
    const t = node.type ?? "";
    if (t === "operation") {
      const next: Record<string, unknown> = { operation: operation.trim() };
      if (operation.trim() === "painter") {
        const pc = paintColor.trim().slice(0, 1);
        next.paint_color = pc || "r";
      } else {
        next.paint_color = undefined;
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

  const kindLabel =
    node.type === "operation"
      ? "연산"
      : node.type === "output"
        ? "출력"
        : node.type === "intermediate"
          ? "중간"
          : "소스";

  return (
    <>
      <button
        aria-label="편집 닫기"
        className="absolute inset-0 z-40 cursor-default bg-black/35"
        type="button"
        onClick={onClose}
      />
      <div
        aria-labelledby={titleId}
        className="absolute z-50 w-[min(92vw,280px)] rounded-lg border border-cyan-700/50 bg-slate-950/98 p-3 shadow-2xl shadow-black/60 backdrop-blur-sm"
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
              {kindLabel} 노드
            </p>
            <h2 className="mt-0.5 truncate font-mono text-xs text-slate-100" id={titleId}>
              {node.id}
            </h2>
          </div>
          <button
            className="shrink-0 rounded border border-slate-600 px-2 py-0.5 text-[11px] text-slate-300 hover:border-rose-600/50 hover:text-rose-200"
            type="button"
            onClick={onClose}
          >
            닫기
          </button>
        </div>

        {node.type === "operation" ? (
          <div className="space-y-2">
            <label className="block">
              <span className="mb-0.5 block font-mono text-[10px] text-slate-500">operation</span>
              <input
                className="w-full rounded border border-slate-600 bg-slate-900 px-2 py-1.5 font-mono text-xs text-slate-100"
                onChange={(e) => {
                  setOperation(e.target.value);
                }}
                spellCheck={false}
                value={operation}
              />
            </label>
            {operation.trim() === "painter" ? (
              <label className="block">
                <span className="mb-0.5 block font-mono text-[10px] text-slate-500">
                  paint_color (한 글자)
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
                role: <span className="text-slate-400">{base.role}</span> (읽기 전용)
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
            취소
          </button>
          <button
            className="rounded border border-cyan-600/60 bg-cyan-950/40 px-3 py-1.5 text-xs font-semibold text-cyan-100 hover:border-cyan-500"
            type="button"
            onClick={apply}
          >
            적용
          </button>
        </div>
      </div>
    </>
  );
}
