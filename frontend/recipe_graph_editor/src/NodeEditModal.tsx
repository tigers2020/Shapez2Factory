import type { Node } from "@xyflow/react";
import type { ReactNode } from "react";
import { useCallback, useEffect, useId, useMemo, useState } from "react";

import type { FluidPrimaryInk } from "./fluidSourceUi";
import { fluidShapeCodeFromInk, inkFromFluidShapeCode } from "./fluidSourceUi";
import { operationChangeGroupId } from "./operationPaletteGroups";
import type { CatalogOperationRow } from "./recipeNodeCatalogMerge";
import { nodeDataIsFluidCarrier } from "./recipeConnection";
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

/** Avoid `[object Object]` when node fields are accidentally non-scalars. */
function scalarToUiString(value: unknown, fallback = ""): string {
  if (value === null || value === undefined) {
    return fallback;
  }
  if (typeof value === "string") {
    return value;
  }
  if (typeof value === "number" || typeof value === "boolean" || typeof value === "bigint") {
    return String(value);
  }
  return fallback;
}

function scalarQuantityToUiString(value: unknown, fallback: number): string {
  if (typeof value === "number" && Number.isFinite(value)) {
    return String(value);
  }
  if (typeof value === "string") {
    return value;
  }
  return String(fallback);
}

function paintOrCrystalToUiString(base: Record<string, unknown>): string {
  const chosen = base.paint_color ?? base.crystal_color;
  return scalarToUiString(chosen, "");
}

function modalHeadingForType(nodeType: string | undefined): string {
  if (nodeType === "operation") {
    return ru("modalHeadingOperation");
  }
  if (nodeType === "output") {
    return ru("modalHeadingOutput");
  }
  if (nodeType === "intermediate") {
    return ru("modalHeadingIntermediate");
  }
  return ru("modalHeadingSource");
}

function roleLabelFromBase(base: Record<string, unknown>, nodeType: string | undefined): string {
  if (typeof base.role === "string") {
    return base.role;
  }
  if (nodeType === "output") {
    return "target";
  }
  if (nodeType === "shape") {
    return "source";
  }
  return "—";
}

function shapeHintFromBase(nodeType: string | undefined, base: Record<string, unknown>): string {
  const codeStr = scalarToUiString(base.shape_code, "");
  const empty = !codeStr.trim();
  if (nodeType === "intermediate" && empty) {
    return ru("kindSummaryMidEmpty");
  }
  if (nodeType === "output" && empty) {
    return ru("kindSummaryTargetEmpty");
  }
  return "";
}

function buildOperationApplyPayload(operation: string, paintColor: string): Record<string, unknown> {
  const next: Record<string, unknown> = { operation: operation.trim() };
  const op = operation.trim();
  if (op === "painter") {
    const pc = paintColor.trim().slice(0, 1);
    if (pc && "rgb".includes(pc)) {
      next.paint_color = pc;
    } else {
      next.paint_color = undefined;
    }
    next.crystal_color = undefined;
  } else if (op === "crystal_generator") {
    const cc = paintColor.trim().slice(0, 1);
    if (cc) {
      next.crystal_color = cc;
    } else {
      delete next.crystal_color;
    }
    next.paint_color = undefined;
  } else {
    next.paint_color = undefined;
    next.crystal_color = undefined;
  }
  return next;
}

type OperationFieldsProps = Readonly<{
  catalogSorted: CatalogOperationRow[];
  engineSet: Set<string>;
  operation: string;
  opKnownInCatalog: boolean;
  opTrim: string;
  paintColor: string;
  setOperation: (v: string) => void;
  setPaintColor: (v: string) => void;
}>;

