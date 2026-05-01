import * as THREE from "three";
import { OrbitControls } from "three/addons/controls/OrbitControls.js";
import { GLTFLoader } from "three/addons/loaders/GLTFLoader.js";

console.info("shape_gltf_viewer view-modes v5 loaded");

const COLOR_HEX = {
  u: 0xf4f1ec,
  r: 0xef4444,
  g: 0x22c55e,
  b: 0x3b82f6,
  c: 0x2ec4b6,
  m: 0xd946ef,
  y: 0xfacc15,
  w: 0xffffff,
};

const MODEL_FILES = {
  default_rect: "ShapeDefaultR.gltf",
  default_circle: "ShapeDefaultC.gltf",
  default_star: "ShapeDefaultS.gltf",
  default_diamond: "ShapeDefaultW.gltf",
  default_pin: "ShapeDefaultP.gltf",
  default_crystal: "ShapeDefaultC.gltf",
};

const BASE_RADIUS = 0.62;
const BASE_HEIGHT = 0.08;
const BASE_COLOR = 0x17121a;
const SIDE_COLOR = 0x050509;

const LAYER_HEIGHT = 0.102;
const MODEL_SCALE = 1;
const LAYER_SCALE_STEP = 0.2;
const MIN_LAYER_SCALE = 0.72;
const QUADRANT_GAP = 0.048;
const LAYER_EXPLODE_HEIGHT = 0.42;
const EXPLODED_QUADRANT_GAP = 0.38;
const QUADRANT_LAYER_EXPLODE_HEIGHT = 0.28;
const VIEW_MODE_TRANSITION_MS = 450;

const SEAM_COLOR = new THREE.Color(0x020204);
const SEAM_WIDTH = 0.022;
const SEAM_FEATHER = 0.006;
const SEAM_OPACITY = 0;

const QUADRANT_ROTATIONS = {
  NE: Math.PI,
  SE: Math.PI / 2,
  SW: 0,
  NW: -Math.PI / 2,
};

const QUADRANT_GAP_OFFSETS = {
  NE: { x: QUADRANT_GAP, z: -QUADRANT_GAP },
  SE: { x: QUADRANT_GAP, z: QUADRANT_GAP },
  SW: { x: -QUADRANT_GAP, z: QUADRANT_GAP },
  NW: { x: -QUADRANT_GAP, z: -QUADRANT_GAP },
};

const QUADRANT_EXPLODE_OFFSETS = {
  NE: { x: EXPLODED_QUADRANT_GAP, z: -EXPLODED_QUADRANT_GAP },
  SE: { x: EXPLODED_QUADRANT_GAP, z: EXPLODED_QUADRANT_GAP },
  SW: { x: -EXPLODED_QUADRANT_GAP, z: EXPLODED_QUADRANT_GAP },
  NW: { x: -EXPLODED_QUADRANT_GAP, z: -EXPLODED_QUADRANT_GAP },
};

const CAMERA_FRAMES = {
  original: {
    position: new THREE.Vector3(1.35, 1.1, 1.65),
    target: new THREE.Vector3(0, 0.12, 0),
  },
  layer: {
    position: new THREE.Vector3(2.1, 2.05, 2.75),
    target: new THREE.Vector3(0, 0.35, 0),
  },
  quadrant: {
    position: new THREE.Vector3(2.8, 2.1, 3.2),
    target: new THREE.Vector3(0, 0.24, 0),
  },
};

const modelCache = new Map();

function readScene(container) {
  const script = container.querySelector('script[type="application/json"]');
  if (!script) {
    throw new Error("Missing shape scene JSON");
  }
  return JSON.parse(script.textContent);
}

async function loadModel(loader, assetBase, meshKey) {
  const filename = MODEL_FILES[meshKey];
  if (!filename) {
    return null;
  }
  const url = `${assetBase}${filename}`;
  if (!modelCache.has(url)) {
    modelCache.set(url, loader.loadAsync(url));
  }
  const gltf = await modelCache.get(url);
  return gltf.scene.clone(true);
}

function resolveMaterialColor(materialKey) {
  return COLOR_HEX[materialKey] ?? 0xff00ff;
}

function createPedestal() {
  const geometry = new THREE.CylinderGeometry(BASE_RADIUS, BASE_RADIUS, BASE_HEIGHT, 96);
  const material = new THREE.MeshStandardMaterial({
    color: BASE_COLOR,
    roughness: 0.72,
    metalness: 0.08,
  });

  const pedestal = new THREE.Mesh(geometry, material);
  pedestal.position.set(0, -BASE_HEIGHT / 2, 0);
  pedestal.receiveShadow = true;
  pedestal.castShadow = false;

  return pedestal;
}

