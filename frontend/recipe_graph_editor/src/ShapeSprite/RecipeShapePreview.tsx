import { useEffect, useMemo, useRef, useState } from "react";

import { TILE_PREVIEW_PX } from "./compose";
import { ShapePartSpriteTileLayers } from "./TileLayers";
import { ShapeGltfMountTile, shapeGltfBridgeReady } from "./ShapeGltfMountTile";

const PREVIEW_IMAGE_MAX_RETRIES = 3;

function previewRetryDelayMs(attemptIndexZeroBased: number): number {
  return 200 * 2 ** attemptIndexZeroBased;
}

declare global {
  interface Window {
    __shapeGltfMount?: (el: HTMLElement) => Promise<unknown>;
    __shapeGltfDispose?: (el: HTMLElement) => void;
  }
}

export type RecipeShapePreviewProps = {
  code: string;
  previewAlt?: string;
  previewImageUrl?: string;
  /** 서버 macro visual의 ``preview_scene``. 타일은 스프라이트 우선; 다층 폴백 시 TileLayers가 WebGL 타일을 쓸 수 있음 */
  previewScene?: Record<string, unknown> | null;
  variant: "tile" | "modal";
  /** React Flow 타일 등: 미리보기가 실제로 그려진 뒤 노드 치수·합성을 다시 잡기 위해 호출 */
  onPreviewDisplayReady?: () => void;
};

export function RecipeShapePreview({
  code,
  previewAlt,
  previewImageUrl,
  previewScene,
  variant,
  onPreviewDisplayReady,
}: Readonly<RecipeShapePreviewProps>) {
  const [imgFailed, setImgFailed] = useState(false);
  const [imgRetryNonce, setImgRetryNonce] = useState(0);
  const imgRetryTimerRef = useRef<number | undefined>(undefined);
  const onReadyRef = useRef(onPreviewDisplayReady);
  onReadyRef.current = onPreviewDisplayReady;

  const firePreviewReady = () => {
    queueMicrotask(() => {
      onReadyRef.current?.();
    });
  };

  useEffect(() => {
    setImgFailed(false);
    setImgRetryNonce(0);
    return () => {
      if (imgRetryTimerRef.current !== undefined) {
        window.clearTimeout(imgRetryTimerRef.current);
        imgRetryTimerRef.current = undefined;
      }
    };
  }, [previewImageUrl, code, previewScene]);

  const url = typeof previewImageUrl === "string" ? previewImageUrl.trim() : "";
  const imgSrc = useMemo(() => {
    if (!url) {
      return "";
    }
    if (imgRetryNonce === 0) {
      return url;
    }
    const sep = url.includes("?") ? "&" : "?";
    return `${url}${sep}_shapePvRetry=${imgRetryNonce}`;
  }, [url, imgRetryNonce]);
  const scene =
    previewScene !== null &&
    previewScene !== undefined &&
    typeof previewScene === "object" &&
    !Array.isArray(previewScene)
      ? previewScene
      : null;

  const tile = variant === "tile";

  const tileBox =
    "isolate flex shrink-0 items-center justify-center overflow-hidden rounded border border-slate-600/50 bg-slate-950 [transform:translate3d(0,0,0)]";
  const box = tile
    ? tileBox
    : "flex h-28 w-full max-w-[200px] items-center justify-center overflow-hidden rounded border border-slate-600/50 bg-slate-950";

  const short = code.trim().slice(0, 3) || "—";

  if (tile && scene) {
    return (
      <div
        aria-hidden
        className={box}
        style={{ width: TILE_PREVIEW_PX, height: TILE_PREVIEW_PX }}
      >
        <ShapePartSpriteTileLayers
          fallbackImageUrl={url || undefined}
          fallbackLabel={short}
          previewScene={scene}
          onDisplayReady={firePreviewReady}
        />
      </div>
    );
  }

  if (url && !imgFailed) {
    return (
      <div
        aria-hidden
        className={box}
        style={tile ? { width: TILE_PREVIEW_PX, height: TILE_PREVIEW_PX } : undefined}
      >
        <img
          alt={previewAlt || code || "Shape preview"}
          className={
            tile
              ? "h-full w-full object-contain p-0.5"
              : "max-h-full max-w-full object-contain p-1"
          }
          loading={tile ? "eager" : "lazy"}
          src={imgSrc}
          onLoad={firePreviewReady}
          onError={() => {
            if (imgRetryNonce < PREVIEW_IMAGE_MAX_RETRIES) {
              const delayMs = previewRetryDelayMs(imgRetryNonce);
              if (imgRetryTimerRef.current !== undefined) {
                window.clearTimeout(imgRetryTimerRef.current);
              }
              imgRetryTimerRef.current = window.setTimeout(() => {
                imgRetryTimerRef.current = undefined;
                setImgRetryNonce((n) => n + 1);
              }, delayMs);
            } else {
              setImgFailed(true);
            }
          }}
        />
      </div>
    );
  }

  if (!tile && scene && shapeGltfBridgeReady()) {
    return (
      <div aria-hidden className={box}>
        <ShapeGltfMountTile
          previewScene={scene}
          variant={variant}
          onMountSuccess={firePreviewReady}
        />
      </div>
    );
  }

  return (
    <div
      aria-hidden
      className={
        tile
          ? "flex shrink-0 items-center justify-center rounded border border-slate-600/50 bg-linear-to-br from-cyan-950/80 to-slate-900 font-mono text-[10px] font-semibold text-cyan-100/90"
          : "flex h-28 w-full max-w-[200px] items-center justify-center rounded border border-slate-600/50 bg-linear-to-br from-cyan-950/80 to-slate-900 font-mono text-xs font-semibold text-cyan-100/90"
      }
      style={tile ? { width: TILE_PREVIEW_PX, height: TILE_PREVIEW_PX } : undefined}
    >
      {short}
    </div>
  );
}
