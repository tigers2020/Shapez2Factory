export type GraphEditorFooterActionsProps = Readonly<{
  busy: boolean;
  validationOk: boolean | null;
  footerHint: string;
  onDryRun: () => void;
  onSave: () => void;
}>;

export function GraphEditorFooterActions({
  busy,
  footerHint,
  onDryRun,
  onSave,
  validationOk,
}: GraphEditorFooterActionsProps) {
  let validLabel: string;
  let validClass: string;
  if (validationOk === null) {
    validLabel = "—";
    validClass = "text-slate-500";
  } else if (validationOk) {
    validLabel = "Graph is valid";
    validClass = "text-emerald-400/90";
  } else {
    validLabel = "Graph has issues";
    validClass = "text-rose-300/90";
  }

  return (
    <footer className="flex shrink-0 flex-wrap items-center justify-between gap-2 border-t border-slate-800 pt-2 font-mono text-xs">
      <div className="flex flex-wrap gap-2">
        <button
          className="rounded border border-slate-600 px-3 py-1.5 text-slate-200 hover:border-slate-500 disabled:opacity-40"
          disabled={busy}
          onClick={onDryRun}
          type="button"
        >
          Recompute (dry-run)
        </button>
        <button
          className="rounded border border-amber-600/50 bg-amber-950/40 px-3 py-1.5 font-semibold text-amber-100 hover:border-amber-500/70 disabled:opacity-40"
          disabled={busy}
          onClick={onSave}
          type="button"
        >
          Recompute &amp; save graph
        </button>
      </div>
      <div className="max-w-[42%] text-center text-[11px] text-slate-500">
        <span className={validClass}>{validLabel}</span>
        {footerHint ? (
          <>
            <span className="mx-2 text-slate-600">·</span>
            <span className="text-slate-400">{footerHint}</span>
          </>
        ) : null}
      </div>
      <div className="flex flex-wrap gap-2">
        <button
          className="rounded border border-cyan-700/50 px-3 py-1.5 text-cyan-100 hover:border-cyan-500/60 disabled:opacity-40"
          disabled
          type="button"
        >
          + Add output
        </button>
        <button
          className="rounded border border-red-900/50 px-3 py-1.5 text-red-200/90 hover:border-red-700/60 disabled:opacity-40"
          disabled
          type="button"
        >
          Clear canvas
        </button>
      </div>
    </footer>
  );
}
