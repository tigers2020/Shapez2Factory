# Renderer Perf — Master Execution Checklist

**Status:** PARTIAL — RENDER-0..6 complete; Run 9 rAF p95 **13.8 ms** (budget met); LOCK-2 touch oracle still partial (canvas hit-layer); no commit/PR without user request
**Scope:** Single source of execution truth across PR-RENDER-0 … PR-RENDER-6. Each PR's own file remains
the detailed contract; this file is the cross-PR progress tracker.
**Closing rule:** No commit / push / PR / merge / `CLOSED` without explicit user request ([`AGENTS.md`](../../../../AGENTS.md)).

Legend: `[ ]` not started · `[~]` in progress · `[x]` done · `[-]` skipped (document reason).

---

## 0. Frozen decisions (must hold in every PR)

- [x] FD-1 replay/metrics/artifact are not algorithm input
- [x] FD-2 island-local x/y only; no server_coords bridge; no `x == 0` column
- [x] FD-3 single replay timeline; `window.AsteroidLabReplay` hooks delegated at RENDER-5 (names preserved)
- [x] FD-4 no weakening of existing replay wiring smoke tests (integration shell green)
- [x] FD-5 perf work does not block CLI-first merge

## 1. Approval locks (cross-cutting; verified per touching PR)

- [x] LOCK-1 `baseline-notes.md` filled with recorded numbers (Runs 1–6)
- [x] LOCK-2 RENDER-1 DOM-touch measured (Run 3 DOM ~574; Run 9 canvas hit-layer ~2961 on resets — unchanged-frame 0-touch budget **not met**; optional follow-up: per-cell skip in `applyLabCanvasHitLayer`)
- [x] LOCK-3 RENDER-6 gate evaluated — **not triggered** (Run 6 notes)

## 2. Guards (rendering vs algorithm)

- [x] R1 no class/style change on unchanged-token cells (RENDER-1)
- [x] R2 no per-frame querySelector in paint path (RENDER-1/2)
- [x] R3 no innerHTML grid rebuild on frame change (RENDER-1 assert)
- [x] R4 no layout read mid-update (RENDER-2)
- [x] R5 rAF does not run while paused (RENDER-0 assert; RENDER-3)
- [x] R6 frame change touches changed cells only (RENDER-1/3; canvas path reduces DOM touch further)

---

## PR-RENDER-0 — Spec + perf baseline
Depends: — · File: [`pr-render-0-spec-and-baseline.md`](pr-render-0-spec-and-baseline.md)

- [x] Step 1 — write `perf-baseline.md` (budgets + DevTools capture procedure + lab_perf fields)
- [x] Step 2 — add Guard R1–R6 + LOCK-1..3 to README (done at folder creation)
- [x] Step 3 — `test_lab_playback_stops_raf_on_pause` (R5 static contract)
- [x] Step 4 — `test_lab_renderer_perf_debug_flag` skeleton (asserts debug-flag hook name reserved)
- [x] Step 5 (LOCK-1) — run baselines; fill `baseline-notes.md` (RTTP 88-frame run 300 + small run 250)
- [x] Verify: `pytest tests/unit/asteroid_lab/test_lab_playback_stops_raf_on_pause.py -v` + ruff
- [x] Done: baseline numbers recorded (no empty fields); static contracts green

## PR-RENDER-1 — DOM token-diff paint
Depends: RENDER-0 · File: [`pr-render-1-dom-token-diff.md`](pr-render-1-dom-token-diff.md)

- [x] Step 1 (TDD) — `test_lab_renderer_token_diff.py` source contract (helper present, skip-on-equal)
- [x] Step 2 — `cellRenderToken` + `renderedTokenByKey` skip in `renderFullMapCells`
- [x] Step 3 — token-map invalidation on reset/remount/keyframe; `resetDomCellAtIndex` deletes token
- [x] Step 4 — sprite `img.src` write guarded by token change
- [x] Step 5 — touched-cell debug counter behind `data-lab-perf-debug`
- [x] Step 6 (LOCK-2) — verify DOM-touch on RTTP run 300; `baseline-notes.md` Run 3 (median ~563 touches/frame; LOCK-2 partial — reset clears tokens before paint)
- [x] Verify: token-diff unit + existing integration web tests green; ruff
- [x] Done: token-diff + perf-debug landed; LOCK-2 touch-count gate partially met (documented in Run 3 notes)

