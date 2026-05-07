/** Tile preview size (CSS px); DOM layers scale transparent PNGs without Canvas resampling. */
export const TILE_PREVIEW_PX = 64;

/** Each overlay tier above the bottom is scaled by this factor (10% size reduction per tier). */
export const STACK_OVERLAY_SCALE_STEP = 0.9;

/** Scale by vertical ``layer_index`` tier (0 = full size); not z-order / paint index. */
export function overlayStackScaleFromBottom(tierIndex: number): number {
  const i = Number.isFinite(tierIndex) ? Math.max(0, Math.floor(tierIndex)) : 0;
  return STACK_OVERLAY_SCALE_STEP ** i;
}

export type SpriteManifestEntry = { url: string; width: number; height: number };
export type SpriteManifestResponse = {
  renderer_version: string;
  sprites: Record<string, SpriteManifestEntry>;
};

let cachedManifestUrl = "";
let manifestPromise: Promise<SpriteManifestResponse | null> | null = null;

/** Test-only: reset cached manifest fetch. */
export function resetSpriteManifestCache(): void {
  cachedManifestUrl = "";
  manifestPromise = null;
}

export function loadSpriteManifest(url: string): Promise<SpriteManifestResponse | null> {
  const u = url.trim();
  if (!u) {
    return Promise.resolve(null);
  }
  if (u !== cachedManifestUrl) {
    cachedManifestUrl = u;
    manifestPromise = fetch(u, { credentials: "same-origin" })
      .then((r) => (r.ok ? (r.json() as Promise<SpriteManifestResponse>) : null))
      .catch(() => null);
  }
  return manifestPromise ?? Promise.resolve(null);
}

/** Staff graph root ``data-shape-part-sprite-manifest-url``, else ``#macro-graph-bootstrap`` JSON. */
export function readShapePartSpriteManifestUrl(): string {
  if (typeof document === "undefined") {
    return "";
  }
  const root = document.getElementById("macro-graph-editor-root");
  const fromDataset = root?.dataset.shapePartSpriteManifestUrl?.trim();
  if (typeof fromDataset === "string" && fromDataset.length > 0) {
    return fromDataset;
  }
  const script = document.getElementById("macro-graph-bootstrap");
  const raw = script?.textContent?.trim();
  if (!raw) {
    return "";
  }
  try {
    const o = JSON.parse(raw) as Record<string, unknown>;
    const u = o.api_shape_part_sprite_manifest;
    return typeof u === "string" ? u.trim() : "";
  } catch {
    return "";
  }
}

/** Manifest key for pedestal-only bake (matches ``ShapePartSprite`` pedestal row). */
export function pedestalSpriteKey(rendererVersion: string): string {
  const rv = typeof rendererVersion === "string" ? rendererVersion.trim() : "";
  return `pedestal:${rv || "v1"}`;
}

/** One game layer: 8 chars (four quadrant tokens), same notation as shape code list. */
export function atomicLayerGameCode(shapeCode: string, colorCode: string, quadrantIndex: number): string {
  const slots = ["--", "--", "--", "--"];
  const qi = Number.isFinite(quadrantIndex) ? Math.min(3, Math.max(0, Math.floor(quadrantIndex))) : 0;
  if (shapeCode === "P") {
    slots[qi] = "P-";
  } else {
    slots[qi] = shapeCode + colorCode;
  }
  return slots.join("");
}

/** Manifest key: ``{8-char layer}:{rv}`` for parts; ``color-{ink}:{rv}`` for paint-can ``t``. */
export function shapePartSpriteKey(cell: Record<string, unknown>, rendererVersion: string): string {
  const shapeRaw = cell.shape_code;
  const ccRaw = cell.color_code;
  let shapeCode = "";
  if (typeof shapeRaw === "string") {
    shapeCode = shapeRaw;
  } else if (typeof shapeRaw === "number") {
    shapeCode = String(shapeRaw);
  }
  let colorCode = "";
  if (typeof ccRaw === "string") {
    colorCode = ccRaw;
  } else if (typeof ccRaw === "number") {
    colorCode = String(ccRaw);
  }
  const rv = typeof rendererVersion === "string" ? rendererVersion.trim() : "";
  if (shapeCode === "t") {
    return `color-${colorCode}:${rv || "v1"}`;
  }
  const qiRaw = cell.quadrant_index;
  let qi = 0;
  if (typeof qiRaw === "number") {
    qi = qiRaw;
  } else if (typeof qiRaw === "string") {
    qi = Number.parseInt(qiRaw, 10);
  }
  const qiSafe = Number.isFinite(qi) ? Math.min(3, Math.max(0, qi)) : 0;
  const layer = atomicLayerGameCode(shapeCode, colorCode, qiSafe);
  return `${layer}:${rv || "v1"}`;
}

