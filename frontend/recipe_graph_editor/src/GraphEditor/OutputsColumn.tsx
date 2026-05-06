export function GraphEditorOutputsColumn() {
  return (
    <aside
      aria-label="Outputs"
      className="flex min-h-0 flex-col gap-2 overflow-hidden rounded-lg border border-slate-700 bg-slate-950/90 p-2"
    >
      <p className="font-mono text-[10px] font-semibold uppercase tracking-[0.2em] text-purple-300/90">
        Outputs
      </p>
      <div className="flex-1 space-y-2 overflow-y-auto rounded border border-slate-800 bg-slate-900/50 p-2">
        <div className="rounded border border-orange-500/40 bg-slate-900 px-2 py-2 text-xs text-slate-200">
          <span className="font-mono text-[10px] text-orange-300/90">Output 1</span>
          <p className="mt-1 text-[11px] text-slate-500">Terminal (placeholder)</p>
        </div>
      </div>
    </aside>
  );
}
