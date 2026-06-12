---
id: "replay-sprite-visibility-2026-06-12"
status: "verify"
priority: "high"
assignee: null
epic: null
dueDate: null
created: "2026-06-12T00:00:00.000Z"
modified: "2026-06-12T12:00:00.000Z"
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

## Progress

- 2026-06-12 — **align** — brainstorming: user reports mixed sprite visibility, faded cells, shape_belt/pipe still broken; explored `labSpriteRelpathForCell`, `buildCanvasPaintPlan`, `lab_replay_sprite_wire.py`, golden paint tests
- 2026-06-12 — **align** — Q1: timeline scope → **D** (almost all frames, Map Z "All")
- 2026-06-12 — **align** — Q3: **C** — candidate miner sprite 보이나 흐림; 정본 `shape_belt` 금지 위반; 셀당 모델 과다
- 2026-06-12 — **contract** — §1 APPROVED WITH MINOR CONTRACT AMENDMENTS
- 2026-06-12 — **verify** — Slice 1 Tasks 1–7 subagent-driven complete; validation 31 passed (`pytest` slice 1 gate); allowlist fix for sanitizer in `test_shape_belt_ui_wire_ban.py`
- 2026-06-12 — **implement** — Slice 1 Task 2: `replay_wire_read_sanitize.py` + 4 sanitizer tests; 6/6 pytest green, ruff clean
- 2026-06-12 — **implement** — Slice 1 Task 4: `test_replay_wire_audit.py` (golden assembler + fixture scan); audit fix `_BANNED_LEGACY_COMMITTED_TRANSPORT` (canonical `space_belt` on committed rows was false positive); 2/2 audit + 6/6 sanitizer pytest green
