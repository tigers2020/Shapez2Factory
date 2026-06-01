# PR-RENDER-3 — Playback rAF Budget + DOM Churn Reduction (P3 partial)

**Type:** UI change · implementation change
**Depends on:** PR-RENDER-1 (parallelizable with PR-RENDER-2)
**Enables:** —
**Branch (suggested):** `feat/lab-renderer-raf-budget`

---

## Goal

Keep steady playback within one frame budget on the reference map. Remove the remaining per-frame DOM churn
(bundle-bridge create/remove, demo full-grid loop, per-frame chrome sync) and confirm rAF runs only while
playing (Guard R5, R6).

## Behavior contract

- 88-frame RTTP play-through has **no sustained** `[Violation] requestAnimationFrame handler took >32ms`.
- Bundle-bridge DOM elements are pooled/reused — **0** create/remove per frame in steady playback.
- Demo-matrix mode updates changed cells only (no full `domCells` loop per frame).
- rAF does not run while paused (already true; keep green).

## Non-goals

- No canvas (RENDER-4/5).
- No data-shape change (RENDER-6).

---

## Current code

- Bundle bridges: `applyEquipmentBundleGroupVisualsFromOverlay` → `document.createElement("div")` +
  `el.appendChild(br)` per link, `clearLabCellBundleBridges` removes them — L1395–1463.
- Demo matrix full loop: `applyFrame` non-replay branch iterates **all** `domCells` — L2686–2690.
- Chrome decimation: `playbackChromeTick++ % 2` — L2616; `syncLabTimelineScrub` called each chrome tick.
- `LAB_REPLAY_PLAYBACK_MS = 220` — L114; `gridStage.style.transform` uses `translate(...)` — L2251.

---

## File map

| Action | Path | Why |
|--------|------|-----|
| Modify | [`asteroid_miner_layout_lab.js`](../../../../django_apps/web/static/web/js/asteroid_miner_layout_lab.js) | bridge pooling; demo diff; chrome tuning; translate3d; perf marks |
| Create | `tests/unit/asteroid_lab/test_lab_renderer_raf_budget.py` | source contracts (pooling, demo diff, perf marks) |

---

## Implementation sketch

Bundle-bridge pooling:

```javascript
// reuse a fixed set of bridge elements per cell instead of create/remove every frame
function ensureBundleBridge(el, suffix) {
  let br = el.querySelector('[data-lab-bundle-bridge="' + suffix + '"]');
  if (!br) {
    br = document.createElement("div");
    br.setAttribute("data-lab-bundle-bridge", suffix);
    br.setAttribute("aria-hidden", "true");
    el.appendChild(br);
  }
  return br;
}
// hide unused bridges (display:none) instead of removing nodes
```

Demo-matrix diff (mirror token-diff from RENDER-1):

```javascript
// non-replay branch: only write cells whose matrix row class changed
for (let i = 0; i < domCells.length; i++) {
  const row = matrix[i];
  const next = row && row[oi];
  if (next && demoRenderedClass[i] !== next) {
    domCells[i].className = next;
    demoRenderedClass[i] = next;
  }
}
```

Chrome tuning + transform:

```javascript
gridStage.style.transform = "translate3d(" + tx + "px," + ty + "px,0) scale(" + zoom + ")";
// skip syncLabTimelineScrub on non-chrome ticks during playback
```

Optional perf marks (behind `data-lab-perf-debug`):

```javascript
if (labPerfDebugEnabled()) performance.mark("lab-frame-start");
// ... paint ...
if (labPerfDebugEnabled()) {
  performance.mark("lab-frame-end");
  performance.measure("lab-frame", "lab-frame-start", "lab-frame-end");
}
```

---

## Tasks

- [ ] **Step 1 (SDD) — `test_lab_renderer_raf_budget.py`.**

```python
from pathlib import Path

REPO = Path(__file__).resolve().parents[3]
JS = REPO / "django_apps" / "web" / "static" / "web" / "js" / "asteroid_miner_layout_lab.js"


def test_bundle_bridge_is_pooled_not_recreated() -> None:
    src = JS.read_text(encoding="utf-8")
    assert "function ensureBundleBridge(" in src


def test_demo_matrix_uses_diff() -> None:
    src = JS.read_text(encoding="utf-8")
    assert "demoRenderedClass" in src


def test_grid_stage_uses_translate3d() -> None:
    src = JS.read_text(encoding="utf-8")
    assert "translate3d(" in src


def test_perf_marks_behind_debug_flag() -> None:
    src = JS.read_text(encoding="utf-8")
    assert "performance.measure(" in src
    assert "labPerfDebugEnabled(" in src
```

Run: `python -m pytest tests/unit/asteroid_lab/test_lab_renderer_raf_budget.py -v`
Expected: FAIL.

- [ ] **Step 2 — Bundle-bridge pooling** (`ensureBundleBridge`; hide unused instead of remove).
- [ ] **Step 3 — Demo-matrix diff** (`demoRenderedClass` array; write changed rows only).
- [ ] **Step 4 — Chrome tuning** (skip `syncLabTimelineScrub` on non-chrome ticks) + `translate3d`.
- [ ] **Step 5 — Optional perf marks** behind `data-lab-perf-debug`.
- [ ] **Step 6 — Budget gate** (DevTools): 88-frame play-through, no sustained >32ms violation; append
  `Run <N> — RENDER-3` block to `baseline-notes.md` with rAF p95.
- [ ] **Step 7 — Verify + lint.**

---

## Budget gate (manual until Playwright perf lands)

88-frame RTTP replay play-through — no `[Violation] requestAnimationFrame handler took >32ms` sustained;
rAF p95 ≤ 16.7ms (DOM path target). Record numbers in `baseline-notes.md`.

## Tests / verification

```powershell
python -m pytest tests/unit/asteroid_lab/test_lab_renderer_raf_budget.py -v
python -m pytest tests/integration/web/test_asteroid_lab_replay_timeline_smoke.py -v
python -m ruff check tests/unit/asteroid_lab
```

## Risks

- `uncertain:` `translate3d` may change sub-pixel snapping vs `translate`; verify `snapToDevicePixel` still applies.
- `invariant:` pooled bridges must clear stale color/state when hidden (no ghost bridges).

## Done criteria

- Budget gate met (no sustained >32ms; p95 recorded); pooling + demo-diff + translate3d tests green;
  Guard R5/R6 green; RENDER-3 baseline block recorded.