/** Map quadrant_index to a quarter-rectangle (helper); tile preview stacks full-size sprites instead. */
export function quadrantDestRect(
  quadrantIndex: number,
  totalSize: number,
): { x: number; y: number; w: number; h: number } {
  const h = totalSize / 2;
  if (quadrantIndex === 0) {
    return { x: 0, y: h, w: h, h: h };
  }
  if (quadrantIndex === 1) {
    return { x: 0, y: 0, w: h, h: h };
  }
  if (quadrantIndex === 2) {
    return { x: h, y: 0, w: h, h: h };
  }
  return { x: h, y: h, w: h, h: h };
}

/**
 * DOM stack tier within one ``layer_index`` (low = behind, high = in front).
 * Quadrants: 0=SW, 1=NW, 2=NE, 3=SE — full-tile sprites overlap; SW/SE sit under NW/NE.
 */
export function quadrantOverlayStackTier(quadrantIndex: number): number {
  const qi = Number.isFinite(quadrantIndex) ? Math.min(3, Math.max(0, Math.floor(quadrantIndex))) : 0;
  switch (qi) {
    case 0:
      return 0;
    case 3:
      return 1;
    case 1:
      return 2;
    case 2:
      return 3;
    default:
      return 0;
  }
}

/** z-index for stacked `<img>` layers (pedestal uses 1 separately). */
export function cellOverlayZIndex(cell: Record<string, unknown>): number {
  const layer = Number(cell.layer_index ?? 0);
  const qi = Number(cell.quadrant_index ?? 0);
  return 10 + layer * 10 + quadrantOverlayStackTier(qi);
}

export function sceneCells(scene: Record<string, unknown>): Record<string, unknown>[] | null {
  const raw = scene.cells;
  if (!Array.isArray(raw)) {
    return null;
  }
  return raw as Record<string, unknown>[];
}

/** Stack draw order: ``layer_index`` then quadrant overlay tier (SW/SE behind NW/NE). */
export function sortCellsForStackedOverlay(cells: Record<string, unknown>[]): Record<string, unknown>[] {
  return [...cells].sort((a, b) => {
    const la = Number(a.layer_index ?? 0);
    const lb = Number(b.layer_index ?? 0);
    if (la !== lb) {
      return la - lb;
    }
    const qa = Number(a.quadrant_index ?? 0);
    const qb = Number(b.quadrant_index ?? 0);
    const ta = quadrantOverlayStackTier(qa);
    const tb = quadrantOverlayStackTier(qb);
    if (ta !== tb) {
      return ta - tb;
    }
    return qa - qb;
  });
}

/** Align with ``MAX_GRAPH_SHAPE_LAYERS_PER_PATTERN`` (recipe graph): layers 0..3, ≤16 cells. */
const MAX_TILE_SCENE_LAYER_INDEX = 3;
const MAX_TILE_SCENE_CELLS = (MAX_TILE_SCENE_LAYER_INDEX + 1) * 4;

export function canComposeTileScene(cells: Record<string, unknown>[]): boolean {
  if (cells.length === 0 || cells.length > MAX_TILE_SCENE_CELLS) {
    return false;
  }
  const seen = new Set<string>();
  for (const cell of cells) {
    const layer = Number(cell.layer_index ?? 0);
    const qi = Number(cell.quadrant_index ?? 0);
    if (
      !Number.isFinite(layer) ||
      !Number.isFinite(qi) ||
      !Number.isInteger(layer) ||
      !Number.isInteger(qi)
    ) {
      return false;
    }
    if (layer < 0 || layer > MAX_TILE_SCENE_LAYER_INDEX || qi < 0 || qi > 3) {
      return false;
    }
    const key = `${layer}:${qi}`;
    if (seen.has(key)) {
      return false;
    }
    seen.add(key);
  }
  return true;
}

export function loadImage(src: string): Promise<HTMLImageElement> {
  return new Promise((resolve, reject) => {
    const img = new Image();
    img.onload = () => resolve(img);
    img.onerror = () => reject(new Error("image load failed"));
    img.src = src;
  });
}
