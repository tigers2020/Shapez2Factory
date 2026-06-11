# Asteroid Lab Replay Renderer Performance — Per-PR Plan Set

**Status:** APPROVED FOR DOCUMENTATION EXECUTION (Planning Lead, 2026-05-31)
**Work classification:** UI change · implementation change · documentation change
**Persona routing:** Gina (frontend/renderer) · Denny (templates/static) · Tess (tests)
**Skill used:** `writing-plans` — folder mirrors [`docs/superpowers/plans/2026-05-30-asteroid-lab-cli-first/`](../2026-05-30-asteroid-lab-cli-first/README.md)
**Closing rule:** No commit / push / PR / merge / `CLOSED` without explicit user request ([`AGENTS.md`](../../../../AGENTS.md)).

This folder holds one detailed, independently-executable plan per PR. Each file is self-contained:
goal, depends, behavior contract, non-goals, file map, step-by-step tasks, tests, verification, risks,
done criteria.

**Execution tracker:** [`checklist.md`](checklist.md) — cross-PR master checklist (frozen decisions,
approval locks, guards, per-PR steps, done criteria). PR files remain the detailed contract.
**Perf contract:** [`perf-baseline.md`](perf-baseline.md) — budgets + DevTools capture procedure.
**Recorded numbers (LOCK-1):** [`baseline-notes.md`](baseline-notes.md) — filled during PR-RENDER-0.

---

## Diagnosis (code-backed)

Architect hypothesis **70% UI renderer / 20% replay data / 10% solver** matches the current code in
[`asteroid_miner_layout_lab.js`](../../../../django_apps/web/static/web/js/asteroid_miner_layout_lab.js)
(~4.5k lines):

| Signal | Current code | Gap vs target |
|--------|--------------|---------------|
| div-per-cell | One-time mount in `initializeServerReplaySurface` (L2298–2304) | OK at mount; **paint path** still touches many cells |
| Full frame repaint | `renderReplayFrame` → `resetForFrame()` then `renderFullMapReplayFrame` when `fullMapCellsFromFrame` non-empty (L1947–1958) | No **token skip** inside `renderFullMapCells` (L1296–1339) |
| Incremental playback | `useIncremental` + `replayPaintedCellIndices` (L2622–2638) | Defeated by keyframes, ≥15% cell threshold (`replayFrameNeedsFullGridReset`, L948–971), and full-map frames |
| Per-cell sprites | `ensureLabCellSpriteLayer` creates `div > img` per cell (L243–258) | DOM + layout cost scales with grid size |
| Bundle bridges | `createElement` + `appendChild` per link per frame (L1454–1459) | Dynamic DOM churn during playback |
| Forced reflow | `getBoundingClientRect` (L2194), `offsetWidth` (L2233, L2392) inside layout/paint paths | Read/write not batched |
| Zoom/pan | `gridStage.style.transform` (L2251–2252) | **Partially correct** — container transform exists |
| rAF when paused | `stopPlaybackScheduler` on pause (L2557–2563, L2716–2717) | OK |
| Demo matrix mode | Loops **all** `domCells` every `applyFrame` (L2686–2690) | Full-grid update every frame |

**Data layer evidence** ([`var/log/asteroid_lab_perf/lab_perf.jsonl`](../../../../var/log/asteroid_lab_perf/lab_perf.jsonl)):
`lab_replay_get` ~14MB payload / 88 frames despite `total_full_map_cells: 0` — overlay-heavy frames
dominate transfer + parse, not solver runtime.

**Template anchor:**
[`asteroid_miner_layout_solver.html`](../../../../django_apps/web/templates/web/asteroid_miner_layout_solver.html)
— `#lab-replay-grid-viewport` → `#lab-replay-grid-stage` → `#lab-replay-grid`.

---

## Target architecture

```text
static terrain layer     -> canvas  (drawn once / on keyframe)
dynamic overlay layer    -> canvas  (redraw per replay frame)
sprite layer             -> canvas  (belts / miners / connectors)
tooltip / inspector      -> DOM
controls / timeline / HUD -> DOM
rAF                      -> playing only; changed cells only; read/write split
```

