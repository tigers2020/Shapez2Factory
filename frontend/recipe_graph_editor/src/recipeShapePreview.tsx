import { useEffect, useLayoutEffect, useRef, useState } from "react";

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
  /** 서버 macro visual의 ``preview_scene`` — PNG가 없을 때(예: noop) WebGL 폴백 */
  previewScene?: Record<string, unknown> | null;
  variant: "tile" | "modal";
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

function ShapeGltfMountTile(props: Readonly<{ previewScene: Record<string, unknown>; variant: "tile" | "modal" }>) {
  const ref = useRef<HTMLDivElement>(null);

  useLayoutEffect(() => {
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

    mount(rootEl).catch((err: unknown) => {
      console.error("Shape GLTF tile preview failed", err);
    });

    return () => {
      dispose?.(rootEl);
      rootEl.replaceChildren();
      delete rootEl.dataset.shapeGltfViewer;
      delete rootEl.dataset.assetBase;
    };
  }, [props.previewScene, props.variant]);

  const minH = props.variant === "tile" ? "2.5rem" : "7rem";
  return <div ref={ref} className="h-full w-full" style={{ minHeight: minH }} />;
}

export function RecipeShapePreview({
  code,
  previewAlt,
  previewImageUrl,
  previewScene,
  variant,
}: Readonly<RecipeShapePreviewProps>) {
  const [imgFailed, setImgFailed] = useState(false);
  useEffect(() => {
    setImgFailed(false);
  }, [previewImageUrl, code, previewScene]);

  const url = typeof previewImageUrl === "string" ? previewImageUrl.trim() : "";
  const scene =
    previewScene !== null &&
    previewScene !== undefined &&
    typeof previewScene === "object" &&
    !Array.isArray(previewScene)
      ? previewScene
      : null;

  const tile = variant === "tile";
  const box = tile
    ? "flex h-10 w-10 shrink-0 items-center justify-center overflow-hidden rounded border border-slate-600/50 bg-slate-950"
    : "flex h-28 w-full max-w-[200px] items-center justify-center overflow-hidden rounded border border-slate-600/50 bg-slate-950";

  const short = code.trim().slice(0, 3) || "—";

  if (url && !imgFailed) {
    return (
      <div aria-hidden className={box}>
        <img
          alt={previewAlt || code || "Shape preview"}
          className={tile ? "h-full w-full object-contain p-0.5" : "max-h-full max-w-full object-contain p-1"}
          loading="lazy"
          src={url}
          onError={() => {
            setImgFailed(true);
          }}
        />
      </div>
    );
  }

  if (scene && shapeGltfBridgeReady()) {
    return (
      <div aria-hidden className={box}>
        <ShapeGltfMountTile previewScene={scene} variant={variant} />
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
