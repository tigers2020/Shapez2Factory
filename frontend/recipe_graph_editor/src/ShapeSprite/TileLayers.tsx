import { useEffect, useRef, useState } from "react";

import { macroGraphDebug } from "../EditorFoundation/macroGraphDebug";
import {
  TILE_PREVIEW_PX,
  canComposeTileScene,
  cellOverlayZIndex,
  loadSpriteManifest,
  overlayStackScaleFromBottom,
  pedestalSpriteKey,
  readShapePartSpriteManifestUrl,
  sceneCells,
  shapePartSpriteKey,
  sortCellsForStackedOverlay,
} from "./compose";
import {
  ShapeGltfMountTile,
  previewSceneHasDepthLayers,
  shapeGltfBridgeReady,
} from "./ShapeGltfMountTile";

type TileLayerRow = { key: string; url: string; zIndex: number; scale: number };

export function ShapePartSpriteTileLayers(
  props: Readonly<{
    previewScene: Record<string, unknown>;
    fallbackLabel: string;
    fallbackImageUrl?: string;
    onDisplayReady?: () => void;
  }>,
) {
  const onReadyRef = useRef(props.onDisplayReady);
  onReadyRef.current = props.onDisplayReady;
  const loadedCountRef = useRef(0);

  const initialSkip =
    (() => {
      const cells = sceneCells(props.previewScene);
      const manifestUrl = readShapePartSpriteManifestUrl();
      if (!cells || !canComposeTileScene(cells) || !manifestUrl) {
        return true;
      }
      return false;
    })();

  const [showFallback, setShowFallback] = useState(initialSkip);
  const [layers, setLayers] = useState<TileLayerRow[] | null>(null);

  useEffect(() => {
    const cells = sceneCells(props.previewScene);
    const manifestUrl = readShapePartSpriteManifestUrl();
    const norm =
      typeof props.previewScene.normalized_code === "string"
        ? props.previewScene.normalized_code
        : "";
    macroGraphDebug("TileLayers scene", {
      normalized_code: norm,
      cellCount: cells?.length ?? 0,
      hasManifestUrl: Boolean(manifestUrl?.trim()),
      canCompose: Boolean(cells && canComposeTileScene(cells)),
    });
    if (!cells || !canComposeTileScene(cells) || !manifestUrl) {
      let reason: "no_cells" | "canComposeTileScene_false" | "no_manifest_url" = "no_manifest_url";
      if (!cells) {
        reason = "no_cells";
      } else if (!canComposeTileScene(cells)) {
        reason = "canComposeTileScene_false";
      }
      macroGraphDebug("TileLayers → fallback (no sprite path)", { reason });
      setLayers(null);
      setShowFallback(true);
      return;
    }

    let cancelled = false;
    void (async () => {
      const manifest = await loadSpriteManifest(manifestUrl);
      if (cancelled || !manifest) {
        macroGraphDebug("TileLayers → fallback manifest fetch failed", { manifestUrl });
        setLayers(null);
        setShowFallback(true);
        return;
      }
      const rv = typeof manifest.renderer_version === "string" ? manifest.renderer_version.trim() : "v1";
      const stackedCells = sortCellsForStackedOverlay(cells);
      const cellKeys = stackedCells.map((c) => shapePartSpriteKey(c, rv));
      for (const k of cellKeys) {
        if (!manifest.sprites[k]) {
          macroGraphDebug("TileLayers → fallback missing sprite key", { key: k, rendererVersion: rv });
          setLayers(null);
          setShowFallback(true);
          return;
        }
      }
      const pk = pedestalSpriteKey(rv);
      const pedestalEntry = manifest.sprites[pk];

      const rows: TileLayerRow[] = [];
      if (pedestalEntry) {
        rows.push({
          key: pk,
          url: pedestalEntry.url,
          zIndex: 1,
          scale: 1,
        });
      }
      for (let i = 0; i < stackedCells.length; i += 1) {
        const cell = stackedCells[i];
        const k = cellKeys[i];
        const layerTier = Number(cell.layer_index ?? 0);
        const qi = Number(cell.quadrant_index ?? 0);
        rows.push({
          key: `${layerTier}:${qi}:${k}`,
          url: manifest.sprites[k].url,
          zIndex: cellOverlayZIndex(cell),
          // Use layer depth, not draw-order index: same-layer quadrants must stay scale 1 (matches glTF tile).
          scale: overlayStackScaleFromBottom(layerTier),
        });
      }

      if (cancelled) {
        return;
      }
      loadedCountRef.current = 0;
      setLayers(rows);
      setShowFallback(false);
      macroGraphDebug("TileLayers sprite stack ok", { rowCount: rows.length, rendererVersion: rv });
    })();

    return () => {
      cancelled = true;
    };
  }, [props.previewScene, props.fallbackImageUrl]);

  const onImgLoad = () => {
    loadedCountRef.current += 1;
    const n = layers?.length ?? 0;
    if (n > 0 && loadedCountRef.current >= n) {
      queueMicrotask(() => {
        onReadyRef.current?.();
      });
    }
  };

  if (showFallback) {
    if (shapeGltfBridgeReady() && previewSceneHasDepthLayers(props.previewScene)) {
      macroGraphDebug("TileLayers render fallback → WebGL (depth)", {
        normalized_code: props.previewScene.normalized_code,
      });
      return (
        <div
          aria-hidden
          className="relative shrink-0 overflow-hidden"
          style={{ width: TILE_PREVIEW_PX, height: TILE_PREVIEW_PX }}
        >
          <ShapeGltfMountTile
            previewScene={props.previewScene}
            variant="tile"
            onMountSuccess={() => {
              queueMicrotask(() => {
                onReadyRef.current?.();
              });
            }}
          />
        </div>
      );
    }
    const fallbackSrc = typeof props.fallbackImageUrl === "string" ? props.fallbackImageUrl.trim() : "";
    if (fallbackSrc) {
      macroGraphDebug("TileLayers render fallback → PNG", { urlPrefix: fallbackSrc.slice(0, 96) });
      return (
        <img
          alt=""
          className="block h-full w-full object-contain p-0.5"
          draggable={false}
          loading="eager"
          src={fallbackSrc}
          onLoad={() => {
            queueMicrotask(() => {
              onReadyRef.current?.();
            });
          }}
        />
      );
    }
    macroGraphDebug("TileLayers render fallback → label only", { label: props.fallbackLabel });
    return <span className="font-mono text-[10px] font-semibold text-cyan-100/90">{props.fallbackLabel}</span>;
  }

  if (!showFallback && (!layers || layers.length === 0)) {
    return (
      <div
        aria-hidden
        className="shrink-0 rounded bg-slate-950/80"
        style={{ width: TILE_PREVIEW_PX, height: TILE_PREVIEW_PX }}
      />
    );
  }

  if (!layers?.length) {
    return <span className="font-mono text-[10px] font-semibold text-cyan-100/90">{props.fallbackLabel}</span>;
  }

  return (
    <div
      className="relative shrink-0 overflow-hidden"
      style={{ width: TILE_PREVIEW_PX, height: TILE_PREVIEW_PX }}
    >
      {layers.map((row) => (
        <img
          key={row.key}
          alt=""
          className="pointer-events-none absolute inset-0 h-full w-full object-contain"
          draggable={false}
          loading="eager"
          src={row.url}
          style={{
            zIndex: row.zIndex,
            transform: row.scale < 1 ? `scale(${row.scale})` : undefined,
            transformOrigin: "center center",
          }}
          onLoad={onImgLoad}
        />
      ))}
    </div>
  );
}
