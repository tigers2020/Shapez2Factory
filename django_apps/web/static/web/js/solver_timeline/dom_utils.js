import { disposeShapeGltfViewer } from "../shape_gltf_viewer.js";

export function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#039;");
}

export function setBanner(el, text, visible) {
  if (!el) {
    return;
  }
  el.textContent = text;
  el.classList.toggle("hidden", !visible);
}

export function disposeTimelineViewers(host) {
  for (const el of host.querySelectorAll("[data-shape-gltf-viewer]")) {
    disposeShapeGltfViewer(el);
  }
}

export function clearStepsHost(host) {
  disposeTimelineViewers(host);
  host.replaceChildren();
}

export function setStepsHtml(host, html) {
  disposeTimelineViewers(host);
  host.innerHTML = html;
}