function OperationFields({
  catalogSorted,
  engineSet,
  operation,
  opKnownInCatalog,
  opTrim,
  paintColor,
  setOperation,
  setPaintColor,
}: OperationFieldsProps) {
  return (
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
                {en ? "" : " (engine off)"}
              </option>
            );
          })}
        </select>
      </label>
      {operation.trim() === "painter" ? (
        <label className="block">
          <span className="mb-0.5 block font-mono text-[10px] text-slate-500">
            {ru("paintColorHint")}
          </span>
          <select
            className="w-full rounded border border-slate-600 bg-slate-900 px-2 py-1.5 font-mono text-xs text-slate-100"
            value={
              ["r", "g", "b"].includes(paintColor.trim().slice(0, 1))
                ? paintColor.trim().slice(0, 1)
                : ""
            }
            onChange={(e) => {
              setPaintColor(e.target.value);
            }}
          >
            <option value="">— (two-wire / fluid)</option>
            <option value="r">r</option>
            <option value="g">g</option>
            <option value="b">b</option>
          </select>
          <p className="mt-1 text-[10px] leading-snug text-slate-500">{ru("paintColorFallbackHint")}</p>
        </label>
      ) : null}
      {operation.trim() === "crystal_generator" ? (
        <label className="block">
          <span className="mb-0.5 block font-mono text-[10px] text-slate-500">
            {ru("crystalColorHint")}
          </span>
          <input
            className="w-full rounded border border-slate-600 bg-slate-900 px-2 py-1.5 font-mono text-xs text-slate-100"
            maxLength={1}
            onChange={(e) => {
              setPaintColor(e.target.value);
            }}
            value={paintColor}
          />
          <p className="mt-1 text-[10px] leading-snug text-slate-500">{ru("crystalColorFallbackHint")}</p>
        </label>
      ) : null}
    </div>
  );
}

type IntermediatePanelProps = Readonly<{
  base: Record<string, unknown>;
  roleLabel: string;
  shapeCode: string;
  shapeHint: string;
}>;

function IntermediatePanel({ base, roleLabel, shapeCode, shapeHint }: IntermediatePanelProps) {
  return (
    <div className="space-y-2">
      <p className="text-[10px] leading-snug text-slate-400">{ru("intermediateReadOnlyNotice")}</p>
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
      <div className="block">
        <span className="mb-0.5 block font-mono text-[10px] text-slate-500">{ru("carrierLabel")}</span>
        <p className="rounded border border-slate-700/80 bg-slate-900/80 px-2 py-1.5 font-mono text-xs text-slate-300">
          {nodeDataIsFluidCarrier(base) ? ru("carrierFluid") : ru("carrierMaterial")}
        </p>
      </div>
      <div className="block">
        <span className="mb-0.5 block font-mono text-[10px] text-slate-500">shape_code</span>
        <p className="break-all rounded border border-slate-700/80 bg-slate-900/80 px-2 py-1.5 font-mono text-xs text-slate-300">
          {scalarToUiString(base.shape_code, "")}
        </p>
      </div>
      <div className="block">
        <span className="mb-0.5 block font-mono text-[10px] text-slate-500">quantity</span>
        <p className="rounded border border-slate-700/80 bg-slate-900/80 px-2 py-1.5 font-mono text-xs text-slate-300">
          {scalarQuantityToUiString(base.quantity, 1)}
        </p>
      </div>
      <p className="font-mono text-[10px] text-slate-500">
        role: <span className="text-slate-400">{roleLabel}</span>
        {roleLabel === "source" ? null : <> {ru("roleReadonly")}</>}
      </p>
    </div>
  );
}

type ShapeOutputPanelProps = Readonly<{
  base: Record<string, unknown>;
  carrierMode: "material" | "fluid";
  fluidInk: FluidPrimaryInk;
  node: Node;
  quantity: string;
  setCarrierMode: (v: "material" | "fluid") => void;
  setFluidInk: (v: FluidPrimaryInk) => void;
  setQuantity: (v: string) => void;
  setShapeCode: (v: string) => void;
  shapeCode: string;
  shapeHint: string;
}>;

