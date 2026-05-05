import * as THREE from "three";

import {
  BASE_COLOR,
  BASE_HEIGHT,
  BASE_RADIUS,
  COLOR_HEX,
  SEAM_COLOR,
  SEAM_FEATHER,
  SEAM_OPACITY,
  SEAM_WIDTH,
  SIDE_COLOR,
} from "./constants.js";

function resolveMaterialColor(materialKey) {
  return COLOR_HEX[materialKey] ?? 0xff00ff;
}

export function createPedestal() {
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

function createTopMaterialWithSeam(color, roughness = 0.55) {
  const material = new THREE.MeshStandardMaterial({
    color,
    roughness,
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

export function applyTopSideMaterials(root, materialKey) {
  const topColor = resolveMaterialColor(materialKey);
  const topRoughness = materialKey === "u" ? 0.82 : 0.55;
  const topMaterial = createTopMaterialWithSeam(topColor, topRoughness);
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

/** Fluid tank glTF: top/side split plus mild emissive on upward-facing material. */
export function applyFluidTankFilledMaterials(root, materialKey) {
  applyTopSideMaterials(root, materialKey);
  root.traverse((node) => {
    if (!node.isMesh || !Array.isArray(node.material)) {
      return;
    }
    const top = node.material[0];
    if (top && top.emissive && top.color) {
      top.emissive.copy(top.color);
      top.emissiveIntensity = 0.42;
    }
  });
}
