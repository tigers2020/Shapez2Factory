import * as THREE from "three";

import {
  FLUID_TANK_CENTERED_MESH_KEYS,
  LAYER_EXPLODE_HEIGHT,
  LAYER_HEIGHT,
  LAYER_SCALE_STEP,
  MIN_LAYER_SCALE,
  MODEL_SCALE,
  QUADRANT_EXPLODE_OFFSETS,
  QUADRANT_GAP_OFFSETS,
  QUADRANT_LAYER_EXPLODE_HEIGHT,
  QUADRANT_ROTATIONS,
} from "./constants.js";

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

export function computeTransform(cell, viewMode = "original") {
  const meshKey = typeof cell.mesh_key === "string" ? cell.mesh_key : "";
  const layerIndex = getLayerIndex(cell);
  const layerScale = getLayerScale(layerIndex);

  if (FLUID_TANK_CENTERED_MESH_KEYS.has(meshKey)) {
    let y = layerIndex * LAYER_HEIGHT;
    if (viewMode === "layer") {
      y = layerIndex * LAYER_EXPLODE_HEIGHT;
    } else if (viewMode === "quadrant") {
      y = layerIndex * QUADRANT_LAYER_EXPLODE_HEIGHT;
    }
    return {
      position: new THREE.Vector3(0, y, 0),
      rotationY: 0,
      scale: layerScale,
    };
  }

  const positionKey = getPositionKey(cell);
  const microOffset = QUADRANT_GAP_OFFSETS[positionKey] ?? { x: 0, z: 0 };
  const explodeOffset = QUADRANT_EXPLODE_OFFSETS[positionKey] ?? { x: 0, z: 0 };

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

export function applyComputedTransform(model, transform) {
  model.position.copy(transform.position);
  model.rotation.set(0, transform.rotationY, 0);
  model.scale.setScalar(transform.scale);
}

export function applyTransform(model, cell, viewMode = "original") {
  applyComputedTransform(model, computeTransform(cell, viewMode));
}
