import { mountGraph } from "./solver_timeline/graph_mount.js?v=20260504-grid-pinned";

/**
 * Mount solver-style graph (pan/zoom, node selection) inside a host element.
 * @param {HTMLElement} host
 * @param {{ nodes: unknown[], edges: unknown[], layout?: unknown }} graph
 * @param {string} assetBase
 * @param {{
 *   recipeWireConnect?: (edge: { from: string, to: string, kind: string, slot?: string }) => void | Promise<void>
 *   recipeWireDelete?: (edge: { from: string, to: string, kind: string, slot?: string }) => void | Promise<void>
 *   onGraphNodeSelect?: (nodeId: string) => void
 *   recipeNodeDragCommit?: (args: { nodeId: string, x: number, y: number }) => void | Promise<void>
 *   recipeCanvasDrop?: (args: { kind: string, operation?: string, graphX: number, graphY: number }) => void | Promise<void>
 *   staffOpenNodeDetailModal?: (nodeId: string) => void | Promise<void>
 *   staffOpenNodeEditModal?: (nodeId: string) => void
 * } | undefined} [hooks]
 */
export async function mountMacroRecipeGraph(host, graph, assetBase, hooks) {
  host.innerHTML = `
    <div
      class="rounded-2xl border border-slate-800 bg-slate-950/60 p-4"
      data-macro-graph-panel
      data-asset-base=""
    >
      <p class="text-xs font-semibold uppercase tracking-wide text-cyan-200/90">Recipe graph</p>
      <p class="mt-1 text-xs text-slate-500">
        Same renderer as the solver page. Drag empty canvas to pan, wheel to zoom.
        Drag a <span class="font-semibold text-slate-200">node card</span> (not ports) to move it; positions sync to <span class="font-mono text-slate-300">graph_document</span> and preview refresh (same dry-run as toolbar).
        <span class="mt-1 block text-slate-400/95">
          <span class="font-semibold text-slate-300">Palette:</span> drag Base shape or an operation onto the canvas to drop a node at that spot (20px snap).
        </span>
        <span class="mt-1 block text-slate-400/95">
          Wire: drag from an <span class="font-semibold text-amber-200/90">output</span> port (shape right / operation amber) to an
          <span class="font-semibold text-cyan-200">input</span> (shape left / operation cyan). Esc cancels.
          <span class="mt-1 block text-slate-500"> Staff: click a wire (hit along the line) to remove it after confirming.</span>
        </span>
      </p>
      <div class="mt-3" data-solver-graph-canvas></div>
      <div class="mt-4 hidden text-sm text-slate-300" data-solver-node-detail data-staff-inline-detail-hidden aria-hidden="true"></div>
    </div>
  `;
  const panel = host.querySelector("[data-macro-graph-panel]");
  if (!panel) {
    return;
  }
  panel.dataset.assetBase = assetBase || "";
  const opts = {};
  if (hooks && typeof hooks.recipeWireConnect === "function") {
    opts.recipeWireConnect = hooks.recipeWireConnect;
  }
  if (hooks && typeof hooks.onGraphNodeSelect === "function") {
    opts.onGraphNodeSelect = hooks.onGraphNodeSelect;
  }
  if (hooks && typeof hooks.recipeNodeDragCommit === "function") {
    opts.recipeNodeDragCommit = hooks.recipeNodeDragCommit;
  }
  if (hooks && typeof hooks.recipeWireDelete === "function") {
    opts.recipeWireDelete = hooks.recipeWireDelete;
  }
  if (hooks && typeof hooks.recipeCanvasDrop === "function") {
    opts.recipeCanvasDrop = hooks.recipeCanvasDrop;
  }
  if (hooks && typeof hooks.staffOpenNodeDetailModal === "function") {
    opts.staffNodeModalUi = true;
    opts.staffOpenNodeDetailModal = hooks.staffOpenNodeDetailModal;
    opts.staffOpenNodeEditModal =
      typeof hooks.staffOpenNodeEditModal === "function"
        ? hooks.staffOpenNodeEditModal
        : undefined;
  }
  await mountGraph(panel, graph, Object.keys(opts).length ? opts : undefined);
}
