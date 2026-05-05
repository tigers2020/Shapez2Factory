import * as THREE from "three";

import {
  BASE_COLOR,
  BASE_HEIGHT,
  BASE_RADIUS,
  COLOR_HEX,
  MATERIAL_CRYSTAL_ATTENUATION_DISTANCE,
  MATERIAL_CRYSTAL_CLEARCOAT,
  MATERIAL_CRYSTAL_CLEARCOAT_ROUGHNESS,
  MATERIAL_CRYSTAL_EMISSIVE_INTENSITY,
  MATERIAL_CRYSTAL_ENV_INTENSITY,
  MATERIAL_CRYSTAL_GLOW_OPACITY,
  MATERIAL_CRYSTAL_GLOW_RENDER_ORDER,
  MATERIAL_CRYSTAL_GLOW_SCALE,
  MATERIAL_CRYSTAL_IOR,
  MATERIAL_CRYSTAL_ROUGHNESS,
  MATERIAL_CRYSTAL_SIDE_ENV_INTENSITY,
  MATERIAL_CRYSTAL_SIDE_METALNESS,
  MATERIAL_CRYSTAL_SIDE_ROUGHNESS,
  MATERIAL_CRYSTAL_SPECULAR_INTENSITY,
  MATERIAL_CRYSTAL_THICKNESS,
  MATERIAL_CRYSTAL_TOP_OPACITY,
  MATERIAL_CRYSTAL_TRANSMISSION,
  MATERIAL_FLUID_TANK_FILLED_EMISSIVE_INTENSITY,
  MATERIAL_PEDESTAL_CYLINDER_RADIAL_SEGMENTS,
  MATERIAL_PEDESTAL_METALNESS,
  MATERIAL_PEDESTAL_ROUGHNESS,
  MATERIAL_PREVIEW_CHROMA_L_MAX,
  MATERIAL_PREVIEW_CHROMA_L_MIN,
  MATERIAL_PREVIEW_CHROMA_L_SCALE,
  MATERIAL_PREVIEW_CHROMA_LOW_S_DELTA,
  MATERIAL_PREVIEW_CHROMA_LOW_S_THRESHOLD,
  MATERIAL_PREVIEW_CHROMA_S_OFFSET,
  MATERIAL_PREVIEW_CHROMA_S_SCALE,
  MATERIAL_PREVIEW_UNCUT_LIGHTNESS_FACTOR,
  MATERIAL_PREVIEW_UNCUT_LIGHTNESS_MAX,
  MATERIAL_PREVIEW_UNCUT_LIGHTNESS_MIN,
  MATERIAL_SIDE_ENV_INTENSITY,
  MATERIAL_SIDE_METALNESS,
  MATERIAL_SIDE_ROUGHNESS,
  MATERIAL_TOP_ENV_INTENSITY_DEFAULT,
  MATERIAL_TOP_ENV_INTENSITY_WHITE,
  MATERIAL_TOP_ROUGHNESS_UNCUT,
  MATERIAL_TOP_SEAM_DEFAULT_ROUGHNESS,
  MATERIAL_TOP_SEAM_METALNESS,
  MATERIAL_TWO_FACE_UP_NORMAL_Y_THRESHOLD,
  MATERIAL_UNKNOWN_COLOR_HEX,
  SEAM_COLOR,
  SEAM_FEATHER,
  SEAM_OPACITY,
  SEAM_WIDTH,
  SIDE_COLOR,
} from "./constants.js";

function resolveMaterialColor(materialKey) {
  return COLOR_HEX[materialKey] ?? MATERIAL_UNKNOWN_COLOR_HEX;
}

/**
 * Thumbnail previews read chalky under ACES + IBL; nudge chroma and depth (skip white).
 * @param {THREE.Color} color
 * @param {string} materialKey
 */
