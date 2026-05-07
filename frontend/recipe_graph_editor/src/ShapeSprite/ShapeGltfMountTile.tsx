import { useLayoutEffect, useMemo, useRef, useState } from "react";

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

export function readMacroAssetBase(): string {
  if (typeof document === "undefined") {
    return "";
  }
  const root = document.getElementById("macro-graph-editor-root");
  const raw = root?.dataset.shapePreviewAssetBase?.trim();
  return typeof raw === "string" ? raw : "";
}

export function shapeGltfBridgeReady(): boolean {
  const w = typeof globalThis !== "undefined" ? (globalThis as unknown as Window) : undefined;
  return Boolean(w && w.__shapeGltfMount && readMacroAssetBase());
}

/** True when ``preview_scene`` represents stacked game layers (sprite fallback alone may look flat). */
export function previewSceneHasDepthLayers(previewScene: Record<string, unknown>): boolean {
  const norm = previewScene.normalized_code;
  if (typeof norm === "string" && norm.includes(":")) {
    return true;
  }
  const raw = previewScene.cells;
  if (!Array.isArray(raw)) {
    return false;
  }
  return raw.some((c) => {
    if (!c || typeof c !== "object" || Array.isArray(c)) {
      return false;
    }
    const layer = Number((c as { layer_index?: unknown }).layer_index ?? 0);
    return Number.isFinite(layer) && layer > 0;
  });
}

export function ShapeGltfMountTile(
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
