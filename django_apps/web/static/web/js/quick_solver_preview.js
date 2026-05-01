import { disposeShapeGltfViewer, mountShapeGltfViewer } from "./shape_gltf_viewer.js";

const DEBOUNCE_MS = 320;

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
  const tpl = document.getElementById("quick-solver-viewer-template");
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

const panel = document.getElementById("quick-start");
if (panel) {
  const input = document.getElementById("quick-code");
  if (input && panel.dataset.previewApi && panel.dataset.assetBase) {
    input.addEventListener("input", () => schedulePreview(panel, input, DEBOUNCE_MS));
    input.addEventListener("change", () => schedulePreview(panel, input, DEBOUNCE_MS));
    schedulePreview(panel, input, 0);
  }
}