function createTopMaterialWithSeam(color) {
  const material = new THREE.MeshStandardMaterial({
    color,
    roughness: 0.55,
    metalness: 0.04,
  });

  material.onBeforeCompile = (shader) => {
    shader.uniforms.uSeamColor = { value: SEAM_COLOR };
    shader.uniforms.uSeamWidth = { value: SEAM_WIDTH };
    shader.uniforms.uSeamFeather = { value: SEAM_FEATHER };
    shader.uniforms.uSeamOpacity = { value: SEAM_OPACITY };

    shader.vertexShader = shader.vertexShader.replace(
      "void main() {",
      `
      varying vec3 vSeamWorldPosition;

      void main() {
      `
    );

    shader.vertexShader = shader.vertexShader.replace(
      "#include <worldpos_vertex>",
      `
      #include <worldpos_vertex>
      vSeamWorldPosition = worldPosition.xyz;
      `
    );

    shader.fragmentShader = shader.fragmentShader.replace(
      "void main() {",
      `
      varying vec3 vSeamWorldPosition;
      uniform vec3 uSeamColor;
      uniform float uSeamWidth;
      uniform float uSeamFeather;
      uniform float uSeamOpacity;

      void main() {
      `
    );

    shader.fragmentShader = shader.fragmentShader.replace(
      "#include <dithering_fragment>",
      `
      float seamX = 1.0 - smoothstep(
        uSeamWidth,
        uSeamWidth + uSeamFeather,
        abs(vSeamWorldPosition.x)
      );
      float seamZ = 1.0 - smoothstep(
        uSeamWidth,
        uSeamWidth + uSeamFeather,
        abs(vSeamWorldPosition.z)
      );
      float seamMask = max(seamX, seamZ) * uSeamOpacity;

      gl_FragColor.rgb = mix(gl_FragColor.rgb, uSeamColor, seamMask);

      #include <dithering_fragment>
      `
    );
  };

  material.needsUpdate = true;
  return material;
}

function applyTopSideMaterials(root, materialKey) {
  const topColor = resolveMaterialColor(materialKey);
  const topMaterial = createTopMaterialWithSeam(topColor);
  const sideMaterial = new THREE.MeshStandardMaterial({
    color: SIDE_COLOR,
    roughness: 0.82,
    metalness: 0.02,
  });

  root.traverse((node) => {
    if (!node.isMesh || !node.geometry) {
      return;
    }

    const geometry = node.geometry.index ? node.geometry.toNonIndexed() : node.geometry.clone();
    const normals = geometry.getAttribute("normal");
    geometry.clearGroups();

    if (!normals) {
      geometry.addGroup(0, geometry.getAttribute("position").count, 1);
      node.geometry = geometry;
      node.material = [topMaterial, sideMaterial];
      node.castShadow = true;
      node.receiveShadow = true;
      return;
    }

    let groupStart = 0;
    let groupCount = 0;
    let currentMaterialIndex = null;

    for (let i = 0; i < normals.count; i += 3) {
      const avgNormalY = (normals.getY(i) + normals.getY(i + 1) + normals.getY(i + 2)) / 3;
      const materialIndex = avgNormalY > 0.55 ? 0 : 1;

      if (currentMaterialIndex === null) {
        currentMaterialIndex = materialIndex;
        groupStart = i;
        groupCount = 3;
      } else if (materialIndex === currentMaterialIndex) {
        groupCount += 3;
      } else {
        geometry.addGroup(groupStart, groupCount, currentMaterialIndex);
        currentMaterialIndex = materialIndex;
        groupStart = i;
        groupCount = 3;
      }
    }

    if (currentMaterialIndex !== null) {
      geometry.addGroup(groupStart, groupCount, currentMaterialIndex);
    }

    node.geometry = geometry;
    node.material = [topMaterial, sideMaterial];
    node.castShadow = true;
    node.receiveShadow = true;
  });
}

function getPositionKey(cell) {
  if (typeof cell.position === "string") {
    return cell.position;
  }

  if (typeof cell.transform_key === "string") {
    return cell.transform_key.split(":")[0];
  }

  return "NE";
}

function getLayerIndex(cell) {
  if (typeof cell.layer_index === "number") {
    return cell.layer_index;
  }

  if (typeof cell.transform_key === "string") {
    const layerKey = cell.transform_key.split(":")[1] ?? "L0";
    return Number.parseInt(layerKey.replace("L", ""), 10) || 0;
  }

  return 0;
}

function getLayerScale(layerIndex) {
  return Math.max(MIN_LAYER_SCALE, MODEL_SCALE - layerIndex * LAYER_SCALE_STEP);
}

function computeTransform(cell, viewMode = "original") {
  const positionKey = getPositionKey(cell);
  const layerIndex = getLayerIndex(cell);
  const microOffset = QUADRANT_GAP_OFFSETS[positionKey] ?? { x: 0, z: 0 };
  const explodeOffset = QUADRANT_EXPLODE_OFFSETS[positionKey] ?? { x: 0, z: 0 };
  const layerScale = getLayerScale(layerIndex);

  let x = microOffset.x;
  let y = layerIndex * LAYER_HEIGHT;
  let z = microOffset.z;

  if (viewMode === "layer") {
    y = layerIndex * LAYER_EXPLODE_HEIGHT;
  } else if (viewMode === "quadrant") {
    x = explodeOffset.x;
    y = layerIndex * QUADRANT_LAYER_EXPLODE_HEIGHT;
    z = explodeOffset.z;
  }

  return {
    position: new THREE.Vector3(x, y, z),
    rotationY: QUADRANT_ROTATIONS[positionKey] ?? 0,
    scale: layerScale,
  };
}

