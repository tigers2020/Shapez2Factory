# PR-RENDER-2 — Layout Read/Write Separation (P2)

**Type:** UI change · implementation change
**Depends on:** PR-RENDER-1
**Enables:** PR-RENDER-4
**Branch (suggested):** `feat/lab-renderer-layout-split`

---

## Goal

Eliminate forced reflow during frame paint by separating layout **reads** from **writes**. The frame paint
path must not read layout geometry (`offsetWidth`, `getBoundingClientRect`) interleaved with style writes
(Guard R4).

## Behavior contract

- Steady playback produces **0** forced reflows (DevTools "Recalculate Layout" forced warnings excluded
  from initial mount).
- Layout geometry (cellPx, gapPx, stage rect) is read on resize/zoom only, cached, and reused by paint.
- Visual output unchanged; pan/zoom still correct.

## Non-goals

- No canvas (RENDER-4/5).
- No token-diff changes (RENDER-1 owns that).

---

## Current code (forced-reflow sources)

- `labViewportContentOffset` reads `gridViewport.getBoundingClientRect()` + `getComputedStyle` — L2190–2202
  (called from pointer handlers).
- `syncLabReplayStageSizeFromGrid` reads `gridEl.offsetWidth/offsetHeight` then writes
  `gridStage.style.width/height` — L2229–2239.
- Demo init reads `domCells[0].offsetWidth` inside a rAF — L2390–2396.
- `applyReplayGridSizing` reads `gridViewport.clientWidth/Height` — L2329–2336 (resize path, acceptable).

---

## File map

| Action | Path | Why |
|--------|------|-----|
| Modify | [`asteroid_miner_layout_lab.js`](../../../../django_apps/web/static/web/js/asteroid_miner_layout_lab.js) | introduce `labLayoutCache`; move reads to resize/zoom; split server-replay `applyFrame` |
| Create | `tests/unit/asteroid_lab/test_lab_renderer_layout_cache.py` | assert no layout read in paint path |

---

## Implementation sketch

```javascript
// resize/zoom-only cache
let labLayoutCache = { cellPx: 20, gapPx: 4, stageW: 0, stageH: 0, viewportRect: null };

function refreshLabLayoutCache() {
  // ONLY called from ResizeObserver / zoom-end / surface init — never per frame
  const vr = gridViewport ? gridViewport.getBoundingClientRect() : null;
  labLayoutCache = {
    cellPx: Math.max(4, Math.round(Number(replayFitBasePx))),
    gapPx: Math.max(0, Math.round(Number(replayFitBasePx) * 0.2)),
    stageW: gridEl ? gridEl.offsetWidth : 0,
    stageH: gridEl ? gridEl.offsetHeight : 0,
    viewportRect: vr,
  };
  if (gridStage && labLayoutCache.stageW > 0) {
    gridStage.style.width = labLayoutCache.stageW + "px";
    gridStage.style.height = labLayoutCache.stageH + "px";
  }
}

// pointer handler uses cached rect (refresh on scroll/resize, not per move)
function labViewportContentOffset(clientX, clientY) {
  const vr = labLayoutCache.viewportRect || (gridViewport && gridViewport.getBoundingClientRect());
  // ... compute from vr ...
}
```

Server-replay `applyFrame` split (read → compute → write):

```javascript
function applyServerReplayFrame(fr, playback) {
  // READ phase: pull cached layout only (no DOM geometry read here)
  const rimDrawCtx = getLabRimDrawCtx();        // uses labLayoutCache
  // COMPUTE phase: resolve indices + tokens (pure)
  const patches = computeFramePatches(fr);       // returns [{idx, className, sprite, hud}]
  // WRITE phase: apply class/style/sprite only
  for (const p of patches) writeCellPatch(domCells[p.idx], p);
}
```

> Keep the change minimal: the main requirement is that **no `offsetWidth`/`getBoundingClientRect` is read
> between style writes during playback**. If a full read/compute/write refactor is too large, the
> acceptance gate is still "0 forced reflows in steady playback" — achieve it by hoisting the reads.

---

## Tasks

- [ ] **Step 1 (TDD) — `test_lab_renderer_layout_cache.py`.**

```python
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
JS = REPO / "django_apps" / "web" / "static" / "web" / "js" / "asteroid_miner_layout_lab.js"


def test_layout_cache_present() -> None:
    src = JS.read_text(encoding="utf-8")
    assert "labLayoutCache" in src
    assert "function refreshLabLayoutCache(" in src


def test_apply_frame_does_not_read_offset_width() -> None:
    src = JS.read_text(encoding="utf-8")
    idx = src.find("function applyFrame(")
    assert idx >= 0
    end = src.find("function setPlaying(", idx)
    body = src[idx:end] if end > idx else src[idx : idx + 4000]
    assert "offsetWidth" not in body
    assert "getBoundingClientRect" not in body
```

Run: `python -m pytest tests/unit/asteroid_lab/test_lab_renderer_layout_cache.py -v`
Expected: FAIL (cache not present; `applyFrame` may transitively read).

- [ ] **Step 2 — Introduce `labLayoutCache` + `refreshLabLayoutCache`**, called from ResizeObserver /
  zoom-end / surface init only.
- [ ] **Step 3 — Move `offsetWidth` / `getBoundingClientRect` reads** out of the per-frame path; pointer
  handlers use cached rect (refresh on scroll/resize).
- [ ] **Step 4 — Split server-replay `applyFrame`** into read → compute → write (or hoist reads if minimal).
- [ ] **Step 5 — Verify forced reflow == 0** in steady playback (DevTools); append `Run <N> — RENDER-2`
  block to `baseline-notes.md`.
- [ ] **Step 6 — Verify + lint.**

---

## Tests / verification

```powershell
python -m pytest tests/unit/asteroid_lab/test_lab_renderer_layout_cache.py -v
python -m pytest tests/integration/web/test_asteroid_miner_layout_solver.py -v
python -m ruff check tests/unit/asteroid_lab
```

DevTools: record steady playback; confirm 0 forced-reflow warnings (Guard R4).

## Risks

- `uncertain:` cached viewport rect can go stale on scroll; refresh on scroll/resize events, not per move.
- `invariant:` pan/zoom math must stay correct (FD-2 coords) — diff against current behavior.

## Done criteria

- Guard R4 green (0 forced reflows in steady playback); layout-cache test green; pan/zoom unchanged;
  RENDER-2 baseline block recorded.
