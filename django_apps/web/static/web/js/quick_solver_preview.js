import { disposeShapeGltfViewer, mountShapeGltfViewer } from "./shape_gltf_viewer.js";
import { TIMELINE_DEBOUNCE_MS } from "./solver_timeline/constants.js";

function clearViewerHost(host) {
  for (const el of [...host.querySelectorAll("[data-shape-gltf-viewer]")]) {
    disposeShapeGltfViewer(el);
  }
  host.replaceChildren();
}

function setBanner(el, text, visible) {
  if (!el) {
    return;
  }
  el.textContent = text;
  el.classList.toggle("hidden", !visible);
}

async function runPreview(panel, input, seq) {
  const apiUrl = panel.dataset.previewApi;
  const assetBase = panel.dataset.assetBase;
  const viewersHost = panel.querySelector("[data-quick-preview-viewers]");
  const errEl = panel.querySelector("[data-quick-preview-error]");
  const warnEl = panel.querySelector("[data-quick-preview-warnings]");

  if (!apiUrl || !assetBase || !viewersHost) {
    return;
  }

  const code = input.value.trim();

  if (!code) {
    clearViewerHost(viewersHost);
    setBanner(errEl, "", false);
    setBanner(warnEl, "", false);
    return;
  }

  let data;
  try {
    const url = new URL(apiUrl, window.location.origin);
    url.searchParams.set("code", code);
    const res = await fetch(url.toString(), { headers: { Accept: "application/json" } });
    data = await res.json();
  } catch {
    if (seq !== panel._previewSeq) {
      return;
    }
    clearViewerHost(viewersHost);
    setBanner(errEl, "Could not reach preview service.", true);
    setBanner(warnEl, "", false);
    return;
  }

  if (seq !== panel._previewSeq) {
    return;
  }

  if (!data.ok) {
    setBanner(errEl, data.error || "Invalid shape code.", true);
    setBanner(warnEl, "", false);
    return;
  }

  setBanner(errEl, "", false);

  const warnings = data.warnings ?? [];
  if (warnings.length) {
    setBanner(warnEl, warnings.join(" "), true);
  } else {
    setBanner(warnEl, "", false);
  }

  clearViewerHost(viewersHost);
  const tpl = panel.querySelector("#quick-solver-viewer-template");
  if (!tpl) {
    return;
  }

  const mounted = [];
  for (let i = 0; i < data.patterns.length; i += 1) {
    const frag = tpl.content.cloneNode(true);
    const root = frag.querySelector("[data-shape-gltf-viewer]");
    root.dataset.assetBase = assetBase;
    if (i > 0) {
      root.classList.add("mt-8", "border-t", "border-slate-800", "pt-6");
    }
    const script = root.querySelector('script[type="application/json"]');
    script.textContent = JSON.stringify(data.patterns[i].preview_scene);
    viewersHost.appendChild(frag);
    await mountShapeGltfViewer(root);
    mounted.push(root);
    if (seq !== panel._previewSeq) {
      for (const r of mounted) {
        disposeShapeGltfViewer(r);
      }
      clearViewerHost(viewersHost);
      return;
    }
  }
}

function schedulePreview(panel, input, delayMs) {
  panel._previewSeq = (panel._previewSeq || 0) + 1;
  const seq = panel._previewSeq;

  clearTimeout(panel._previewTimer);
  panel._previewTimer = setTimeout(() => {
    runPreview(panel, input, seq);
  }, delayMs);
}

function findPreviewInput(panel) {
  const scoped = panel.querySelector("[data-shape-preview-code]");
  if (scoped) {
    return scoped;
  }
  const ref = panel.dataset.shapePreviewCodeRef?.trim();
  if (ref) {
    try {
      return document.querySelector(ref);
    } catch {
      return null;
    }
  }
  return null;
}

/**
 * Keep an <a data-solver-page-link> href in sync with the shape code field.
 * Native navigation avoids lost click handlers (third-party scripts, CSP edge cases).
 */
function syncSolverPageLink(panel) {
  const link = panel.querySelector("a[data-solver-page-link]");
  const input = findPreviewInput(panel);
  if (!link || !input) {
    return;
  }

  let pathWithQueryBase = panel.dataset.solverUrl?.trim();
  if (!pathWithQueryBase) {
    const hrefAttr = link.getAttribute("href")?.trim() || "";
    if (!hrefAttr) {
      return;
    }
    try {
      pathWithQueryBase = new URL(hrefAttr, window.location.origin).pathname;
    } catch {
      return;
    }
  }

  const apply = () => {
    const code = input.value.trim();
    const next = new URL(pathWithQueryBase, window.location.origin);
    if (code) {
      next.searchParams.set("code", code);
    } else {
      next.searchParams.delete("code");
    }
    link.setAttribute("href", `${next.pathname}${next.search}`);
  };

  input.addEventListener("input", apply);
  input.addEventListener("change", apply);
  apply();
}

function initShapePreviewPanel(panel) {
  syncSolverPageLink(panel);
  const input = findPreviewInput(panel);
  if (!input || !panel.dataset.previewApi || !panel.dataset.assetBase) {
    return;
  }
  const viewersHost = panel.querySelector("[data-quick-preview-viewers]");
  if (!viewersHost) {
    return;
  }
  input.addEventListener("input", () => schedulePreview(panel, input, TIMELINE_DEBOUNCE_MS));
  input.addEventListener("change", () => schedulePreview(panel, input, TIMELINE_DEBOUNCE_MS));
  schedulePreview(panel, input, 0);
}

document.querySelectorAll("[data-shape-preview-panel]").forEach(initShapePreviewPanel);