**End state:** Canvas 2D hybrid; DOM for controls/inspector only. **Intermediate PRs** keep the DOM grid
working while metrics improve each step.

---

## Frozen decisions (every PR must preserve)

- **FD-1** Replay / metrics / artifact are **not algorithm input** ([asteroid-lab-invariants.mdc](../../../../.cursor/rules/asteroid-lab-invariants.mdc)).
- **FD-2** Island-local `x`/`y` only in Lab UI; no `server_coords` bridge (no `x == 0` column).
- **FD-3** Single replay timeline; `window.AsteroidLabReplay` test hooks preserved until PR-RENDER-5 explicitly replaces them.
- **FD-4** No weakening of existing replay wiring smoke tests; add perf contracts alongside.
- **FD-5** Renderer perf work does not block CLI-first merge; optional synergy with PR-CLI-5 lazy JSONL streaming.

---

## Approval locks (Planning Lead, 2026-05-31)

These three locks override softer wording anywhere else in the plan set.

- **LOCK-1 — RENDER-0 must produce recorded numbers, not just a budget doc.**
  [`baseline-notes.md`](baseline-notes.md) is a required deliverable and must record, per measured run:
  `replay slug/run` · `frame count` · `decoded payload size` · `rAF median` · `rAF p95` ·
  `forced reflow count` · `total DOM node count` · `full reset count` · `changed/touched cell count`.
  RENDER-0 cannot be marked done with an empty `baseline-notes.md`.

- **LOCK-2 — RENDER-1 acceptance is DOM-touch count, not speed.**
  Done criteria are expressed as touched-DOM invariants (see [`pr-render-1`](pr-render-1-dom-token-diff.md)),
  measured before any timing claim.

- **LOCK-3 — RENDER-6 has a hard start gate (no "perf intuition" start).**
  RENDER-6 may start ONLY if, after RENDER-1..5, at least one holds:
  (a) payload/parse/hydrate remains a dominant measured cost, OR
  (b) replay payload remains >5MB compressed / >15MB decoded, OR
  (c) full/overlay duplication proven by byte accounting.

**Execution rule:** development starts only after PR-RENDER-0 baseline is closed (numbers committed in
`baseline-notes.md`).

---

## Guards (rendering vs algorithm; cross-cutting)

Architect's rendering-vs-algorithm checklist, locked here as **Guard R1–R6**. Each touching PR keeps
the relevant guards green.

| Guard | Statement (renderer is the cause when true) | Where enforced |
|-------|-----|-----|
| R1 | rAF tick must not change class/style on cells whose token is unchanged | RENDER-1 |
| R2 | No `querySelector`/`querySelectorAll` per frame in the paint path | RENDER-1, RENDER-2 |
| R3 | No `innerHTML` grid rebuild on frame change (mount once) | RENDER-1 (already true; assert) |
| R4 | No `getBoundingClientRect`/`offsetWidth`/`scrollWidth` read mid-update | RENDER-2 |
| R5 | rAF does not run while paused | RENDER-0 assert; RENDER-3 |
| R6 | Frame change touches changed cells only, not the whole grid | RENDER-1, RENDER-3 |

Data-shape guards (algorithm/replay design is the cause when true) drive **RENDER-6** only and are gated
by LOCK-3:

```text
[ ] rAF recomputes route/path/topology
[ ] per-frame JSON parse of full payload
[ ] per-frame deep clone of full_map
[ ] overlay_cells accumulates (frame grows over time)
[ ] change is small but only full-frame snapshots exist
```

---

## PR index

