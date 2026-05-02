import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";

import { renderSceneToThree } from "./shape_gltf/render_scene.js";
import { disposeViewerState, setupRenderer } from "./shape_gltf/renderer.js";
import { updateTransitions } from "./shape_gltf/transitions.js";
import { bindModeControls } from "./shape_gltf/ui_modes.js";

console.info("shape_gltf_viewer view-modes v5 loaded");

const viewerStates = new WeakMap();

function readScene(container) {
  const script = container.querySelector('script[type="application/json"]');
  if (!script) {
    throw new Error("Missing shape scene JSON");
  }
  return JSON.parse(script.textContent);
}

async function mountViewer(container) {
  const existing = viewerStates.get(container);
  if (existing) {
    disposeViewerState(existing);
    viewerStates.delete(container);
  }

  const viewport = container.querySelector("[data-shape-gltf-viewport]");
  const assetBase = container.dataset.assetBase;
  const renderScene = readScene(container);

  const rendererContext = setupRenderer(viewport);
  const state = {
    ...rendererContext,
    cameraTransition: null,
    container,
    currentViewMode: "original",
    records: [],
  };
  bindModeControls(state);

  state.renderer.setAnimationLoop(() => {
    updateTransitions(state);
    state.controls.update();
    state.renderer.render(state.scene, state.camera);
  });

  const loader = new GLTFLoader();
  state.records = await renderSceneToThree(
    state.scene,
    loader,
    assetBase,
    renderScene,
    state.currentViewMode
  );

  viewerStates.set(container, state);
  return state;
}

export async function mountShapeGltfViewer(container) {
  return mountViewer(container);
}

export function disposeShapeGltfViewer(container) {
  const state = viewerStates.get(container);
  if (state) {
    disposeViewerState(state);
    viewerStates.delete(container);
  }
}

const autoMountRoots = document.querySelectorAll("[data-shape-gltf-viewer][data-shape-gltf-auto-mount]");
for (const container of autoMountRoots) {
  mountViewer(container).catch((error) => {
    console.error("Shape glTF viewer failed to mount", error);
  });
}
