---
id: "replay-sprite-visibility-2026-06-12"
status: "verify"
priority: "high"
assignee: null
epic: null
dueDate: null
created: "2026-06-12T00:00:00.000Z"
modified: "2026-06-12T23:45:00.000Z"
labels: ["asteroid-lab", "replay", "sprites", "ui"]
order: "a0"
---
# Replay map sprite visibility & shape_belt/pipe

## Scope

Replay map에서 sprite 일부 미표시·흐림(faded overlay 대체), legacy `shape_belt`/`fluid_pipe` wire → sprite resolve 실패. `replay-cell-semantics` epic 이후 렌더/paint 경로 정리.

## Acceptance

- [x] 재현 조건·실패 셀 종류 문서화
- [x] root cause (wire vs resolve vs paint-plan vs canvas/DOM) 확정
- [x] design spec + implementation plan 승인
- [x] golden/parity tests + UI 검증 (Slice 1 gate)

## Artifacts

| Kind | Path | Updated |
|------|------|---------|
| spec | docs/superpowers/specs/2026-06-12-replay-sprite-visibility-design.md | 2026-06-12 |
| plan | docs/superpowers/plans/2026-06-12-replay-sprite-visibility-slice-1.md | 2026-06-12 |
| plan | docs/superpowers/plans/2026-06-12-replay-sprite-visibility-slice-2.md | 2026-06-12 |
| plan | docs/superpowers/plans/2026-06-12-replay-sprite-visibility-slice-3.md | 2026-06-12 |
| plan | docs/superpowers/plans/2026-06-12-replay-sprite-visibility-slice-4.md | 2026-06-12 |
| plan | docs/superpowers/plans/2026-06-12-replay-sprite-visibility-slice-5.md | 2026-06-12 |

## Progress