| PR | File | Depends | Scope | Expected win |
|----|------|---------|-------|--------------|
| PR-RENDER-0 | [`pr-render-0-spec-and-baseline.md`](pr-render-0-spec-and-baseline.md) | — | Spec, perf budget, DevTools checklist, recorded baseline, static test skeleton | Measurement baseline |
| PR-RENDER-1 | [`pr-render-1-dom-token-diff.md`](pr-render-1-dom-token-diff.md) | RENDER-0 | Token-diff skip in `renderFullMapCells`; reduce redundant className/sprite writes | Largest DOM paint cut |
| PR-RENDER-2 | [`pr-render-2-layout-read-write-split.md`](pr-render-2-layout-read-write-split.md) | RENDER-1 | Batch layout reads; cache cellPx/gapPx; defer `offsetWidth`/`getBoundingClientRect` from paint | Fixes forced reflow ~30ms |
| PR-RENDER-3 | [`pr-render-3-playback-raf-budget.md`](pr-render-3-playback-raf-budget.md) | RENDER-1 | rAF frame budget guard; bundle-bridge pooling; demo-mode diff; chrome decimation tuning | rAF under 16.7ms target (DOM path) |
| PR-RENDER-4 | [`pr-render-4-canvas-terrain-layer.md`](pr-render-4-canvas-terrain-layer.md) | RENDER-2 | Static terrain on canvas; DOM cells → hit-test grid or transparent overlay | Cuts static cell DOM paint |
| PR-RENDER-5 | [`pr-render-5-canvas-overlay-sprite.md`](pr-render-5-canvas-overlay-sprite.md) | RENDER-4 | Dynamic overlay + sprite canvas; extract `lab_replay_canvas_renderer.js` module | Final renderer; 10k cells viable |
| PR-RENDER-6 | [`pr-render-6-replay-frame-compact-optional.md`](pr-render-6-replay-frame-compact-optional.md) | RENDER-1..5 + LOCK-3 gate | Viewer-side compact frame adapter; optional backend diff emission | Payload/parse reduction (~20%) |

---

## Dependency graph

```text
RENDER-0 ──> RENDER-1 ──> RENDER-2 ──> RENDER-4 ──> RENDER-5
                 │
                 ├──> RENDER-3
                 │
                 └──> RENDER-6   (only when LOCK-3 gate met)
   PR-CLI-5 (optional) ┄┄┄> RENDER-6
```

**Recommended execution order:** RENDER-0 (close baseline first) → 1 → (2 and 3 parallel) → 4 → 5;
RENDER-6 only when the LOCK-3 start gate is met and recorded in `baseline-notes.md`.

---

## Cross-cutting test strategy

| Layer | Approach |
|-------|----------|
| Static JS contracts | Python reads `asteroid_miner_layout_lab.js` / new modules (existing repo pattern, e.g. [`test_asteroid_lab_lazy_replay_metrics.py`](../../../../tests/unit/asteroid_lab/test_asteroid_lab_lazy_replay_metrics.py)) |
| Integration | Extend [`test_asteroid_miner_layout_solver.py`](../../../../tests/integration/web/test_asteroid_miner_layout_solver.py), [`test_asteroid_lab_replay_timeline_smoke.py`](../../../../tests/integration/web/test_asteroid_lab_replay_timeline_smoke.py) |
| Browser perf | Manual DevTools checklist in RENDER-0; optional Playwright trace in RENDER-3+ |
| Regression | `window.AsteroidLabReplay.renderReplayFrame` behavior preserved through RENDER-4 |

**Iteration gate:** `python -m pytest tests/unit/asteroid_lab/test_lab_renderer_*.py -v` then targeted
integration web tests. (No `-q` / `--quiet` / `--tb=no` per [shapez2-core.mdc](../../../../.cursor/rules/shapez2-core.mdc).)

---

## Risks

- `invariant:` Sprite filename rules must stay aligned with Python ([`genetic_sample_model_admin_preview.md`](../../../../documents/ai/plans/genetic_sample_model_admin_preview.md)).
- `assumption:` Token-diff sufficient before full canvas migration — validate on RTTP 88-frame fixture first.
- `uncertain:` Inspector/hit-test UX during canvas migration — keep transparent DOM grid until RENDER-5 hitTest proven.
- Monolith JS file — extract modules incrementally; avoid big-bang rename per AGENTS.md leading-underscore rule.
