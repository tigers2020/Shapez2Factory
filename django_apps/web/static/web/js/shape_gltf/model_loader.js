import { MODEL_FILES } from "./constants.js";

const modelCache = new Map();

export async function loadModel(loader, assetBase, meshKey) {
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
