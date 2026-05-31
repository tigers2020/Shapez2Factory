# PR-RENDER-4 — Canvas Static Terrain Layer

**Type:** UI change · implementation change
**Depends on:** PR-RENDER-2
**Enables:** PR-RENDER-5
**Branch (suggested):** `feat/lab-renderer-canvas-terrain`

---

## Goal

Draw the static terrain / base grid once on a canvas so replay frames stop repainting static cells on the
DOM. This is the first canvas-hybrid step; the DOM grid stays for hit-testing and as a fallback.

## Behavior contract

- Terrain is drawn on a `<canvas>` once at surface init and on keyframe layout change.
- Replay frames no longer repaint static (unchanged terrain) cells on the DOM.
- Cell inspector still works (DOM cells become transparent hit targets above the canvas).
- If canvas is unsupported, the existing DOM path is used (feature flag), with identical visuals.

## Non-goals

- Dynamic overlay / sprite on canvas (RENDER-5).
- Removing `window.AsteroidLabReplay` hooks (RENDER-5).

---

## File map

| Action | Path | Why |
|--------|------|-----|
| Modify | [`asteroid_miner_layout_solver.html`](../../../../django_apps/web/templates/web/asteroid_miner_layout_solver.html) | add `#lab-replay-terrain-canvas` under `#lab-replay-grid-stage` (before `#lab-replay-grid`) |
| Create | `django_apps/web/static/web/js/lab_replay_canvas_terrain.js` | `drawTerrainLayer(ctx, cells, layout, cellPx, gapPx)` |
| Modify | [`asteroid_miner_layout_lab.js`](../../../../django_apps/web/static/web/js/asteroid_miner_layout_lab.js) | mount terrain canvas; mark DOM terrain cells transparent; feature flag |
| Create | `tests/unit/asteroid_lab/test_lab_canvas_terrain.py` | static export + module contract |
| Modify | `tests/integration/web/test_asteroid_miner_layout_solver.py` | assert canvas element present when replay loaded |

---

## Template change

```html
<div id="lab-replay-grid-stage" class="min-w-0">
  <canvas id="lab-replay-terrain-canvas" aria-hidden="true"></canvas>
  <div id="lab-replay-grid" ...><!-- now hit targets / fallback --></div>
</div>
```

Canvas sits behind the DOM grid (z-order), sized to the stage; DOM grid above it for pointer/inspector.

## New module sketch (`lab_replay_canvas_terrain.js`)

```javascript
export function drawTerrainLayer(ctx, cells, layout, cellPx, gapPx) {
  ctx.clearRect(0, 0, ctx.canvas.width, ctx.canvas.height);
  for (const cell of cells) {
    const col = /* resolve via layout (island-local x/y, no x==0) */;
    const row = /* ... */;
    const x = col * (cellPx + gapPx);
    const y = row * (cellPx + gapPx);
    ctx.fillStyle = terrainFillForCell(cell);
    ctx.fillRect(x, y, cellPx, cellPx);
  }
}
```

> Module is ES-module style to match RENDER-5; if the page does not load modules, expose via a global
> namespace `window.LabReplayCanvas` instead. Decide consistently with RENDER-5.

---

## Tasks

- [ ] **Step 1 — Template:** add `#lab-replay-terrain-canvas` (Step verifies SSR includes it when replay
  is present).
- [ ] **Step 2 — `lab_replay_canvas_terrain.js`** `drawTerrainLayer` (island-local coord mapping, FD-2).
- [ ] **Step 3 — Mount + draw** terrain on surface init / keyframe; mark DOM terrain cells transparent
  (keep them as hit targets).
- [ ] **Step 4 — Feature flag** `data-lab-renderer` (`dom` default until RENDER-5 flips to `canvas`); canvas
  unsupported → DOM path.
- [ ] **Step 5 (TDD) — `test_lab_canvas_terrain.py`.**

```python
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
JS_DIR = REPO / "django_apps" / "web" / "static" / "web" / "js"
TPL = REPO / "django_apps" / "web" / "templates" / "web" / "asteroid_miner_layout_solver.html"


def test_terrain_module_exports_draw() -> None:
    src = (JS_DIR / "lab_replay_canvas_terrain.js").read_text(encoding="utf-8")
    assert "drawTerrainLayer" in src


def test_template_has_terrain_canvas() -> None:
    tpl = TPL.read_text(encoding="utf-8")
    assert 'id="lab-replay-terrain-canvas"' in tpl
```

- [ ] **Step 6 — Integration smoke:** extend `test_asteroid_miner_layout_solver.py` to assert
  `lab-replay-terrain-canvas` present in rendered page when a replay run exists.
- [ ] **Step 7 — Verify static cell DOM paint cut**; append `Run <N> — RENDER-4` block to `baseline-notes.md`.
- [ ] **Step 8 — Verify + lint.**

---

## Tests / verification

```powershell
python -m pytest tests/unit/asteroid_lab/test_lab_canvas_terrain.py -v
python -m pytest tests/integration/web/test_asteroid_miner_layout_solver.py -v
python -m ruff check tests/unit/asteroid_lab
```

DevTools: confirm terrain cells no longer appear in per-frame DOM paint.

## Risks

- `uncertain:` canvas / DOM z-order + pointer hit-test alignment; keep DOM grid transparent on top.
- `invariant:` island-local coord mapping must match `resolveCellIndex` (no `x==0` column, FD-2).
- `uncertain:` HiDPI scaling — size canvas by `devicePixelRatio` to avoid blur.

## Done criteria

- Terrain on canvas; static cell DOM paint removed; inspector still works; fallback path intact; tests
  green; RENDER-4 baseline block recorded.
