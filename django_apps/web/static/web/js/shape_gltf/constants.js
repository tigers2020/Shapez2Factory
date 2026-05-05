import * as THREE from "three";

export const COLOR_HEX = {
  u: 0x94a3b8,
  r: 0xef4444,
  g: 0x22c55e,
  b: 0x3b82f6,
  c: 0x2ec4b6,
  m: 0xd946ef,
  y: 0xfacc15,
  w: 0xffffff,
};

export const MODEL_FILES = {
  default_rect: "ShapeDefaultR.gltf",
  default_circle: "ShapeDefaultC.gltf",
  default_star: "ShapeDefaultS.gltf",
  default_diamond: "ShapeDefaultW.gltf",
  default_pin: "ShapeDefaultP.gltf",
  default_crystal: "ShapeDefaultC.gltf",
  default_fluid_tank: "ShapeDefaultFluidTank.gltf",
  default_fluid_tank_filled: "ShapeDefaultFluidTankFilled.gltf",
};

export const FLUID_TANK_CENTERED_MESH_KEYS = new Set(["default_fluid_tank_filled", "default_fluid_tank"]);

export const BASE_RADIUS = 0.62;
export const BASE_HEIGHT = 0.08;
export const BASE_COLOR = 0x17121a;
export const SIDE_COLOR = 0x050509;

/** Renderer + lights (shape_gltf viewer) — Neutral TM keeps palette less washed than ACES */
export const RENDERER_TONE_MAPPING = THREE.NeutralToneMapping;
export const RENDERER_TONE_MAPPING_EXPOSURE = 1;
export const RENDERER_HEMI_SKY = 0x9ec8ff;
export const RENDERER_HEMI_GROUND = 0x202028;
export const RENDERER_HEMI_INTENSITY = 0.25;
export const RENDERER_AMBIENT_INTENSITY = 0.35;
export const RENDERER_KEY_INTENSITY = 1.8;
export const RENDERER_FILL_INTENSITY = 0.28;

/** glTF / MeshStandard tuning — see materials.js */
export const MATERIAL_UNKNOWN_COLOR_HEX = 0xff00ff;
export const MATERIAL_PEDESTAL_CYLINDER_RADIAL_SEGMENTS = 96;
export const MATERIAL_PEDESTAL_ROUGHNESS = 0.72;
export const MATERIAL_PEDESTAL_METALNESS = 0.08;
export const MATERIAL_TOP_SEAM_DEFAULT_ROUGHNESS = 0.55;
export const MATERIAL_TOP_SEAM_METALNESS = 0.12;
export const MATERIAL_TWO_FACE_UP_NORMAL_Y_THRESHOLD = 0.55;
export const MATERIAL_TOP_ROUGHNESS_UNCUT = 0.82;
export const MATERIAL_TOP_ENV_INTENSITY_WHITE = 0.55;
export const MATERIAL_TOP_ENV_INTENSITY_DEFAULT = 0.55;
export const MATERIAL_SIDE_ROUGHNESS = 0.85;
export const MATERIAL_SIDE_METALNESS = 0.02;
export const MATERIAL_SIDE_ENV_INTENSITY = 0.45;
export const MATERIAL_PREVIEW_UNCUT_LIGHTNESS_FACTOR = 0.9;
export const MATERIAL_PREVIEW_UNCUT_LIGHTNESS_MIN = 0.28;
export const MATERIAL_PREVIEW_UNCUT_LIGHTNESS_MAX = 0.82;
export const MATERIAL_PREVIEW_CHROMA_LOW_S_THRESHOLD = 0.1;
export const MATERIAL_PREVIEW_CHROMA_LOW_S_DELTA = 0.22;
export const MATERIAL_PREVIEW_CHROMA_S_SCALE = 1.32;
export const MATERIAL_PREVIEW_CHROMA_S_OFFSET = 0.05;
export const MATERIAL_PREVIEW_CHROMA_L_SCALE = 0.88;
export const MATERIAL_PREVIEW_CHROMA_L_MIN = 0.22;
export const MATERIAL_PREVIEW_CHROMA_L_MAX = 0.66;
export const MATERIAL_CRYSTAL_ROUGHNESS = 0.02;
export const MATERIAL_CRYSTAL_TRANSMISSION = 0.55;
export const MATERIAL_CRYSTAL_THICKNESS = 0.75;
export const MATERIAL_CRYSTAL_IOR = 1.65;
export const MATERIAL_CRYSTAL_ATTENUATION_DISTANCE = 0.45;
export const MATERIAL_CRYSTAL_CLEARCOAT = 1;
export const MATERIAL_CRYSTAL_CLEARCOAT_ROUGHNESS = 0.03;
export const MATERIAL_CRYSTAL_SPECULAR_INTENSITY = 2;
export const MATERIAL_CRYSTAL_ENV_INTENSITY = 2.5;
export const MATERIAL_CRYSTAL_TOP_OPACITY = 0.82;
export const MATERIAL_CRYSTAL_EMISSIVE_INTENSITY = 0.22;
export const MATERIAL_CRYSTAL_SIDE_ROUGHNESS = 0.82;
export const MATERIAL_CRYSTAL_SIDE_METALNESS = 0.02;
export const MATERIAL_CRYSTAL_SIDE_ENV_INTENSITY = 0.5;
/** Rim shell: BackSide additive mesh slightly larger than crystal body */
export const MATERIAL_CRYSTAL_GLOW_SCALE = 1.045;
export const MATERIAL_CRYSTAL_GLOW_OPACITY = 0.28;
export const MATERIAL_CRYSTAL_GLOW_RENDER_ORDER = 10;
export const MATERIAL_FLUID_TANK_FILLED_EMISSIVE_INTENSITY = 0.42;