function ShapeOutputPanel({
  base,
  carrierMode,
  fluidInk,
  node,
  quantity,
  setCarrierMode,
  setFluidInk,
  setQuantity,
  setShapeCode,
  shapeCode,
  shapeHint,
}: ShapeOutputPanelProps) {
  const showFluidInkControls =
    node.type === "shape" && carrierMode === "fluid" && base.role === "source";
  const showShapeCodeInput =
    node.type === "shape" && (carrierMode !== "fluid" || base.role !== "source");

  return (
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
      {node.type === "shape" ? (
        <label className="block">
          <span className="mb-0.5 block font-mono text-[10px] text-slate-500">{ru("carrierLabel")}</span>
          <select
            className="w-full rounded border border-slate-600 bg-slate-900 px-2 py-1.5 font-mono text-xs text-slate-100"
            value={carrierMode}
            onChange={(e) => {
              const v = e.target.value as "material" | "fluid";
              setCarrierMode(v);
              if (v === "fluid" && node.type === "shape" && base.role === "source") {
                setShapeCode(fluidShapeCodeFromInk(fluidInk));
              }
            }}
          >
            <option value="material">{ru("carrierMaterial")}</option>
            <option value="fluid">{ru("carrierFluid")}</option>
          </select>
        </label>
      ) : null}
      {showFluidInkControls ? (
        <>
          <label className="block">
            <span className="mb-0.5 block font-mono text-[10px] text-slate-500">
              {ru("fluidInkLabel")}
            </span>
            <select
              className="w-full rounded border border-slate-600 bg-slate-900 px-2 py-1.5 font-mono text-xs text-slate-100"
              value={fluidInk}
              onChange={(e) => {
                const v = e.target.value as FluidPrimaryInk;
                setFluidInk(v);
                setShapeCode(fluidShapeCodeFromInk(v));
              }}
            >
              <option value="r">r (red)</option>
              <option value="g">g (green)</option>
              <option value="b">b (blue)</option>
            </select>
            <p className="mt-1 text-[10px] leading-snug text-slate-500">{ru("fluidInkHint")}</p>
          </label>
          <p className="font-mono text-[10px] text-slate-500">
            shape_code{" "}
            <span className="break-all text-slate-400">{fluidShapeCodeFromInk(fluidInk)}</span>
          </p>
        </>
      ) : null}
      {showShapeCodeInput ? (
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
      ) : null}
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
          role: <span className="text-slate-400">{base.role}</span>
          {base.role === "source" ? null : <> {ru("roleReadonly")}</>}
        </p>
      ) : null}
    </div>
  );
}

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

  const [carrierMode, setCarrierMode] = useState<"material" | "fluid">(() =>
    nodeDataIsFluidCarrier(base) ? "fluid" : "material",
  );

  const [shapeCode, setShapeCode] = useState(() => scalarToUiString(base.shape_code, ""));
  const [fluidInk, setFluidInk] = useState<FluidPrimaryInk>(() =>
    nodeDataIsFluidCarrier(base)
      ? inkFromFluidShapeCode(scalarToUiString(base.shape_code, ""))
      : "r",
  );
  const [quantity, setQuantity] = useState(() => scalarQuantityToUiString(base.quantity, 1));
  const [operation, setOperation] = useState(() => scalarToUiString(base.operation, ""));
  const [paintColor, setPaintColor] = useState(() => paintOrCrystalToUiString(base));

  const engineSet = useMemo(() => new Set(engineOperationIds), [engineOperationIds]);

  const catalogSorted = useMemo(() => {
    return [...catalogOperations].sort((a, b) =>
      (a.label || a.value).localeCompare(b.label || b.value, undefined, { sensitivity: "base" }),
    );
  }, [catalogOperations]);

  const persistedOperation = scalarToUiString(base.operation, "");
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
    setShapeCode(scalarToUiString(d.shape_code, ""));
    setFluidInk(inkFromFluidShapeCode(scalarToUiString(d.shape_code, "")));
    setCarrierMode(nodeDataIsFluidCarrier(d) ? "fluid" : "material");
    setQuantity(scalarQuantityToUiString(d.quantity, 1));
    setOperation(scalarToUiString(d.operation, ""));
    setPaintColor(paintOrCrystalToUiString(d));
  }, [node.id, dataSig]);

  const opTrim = operation.trim();
  const opKnownInCatalog = catalogSorted.some((r) => r.value === opTrim);

  const apply = useCallback(() => {
    const t = node.type ?? "";
    if (t === "intermediate") {
      return;
    }
    if (t === "operation") {
      onApply(buildOperationApplyPayload(operation, paintColor));
      return;
    }
    const q = Number.parseInt(quantity, 10);
    const qty = Number.isFinite(q) && q >= 1 ? q : 1;
    if (node.type === "output") {
      onApply({
        shape_code: shapeCode.trim(),
        quantity: qty,
      });
      return;
    }
    if (node.type !== "shape") {
      return;
    }
    const patch: Record<string, unknown> = { quantity: qty };
    if (carrierMode === "fluid") {
      patch.source_carrier = "fluid";
      if (node.type === "shape" && base.role === "source") {
        patch.shape_code = fluidShapeCodeFromInk(fluidInk);
      } else {
        patch.shape_code = shapeCode.trim();
      }
    } else {
      patch.source_carrier = undefined;
      patch.shape_code = shapeCode.trim();
    }
    onApply(patch);
  }, [
    base.role,
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
      <IntermediatePanel base={base} roleLabel={roleLabel} shapeCode={shapeCode} shapeHint={shapeHint} />
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
