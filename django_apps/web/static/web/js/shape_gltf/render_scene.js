import {
  applyCrystalMaterials,
  applyFluidTankFilledMaterials,
  applyTopSideMaterials,
  createPedestal,
} from "./materials.js";
import { loadModel } from "./model_loader.js";
import { applyTransform } from "./transform.js";

export async function renderSceneToThree(scene, loader, assetBase, renderScene, viewMode) {
  const records = [];
  scene.add(createPedestal());

  for (const cell of renderScene.cells) {
    const model = await loadModel(loader, assetBase, cell.mesh_key);
    if (!model) {
      continue;
    }

    if (cell.mesh_key === "default_fluid_tank_filled") {
      applyFluidTankFilledMaterials(model, cell.material_key);
    } else if (cell.mesh_key === "default_crystal") {
      applyCrystalMaterials(model, cell.material_key);
    } else {
      applyTopSideMaterials(model, cell.material_key);
    }
    applyTransform(model, cell, viewMode);
    scene.add(model);
    records.push({ cell, model, transition: null });
  }

  return records;
}
