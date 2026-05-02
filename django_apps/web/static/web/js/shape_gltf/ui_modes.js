import { CAMERA_FRAMES } from "./constants.js";
import { transitionToViewMode } from "./transitions.js";

export function setModeButtonState(container, viewMode) {
  for (const button of container.querySelectorAll("[data-shape-gltf-mode]")) {
    const isActive = button.dataset.shapeGltfMode === viewMode;
    button.setAttribute("aria-pressed", String(isActive));
    button.classList.toggle("border-cyan-400/50", isActive);
    button.classList.toggle("bg-cyan-400/15", isActive);
    button.classList.toggle("text-cyan-100", isActive);
    button.classList.toggle("border-slate-700", !isActive);
    button.classList.toggle("bg-slate-950/60", !isActive);
    button.classList.toggle("text-slate-400", !isActive);
  }
}

export function bindModeControls(state) {
  setModeButtonState(state.container, state.currentViewMode);

  for (const button of state.container.querySelectorAll("[data-shape-gltf-mode]")) {
    button.addEventListener("click", () => {
      const viewMode = button.dataset.shapeGltfMode;
      if (!viewMode || !CAMERA_FRAMES[viewMode]) {
        return;
      }

      transitionToViewMode(state, viewMode, setModeButtonState);
    });
  }
}
