import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { RoomEnvironment } from "three/addons/environments/RoomEnvironment.js";

import {
  CAMERA_FRAMES,
  RENDERER_AMBIENT_INTENSITY,
  RENDERER_FILL_INTENSITY,
  RENDERER_HEMI_GROUND,
  RENDERER_HEMI_INTENSITY,
  RENDERER_HEMI_SKY,
  RENDERER_KEY_INTENSITY,
  RENDERER_TONE_MAPPING,
  RENDERER_TONE_MAPPING_EXPOSURE,
} from "./constants.js";

export function setupRenderer(container) {
  const scene = new THREE.Scene();
  scene.background = new THREE.Color(0x09090f);

  const camera = new THREE.PerspectiveCamera(45, 1, 0.1, 100);
  camera.position.copy(CAMERA_FRAMES.original.position);

  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: false });
  renderer.setPixelRatio(window.devicePixelRatio);
  renderer.setSize(container.clientWidth, container.clientHeight);
  renderer.shadowMap.enabled = true;
  renderer.outputColorSpace = THREE.SRGBColorSpace;
  renderer.toneMapping = RENDERER_TONE_MAPPING;
  renderer.toneMappingExposure = RENDERER_TONE_MAPPING_EXPOSURE;
  container.appendChild(renderer.domElement);

  const pmremGenerator = new THREE.PMREMGenerator(renderer);
  pmremGenerator.compileCubemapShader();

  const roomEnvironment = new RoomEnvironment();
  const envRenderTarget = pmremGenerator.fromScene(roomEnvironment, 0.04);
  scene.environment = envRenderTarget.texture;
  roomEnvironment.dispose();

  const controls = new OrbitControls(camera, renderer.domElement);
  controls.enableDamping = true;
  controls.target.copy(CAMERA_FRAMES.original.target);
  controls.update();

  scene.add(new THREE.HemisphereLight(RENDERER_HEMI_SKY, RENDERER_HEMI_GROUND, RENDERER_HEMI_INTENSITY));
  scene.add(new THREE.AmbientLight(0xffffff, RENDERER_AMBIENT_INTENSITY));
  const keyLight = new THREE.DirectionalLight(0xffffff, RENDERER_KEY_INTENSITY);
  keyLight.position.set(2, 4, 3);
  keyLight.castShadow = true;
  scene.add(keyLight);
  const fillLight = new THREE.DirectionalLight(0xf0f4ff, RENDERER_FILL_INTENSITY);
  fillLight.position.set(-3.5, 2.2, -4);
  scene.add(fillLight);

  const resizeObserver = new ResizeObserver(() => {
    const width = container.clientWidth;
    const height = container.clientHeight;
    camera.aspect = width / height;
    camera.updateProjectionMatrix();
    renderer.setSize(width, height);
  });
  resizeObserver.observe(container);

  return {
    camera,
    controls,
    envRenderTarget,
    pmremGenerator,
    renderer,
    scene,
    resizeObserver,
  };
}

export function disposeViewerState(state) {
  if (!state) {
    return;
  }
  state.renderer.setAnimationLoop(null);
  state.resizeObserver.disconnect();
  state.controls.dispose();

  state.scene.environment = null;
  if (state.envRenderTarget) {
    state.envRenderTarget.dispose();
    state.envRenderTarget = null;
  }
  if (state.pmremGenerator) {
    state.pmremGenerator.dispose();
    state.pmremGenerator = null;
  }

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
    state.renderer.domElement.remove();
  }
  state.renderer.dispose();
}
