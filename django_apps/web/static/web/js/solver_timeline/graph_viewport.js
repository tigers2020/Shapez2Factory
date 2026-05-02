import { GRAPH_PADDING } from "./graph_markup.js";
import { GRAPH_ZOOM_STEP, MAX_GRAPH_SCALE, MIN_GRAPH_SCALE } from "./constants.js";

function clamp(value, min, max) {
  return Math.min(max, Math.max(min, value));
}

function applyGraphTransform(viewport) {
  const stage = viewport.querySelector("[data-graph-stage]");
  const state = viewport._graphTransform;
  if (!stage || !state) {
    return;
  }
  stage.style.transform = `translate(${state.x}px, ${state.y}px) scale(${state.scale})`;
}

function resetGraphViewport(viewport) {
  const stage = viewport.querySelector("[data-graph-stage]");
  if (!stage) {
    return;
  }

  const viewportWidth = Math.max(1, viewport.clientWidth);
  const viewportHeight = Math.max(1, viewport.clientHeight);
  const contentMinX = Number(stage.dataset.contentMinX || 0);
  const contentMinY = Number(stage.dataset.contentMinY || 0);
  const contentWidth = Number(stage.dataset.contentWidth || stage.offsetWidth);
  const contentHeight = Number(stage.dataset.contentHeight || stage.offsetHeight);
  const fitWidthScale = (viewportWidth - GRAPH_PADDING * 2) / contentWidth;
  const fitHeightScale = (viewportHeight - GRAPH_PADDING * 2) / contentHeight;
  const scale = clamp(Math.min(1, fitWidthScale, fitHeightScale), MIN_GRAPH_SCALE, MAX_GRAPH_SCALE);
  const scaledWidth = contentWidth * scale;
  const scaledHeight = contentHeight * scale;
  viewport._graphTransform = {
    scale,
    x: (viewportWidth - scaledWidth) / 2 - contentMinX * scale,
    y: (viewportHeight - scaledHeight) / 2 - contentMinY * scale,
    dragging: false,
    startX: 0,
    startY: 0,
    originX: 0,
    originY: 0,
  };
  applyGraphTransform(viewport);
}

function zoomGraphViewport(viewport, nextScale, anchorX, anchorY) {
  const state = viewport._graphTransform;
  if (!state) {
    return;
  }
  const scale = clamp(nextScale, MIN_GRAPH_SCALE, MAX_GRAPH_SCALE);
  const ratio = scale / state.scale;
  state.x = anchorX - (anchorX - state.x) * ratio;
  state.y = anchorY - (anchorY - state.y) * ratio;
  state.scale = scale;
  applyGraphTransform(viewport);
}

export function initGraphViewport(canvas) {
  const viewport = canvas.querySelector("[data-graph-viewport]");
  if (!viewport) {
    return;
  }
  const root = document.documentElement;
  resetGraphViewport(viewport);

  viewport.querySelector("[data-graph-zoom-in]")?.addEventListener("click", () => {
    zoomGraphViewport(
      viewport,
      viewport._graphTransform.scale * GRAPH_ZOOM_STEP,
      viewport.clientWidth / 2,
      viewport.clientHeight / 2
    );
  });
  viewport.querySelector("[data-graph-zoom-out]")?.addEventListener("click", () => {
    zoomGraphViewport(
      viewport,
      viewport._graphTransform.scale / GRAPH_ZOOM_STEP,
      viewport.clientWidth / 2,
      viewport.clientHeight / 2
    );
  });
  viewport.querySelector("[data-graph-reset]")?.addEventListener("click", () => {
    resetGraphViewport(viewport);
  });

  viewport.addEventListener(
    "wheel",
    (event) => {
      event.preventDefault();
      const rect = viewport.getBoundingClientRect();
      const anchorX = event.clientX - rect.left;
      const anchorY = event.clientY - rect.top;
      const factor = event.deltaY < 0 ? GRAPH_ZOOM_STEP : 1 / GRAPH_ZOOM_STEP;
      zoomGraphViewport(viewport, viewport._graphTransform.scale * factor, anchorX, anchorY);
    },
    { passive: false }
  );

  viewport.addEventListener("selectstart", (event) => {
    event.preventDefault();
  });

  viewport.addEventListener("dragstart", (event) => {
    event.preventDefault();
  });

  viewport.addEventListener("pointerdown", (event) => {
    event.preventDefault();
    if (event.target.closest("[data-graph-node-id], button")) {
      return;
    }
    const state = viewport._graphTransform;
    state.dragging = true;
    state.startX = event.clientX;
    state.startY = event.clientY;
    state.originX = state.x;
    state.originY = state.y;
    viewport.setPointerCapture(event.pointerId);
    viewport.style.cursor = "grabbing";
    document.body.classList.add("select-none");
    root.style.userSelect = "none";
  });

  viewport.addEventListener("pointermove", (event) => {
    const state = viewport._graphTransform;
    if (!state?.dragging) {
      return;
    }
    event.preventDefault();
    state.x = state.originX + event.clientX - state.startX;
    state.y = state.originY + event.clientY - state.startY;
    applyGraphTransform(viewport);
  });

  const stopDragging = (event) => {
    const state = viewport._graphTransform;
    if (!state?.dragging) {
      return;
    }
    state.dragging = false;
    viewport.releasePointerCapture?.(event.pointerId);
    viewport.style.cursor = "grab";
    document.body.classList.remove("select-none");
    root.style.userSelect = "";
  };

  viewport.addEventListener("pointerup", stopDragging);
  viewport.addEventListener("pointercancel", stopDragging);
}
