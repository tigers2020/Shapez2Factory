import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";

import { CAMERA_FRAMES } from "./constants.js";

export function setupRenderer(container) {
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x09090f);

  const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 100);
  camera.position.copy(CAMERA_FRAMES.original.position);

  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
  renderer.setPixelRatio(window.devicePixelRatio);
  renderer.setSize(container.clientWidth, container.clientHeight);
  renderer.shadowMap.enabled = true;
  container.appendChild(renderer.domElement);

  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.target.copy(CAMERA_FRAMES.original.target);
  controls.update();

  scene.add(new THREE.AmbientLight(0xffffff, 1.6));
  const keyLight = new THREE.DirectionalLight(0xffffff, 2.2);
  keyLight.position.set(2, 4, 3);
  keyLight.castShadow = true;
  scene.add(keyLight);

  const resizeObserver = new ResizeObserver(() => {
    const width = container.clientWidth;
    const height = container.clientHeight;
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
    renderer.setSize(width, height);
  });
  resizeObserver.observe(container);

  return { camera, controls, renderer, scene, resizeObserver };
}

export function disposeViewerState(state) {
  if (!state) {
    return;
  }
  state.renderer.setAnimationLoop(null);
  state.resizeObserver.disconnect();
  state.controls.dispose();

  state.scene.traverse((obj) => {
    if (!obj.isMesh) {
      return;
    }
    obj.geometry?.dispose();
    const mat = obj.material;
    if (Array.isArray(mat)) {
      mat.forEach((m) => m.dispose());
    } else {
      mat?.dispose();
    }
  });
  state.scene.clear();

  const viewport = state.container.querySelector("[data-shape-gltf-viewport]");
  if (viewport && state.renderer.domElement.parentNode === viewport) {
    viewport.removeChild(state.renderer.domElement);
  }
  state.renderer.dispose();
}
