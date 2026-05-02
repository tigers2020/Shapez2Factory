import { mountShapeGltfViewer } from "../shape_gltf_viewer.js";
import { disposeTimelineViewers, escapeHtml } from "./dom_utils.js";

function connectedEdges(graph, nodeId) {
  return (graph.edges || []).filter((edge) => edge.from === nodeId || edge.to === nodeId);
}

export async function renderSelectedNodeDetail(panel, graph, nodeId) {
  const detailHost = panel.querySelector("[data-solver-node-detail]");
  const assetBase = panel.dataset.assetBase || "";
  if (!detailHost) {
    return;
  }
  disposeTimelineViewers(detailHost);

  const node = (graph.nodes || []).find((candidate) => candidate.id === nodeId);
  if (!node) {
    detailHost.innerHTML = '<p class="text-xs text-slate-500">Select a graph node.</p>';
    return;
  }

  const edges = connectedEdges(graph, node.id);
  const batchTotal = Number(node.batch_total ?? 0);
  const batchIndex = Number(node.batch_index ?? 0);
  const batchNote =
    batchTotal > 1 && batchIndex > 0
      ? `<p class="mt-2 text-xs font-semibold uppercase tracking-wide text-fuchsia-200">Batch ${escapeHtml(batchIndex)} of ${escapeHtml(batchTotal)}</p>`
      : "";
  const producedStateNote =
    typeof node.produced_state === "string"
      ? `<p class="mt-2 text-xs font-semibold uppercase tracking-wide ${node.produced_state === "unused" ? "text-rose-200" : node.produced_state === "consumed" ? "text-emerald-200" : "text-cyan-200"}">${escapeHtml(node.produced_state)}</p>`
      : "";
  if (node.kind === "operation") {
    const operation = node.operation || {};
    const runNote =
      Number(node.run_total ?? 0) > 1 && Number(node.run_index ?? 0) > 0
        ? `<p class="mt-2 text-xs font-semibold uppercase tracking-wide text-fuchsia-200">Run ${escapeHtml(node.run_index)} of ${escapeHtml(node.run_total)}</p>`
        : "";
    detailHost.innerHTML = `
      <div class="rounded-3xl border border-slate-800 bg-slate-950/70 p-5">
        <p class="text-xs font-semibold uppercase tracking-[0.2em] text-orange-200">Selected operation</p>
        <div class="mt-4 flex flex-wrap items-center gap-4">
          <div class="flex h-20 w-20 items-center justify-center rounded-full border border-orange-300/40 bg-orange-400/10">
            <img src="${escapeHtml(operation.icon)}" alt="${escapeHtml(operation.label)}" class="h-12 w-12 object-contain" />
          </div>
          <div>
            <h3 class="text-lg font-semibold text-slate-100">${escapeHtml(operation.label)}</h3>
            <p class="mt-1 text-sm text-slate-400">${escapeHtml(operation.description || "")}</p>
            ${runNote}
            <p class="mt-2 text-xs text-slate-500">
              <span class="block">${escapeHtml(operation.input_count)} in / ${escapeHtml(operation.output_count)} out</span>
              <span class="mt-0.5 block font-mono text-slate-400">${escapeHtml(operation.input_count)}:${escapeHtml(operation.output_count)} \xb7 ${escapeHtml(operation.input_count)}\u2192${escapeHtml(operation.output_count)}</span>
            </p>
          </div>
        </div>
        <p class="mt-4 text-xs text-slate-500">${escapeHtml(edges.map((edge) => edge.label || edge.kind).join(" \xb7 "))}</p>
      </div>
    `;
    return;
  }

  detailHost.innerHTML = `
    <div class="rounded-3xl border border-cyan-400/20 bg-slate-950/70 p-5">
      <div class="mb-4 flex flex-wrap items-start justify-between gap-3">
        <div>
          <p class="text-xs font-semibold uppercase tracking-[0.2em] text-cyan-200">Selected shape</p>
          <h3 class="mt-1 font-mono text-lg text-slate-100">${escapeHtml(node.shape_code)}</h3>
          <p class="mt-1 text-xs uppercase tracking-wide text-slate-500">${escapeHtml(node.role)} \xb7 ${escapeHtml(node.label)}</p>
          <p class="mt-2 text-xs font-semibold uppercase tracking-wide text-cyan-200">Quantity x${escapeHtml(Number(node.quantity ?? 1))}</p>
          ${producedStateNote}
          ${batchNote}
        </div>
        ${node.role === "target" ? '<span class="rounded-full bg-emerald-300 px-3 py-1 text-[11px] font-bold text-emerald-950">TARGET</span>' : ""}
      </div>
      <div class="rounded-3xl bg-black/30 p-3 ring-1 ring-cyan-400/20" data-shape-gltf-viewer data-asset-base="">
        <div class="h-64 overflow-hidden rounded-2xl border border-slate-800 bg-slate-950" style="height: 16rem; min-height: 16rem;" data-shape-gltf-viewport></div>
        <script type="application/json">{}</script>
      </div>
      <p class="mt-4 text-xs text-slate-500">${escapeHtml(edges.map((edge) => edge.label || edge.kind).join(" \xb7 "))}</p>
    </div>
  `;

  const viewer = detailHost.querySelector("[data-shape-gltf-viewer]");
  const script = viewer?.querySelector('script[type="application/json"]');
  if (viewer && script && node.preview_scene) {
    viewer.dataset.assetBase = assetBase;
    script.textContent = JSON.stringify(node.preview_scene);
    await mountShapeGltfViewer(viewer);
  }
}
