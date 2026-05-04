import { escapeHtml } from "./dom_utils.js";

function renderThroughputSummary(data) {
  const targetCount = Number((data.target?.count ?? null) || 1);
  const baseDemands = Array.isArray(data.base_demands) ? data.base_demands : [];
  const solver = data.solver && typeof data.solver === "object" ? data.solver : null;
  const lines = [
    `<p class="text-xs font-semibold uppercase tracking-[0.18em] text-cyan-200">Throughput summary</p>`,
    `<p class="mt-2 text-sm text-slate-200">Target output x${escapeHtml(targetCount)}</p>`,
  ];
  if (solver?.mode) {
    lines.push(
      `<p class="mt-1 text-xs text-slate-400">Solver mode: <span class="font-mono text-slate-300">${escapeHtml(String(solver.mode))}</span></p>`
    );
  }
  if (Array.isArray(solver?.used_macro_sources) && solver.used_macro_sources.length) {
    lines.push(
      `<div class="mt-2 flex flex-wrap gap-2">${solver.used_macro_sources
        .map(
          (item) =>
            `<span class="rounded-full border border-emerald-400/20 bg-emerald-400/10 px-2 py-1 font-mono text-[11px] text-emerald-100">${escapeHtml(item)}</span>`
        )
        .join("")}</div>`
    );
  }

  if (!baseDemands.length) {
    lines.push('<p class="mt-2 text-xs text-slate-500">No base-demand breakdown is available for this target.</p>');
    return lines.join("");
  }

  lines.push(
    `<div class="mt-3 flex flex-wrap gap-2">${baseDemands
      .map(
        (demand) => `<span class="rounded-full border border-cyan-400/20 bg-cyan-400/10 px-3 py-1 font-mono text-xs text-cyan-100">${escapeHtml(demand.base_shape_code)} x${escapeHtml(demand.full_source_count)}</span>`
      )
      .join("")}</div>`
  );
  return lines.join("");
}

export function updateThroughputSummary(panel, data, visible) {
  const host = panel.querySelector("[data-solver-throughput-summary]");
  if (!host) {
    return;
  }
  if (!visible) {
    host.innerHTML = "";
    host.classList.add("hidden");
    return;
  }
  host.innerHTML = renderThroughputSummary(data);
  host.classList.remove("hidden");
}
