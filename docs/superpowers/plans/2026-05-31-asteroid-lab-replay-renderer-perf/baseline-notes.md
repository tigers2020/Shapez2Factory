# Renderer Perf — Recorded Baseline Numbers (LOCK-1)

**Required deliverable of PR-RENDER-0.** RENDER-0 cannot be marked done while any field below is empty.
Capture procedure: [`perf-baseline.md`](perf-baseline.md) § Chrome DevTools capture procedure.

> These are observability measurements only (FD-1). Do not feed any value here into solver / replay
> algorithm inputs.

Fill one block per measured run. Keep blocks append-only (one per PR milestone), so RENDER-1..5 deltas
stay comparable against RENDER-0.

---

## Template (copy per run)

```markdown
### Run <N> — <milestone, e.g. RENDER-0 baseline>
- date / commit:
- browser / machine:
- replay slug/run:
- frame count:
- decoded payload size (bytes):
- rAF median (ms):
- rAF p95 (ms):
- forced reflow count (per play-through):
- total DOM node count (#lab-replay-grid subtree):
- full reset count (per play-through):
- changed/touched cell count (median per frame):
- capture (trace path / screenshot):
- notes:
```

---

## RENDER-0 baseline (recorded 2026-05-31)

### Run 1 — RENDER-0 baseline (reference map, 88 frames)
- date / commit: 2026-05-31 / `f0fd9800`
- browser / machine: Playwright Chromium (headless hook) / Windows dev host
- replay slug/run: `rttp-core-recovery-test-map` / run **300** (88 frames; run 297 same payload class)
- frame count: **88**
- decoded payload size (bytes): **15_807_363** (UTF-8 JSON from `GET …/solver-runs/300/lab-replay/`; `lab_perf.jsonl` `payload_bytes` **14_191_884** for run 297 `lab_replay_get`)
- rAF median (ms): **50.4** (handler samples with duration >1 ms during one full play-through)
- rAF p95 (ms): **64.0** (same capture; max **69.7** ms; **136** ticks >32 ms)
- forced reflow count (per play-through): **not counted** (pre-`data-lab-perf-debug`; static audit: `getBoundingClientRect` + `offsetWidth` in paint path — expect >0 until RENDER-2)
- total DOM node count (#lab-replay-grid subtree): **4113** (`querySelectorAll('*')` after replay mount)
- full reset count (per play-through): **not instrumented** (RENDER-1 adds counter; keyframe + ≥15% threshold path active in `replayFrameNeedsFullGridReset`)
- changed/touched cell count (median per frame): **not instrumented** (RENDER-1); overlay-heavy frames repaint large cell sets per `renderFullMapCells`
- capture (trace path / screenshot): Playwright `browser_evaluate` rAF wrapper on `http://127.0.0.1:8000` lab page, run 300 loaded via `replaceLabReplayPayload`, single play-through
- notes: Budget violation expected (p95 ≫ 16.7 ms). Median uses paint samples >1 ms only (idle scheduling ticks excluded). Re-run with Chrome Performance panel optional for forced-reflow count before RENDER-2.

### Run 2 — RENDER-0 baseline (small map, 24 frames)
- date / commit: 2026-05-31 / `f0fd9800`
- browser / machine: Playwright Chromium (headless hook) / Windows dev host
- replay slug/run: `rttp-core-recovery-test-map` / run **250** (24 frames; local substitute for `copy-import-*` fixture — slug not present in dev DB)
- frame count: **24**
- decoded payload size (bytes): **4_775_659** (UTF-8 JSON from `GET …/solver-runs/250/lab-replay/`; `lab_perf.jsonl` reference for `copy-import-a9a62960` run 2: **72_781** `payload_bytes`, 27 frames)
- rAF median (ms): **19.6** (handler samples >1 ms, one play-through)
- rAF p95 (ms): **42.1** (max **43.3** ms; **4** ticks >32 ms)
- forced reflow count (per play-through): **not counted** (same as Run 1)
- total DOM node count (#lab-replay-grid subtree): **2701**
- full reset count (per play-through): **not instrumented**
- changed/touched cell count (median per frame): **not instrumented**
- capture (trace path / screenshot): same Playwright procedure as Run 1
- notes: Smaller frame count still exceeds 16.7 ms p95 on heavy DOM path. Server-side small-map oracle: `var/log/asteroid_lab_perf/lab_perf.jsonl` `copy-import-a9a62960` `lab_replay_get` line (2026-05-29).

---

## Post-PR milestone blocks (append as each PR lands)

### Run 3 — RENDER-1 token-diff (reference map, 88 frames)
- date / commit: 2026-05-31 / working tree post-RENDER-1
- browser / machine: Playwright Chromium + `data-lab-perf-debug="1"` / Windows dev host
- replay slug/run: `rttp-core-recovery-test-map` / run **300**
- frame count: **88**
- decoded payload size (bytes): **15_807_363** (unchanged)
- rAF median (ms): _(not re-measured this PR; RENDER-3 owns timing claim)_
- rAF p95 (ms): _(not re-measured)_
- forced reflow count (per play-through): _(not re-measured)_
- total DOM node count (#lab-replay-grid subtree): **4113** (unchanged)
- full reset count (per play-through): **not instrumented**
- changed/touched cell count (median per frame): **~563** (`[lab-perf] touched_cells` during one play-through; steady segment frames 38–82 ≈563–578; spikes at keyframes e.g. frame 28 **964**, frame 87 **1030**)
- capture (trace path / screenshot): Playwright console hook on full play-through after `replaceLabReplayPayload`
- notes: LOCK-2 **partial (Run 3)** — token skip in `renderFullMapCells` active; incremental reset still cleared tokens before paint (~563 touches). **Follow-up (post-RENDER-5):** `resetDomCellsAtIndicesForFrame` skips reset when incoming token matches `renderedTokenByKey` — re-measure with `data-lab-perf-debug` play-through (Run 8).

### Run 4 — RENDER-2 layout cache (reference map)
- date / commit: 2026-05-31 / working tree post-RENDER-2
- browser / machine: static + unit tests (DevTools forced-reflow recount optional)
- replay slug/run: `rttp-core-recovery-test-map` / run **300**
- frame count: **88**
- decoded payload size (bytes): _(unchanged)_
- rAF median (ms): _(not re-measured)_
- rAF p95 (ms): _(not re-measured)_
- forced reflow count (per play-through): **expected 0 in steady playback** (`applyFrame` no longer reads `offsetWidth`/`getBoundingClientRect`; reads only in `refreshLabLayoutCache` on resize/zoom/pointer-down)
- total DOM node count (#lab-replay-grid subtree): **4113** (unchanged)
- full reset count (per play-through): **not instrumented**
- changed/touched cell count (median per frame): _(see Run 3; unchanged this PR)_
- capture (trace path / screenshot): `test_lab_renderer_layout_cache.py` green
- notes: Re-verify forced-reflow count in Chrome Performance after deploy; pan/zoom uses cached viewport rect.

### Run 5 — RENDER-4 canvas terrain (reference map)
- date / commit: 2026-05-31 / working tree post-RENDER-4
- browser / machine: unit + integration tests (DOM paint cut DevTools optional)
- replay slug/run: `rttp-core-recovery-test-map` / run **300**
- frame count: **88**
- decoded payload size (bytes): _(unchanged)_
- rAF median (ms): _(not re-measured)_
- rAF p95 (ms): _(not re-measured)_
- forced reflow count (per play-through): _(see Run 4)_
- total DOM node count (#lab-replay-grid subtree): **4113** (unchanged; terrain on canvas)
- full reset count (per play-through): **not instrumented**
- changed/touched cell count (median per frame): **expected drop for static field kinds** (`asteroid_*_field`, `internal_void` skip DOM tone; see Run 3 ~563)
- capture (trace path / screenshot): `test_lab_canvas_terrain.py` + template `#lab-replay-terrain-canvas`
- notes: `data-lab-terrain-canvas="0"` forces DOM-only path. Overlay/sprites still DOM until RENDER-5.

### Run 6 — RENDER-5 canvas overlay + sprite (final hybrid)
- date / commit: 2026-05-31 / working tree post-RENDER-5
- browser / machine: unit + integration contracts (DevTools rAF/touched recount optional)
- replay slug/run: `rttp-core-recovery-test-map` / run **300**
- frame count: **88**
- decoded payload size (bytes): _(unchanged ~15.8MB from Run 1)_
- rAF median (ms): _(not re-measured; recount after manual play-through)_
- rAF p95 (ms): _(not re-measured)_
- forced reflow count (per play-through): _(see Run 4)_
- total DOM node count (#lab-replay-grid subtree): **4113** (grid = hit layer only under `data-lab-renderer="canvas"`)
- full reset count (per play-through): **not instrumented**
- changed/touched cell count (median per frame): **expected large drop** (paint on overlay/sprite canvas; DOM hit layer class-only)
- capture (trace path / screenshot): `test_lab_canvas_renderer.py` + `#lab-replay-overlay-canvas` / `#lab-replay-sprite-canvas`
- notes: Rim/pattern highlights remain SVG via `applyLabOverlayHighlights`. `data-lab-renderer="dom"` restores full DOM paint path. **LOCK-3 (RENDER-6):** payload size unchanged; defer compact frames unless post-deploy profiling shows parse/hydrate still dominant.

### Run 7 — post-RENDER-5 verification (2026-05-31)
- date / commit: 2026-05-31 / working tree + runtime fixes (TDZ, `let layout`, canvas-mode on each canvas frame)
- browser / machine: Playwright Chromium / Windows dev host (`rttp-core-recovery-test-map` project page)
- replay slug/run: `rttp-core-recovery-test-map` / run **300** loaded on page (38 frames on project default run; run 300 payload used in prior Run 1–3)
- frame count: **88** (run 300 oracle; project UI may show fewer frames until run selected)
- decoded payload size (bytes): _(unchanged ~15.8MB for run 300)_
- rAF median (ms): _(Run 1 paint-path **50.4** still authoritative until Chrome Performance re-run on canvas path)_
- rAF p95 (ms): _(Run 1 **64.0**; post-canvas play-through recount **deferred** — use same Playwright handler-duration wrapper as Run 1)_
- forced reflow count (per play-through): _(not re-counted)_
- total DOM node count (#lab-replay-grid subtree): **4113** (unchanged)
- full reset count (per play-through): **not instrumented**
- changed/touched cell count (median per frame): canvas path — DOM class-only hit layer; `[lab-perf] touched_cells` only when `#lab-root` has `data-lab-perf-debug="1"` (not in template by default)
- capture (trace path / screenshot): Playwright 2026-05-31 — no `pageerror`; terrain/overlay/sprite canvas pixels present; scrub/playback/inspector OK; **LOCK-2 still partial** for DOM path (Run 3)
- notes: **Functional sign-off** for RENDER-5 hybrid. **Budget sign-off** still open: rAF ≤16.7ms p95 and LOCK-2 unchanged-frame 0-touch not proven. Optional follow-up PR: preserve `renderedTokenByKey` across incremental reset; Run 8 = Chrome Performance on canvas + `data-lab-perf-debug` play-through.

### Run 8 — post-LOCK-2 + canvas verification (2026-05-31)
- date / commit: 2026-05-31 / working tree (`resetDomCellsAtIndicesForFrame`, hit-layer perf counter)
- browser / machine: Playwright Chromium / Windows dev host
- replay slug/run: `rttp-core-recovery-test-map` — **lazy replay compose failed** on project page (`Replay: failed to load`); run **300** JSON endpoint OK but not wired via `replaceLabReplayPayload` shape
- frame count: project UI scrub max **37** when loaded; run **300** oracle **88** (Run 1)
- decoded payload size (bytes): _(unchanged)_
- rAF median (ms): _(not re-measured — use Run 1 **50.4** until lazy replay loads for automated play-through)_
- rAF p95 (ms): _(Run 1 **64.0** pre-canvas DOM path; post-canvas play-through recount **blocked** on lazy load failure)_
- forced reflow count (per play-through): _(not re-counted)_
- total DOM node count (#lab-replay-grid subtree): **2961** (project page, smaller map than Run 1 **4113**)
- full reset count (per play-through): **not instrumented**
- changed/touched cell count (median per frame): **automated capture 0 samples** — `data-lab-perf-debug` set in-page; `applyFrame` not exercised (replay load error). **Expected canvas path:** overlay/sprite off-DOM; hit-layer `className` only (counter added in `applyLabCanvasHitLayer`). **DOM path (Run 3):** ~563 before `resetDomCellsAtIndicesForFrame`.
- capture (trace path / screenshot): Playwright SDD Run 8 attempt; `renderReplayFrame` hook probe shows `canvasMode: true` when replay mounted
- notes: **Do not mark LOCK-2 or rAF budgets green from Run 8.** Operator recount when lazy replay green: `#lab-root[data-lab-perf-debug="1"]` + play run 300 + compare `[lab-perf] touched_cells` to Run 3. Compare rAF to Run 1 on same fixture.

### Run 9 — post-RENDER-5 budget recount (run 300, canvas path, 2026-05-31)
- date / commit: 2026-05-31 / working tree post-Run 8c + `mountLabCanvasRenderer` on `replaceLabReplayPayload`
- browser / machine: Playwright Chromium / Windows dev host
- replay slug/run: `rttp-core-recovery-test-map` / run **300** (88 frames)
- frame count: **88**
- decoded payload size (bytes): **15_807_363** (unchanged)
- rAF median (ms): **11.1** (handler wrapper, samples >1 ms)
- rAF p95 (ms): **13.8** (max **14.7**; **0** ticks >32 ms) — **meets ≤16.7 ms budget** vs Run 1 **64.0**
- forced reflow count (per play-through): **not counted** (RENDER-2 static path; DevTools optional)
- total DOM node count (#lab-replay-grid subtree): **2961** (canvas hit layer; Run 1 DOM paint **4113**)
- full reset count (per play-through): **not instrumented**
- changed/touched cell count (median per frame): **2961** (`[lab-perf] touched_cells`; canvas hit-layer applies to full grid on non-incremental frames — not comparable to Run 3 DOM **~574** token-diff path)
- capture (trace path / screenshot): Playwright `replaceLabReplayPayload` + `data-lab-perf-debug="1"` + full play-through; `lab-replay-grid--canvas-mode` **true**
- notes: **rAF budget sign-off (Playwright oracle).** LOCK-2 unchanged-frame 0-touch **not proven** on canvas hit-layer counter (full-grid class apply on resets). Run 8 (failed lazy) superseded for timing claims.

### Run 8c — lazy + canvas regression fixes (2026-05-31)
- date / commit: 2026-05-31 / restore `bc5071e2` canvas wiring + lazy prefetch; `tone` ReferenceError fix; `mountLabCanvasRenderer()` after lazy `applyLoadedLabReplayPayload`
- browser / machine: Playwright Chromium / `rttp-core-recovery-test-map`
- replay slug/run: run **398** / **38** frames
- notes: Root cause of Run 8 `failed to load`: `renderFullMapCells` used undefined `tone` after token-diff refactor (threw on prefetch `applyFrame`). Lazy load OK after fix; canvas mode active after lazy hydrate. Automated `lab-frame` measures during 5s play: ~2–10 ms/sample (not full 88-frame p95 oracle).

### Run 8b — lazy replay follow-up (2026-05-31)
- date / commit: 2026-05-31 / `scheduleLazyReplayPrefetch`, load-status retry, console error on lazy fetch failure
- browser / machine: Playwright Chromium / Windows dev host (`rttp-core-recovery-test-map`)
- replay slug/run: `rttp-core-recovery-test-map` / run **398** (`fetch_url` …/solver-runs/398/lab-replay/, **38** frames, ~6.1MB JSON)
- frame count: **38** after prefetch or play (init stays preview-only until idle prefetch completes)
- notes: Run 8 `failed to load` was **not** a broken compose endpoint (GET 200 + `frames[]`). SSR preview uses `map_view` so `needsLazyReplayComposeFetch()` is false on init; full timeline loads on play/scrub/prefetch. Automated Run 8 should wait for `Replay: loaded N frames` or allow ≥10s after play. `replaceLabReplayPayload` expects POST solver JSON shape, not raw lab-replay GET body.

> Add a `### Run <N> — RENDER-<k>` block after each PR so deltas are recorded. RENDER-6's LOCK-3 start
> gate is decided from the post-RENDER-5 block here (payload still >5MB compressed / >15MB decoded, or
> parse/hydrate still dominant, or duplication proven by byte accounting).
