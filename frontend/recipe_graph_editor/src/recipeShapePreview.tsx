import { useEffect, useLayoutEffect, useMemo, useRef, useState } from "react";

const PREVIEW_IMAGE_MAX_RETRIES = 3;
const PREVIEW_GLTF_MAX_RETRIES = 3;

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
  /** 서버 macro visual의 ``preview_scene`` — 모달에서만 PNG 실패 시 WebGL 폴백; 타일은 다중 WebGL 컨텍스트 방지 */
  previewScene?: Record<string, unknown> | null;
  variant: "tile" | "modal";
  /** React Flow 타일 등: 미리보기가 실제로 그려진 뒤 노드 치수·합성을 다시 잡기 위해 호출 */
  onPreviewDisplayReady?: () => void;
};

function readMacroAssetBase(): string {
  if (typeof document === "undefined") {
    return "";
  }
  const root = document.getElementById("macro-graph-editor-root");
  const raw = root?.dataset.shapePreviewAssetBase?.trim();
  return typeof raw === "string" ? raw : "";
}

function shapeGltfBridgeReady(): boolean {
  const w = typeof globalThis !== "undefined" ? (globalThis as unknown as Window) : undefined;
  return Boolean(w && w.__shapeGltfMount && readMacroAssetBase());
}

function ShapeGltfMountTile(
  props: Readonly<{
    previewScene: Record<string, unknown>;
    variant: "tile" | "modal";
    onRetriesExhausted?: () => void;
    onMountSuccess?: () => void;
  }>,
) {
  const ref = useRef<HTMLDivElement>(null);
  const onRetriesExhaustedRef = useRef(props.onRetriesExhausted);
  onRetriesExhaustedRef.current = props.onRetriesExhausted;
  const onMountSuccessRef = useRef(props.onMountSuccess);
  onMountSuccessRef.current = props.onMountSuccess;
  const sceneSig = useMemo(() => {
    try {
      return JSON.stringify(props.previewScene);
    } catch {
      return "";
    }
  }, [props.previewScene]);
  const lastSceneSig = useRef("");
  const gltfAttemptRef = useRef(0);
  const gltfRetryTimerRef = useRef<number | undefined>(undefined);
  const [gltfRetryTick, setGltfRetryTick] = useState(0);

  useLayoutEffect(() => {
    if (lastSceneSig.current !== sceneSig) {
      lastSceneSig.current = sceneSig;
      gltfAttemptRef.current = 0;
    }

    const rootEl = ref.current;
    const w = typeof globalThis !== "undefined" ? (globalThis as unknown as Window) : undefined;
    const mount = w?.__shapeGltfMount;
    const dispose = w?.__shapeGltfDispose;
    const assetBase = readMacroAssetBase();
    if (!rootEl || !mount || !assetBase) {
      return;
    }

    rootEl.dataset.shapeGltfViewer = "";

    rootEl.dataset.assetBase = assetBase;

    const viewport = document.createElement("div");
    viewport.dataset.shapeGltfViewport = "";

    viewport.style.height = "100%";
    viewport.style.width = "100%";

    const script = document.createElement("script");
    script.type = "application/json";
    script.textContent = JSON.stringify(props.previewScene);

    rootEl.replaceChildren(viewport, script);

    let cancelled = false;
    mount(rootEl)
      .then(() => {
        if (!cancelled) {
          onMountSuccessRef.current?.();
        }
      })
      .catch((err: unknown) => {
        console.error("Shape GLTF tile preview failed", err);
        if (cancelled) {
          return;
        }
        if (gltfAttemptRef.current < PREVIEW_GLTF_MAX_RETRIES) {
          gltfAttemptRef.current += 1;
          const delay = previewRetryDelayMs(gltfAttemptRef.current - 1);
          if (gltfRetryTimerRef.current !== undefined) {
            window.clearTimeout(gltfRetryTimerRef.current);
          }
          gltfRetryTimerRef.current = window.setTimeout(() => {
            gltfRetryTimerRef.current = undefined;
            if (!cancelled) {
              setGltfRetryTick((t) => t + 1);
            }
          }, delay);
        } else {
          onRetriesExhaustedRef.current?.();
        }
      });

    return () => {
      cancelled = true;
      if (gltfRetryTimerRef.current !== undefined) {
        window.clearTimeout(gltfRetryTimerRef.current);
        gltfRetryTimerRef.current = undefined;
      }
      dispose?.(rootEl);
      rootEl.replaceChildren();
      delete rootEl.dataset.shapeGltfViewer;
      delete rootEl.dataset.assetBase;
    };
  }, [sceneSig, props.variant, gltfRetryTick]);

  const minH = props.variant === "tile" ? "2.5rem" : "7rem";
  return <div ref={ref} className="h-full w-full" style={{ minHeight: minH }} />;
}

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
  const box = tile
    ? "isolate flex h-10 w-10 shrink-0 items-center justify-center overflow-hidden rounded border border-slate-600/50 bg-slate-950 [transform:translate3d(0,0,0)]"
    : "flex h-28 w-full max-w-[200px] items-center justify-center overflow-hidden rounded border border-slate-600/50 bg-slate-950";

  const short = code.trim().slice(0, 3) || "—";

  if (url && !imgFailed) {
    return (
      <div aria-hidden className={box}>
        <img
          alt={previewAlt || code || "Shape preview"}
          className={tile ? "h-full w-full object-contain p-0.5" : "max-h-full max-w-full object-contain p-1"}
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
          ? "flex h-10 w-10 shrink-0 items-center justify-center rounded border border-slate-600/50 bg-linear-to-br from-cyan-950/80 to-slate-900 font-mono text-[10px] font-semibold text-cyan-100/90"
          : "flex h-28 w-full max-w-[200px] items-center justify-center rounded border border-slate-600/50 bg-linear-to-br from-cyan-950/80 to-slate-900 font-mono text-xs font-semibold text-cyan-100/90"
      }
    >
      {short}
    </div>
  );
}
