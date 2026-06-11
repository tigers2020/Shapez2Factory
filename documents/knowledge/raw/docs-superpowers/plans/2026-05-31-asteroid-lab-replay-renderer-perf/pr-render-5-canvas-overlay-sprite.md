# PR-RENDER-5 — Canvas Overlay + Sprite Layer (Final Hybrid)

**Type:** UI change · implementation change · refactoring
**Depends on:** PR-RENDER-4
**Enables:** — (final renderer)
**Branch (suggested):** `feat/lab-renderer-canvas-final`

---

## Goal

Move the dynamic replay (overlay + sprites) onto canvas layers, leaving the DOM responsible only for
controls, inspector/tooltip, and HUD. This is the final Canvas-2D hybrid renderer; a div-per-cell grid is
no longer the paint surface.

## Behavior contract

- Replay frames are drawn on `overlayCanvas` + `spriteCanvas`; terrain on `terrainCanvas` (RENDER-4).
- DOM under `#lab-replay-grid` no longer paints per cell; cell inspector uses `hitTest(wx, wy)`.
- `window.AsteroidLabReplay` hooks keep their names but delegate to the canvas renderer (FD-3 boundary:
  this is the explicit PR allowed to replace them).
- Visual parity with the DOM renderer for all frame kinds (full_map, overlay, decode, diff, bundles, rim).

## Non-goals

- WebGL (defer until Canvas 2D proven insufficient — sprite count / zoom-pan heavy).
- Backend data-shape change (RENDER-6).

---

## File map

| Action | Path | Why |
|--------|------|-----|
| Create | `django_apps/web/static/web/js/lab_replay_canvas_renderer.js` | `createLabCanvasRenderer` (overlay + sprite + hitTest) |
| Modify | [`asteroid_miner_layout_solver.html`](../../../../django_apps/web/templates/web/asteroid_miner_layout_solver.html) | add `#lab-replay-overlay-canvas`, `#lab-replay-sprite-canvas` |
| Modify | [`asteroid_miner_layout_lab.js`](../../../../django_apps/web/static/web/js/asteroid_miner_layout_lab.js) | wire `applyFrame` → renderer; delegate `window.AsteroidLabReplay`; inspector via hitTest |
| Create | `tests/unit/asteroid_lab/test_lab_canvas_renderer.py` | module contract + delegation |
| Modify | `tests/integration/web/test_asteroid_lab_replay_timeline_smoke.py` | canvas renderer smoke |

---

## New module sketch (`lab_replay_canvas_renderer.js`)

```javascript
export function createLabCanvasRenderer({ terrainCanvas, overlayCanvas, spriteCanvas, layout, spriteBaseUrl }) {
  const overlayCtx = overlayCanvas.getContext("2d");
  const spriteCtx = spriteCanvas.getContext("2d");
  const imgCache = new Map(); // rel -> HTMLImageElement

  function drawFrame(frame, trackMetrics, rimDrawCtx) {
    overlayCtx.clearRect(0, 0, overlayCanvas.width, overlayCanvas.height);
    spriteCtx.clearRect(0, 0, spriteCanvas.width, spriteCanvas.height);
    for (const cell of overlayCellsOf(frame)) drawOverlayCell(overlayCtx, cell, layout);
    for (const cell of spriteCellsOf(frame)) drawSpriteCell(spriteCtx, imgCache, cell, layout, spriteBaseUrl);
    // rim / pattern highlights: stroke on overlayCtx OR keep existing SVG layer above canvas
  }

  function hitTest(wx, wy) {
    return cellIndexFromWorldPoint(wx, wy, layout); // island-local; no x==0
  }

  return { drawFrame, hitTest, destroy() { imgCache.clear(); } };
}
```

Wiring in `asteroid_miner_layout_lab.js`:

```javascript
if (rootEl?.dataset.labRenderer === "canvas" && canvasSupported()) {
  labRenderer = createLabCanvasRenderer({ ... });
  // applyFrame → labRenderer.drawFrame(fr, replayTrackMetrics, getLabRimDrawCtx())
  // inspector pointer handler → labRenderer.hitTest(wx, wy)
}
window.AsteroidLabReplay = {
  // keep names; delegate
  renderReplayFrame: (fr) => labRenderer ? labRenderer.drawFrame(fr, replayTrackMetrics, getLabRimDrawCtx())
                                         : /* legacy DOM path */,
  // ...
};
```

---

## Migration steps

1. Add overlay + sprite canvases to the template; size with terrain (HiDPI-aware).
2. `createLabCanvasRenderer` with `drawFrame` (overlay + sprite) + `hitTest`.
3. Port `applyLabCellSprite` → `drawSpriteCell(ctx, imgCache, cell)` (image cache keyed by rel path;
   rotation via `ctx.rotate`, matching the East-facing R-only contract, L48–53).
4. Port rim/pattern SVG highlights → canvas stroke, OR retain the existing SVG overlay positioned above
   the canvas (lower-risk; choose and document).
5. Inspector: pointer → world point → `hitTest` → existing cell-detail flow.
6. Shrink `window.AsteroidLabReplay` to delegate; keep method names so regression tests pass (FD-3/FD-4).

---

## Tasks

- [ ] **Step 1 — Template:** add overlay + sprite canvases.
- [ ] **Step 2 (SDD) — `test_lab_canvas_renderer.py`.**

```python
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
JS_DIR = REPO / "django_apps" / "web" / "static" / "web" / "js"
LAB = JS_DIR / "asteroid_miner_layout_lab.js"


def test_canvas_renderer_module_contract() -> None:
    src = (JS_DIR / "lab_replay_canvas_renderer.js").read_text(encoding="utf-8")
    assert "createLabCanvasRenderer" in src
    assert "drawFrame" in src
    assert "hitTest" in src


def test_lab_replay_hooks_preserved() -> None:
    src = LAB.read_text(encoding="utf-8")
    # FD-3: hook names preserved even after delegation
    assert "window.AsteroidLabReplay" in src
    assert "renderReplayFrame:" in src
```

- [ ] **Step 3 — `createLabCanvasRenderer`** drawFrame (overlay + sprite) + sprite image cache.
- [ ] **Step 4 — Rim/pattern highlights** (canvas stroke or retained SVG overlay).
- [ ] **Step 5 — Inspector hitTest** wired to pointer handler.
- [ ] **Step 6 — Delegate `window.AsteroidLabReplay`** (names preserved).
- [ ] **Step 7 — Visual parity check** across frame kinds; append `Run <N> — RENDER-5` block to
  `baseline-notes.md` (this block feeds the RENDER-6 LOCK-3 decision).
- [ ] **Step 8 — Verify + lint.**

---

## Tests / verification

```powershell
python -m pytest tests/unit/asteroid_lab/test_lab_canvas_renderer.py -v
python -m pytest tests/integration/web/test_asteroid_lab_replay_timeline_smoke.py tests/integration/web/test_asteroid_miner_layout_solver.py -v
python -m ruff check tests/unit/asteroid_lab
```

## Risks

- `invariant:` visual parity for every frame kind — keep DOM renderer behind the flag until parity proven.
- `invariant:` sprite filename + rotation rules unchanged (FD; align with Python sprite key rules).
- `uncertain:` rim/pattern SVG → canvas port is the highest-risk piece; SVG-overlay-above-canvas is the safe fallback.
- `uncertain:` hit-test precision under zoom/pan; reuse `labWorldPointFromClient`.

## Done criteria

- Replay drawn on canvas; DOM limited to controls/inspector/HUD; hooks delegated (names kept); visual
  parity confirmed; tests green; RENDER-5 baseline block recorded (used for RENDER-6 LOCK-3 gate).
