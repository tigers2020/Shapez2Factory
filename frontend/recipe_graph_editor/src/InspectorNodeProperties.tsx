import type { Node } from "@xyflow/react";

import { ru } from "./recipeUiStrings";

type InspectorNodePropertiesProps = Readonly<{
  node: Node | undefined;
  onPatch: (nodeId: string, patch: Record<string, unknown>) => void;
}>;

export function InspectorNodeProperties({ node, onPatch: _onPatch }: InspectorNodePropertiesProps) {
  if (!node) {
    return <p className="mt-1 text-[11px] leading-snug text-slate-500">{ru("hintInspectorSelect")}</p>;
  }

  const t = node.type ?? "?";
  return (
    <div className="mt-1 space-y-1">
      <p className="font-mono text-[10px] text-slate-300">
        {t} · <span className="text-slate-400">{node.id}</span>
      </p>
      <p className="text-[10px] leading-snug text-slate-500">{ru("inspectorSummaryHint")}</p>
    </div>
  );
}
