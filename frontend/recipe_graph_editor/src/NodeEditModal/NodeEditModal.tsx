import type { Node } from "@xyflow/react";
import type { ReactNode } from "react";
import { useCallback, useEffect, useId, useMemo, useState } from "react";

import type { CatalogOperationRow } from "../Operation/nodeCatalogMerge";
import { operationChangeGroupId } from "../Operation/paletteGroups";
import { buildNodeEditApplyPayload } from "./apply";
import { formFieldsFromNodeData } from "./formState";
import {
  modalHeadingForType,
  roleLabelFromBase,
  shapeHintFromBase,
} from "./labels";
import { coerceRecord } from "./scalars";
import {
  IntermediatePanel,
  OperationFields,
  ShapeOutputPanel,
} from "./Panels";
import { ru } from "../EditorFoundation/recipeUiStrings";

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

export function NodeEditModal({
  anchor,
  catalogOperations,
  engineOperationIds,
  node,
  onApply,
  onClose,
}: Readonly<NodeEditModalProps>) {
  const titleId = useId();
  const base = useMemo(() => coerceRecord(node.data), [node.data]);
  const dataSig = useMemo(() => JSON.stringify(node.data ?? null), [node.data]);

  const initialFields = useMemo(() => formFieldsFromNodeData(base), [base]);

  const [carrierMode, setCarrierMode] = useState(initialFields.carrierMode);
  const [shapeCode, setShapeCode] = useState(initialFields.shapeCode);
  const [fluidInk, setFluidInk] = useState(initialFields.fluidInk);
  const [quantity, setQuantity] = useState(initialFields.quantity);
  const [operation, setOperation] = useState(initialFields.operation);
  const [paintColor, setPaintColor] = useState(initialFields.paintColor);

  const engineSet = useMemo(() => new Set(engineOperationIds), [engineOperationIds]);

  const catalogSorted = useMemo(() => {
    return [...catalogOperations].sort((a, b) =>
      (a.label || a.value).localeCompare(b.label || b.value, undefined, { sensitivity: "base" }),
    );
  }, [catalogOperations]);

  const persistedOperation = formFieldsFromNodeData(base).operation;
  const operationSwapGroup = operationChangeGroupId(persistedOperation);
  const catalogSortedForOperationEdit = useMemo(() => {
    if (operationSwapGroup === null) {
      return catalogSorted;
    }
    return catalogSorted.filter((row) => operationChangeGroupId(row.value) === operationSwapGroup);
  }, [catalogSorted, operationSwapGroup]);

  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        onClose();
      }
    };
    globalThis.addEventListener("keydown", onKey);
    return () => {
      globalThis.removeEventListener("keydown", onKey);
    };
  }, [onClose]);

  useEffect(() => {
    const d = coerceRecord(node.data);
    const f = formFieldsFromNodeData(d);
    setShapeCode(f.shapeCode);
    setFluidInk(f.fluidInk);
    setCarrierMode(f.carrierMode);
    setQuantity(f.quantity);
    setOperation(f.operation);
    setPaintColor(f.paintColor);
  }, [node.id, dataSig]);

  const opTrim = operation.trim();
  const opKnownInCatalog = catalogSorted.some((r) => r.value === opTrim);

  const apply = useCallback(() => {
    const patch = buildNodeEditApplyPayload({
      nodeType: node.type,
      base,
      operation,
      paintColor,
      shapeCode,
      quantity,
      carrierMode,
      fluidInk,
    });
    if (patch !== null) {
      onApply(patch);
    }
  }, [
    base,
    carrierMode,
    fluidInk,
    node.type,
    onApply,
    operation,
    paintColor,
    quantity,
    shapeCode,
  ]);

  const modalHeading = modalHeadingForType(node.type);
  const roleLabel = roleLabelFromBase(base, node.type);
  const shapeHint = shapeHintFromBase(node.type, base);

  let mainBody: ReactNode;
  if (node.type === "operation") {
    mainBody = (
      <OperationFields
        catalogSorted={catalogSortedForOperationEdit}
        engineSet={engineSet}
        operation={operation}
        opKnownInCatalog={opKnownInCatalog}
        opTrim={opTrim}
        paintColor={paintColor}
        setOperation={setOperation}
        setPaintColor={setPaintColor}
      />
    );
  } else if (node.type === "intermediate") {
    mainBody = (
      <IntermediatePanel base={base} roleLabel={roleLabel} shapeHint={shapeHint} />
    );
  } else {
    mainBody = (
      <ShapeOutputPanel
        base={base}
        carrierMode={carrierMode}
        fluidInk={fluidInk}
        node={node}
        quantity={quantity}
        setCarrierMode={setCarrierMode}
        setFluidInk={setFluidInk}
        setQuantity={setQuantity}
        setShapeCode={setShapeCode}
        shapeCode={shapeCode}
        shapeHint={shapeHint}
      />
    );
  }

  return (
    <>
      <button
        aria-label={ru("ariaCloseEditor")}
        className="absolute inset-0 z-40 cursor-default bg-black/35"
        type="button"
        onClick={onClose}
      />
      <dialog
        aria-labelledby={titleId}
        className="absolute z-50 w-[min(92vw,320px)] rounded-lg border border-cyan-700/50 bg-slate-950/98 p-3 shadow-2xl shadow-black/60 backdrop-blur-sm open:flex open:max-h-none open:max-w-none open:flex-col"
        open
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
            {node.type === "operation" ? null : (
              <p className="mt-1 font-mono text-[9px] text-slate-500">
                {ru("modalNodeMeta")}: <span className="text-slate-400">{roleLabel}</span>
              </p>
            )}
          </div>
          <button
            className="shrink-0 rounded border border-slate-600 px-2 py-0.5 text-[11px] text-slate-300 hover:border-rose-600/50 hover:text-rose-200"
            type="button"
            onClick={onClose}
          >
            {ru("btnClose")}
          </button>
        </div>

        {mainBody}

        {node.type === "intermediate" ? (
          <div className="mt-3 flex justify-end">
            <button
              className="rounded border border-slate-600 px-3 py-1.5 text-xs text-slate-300 hover:border-slate-500"
              type="button"
              onClick={onClose}
            >
              {ru("btnClose")}
            </button>
          </div>
        ) : (
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
        )}
      </dialog>
    </>
  );
}
