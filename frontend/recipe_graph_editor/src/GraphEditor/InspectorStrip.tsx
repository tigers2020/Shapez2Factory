import type { Node } from "@xyflow/react";
import { useMemo } from "react";

import { InspectorNodeProperties } from "./InspectorNodeProperties";
import { shallowRecordFromUnknown, unknownScalarToString } from "./nodeData";
import { ru } from "../EditorFoundation/recipeUiStrings";

export type GraphEditorInspectorStripProps = Readonly<{
  validationOk: boolean | null;
  footerHint: string;
  connectionFeedback: string;
  nodeCount: number;
  edgeCount: number;
  outputCount: number;
  selectedNodeIds: string[];
  nodes: Node[];
  onPatchNodeData: (nodeId: string, patch: Record<string, unknown>) => void;
  notes: string;
  onNotesChange: (text: string) => void;
}>;

export function GraphEditorInspectorStrip({
  connectionFeedback,
  edgeCount,
  footerHint,
  nodeCount,
  nodes,
  notes,
  onNotesChange,
  onPatchNodeData,
  outputCount,
  selectedNodeIds,
  validationOk,
}: GraphEditorInspectorStripProps) {
  const firstSel = useMemo(() => {
    const id = selectedNodeIds[0];
    return id ? nodes.find((n) => n.id === id) : undefined;
  }, [nodes, selectedNodeIds]);

  let selectedSummary: string;
  if (selectedNodeIds.length === 0) {
    selectedSummary = ru("selNone");
  } else if (selectedNodeIds.length === 1) {
    selectedSummary = ru("selOne", { id: selectedNodeIds[0] });
  } else {
    selectedSummary = ru("selMulti", { n: selectedNodeIds.length });
  }

  const propertiesSummary = useMemo(() => {
    if (selectedNodeIds.length === 0) {
      return ru("summaryPickNode");
    }
    if (selectedNodeIds.length > 1) {
      return ru("summaryMultiEdit");
    }
    const n = firstSel;
    if (!n) {
      return "—";
    }
    const t = n.type ?? "?";
    const d = shallowRecordFromUnknown(n.data);
    if (t === "operation") {
      return ru("kindSummaryOp", { op: unknownScalarToString(d.operation, "?") });
    }
    if (t === "shape") {
      return ru("kindSummarySource", { role: unknownScalarToString(d.role, "?") });
    }
    if (t === "intermediate") {
      const code = unknownScalarToString(d.shape_code, "");
      return code
        ? ru("kindSummaryMidCode", { code: code.slice(0, 36) })
        : ru("kindSummaryMidEmpty");
    }
    if (t === "output") {
      const code = unknownScalarToString(d.shape_code, "");
      return code
        ? ru("kindSummaryTargetCode", { code: code.slice(0, 36) })
        : ru("kindSummaryTargetEmpty");
    }
    return ru("kindUnknown", { t });
  }, [firstSel, selectedNodeIds.length]);

  let validationSummary: string;
  let validationClass: string;
  if (validationOk === null) {
    validationSummary = ru("validationPrompt");
    validationClass = "text-slate-500";
  } else if (validationOk) {
    validationSummary = ru("validationOk");
    validationClass = "text-emerald-300/85";
  } else {
    validationSummary = ru("validationIssues");
    validationClass = "text-rose-300/90";
  }

  return (
    <div
      aria-label="Inspector"
      className="grid shrink-0 grid-cols-5 gap-2 border-t border-slate-800 pt-2"
    >
      <div className="min-h-[72px] rounded border border-slate-700 bg-slate-950/80 p-2">
        <p className="font-mono text-[10px] font-semibold uppercase tracking-wider text-slate-500">
          Selected
        </p>
        <p className="mt-1 text-[11px] leading-snug text-slate-300">{selectedSummary}</p>
      </div>
      <div className="max-h-44 min-h-[72px] overflow-y-auto rounded border border-slate-700 bg-slate-950/80 p-2">
        <p className="font-mono text-[10px] font-semibold uppercase tracking-wider text-slate-500">
          Properties
        </p>
        {selectedNodeIds.length === 1 && firstSel ? (
          <InspectorNodeProperties node={firstSel} onPatch={onPatchNodeData} />
        ) : (
          <p className="mt-1 text-[11px] leading-snug text-slate-400">{propertiesSummary}</p>
        )}
      </div>
      <div className="min-h-[72px] rounded border border-slate-700 bg-slate-950/80 p-2">
        <p className="font-mono text-[10px] font-semibold uppercase tracking-wider text-slate-500">
          Validation
        </p>
        <p className={`mt-1 text-[11px] leading-snug ${validationClass}`}>{validationSummary}</p>
        {(() => {
          if (connectionFeedback) {
            return (
              <p className="mt-1 border-t border-slate-800 pt-1 text-[11px] leading-snug text-amber-200/90">
                {ru("connFeedback")} {connectionFeedback}
              </p>
            );
          }
          if (footerHint) {
            return <p className="mt-1 text-[10px] leading-snug text-slate-500">{footerHint}</p>;
          }
          return null;
        })()}
      </div>
      <div className="min-h-[72px] rounded border border-slate-700 bg-slate-950/80 p-2">
        <p className="font-mono text-[10px] font-semibold uppercase tracking-wider text-slate-500">
          Stats
        </p>
        <p className="mt-1 font-mono text-[11px] leading-snug text-slate-400">
          {ru("statsLine", { nodeCount, edgeCount, outputCount })}
        </p>
      </div>
      <div className="flex min-h-[72px] flex-col rounded border border-slate-700 bg-slate-950/80 p-2">
        <label className="font-mono text-[10px] font-semibold uppercase tracking-wider text-slate-500" htmlFor="inspector-notes">
          Notes
        </label>
        <textarea
          className="mt-1 min-h-[52px] w-full flex-1 resize-y rounded border border-slate-700 bg-slate-900 px-1.5 py-1 font-mono text-[10px] leading-snug text-slate-300 placeholder:text-slate-600"
          id="inspector-notes"
          onChange={(e) => {
            onNotesChange(e.target.value);
          }}
          placeholder={ru("notesPlaceholder")}
          spellCheck={true}
          value={notes}
        />
        <p className="mt-0.5 text-[9px] text-slate-600">
          {ru("notesFooter")}
        </p>
      </div>
    </div>
  );
}
