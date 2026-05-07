import * as THREE from "three";

import {
  applyCrystalMaterials,
  applyFluidTankFilledMaterials,
  applyFluidTankVortexMaterials,
  applyTopSideMaterials,
  createPedestal,
} from "./materials.js";
import { loadModel } from "./model_loader.js";
import { applyTransform } from "./transform.js";

/** When glTF root origin != mesh centroid, Y-rotation orbits look non-rigid; pivot at AABB center. */
function wrapModelAtBoundingBoxCenter(model) {
  const box = new THREE.Box3().setFromObject(model);
  if (box.isEmpty()) {
    return model;
  }
  const center = new THREE.Vector3();
  box.getCenter(center);
  if (center.lengthSq() < 1e-12) {
    return model;
  }
  const pivot = new THREE.Group();
  model.position.sub(center);
  pivot.add(model);
  return pivot;
}

export async function renderSceneToThree(scene, loader, assetBase, renderScene, viewMode) {
  const records = [];
  const showPedestal = renderScene.include_pedestal !== false;
  if (showPedestal) {
    scene.add(createPedestal());
  }

  for (const cell of renderScene.cells) {
    const model = await loadModel(loader, assetBase, cell.mesh_key);
    if (!model) {
      continue;
    }

    if (cell.mesh_key === "default_fluid_tank_filled") {
      applyFluidTankFilledMaterials(model, cell.material_key);
    } else if (cell.mesh_key === "default_fluid_tank_vortex") {
      applyFluidTankVortexMaterials(model, cell.material_key);
    } else if (cell.mesh_key === "default_crystal") {
      applyCrystalMaterials(model, cell.material_key);
    } else {
      applyTopSideMaterials(model, cell.material_key);
    }
    const pivot = wrapModelAtBoundingBoxCenter(model);
    applyTransform(pivot, cell, viewMode);
    scene.add(pivot);
    records.push({ cell, model: pivot, transition: null });
  }

  return records;
}