- 2026-06-12 — **align** — brainstorming: user reports mixed sprite visibility, faded cells, shape_belt/pipe still broken; explored `labSpriteRelpathForCell`, `buildCanvasPaintPlan`, `lab_replay_sprite_wire.py`, golden paint tests
- 2026-06-12 — **align** — Q1: timeline scope → **D** (almost all frames, Map Z "All")
- 2026-06-12 — **align** — Q3: **C** — candidate miner sprite 보이나 흐림; 정본 `shape_belt` 금지 위반; 셀당 모델 과다
- 2026-06-12 — **contract** — §1 APPROVED WITH MINOR CONTRACT AMENDMENTS
- 2026-06-12 — **verify** — Slice 1 committed `6e4eb56a`; Slice 2 plan drafted (`docs/superpowers/plans/2026-06-12-replay-sprite-visibility-slice-2.md`) — awaiting review before execution
- 2026-06-12 — **implement** — Slice 1 Task 2: `replay_wire_read_sanitize.py` + 4 sanitizer tests; 6/6 pytest green, ruff clean
- 2026-06-12 — **implement** — Slice 1 Task 4: `test_replay_wire_audit.py` (golden assembler + fixture scan); audit fix `_BANNED_LEGACY_COMMITTED_TRANSPORT` (canonical `space_belt` on committed rows was false positive); 2/2 audit + 6/6 sanitizer pytest green
- 2026-06-12 — **implement** — Slice 2 Task 3: `build_effective_cell_view_index` + `test_build_effective_cell_view_index_frame_38`; 6/6 paint-plan pytest green, ruff clean
- 2026-06-12 — **verify** — Slice 2 complete (Tasks 1–6): `lab_paint_layers_from_view` + `build_effective_cell_view_index` (Python), `lab_replay_paint_plan.js` mirror, golden/parity/anti-fade/candidate tests; `test_python_paint_layers_frame_38_contract_snapshot` added; Slice 2 gate 10/10 pytest green; Slice 1 regression green; `buildCanvasPaintPlan` untouched
- 2026-06-12 — **implement** — Slice 3 Task 1: `canvas_plan_from_paint_layers` Python mirror + `test_lab_replay_paint_canvas_adapter.py` (frame-38 miner sprite, anti-fade no rgba fill); 2/2 pytest green
- 2026-06-12 — **implement** — Slice 3 Task 2: JS `canvasPlanFromPaintLayers` + `buildLabPaintPlanFromFrame` (layout carry via `lastFrameWithSpriteCapableCells` pattern); contract tests in `test_lab_canvas_renderer.py`; 2/2 pytest green; no `lab.js` changes
- 2026-06-12 — **implement** — Slice 3 Task 3: `labPaintV2Enabled()` + `buildCanvasPaintPlan` v2 delegate behind `data-lab-paint-v2="1"`; `test_lab_js_lab_paint_v2_enabled_helper`; legacy path unchanged when flag off
- 2026-06-12 — **implement** — Slice 3 Task 4: `filterTerrainCellsForPaintV2` excludes field_sprite indices from terrain canvas when v2; wired in `refreshLabCanvasAfterLayoutChange` + `applyLabCanvasServerReplayFrame`; `test_lab_js_filter_terrain_cells_for_paint_v2_exists`
- 2026-06-12 — **verify** — Slice 3 complete (Tasks 1–5): canvas adapter + `buildLabPaintPlanFromFrame` + `labPaintV2Enabled` delegate + terrain anti-fade; gate 26/26 paint/canvas + 16/16 Slice 1 regression pytest green; manual smoke frame 38 (10,7) sharp miner + ring; commit `f099e7f4`
- 2026-06-12 — **align** — Slice 4 plan drafted + reviewer amendments (frame-cached resolver, occupant-only DOM sprite, exact class tokens); approved Subagent-Driven Tasks 1→5
- 2026-06-12 — **verify** — Slice 4 complete (Tasks 1–5, Task 7 skipped): Python/JS `domPlanFromPaintLayers`, `buildDomPlanResolverForFrame` (index once per frame), v2 DOM chrome in `renderFullMapCells`; legacy + detail lookup preserved; gate 42/42 Slice 4 + 16/16 Slice 1 regression; commits `d9cdd73e`→`de21d642`; plan doc `3a0d60ee`
- 2026-06-12 — **verify** — workflow gate: re-ran 58 passed (10.20s); commit graph `d9cdd73e..3a0d60ee` (5 Slice 4 commits); `buildDomPlanForCell` absent; `createDomPlanResolverForFrame` before loop — **Slice 4 closed**
- 2026-06-12 — **align** — Slice 5 plan drafted (harvest quarantine/delete); Task 7 NON_SPRITE cleanup deferred to post-Slice-5 HITL subtask
- 2026-06-12 — **align** — Slice 5 plan review APPROVED WITH AMENDMENTS: Task 5 default policy (A) soft quarantine; hard delete + NON_SPRITE → Task 6 HITL; no tag until requested
- 2026-06-13 — **verify** — Slice 5 Tasks 1→5 (policy A): harvest quarantine markers; frameCellIndexMap v2; preload/carry dedup; Python sprite_entries paint plan; soft quarantine gate **66/66** pytest; commits `2fbd5f9e`→`cfd117e6`; legacy stageCell retained; Task 6/7 HITL
- 2026-06-12 — **implement** — Slice 5 Task 2: `buildCellByGridIndexFromFrame` + v2 `frameCellIndexMap` delegate; legacy harvest when flag off; 27/27 pytest green; commit `8d9acf4b`
- 2026-06-12 — **verify** — Slice 5 Task 5 policy (A) soft quarantine: v2 early-return clean; `test_build_canvas_paint_plan_v2_has_no_stage_cell` + `test_legacy_canvas_harvest_still_present_when_flag_off`; legacy `stageCell` + `const overlays` retained; Slice 5 gate green
- 2026-06-12 — **implement** — Task 6a (HITL approved): policy A — `build_effective_cell_view_index` unions `cell_overlay_json` paint-target rows (Python registry + JS mirror); transport rotation from overlay sources; `test_build_effective_cell_view_index_unions_cell_overlay_json` + green `test_overlay_fallback_frame_includes_pipe_sprite_from_cell_overlay_json`; no harvest delete / flag / NON_SPRITE / tag
