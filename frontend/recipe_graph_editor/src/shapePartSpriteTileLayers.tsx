import { useEffect, useRef, useState } from "react";

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
} from "./shapePartSpriteCompose";

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
    if (!cells || !canComposeTileScene(cells) || !manifestUrl) {
      setLayers(null);
      setShowFallback(true);
      return;
    }

    let cancelled = false;
    void (async () => {
      const manifest = await loadSpriteManifest(manifestUrl);
      if (cancelled || !manifest) {
        setLayers(null);
        setShowFallback(true);
        return;
      }
      const rv = typeof manifest.renderer_version === "string" ? manifest.renderer_version.trim() : "v1";
      const stackedCells = sortCellsForStackedOverlay(cells);
      const cellKeys = stackedCells.map((c) => shapePartSpriteKey(c, rv));
      for (const k of cellKeys) {
        if (!manifest.sprites[k]) {
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
        rows.push({
          key: k,
          url: manifest.sprites[k].url,
          zIndex: cellOverlayZIndex(cell),
          scale: overlayStackScaleFromBottom(i),
        });
      }

      if (cancelled) {
        return;
      }
      loadedCountRef.current = 0;
      setLayers(rows);
      setShowFallback(false);
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
    const fallbackSrc = typeof props.fallbackImageUrl === "string" ? props.fallbackImageUrl.trim() : "";
    if (fallbackSrc) {
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