export const LAYER_HEIGHT = 0.102;
export const MODEL_SCALE = 1;
export const LAYER_SCALE_STEP = 0.2;
export const MIN_LAYER_SCALE = 0.72;
export const QUADRANT_GAP = 0.048;
export const LAYER_EXPLODE_HEIGHT = 0.42;
export const EXPLODED_QUADRANT_GAP = 0.38;
export const QUADRANT_LAYER_EXPLODE_HEIGHT = 0.28;
export const VIEW_MODE_TRANSITION_MS = 450;

export const SEAM_COLOR = new THREE.Color(0x020204);
export const SEAM_WIDTH = 0.022;
export const SEAM_FEATHER = 0.006;
export const SEAM_OPACITY = 0;

export const QUADRANT_ROTATIONS = {
  NE: Math.PI,
  SE: Math.PI / 2,
  SW: 0,
  NW: -Math.PI / 2,
};

export const QUADRANT_GAP_OFFSETS = {
  NE: { x: QUADRANT_GAP, z: -QUADRANT_GAP },
  SE: { x: QUADRANT_GAP, z: QUADRANT_GAP },
  SW: { x: -QUADRANT_GAP, z: QUADRANT_GAP },
  NW: { x: -QUADRANT_GAP, z: -QUADRANT_GAP },
};

export const QUADRANT_EXPLODE_OFFSETS = {
  NE: { x: EXPLODED_QUADRANT_GAP, z: -EXPLODED_QUADRANT_GAP },
  SE: { x: EXPLODED_QUADRANT_GAP, z: EXPLODED_QUADRANT_GAP },
  SW: { x: -EXPLODED_QUADRANT_GAP, z: EXPLODED_QUADRANT_GAP },
  NW: { x: -EXPLODED_QUADRANT_GAP, z: -EXPLODED_QUADRANT_GAP },
};

function cameraFrame(distance, targetY) {
  const target = new THREE.Vector3(0, targetY, 0);
  const phi = THREE.MathUtils.degToRad(30);
  const theta = Math.PI;
  const position = new THREE.Vector3()
    .setFromSpherical(new THREE.Spherical(distance, phi, theta))
    .add(target);
  return { position, target };
}

export const CAMERA_FRAMES = {
  original: cameraFrame(2.35, 0.12),
  layer: cameraFrame(3.65, 0.35),
  quadrant: cameraFrame(4.5, 0.24),
};
