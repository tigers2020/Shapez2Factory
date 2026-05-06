import type { Node } from "@xyflow/react";
import type { FluidPrimaryInk } from "../EditorFoundation/fluidSourceUi";
import { fluidShapeCodeFromInk } from "../EditorFoundation/fluidSourceUi";
import type { CatalogOperationRow } from "../Operation/nodeCatalogMerge";
import { nodeDataIsFluidCarrier } from "../RecipeConnection";
import { RecipeShapePreview } from "../ShapeSprite/RecipeShapePreview";
import { ru } from "../EditorFoundation/recipeUiStrings";
import {
  previewSceneFromBase,
  scalarQuantityToUiString,
  scalarToUiString,
} from "./scalars";

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

export function OperationFields({
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
  shapeHint: string;
}>;

export function IntermediatePanel({ base, roleLabel, shapeHint }: IntermediatePanelProps) {
  return (
    <div className="space-y-2">
      <p className="text-[10px] leading-snug text-slate-400">{ru("intermediateReadOnlyNotice")}</p>
      <div>
        <p className="mb-1 font-mono text-[10px] text-slate-500">{ru("modalPreviewLabel")}</p>
        <div className="flex justify-center">
          <RecipeShapePreview
            code={scalarToUiString(base.shape_code, "")}
            previewAlt={typeof base.preview_alt === "string" ? base.preview_alt : undefined}
            previewImageUrl={
              typeof base.preview_image_url === "string" ? base.preview_image_url : undefined
            }
            previewScene={previewSceneFromBase(base)}
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

export function ShapeOutputPanel({
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
            previewScene={previewSceneFromBase(base)}
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