function punchPreviewColor(color, materialKey) {
  if (materialKey === "w") {
    return;
  }
  const hsl = { h: 0, s: 0, l: 0 };
  color.getHSL(hsl);
  if (materialKey === "u") {
    hsl.l = THREE.MathUtils.clamp(
      hsl.l * MATERIAL_PREVIEW_UNCUT_LIGHTNESS_FACTOR,
      MATERIAL_PREVIEW_UNCUT_LIGHTNESS_MIN,
      MATERIAL_PREVIEW_UNCUT_LIGHTNESS_MAX,
    );
    color.setHSL(hsl.h, hsl.s, hsl.l);
    return;
  }
  const nextS = Math.min(
    1,
    hsl.s < MATERIAL_PREVIEW_CHROMA_LOW_S_THRESHOLD
      ? hsl.s + MATERIAL_PREVIEW_CHROMA_LOW_S_DELTA
      : hsl.s * MATERIAL_PREVIEW_CHROMA_S_SCALE + MATERIAL_PREVIEW_CHROMA_S_OFFSET,
  );
  const nextL = THREE.MathUtils.clamp(
    hsl.l * MATERIAL_PREVIEW_CHROMA_L_SCALE,
    MATERIAL_PREVIEW_CHROMA_L_MIN,
    MATERIAL_PREVIEW_CHROMA_L_MAX,
  );
  color.setHSL(hsl.h, nextS, nextL);
}

export function createPedestal() {
  const geometry = new THREE.CylinderGeometry(
    BASE_RADIUS,
    BASE_RADIUS,
    BASE_HEIGHT,
    MATERIAL_PEDESTAL_CYLINDER_RADIAL_SEGMENTS,
  );
  const material = new THREE.MeshStandardMaterial({
    color: BASE_COLOR,
    roughness: MATERIAL_PEDESTAL_ROUGHNESS,
    metalness: MATERIAL_PEDESTAL_METALNESS,
  });

  const pedestal = new THREE.Mesh(geometry, material);
  pedestal.position.set(0, -BASE_HEIGHT / 2, 0);
  pedestal.receiveShadow = true;
  pedestal.castShadow = false;

  return pedestal;
}