## PR-RENDER-2 — Layout read/write separation
Depends: RENDER-1 · File: [`pr-render-2-layout-read-write-split.md`](pr-render-2-layout-read-write-split.md)

- [x] Step 1 (TDD) — `test_lab_renderer_layout_cache.py` (no layout read in paint path)
- [x] Step 2 — `labLayoutCache` + `refreshLabLayoutCache` on resize/zoom/pointer-down
- [x] Step 3 — `offsetWidth`/`getBoundingClientRect` hoisted to `refreshLabLayoutCache` only
- [x] Step 4 — server-replay `applyFrame` read/write comment split (no geometry read in paint path)
- [x] Verify: units + integration green; ruff
- [x] Done: R4 static path clean; Run 4 in `baseline-notes.md` (DevTools forced-reflow recount optional)

## PR-RENDER-3 — Playback rAF budget + DOM churn reduction
Depends: RENDER-1 · File: [`pr-render-3-playback-raf-budget.md`](pr-render-3-playback-raf-budget.md)

- [x] Step 1 — `test_lab_renderer_raf_budget.py` + `performance.mark`/`measure` behind `data-lab-perf-debug`
- [x] Step 2 — bundle-bridge pooling (`ensureBundleBridge`; hide unused)
- [x] Step 3 — demo-matrix diff (`demoRenderedClass`)
- [x] Step 4 — chrome decimation; skip `syncLabTimelineScrub` on non-chrome playback ticks
- [x] Step 5 — `translate3d` on `gridStage`
- [x] Verify: units + integration green; ruff (DevTools 88-frame rAF p95 recount **optional**)
- [x] Done: static contracts landed; Run 1 pre-path p95 **64 ms**; Run 9 post-canvas p95 **13.8 ms** (Playwright oracle, budget met)

## PR-RENDER-4 — Canvas static terrain layer
Depends: RENDER-2 · File: [`pr-render-4-canvas-terrain-layer.md`](pr-render-4-canvas-terrain-layer.md)

- [x] Step 1 — template: add `#lab-replay-terrain-canvas` under `#lab-replay-grid-stage`
- [x] Step 2 — `lab_replay_canvas_terrain.js` `drawTerrainLayer`
- [x] Step 3 — terrain draws on surface init / keyframe; DOM terrain cells transparent
- [x] Step 4 — canvas-unsupported fallback (`data-lab-terrain-canvas="0"` or no module → DOM path)
- [x] Verify: `test_lab_canvas_terrain.py` + integration smoke; ruff
- [x] Done: terrain on canvas; static kinds skip DOM tone paint; inspector via transparent hit cells

## PR-RENDER-5 — Canvas overlay + sprite final hybrid
Depends: RENDER-4 · File: [`pr-render-5-canvas-overlay-sprite.md`](pr-render-5-canvas-overlay-sprite.md)

- [x] Step 1 — `lab_replay_canvas_renderer.js` (`createLabCanvasRenderer`)
- [x] Step 2 — `applyFrame` → `renderer.drawFrame` when `data-lab-renderer=canvas`
- [x] Step 3 — port sprite draw; rim/pattern via retained SVG (`applyLabOverlayHighlights`)
- [x] Step 4 — `hitTest` for inspector; `renderReplayFrame` delegates on `window.AsteroidLabReplay`
- [x] Verify: `test_lab_canvas_renderer.py` + shell z-order; ruff
- [x] Done: DOM hit layer + HUD; canvas paints overlay/sprites; Run 6 in `baseline-notes.md`

## PR-RENDER-6 — Replay frame compact adapter (OPTIONAL — gated)
Depends: RENDER-1..5 + LOCK-3 · File: [`pr-render-6-replay-frame-compact-optional.md`](pr-render-6-replay-frame-compact-optional.md)

- [x] Gate (LOCK-3) — **not triggered** (Run 6: payload unchanged; renderer path complete; see `baseline-notes.md`)
- [x] Step 1 — skipped (LOCK-3 not met)
- [x] Step 2 — skipped
- [x] Step 3 — skipped
- [x] Verify: N/A
- [x] Done: **closed not-triggered** — re-open only if post-deploy profiling shows parse/hydrate or compressed payload still dominant
