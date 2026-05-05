import { useEffect, useState } from "react";

export type RecipeShapePreviewProps = {
  code: string;
  previewAlt?: string;
  previewImageUrl?: string;
  /** 타일 노드용 / 모달 대형 미리보기 */
  variant: "tile" | "modal";
};

export function RecipeShapePreview({
  code,
  previewAlt,
  previewImageUrl,
  variant,
}: RecipeShapePreviewProps) {
  const [imgFailed, setImgFailed] = useState(false);
  useEffect(() => {
    setImgFailed(false);
  }, [previewImageUrl, code]);
  const url = typeof previewImageUrl === "string" ? previewImageUrl.trim() : "";
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
