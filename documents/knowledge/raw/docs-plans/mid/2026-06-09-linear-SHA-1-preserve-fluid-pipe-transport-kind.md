# Plan: SHA-1 - Preserve fluid_pipe transport_kind (Mid: DTO threading, replay, tests)

## Source

- Linear issue: https://linear.app/zkaufman/issue/SHA-1
- Priority: Mid
- Labels: bug, solver, spec
- Status at planning time: Todo

## Problem

Transport kind is lost between candidate probe and committed provisional overlay because DTO and overlay builders omit the field and replay stubs assume belt-only wiring.

## Scope

- Thread `transport_kind` through DTO construction, overlay build, and replay wire helpers.
- Add regression test coverage for mixed shape/fluid maps.

## Non-goals

- Candidate generation changes.
- SHA-2 route domain builder work.

## Implementation Plan

1. Update `_build_overlay` / `_committed_placement` in `commit_finalize.py` to pass `transport_kind` end-to-end.
2. Audit and fix all `CommittedRimSeedPlacement(...)` call sites in unit tests and replay tests to include `transport_kind`.
3. Fix replay `_transport_wire()` in the L3 replay segment to use placement-level transport.
4. Add mixed-map regression test: fluid rim commit → overlay cells and replay wire assert `FLUID_PIPE`.
5. Update any golden/replay fixtures that hardcode belt transport for fluid placements.

## Files / Areas Likely Affected

- `src/shapez2_factory/application/asteroid_lab/layers/layer_03_rim_greedy_placement/commit_finalize.py`
- `tests/unit/asteroid_lab/replay/test_layer03_persistent_equipment_replay.py`
- `tests/unit/asteroid_lab/layers/` transport and commit tests
- Replay segment module for L3 rim greedy

## Tests / Validation

- `pytest tests/unit/asteroid_lab/replay/test_layer03_persistent_equipment_replay.py -q`
- `pytest tests/unit/asteroid_lab/ -k transport -q`

## Acceptance Criteria

- [ ] DTO + overlay threading complete with no hardcoded `SHAPE_BELT` in commit overlay path
- [ ] Replay segment fix verified
- [ ] Regression test coverage added for mixed transport profiles

## Risks

- Test fixture churn across multiple files constructing `CommittedRimSeedPlacement`.

## Human Review Required

- no
- reason: Standard DTO extension and test updates within L3 contract.

## Automation Notes

Generated from Linear Todo issue by planning automation.

Depends on High-priority correctness fix in `docs/plans/high/2026-06-09-linear-SHA-1-preserve-fluid-pipe-transport-kind.md`.
