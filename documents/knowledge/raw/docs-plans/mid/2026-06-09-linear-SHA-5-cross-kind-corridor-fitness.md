# Plan: SHA-5 - Cross-kind corridor fitness (Mid: regression tests)

## Source

- Linear issue: https://linear.app/zkaufman/issue/SHA-5
- Priority: Mid
- Labels: test, bug, solver, spec
- Status at planning time: Todo

## Problem

Existing dual-transport test only asserts probe goals differ; it does not lock commit-time corridor-pressure separation between transport kinds.

## Scope

- Add dual-transport regression test for commit-phase fitness separation.
- Ensure narrow-corridor regression pack remains green.

## Non-goals

- Phase B probe changes.
- Beam heuristic changes beyond corridor domain tracking.

## Implementation Plan

1. Add regression on `s4_dual_transport_*` fixtures: commit belt bundle, evaluate fluid candidate with overlapping void cell — assert `shared_corridor_cells == 0` in fitness breakdown (and vice versa).
2. Extend or update `test_transport_kind_corridor_conflict_regression` to cover commit-phase corridor pressure, not just probe goals.
3. Run full narrow corridor pack: `pytest tests/unit/asteroid_lab/layers/test_narrow_corridor_regression.py`.

## Files / Areas Likely Affected

- `tests/unit/asteroid_lab/layers/test_narrow_corridor_regression.py`
- Dual-transport fixture data under `tests/unit/asteroid_lab/`

## Tests / Validation

- `pytest tests/unit/asteroid_lab/layers/test_narrow_corridor_regression.py -q`

## Acceptance Criteria

- [ ] Dual-transport regression proves fluid candidates not penalized for overlapping committed belt corridors (and vice versa)
- [ ] Narrow-corridor regression pack green

## Risks

- Fixture availability for dual-transport commit scenarios.

## Human Review Required

- no
- reason: Test coverage for approved High-priority fix.

## Automation Notes

Generated from Linear Todo issue by planning automation.

Depends on High-priority RC4 fix in `docs/plans/high/2026-06-09-linear-SHA-5-cross-kind-corridor-fitness.md`.