function createTopMaterialWithSeam(color, roughness = MATERIAL_TOP_SEAM_DEFAULT_ROUGHNESS) {
  const material = new THREE.MeshStandardMaterial({
    color,
    roughness,
    metalness: MATERIAL_TOP_SEAM_METALNESS,
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

/**
 * Split each mesh into upward-facing (material slot 0) vs side/bottom (slot 1) groups.
 * @param {THREE.Object3D} root
 * @param {THREE.Material} topMaterial
 * @param {THREE.Material} sideMaterial
 */
function applyTwoFaceMaterials(root, topMaterial, sideMaterial) {
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
      const materialIndex = avgNormalY > MATERIAL_TWO_FACE_UP_NORMAL_Y_THRESHOLD ? 0 : 1;

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

/**
 * Crystal-only: thin BackSide additive shell so tiles read as crystal vs matte shapes.
 * @param {THREE.Object3D} root
 * @param {THREE.Color} color
 */
function addCrystalGlowShell(root, color) {
  root.traverse((node) => {
    if (!node.isMesh || !node.geometry || node.userData._crystalGlowShell) {
      return;
    }

    const glowMaterial = new THREE.MeshBasicMaterial({
      color,
      transparent: true,
      opacity: MATERIAL_CRYSTAL_GLOW_OPACITY,
      blending: THREE.AdditiveBlending,
      depthWrite: false,
      side: THREE.BackSide,
    });

    const geo = node.geometry.clone();
    if (typeof geo.clearGroups === "function") {
      geo.clearGroups();
    }
    const glow = new THREE.Mesh(geo, glowMaterial);
    glow.userData._crystalGlowShell = true;
    glow.scale.multiplyScalar(MATERIAL_CRYSTAL_GLOW_SCALE);
    glow.renderOrder = MATERIAL_CRYSTAL_GLOW_RENDER_ORDER;
    node.add(glow);
  });
}

export function applyTopSideMaterials(root, materialKey) {
  const topColor = resolveMaterialColor(materialKey);
  const topRoughness = materialKey === "u" ? MATERIAL_TOP_ROUGHNESS_UNCUT : MATERIAL_TOP_SEAM_DEFAULT_ROUGHNESS;
  const topColorThree = new THREE.Color(topColor);
  punchPreviewColor(topColorThree, materialKey);
  const topMaterial = createTopMaterialWithSeam(topColorThree, topRoughness);
  topMaterial.envMapIntensity =
    materialKey === "w" ? MATERIAL_TOP_ENV_INTENSITY_WHITE : MATERIAL_TOP_ENV_INTENSITY_DEFAULT;
  topMaterial.emissive.setRGB(0, 0, 0);
  topMaterial.emissiveIntensity = 0;
  const sideMaterial = new THREE.MeshStandardMaterial({
    color: SIDE_COLOR,
    roughness: MATERIAL_SIDE_ROUGHNESS,
    metalness: MATERIAL_SIDE_METALNESS,
    envMapIntensity: MATERIAL_SIDE_ENV_INTENSITY,
  });

  applyTwoFaceMaterials(root, topMaterial, sideMaterial);
}

/** Crystal glTF: glassy body + rim glow shell vs matte normal shapes (constants.js). */
export function applyCrystalMaterials(root, materialKey) {
  const baseHex = resolveMaterialColor(materialKey);
  const baseColor = new THREE.Color(baseHex);
  punchPreviewColor(baseColor, materialKey);
  const attenColor = baseColor.clone();

  const topMaterial = new THREE.MeshPhysicalMaterial({
    color: baseColor,
    roughness: MATERIAL_CRYSTAL_ROUGHNESS,
    metalness: 0,
    transmission: MATERIAL_CRYSTAL_TRANSMISSION,
    thickness: MATERIAL_CRYSTAL_THICKNESS,
    ior: MATERIAL_CRYSTAL_IOR,
    transparent: true,
    opacity: MATERIAL_CRYSTAL_TOP_OPACITY,
    attenuationColor: attenColor,
    attenuationDistance: MATERIAL_CRYSTAL_ATTENUATION_DISTANCE,
    clearcoat: MATERIAL_CRYSTAL_CLEARCOAT,
    clearcoatRoughness: MATERIAL_CRYSTAL_CLEARCOAT_ROUGHNESS,
    specularIntensity: MATERIAL_CRYSTAL_SPECULAR_INTENSITY,
    envMapIntensity: MATERIAL_CRYSTAL_ENV_INTENSITY,
  });
  topMaterial.emissive.copy(baseColor);
  topMaterial.emissiveIntensity = MATERIAL_CRYSTAL_EMISSIVE_INTENSITY;

  const sideMaterial = new THREE.MeshStandardMaterial({
    color: SIDE_COLOR,
    roughness: MATERIAL_CRYSTAL_SIDE_ROUGHNESS,
    metalness: MATERIAL_CRYSTAL_SIDE_METALNESS,
    envMapIntensity: MATERIAL_CRYSTAL_SIDE_ENV_INTENSITY,
  });

  applyTwoFaceMaterials(root, topMaterial, sideMaterial);
  addCrystalGlowShell(root, baseColor);
}

/** Fluid tank glTF: top/side split plus mild emissive on upward-facing material. */
export function applyFluidTankFilledMaterials(root, materialKey) {
  applyTopSideMaterials(root, materialKey);
  root.traverse((node) => {
    if (!node.isMesh || !Array.isArray(node.material)) {
      return;
    }
    const top = node.material[0];
    if (top?.emissive && top?.color) {
      top.emissive.copy(top.color);
      top.emissiveIntensity = MATERIAL_FLUID_TANK_FILLED_EMISSIVE_INTENSITY;
    }
  });
}
