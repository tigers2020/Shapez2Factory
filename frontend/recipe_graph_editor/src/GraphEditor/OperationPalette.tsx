import { useMemo, useState } from "react";

import {
  RECIPE_PALETTE_DND_OP,
  RECIPE_PALETTE_DND_SRC,
} from "../EditorFoundation/constants";
import { PALETTE_CATEGORY_ORDER, paletteCategoryForOperation } from "../Operation/paletteGroups";
import { ru } from "../EditorFoundation/recipeUiStrings";
import type { CatalogOperationRow } from "../Operation/nodeCatalogMerge";

export type GraphEditorOperationPaletteProps = Readonly<{
  operations: CatalogOperationRow[];
  engineOperationIds: readonly string[];
  onAddOperation: (operation: string) => void;
  onAddSourceShape: () => void;
}>;

export function GraphEditorOperationPalette({
  engineOperationIds,
  onAddOperation,
  onAddSourceShape,
  operations,
}: GraphEditorOperationPaletteProps) {
  const [query, setQuery] = useState("");
  const engineSet = useMemo(() => new Set(engineOperationIds), [engineOperationIds]);

  const grouped = useMemo(() => {
    const q = query.trim().toLowerCase();
    const filtered = q
      ? operations.filter(
          (o) => o.value.toLowerCase().includes(q) || o.label?.toLowerCase().includes(q),
        )
      : operations;
    const map = new Map<string, CatalogOperationRow[]>();
    for (const cat of PALETTE_CATEGORY_ORDER) {
      if (cat !== "SHAPE") {
        map.set(cat, []);
      }
    }
    for (const o of filtered) {
      const cat = paletteCategoryForOperation(o.value);
      const list = map.get(cat);
      if (list) {
        list.push(o);
      }
    }
    return map;
  }, [operations, query]);

  return (
    <aside
      aria-label="Operation palette"
      className="flex min-h-0 flex-col gap-2 overflow-hidden rounded-lg border border-slate-700 bg-slate-950/90"
    >
      <div className="shrink-0 border-b border-slate-800 p-2">
        <label className="sr-only" htmlFor="op-search">
          Search operations
        </label>
        <input
          className="w-full rounded border border-slate-600 bg-slate-900 px-2 py-1.5 font-mono text-xs text-slate-100 placeholder:text-slate-500"
          id="op-search"
          onChange={(e) => {
            setQuery(e.target.value);
          }}
          placeholder={ru("paletteSearchPh")}
          type="search"
          value={query}
        />
      </div>
      <div className="min-h-0 flex-1 space-y-3 overflow-y-auto p-2">
        <div>
          <p className="mb-1.5 font-mono text-[10px] font-semibold uppercase tracking-wider text-cyan-400/90">
            SHAPE
          </p>
          <ul className="space-y-1">
            <li>
              <button
                className="w-full rounded border border-cyan-800/50 bg-slate-900/80 px-2 py-1.5 text-left text-xs text-cyan-100/90 hover:border-cyan-500/50"
                draggable
                type="button"
                onClick={onAddSourceShape}
                onDragStart={(e) => {
                  e.dataTransfer.setData(RECIPE_PALETTE_DND_SRC, "1");
                  e.dataTransfer.effectAllowed = "copy";
                }}
              >
                <span className="font-mono text-slate-500">◇</span> {ru("emptyUnifiedSourceRow")}
                <span className="mt-0.5 block text-[10px] text-slate-500">
                  {ru("emptyUnifiedHint")}
                </span>
              </button>
            </li>
          </ul>
        </div>
        {PALETTE_CATEGORY_ORDER.filter((c) => c !== "SHAPE").map((cat) => {
          const rows = grouped.get(cat) ?? [];
          return (
            <div key={cat}>
              <p className="mb-1.5 font-mono text-[10px] font-semibold uppercase tracking-wider text-cyan-400/90">
                {cat}
              </p>
              {rows.length === 0 ? (
                <p className="text-[10px] text-slate-600">—</p>
              ) : (
                <ul className="space-y-1">
                  {rows.map((o) => {
                    const enabled = engineSet.has(o.value);
                    return (
                      <li key={o.value}>
                        <button
                          className={[
                            "flex w-full items-center gap-2 rounded border px-2 py-1.5 text-left text-xs",
                            enabled
                              ? "border-slate-700 bg-slate-900/80 text-slate-200 hover:border-cyan-600/40"
                              : "cursor-not-allowed border-slate-800/80 bg-slate-950/50 text-slate-600",
                          ].join(" ")}
                          disabled={!enabled}
                          title={
                            enabled
                              ? ru("opRowHintGridDrag", { value: o.value })
                              : ru("opNotInEngine")
                          }
                          type="button"
                          draggable={enabled}
                          onClick={() => {
                            if (enabled) {
                              onAddOperation(o.value);
                            }
                          }}
                          onDragStart={(e) => {
                            if (!enabled) {
                              e.preventDefault();
                              return;
                            }
                            e.dataTransfer.setData(RECIPE_PALETTE_DND_OP, o.value);
                            e.dataTransfer.effectAllowed = "copy";
                          }}
                        >
                          {o.icon ? (
                            <img
                              alt=""
                              className="h-6 w-6 shrink-0 rounded border border-slate-700 bg-slate-900 object-contain"
                              height={24}
                              src={o.icon}
                              width={24}
                            />
                          ) : (
                            <span className="flex h-6 w-6 shrink-0 items-center justify-center rounded border border-slate-700 font-mono text-[10px] text-slate-500">
                              ◇
                            </span>
                          )}
                          <span className="min-w-0 flex-1 truncate font-mono text-[11px]">{o.label}</span>
                        </button>
                      </li>
                    );
                  })}
                </ul>
              )}
            </div>
          );
        })}
        {operations.length === 0 ? (
          <p className="text-[11px] leading-snug text-amber-200/80">
            {ru("catalogLoadError")}
          </p>
        ) : null}
      </div>
      <div className="shrink-0 border-t border-dashed border-slate-700 p-2">
        <p className="font-mono text-[10px] uppercase tracking-wider text-amber-300/80">
          Quick access
        </p>
        <p className="mt-1 text-[11px] leading-snug text-slate-500">{ru("paletteHelpP1")}</p>
      </div>
    </aside>
  );
}