function applyComputedTransform(model, transform) {
  model.position.copy(transform.position);
  model.rotation.set(0, transform.rotationY, 0);
  model.scale.setScalar(transform.scale);
}

function applyTransform(model, cell, viewMode = "original") {
  applyComputedTransform(model, computeTransform(cell, viewMode));
}

function easeInOutCubic(value) {
  return value < 0.5 ? 4 * value * value * value : 1 - Math.pow(-2 * value + 2, 3) / 2;
}

function lerpAngle(start, end, progress) {
  const delta = Math.atan2(Math.sin(end - start), Math.cos(end - start));
  return start + delta * progress;
}

function createTransition(model, targetTransform, now) {
  return {
    startPosition: model.position.clone(),
    startRotationY: model.rotation.y,
    startScale: model.scale.x,
    targetPosition: targetTransform.position.clone(),
    targetRotationY: targetTransform.rotationY,
    targetScale: targetTransform.scale,
    startedAt: now,
  };
}

function updateModelTransition(record, now) {
  if (!record.transition) {
    return;
  }

  const elapsed = now - record.transition.startedAt;
  const progress = Math.min(elapsed / VIEW_MODE_TRANSITION_MS, 1);
  const eased = easeInOutCubic(progress);

  record.model.position.lerpVectors(
    record.transition.startPosition,
    record.transition.targetPosition,
    eased
  );
  record.model.rotation.y = lerpAngle(
    record.transition.startRotationY,
    record.transition.targetRotationY,
    eased
  );
  const scale =
    record.transition.startScale +
    (record.transition.targetScale - record.transition.startScale) * eased;
  record.model.scale.setScalar(scale);

  if (progress >= 1) {
    applyComputedTransform(record.model, {
      position: record.transition.targetPosition,
      rotationY: record.transition.targetRotationY,
      scale: record.transition.targetScale,
    });
    record.transition = null;
  }
}

function createCameraTransition(camera, controls, targetFrame, now) {
  return {
    startPosition: camera.position.clone(),
    startTarget: controls.target.clone(),
    targetPosition: targetFrame.position.clone(),
    targetTarget: targetFrame.target.clone(),
    startedAt: now,
  };
}

function updateCameraTransition(state, now) {
  if (!state.cameraTransition) {
    return;
  }

  const elapsed = now - state.cameraTransition.startedAt;
  const progress = Math.min(elapsed / VIEW_MODE_TRANSITION_MS, 1);
  const eased = easeInOutCubic(progress);

  state.camera.position.lerpVectors(
    state.cameraTransition.startPosition,
    state.cameraTransition.targetPosition,
    eased
  );
  state.controls.target.lerpVectors(
    state.cameraTransition.startTarget,
    state.cameraTransition.targetTarget,
    eased
  );

  if (progress >= 1) {
    state.camera.position.copy(state.cameraTransition.targetPosition);
    state.controls.target.copy(state.cameraTransition.targetTarget);
    state.cameraTransition = null;
  }
}

function setupRenderer(container) {
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

  return { camera, controls, renderer, scene };
}

async function renderSceneToThree(scene, loader, assetBase, renderScene, viewMode) {
  const records = [];
  scene.add(createPedestal());

  for (const cell of renderScene.cells) {
    const model = await loadModel(loader, assetBase, cell.mesh_key);
    if (!model) {
      continue;
    }

    applyTopSideMaterials(model, cell.material_key);
    applyTransform(model, cell, viewMode);
    scene.add(model);
    records.push({ cell, model, transition: null });
  }

  return records;
}

function setModeButtonState(container, viewMode) {
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

function startViewModeTransition(state, viewMode) {
  if (state.currentViewMode === viewMode) {
    return;
  }

  state.currentViewMode = viewMode;
  setModeButtonState(state.container, viewMode);

  const now = performance.now();
  for (const record of state.records) {
    record.transition = createTransition(record.model, computeTransform(record.cell, viewMode), now);
  }
  state.cameraTransition = createCameraTransition(
    state.camera,
    state.controls,
    CAMERA_FRAMES[viewMode] ?? CAMERA_FRAMES.original,
    now
  );
}

function bindModeControls(state) {
  setModeButtonState(state.container, state.currentViewMode);

  for (const button of state.container.querySelectorAll("[data-shape-gltf-mode]")) {
    button.addEventListener("click", () => {
      const viewMode = button.dataset.shapeGltfMode;
      if (!viewMode || !CAMERA_FRAMES[viewMode]) {
        return;
      }

      startViewModeTransition(state, viewMode);
    });
  }
}

function updateTransitions(state) {
  const now = performance.now();
  for (const record of state.records) {
    updateModelTransition(record, now);
  }
  updateCameraTransition(state, now);
}

async function mountViewer(container) {
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
}

for (const container of document.querySelectorAll("[data-shape-gltf-viewer]")) {
  mountViewer(container).catch((error) => {
    console.error("Shape glTF viewer failed to mount", error);
  });
}
