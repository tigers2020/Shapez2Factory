import type { Node } from "@xyflow/react";
import { useCallback, useEffect, useMemo, useState } from "react";

type InspectorNodePropertiesProps = {
  node: Node | undefined;
  onPatch: (nodeId: string, patch: Record<string, unknown>) => void;
};

function coerceRecord(data: unknown): Record<string, unknown> {
  return data && typeof data === "object" && !Array.isArray(data)
    ? { ...(data as Record<string, unknown>) }
    : {};
}

export function InspectorNodeProperties({ node, onPatch }: InspectorNodePropertiesProps) {
  const [shapeCode, setShapeCode] = useState("");
  const [quantity, setQuantity] = useState("1");
  const [operation, setOperation] = useState("");
  const [paintColor, setPaintColor] = useState("");

  const dataSig = useMemo(() => JSON.stringify(node?.data ?? null), [node?.data]);

  useEffect(() => {
    if (!node) {
      return;
    }
    const d = coerceRecord(node.data);
    setShapeCode(String(d.shape_code ?? ""));
    setQuantity(String(d.quantity ?? 1));
    setOperation(String(d.operation ?? ""));
    setPaintColor(String(d.paint_color ?? ""));
  }, [node?.id, dataSig]);

  const apply = useCallback(() => {
    if (!node) {
      return;
    }
    const t = node.type ?? "";
    if (t === "operation") {
      const next: Record<string, unknown> = { operation: operation.trim() };
      if (operation.trim() === "painter") {
        const pc = paintColor.trim().slice(0, 1);
        next.paint_color = pc || "r";
      } else {
        next.paint_color = undefined;
      }
      onPatch(node.id, next);
      return;
    }
    const q = Number.parseInt(quantity, 10);
    onPatch(node.id, {
      shape_code: shapeCode.trim(),
      quantity: Number.isFinite(q) && q >= 1 ? q : 1,
    });
  }, [node, onPatch, operation, paintColor, quantity, shapeCode]);

  if (!node) {
    return <p className="mt-1 text-[11px] leading-snug text-slate-500">노드를 선택하세요.</p>;
  }

  if (node.type === "operation") {
    return (
      <div className="mt-1 space-y-1.5">
        <label className="block">
          <span className="font-mono text-[9px] text-slate-500">operation</span>
          <input
            className="mt-0.5 w-full rounded border border-slate-600 bg-slate-900 px-1.5 py-1 font-mono text-[10px] text-slate-100"
            onChange={(e) => {
              setOperation(e.target.value);
            }}
            spellCheck={false}
            value={operation}
          />
        </label>
        {operation.trim() === "painter" ? (
          <label className="block">
            <span className="font-mono text-[9px] text-slate-500">paint_color</span>
            <input
              className="mt-0.5 w-full rounded border border-slate-600 bg-slate-900 px-1.5 py-1 font-mono text-[10px] text-slate-100"
              maxLength={1}
              onChange={(e) => {
                setPaintColor(e.target.value);
              }}
              value={paintColor}
            />
          </label>
        ) : null}
        <button
          className="w-full rounded border border-cyan-700/50 bg-cyan-950/30 px-2 py-1 font-mono text-[10px] text-cyan-100 hover:border-cyan-500/60"
          type="button"
          onClick={apply}
        >
          적용
        </button>
      </div>
    );
  }

  return (
    <div className="mt-1 space-y-1.5">
      <label className="block">
        <span className="font-mono text-[9px] text-slate-500">shape_code</span>
        <input
          className="mt-0.5 w-full rounded border border-slate-600 bg-slate-900 px-1.5 py-1 font-mono text-[10px] text-slate-100"
          onChange={(e) => {
            setShapeCode(e.target.value);
          }}
          spellCheck={false}
          value={shapeCode}
        />
      </label>
      <label className="block">
        <span className="font-mono text-[9px] text-slate-500">quantity</span>
        <input
          className="mt-0.5 w-full rounded border border-slate-600 bg-slate-900 px-1.5 py-1 font-mono text-[10px] text-slate-100"
          inputMode="numeric"
          min={1}
          onChange={(e) => {
            setQuantity(e.target.value);
          }}
          type="number"
          value={quantity}
        />
      </label>
      <button
        className="w-full rounded border border-cyan-700/50 bg-cyan-950/30 px-2 py-1 font-mono text-[10px] text-cyan-100 hover:border-cyan-500/60"
        type="button"
        onClick={apply}
      >
        적용
      </button>
      <p className="font-mono text-[9px] text-slate-600">
        더블클릭 편집과 동일 필드입니다. role은 고정입니다.
      </p>
    </div>
  );
}
