/** UI strings for the recipe graph editor (en/ko); follows Django javascript-catalog when embedded. */

import { t } from "./i18n/djangoGettext";

const EN = {
  rfInvalidDoc:
    "Saved graph_document failed schema validation. Fix the JSON via Admin or API, then reopen.",
  rfEmptyWithSteps:
    "The canvas has no nodes. Click or drag sources and operations from the left (auto-sync with DB step rows follows separate rules on save/recompute).",
  rfEmptyDefault:
    "Click or drag operations or an empty source from the left, connect handles, then Dry-run/Save.",
  paletteSearchPh: "Search operations…",
  emptySourceRow: "Empty source material",
  emptySourceHint: "Default {code} — edit via double-click or recompute",
  /** @deprecated Use emptyUnifiedSourceRow in UI; kept for gettext catalogs. */
  emptyFluidRow: "Empty fluid carrier",
  /** @deprecated Use emptyUnifiedHint in UI. */
  emptyFluidHint:
    "Default {code} — primary RGB only; pick R/G/B in the node editor. Secondary colors (c/m/y/w) via color_mixer.",
  emptyUnifiedSourceRow: "Empty source (shape or fluid)",
  emptyUnifiedHint:
    "New shape sources cycle the four full base materials (Cu/Ru/Su/Wu) — set carrier to fluid in the node editor (RGB) or wire per-port rules.",
  fluidInkLabel: "Fluid ink (R / G / B)",
  fluidInkHint:
    "Encoded as uniform circle layer (e.g. CrCrCrCr). Use a color_mixer in the graph for cyan/magenta/yellow/white.",
  carrierLabel: "Carrier",
  carrierMaterial: "Shape (material)",
  carrierFluid: "Fluid",
  paintColorFallbackHint:
    "Optional legacy fallback when only one shape input is wired; two-wire painter: fluid on upper in-1, shape on lower in.",
  opRowHintGridDrag:
    "{value} — click (grid place) or drag to canvas (drop position)",
  opNotInEngine: "This operation is not in the recipe graph engine recompute list.",
  catalogLoadError:
    "Could not load catalog operations. Refresh or check the macro-graph-initial-catalog script.",
  paletteHelpP1:
    "Click adds at the viewport center; drag onto the canvas to place at the drop point (operations auto-create outputs through intermediate). Source palette entry is material by default — switch to fluid in the node editor when needed.",
  selNone: "Nothing selected.",
  selOne: "1 · {id}",
  selMulti: "{n} nodes selected.",
  summaryPickNode: "Select a node to see a summary.",
  summaryMultiEdit: "Multi-select — edit properties after selecting a single node (double-click).",
  lblOperation: "Operation",
  lblOutput: "Output",
  lblIntermediate: "Intermediate",
  lblSource: "Source",
  modalHeadingOperation: "Operation node",
  modalHeadingOutput: "Output node",
  modalHeadingIntermediate: "Intermediate node",
  modalHeadingSource: "Source node",
  ariaCloseEditor: "Close editor",
  titleNodeSuffix: "node",
  btnClose: "Close",
  paintColorHint: "Legacy paint_color: r, g, or b (or unset when using two inputs + fluid wire)",
  crystalColorHint: "crystal_color (one letter, optional)",
  crystalColorFallbackHint:
    "Leave empty for two-wire mode: fluid on upper in-1, target shape on lower in (same as painter).",
  roleReadonly: "(read-only)",
  btnCancel: "Cancel",
  btnApply: "Apply",
  hintInspectorSelect: "Select a node.",
  hintApplySameAsDbl: "Same fields as double-click edit. role is fixed.",
  kindSummaryOp: "Operation: {op}",
  kindSummarySource: "Source · role {role}",
  kindSummaryMidCode: "Intermediate · {code}",
  kindSummaryMidEmpty: "Intermediate — shape_code after dry-run",
  kindSummaryTargetCode: "Delivery · {code}",
  kindSummaryTargetEmpty: "Delivery — shape_code unset",
  kindUnknown: "{t} type",
  validationPrompt: "Run Dry-run or Save for server validation.",
  validationOk: "No issues from the last dry-run/save.",
  validationIssues: "Validation issues in the last result — check the footer message.",
  connFeedback: "Connection attempt:",
  statsLine: "Nodes {nodeCount} · Edges {edgeCount} · Outputs {outputCount}",
  notesPlaceholder: "Local notes (this browser · per recipe only)",
  notesFooter:
    "Not saved to server · only one delivery line from intermediate→output is allowed.",
  opDropRejected: "Operations not in the engine recompute list cannot be placed on the canvas.",
  inspectorSummaryHint:
    "Double-click the node on the canvas for full edit (operation picker, large shape preview).",
  modalOperationField: "Operation",
  modalPreviewLabel: "Preview",
  modalNodeMeta: "Node id · role",
  modalUnknownOp: "not in catalog",
  intermediateReadOnlyNotice:
    "Operation outputs are determined by recompute; shape, carrier, and quantity cannot be edited here.",
} as const;

export type RecipeUiKey = keyof typeof EN;

/** Interpolate `{name}` placeholders; Korean comes from djangojs when catalog is loaded. */
export function ru(key: RecipeUiKey, vars?: Record<string, string | number>): string {
  let s = t(EN[key]);
  if (vars) {
    for (const [name, val] of Object.entries(vars)) {
      s = s.replaceAll(`{${name}}`, String(val));
    }
  }
  return s;
}
