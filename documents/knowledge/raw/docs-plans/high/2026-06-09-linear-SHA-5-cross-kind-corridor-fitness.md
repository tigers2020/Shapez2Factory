# Plan: SHA-5 - CommitDomainState cross-kind corridor fitness (RC4)

## Source

- Linear issue: https://linear.app/zkaufman/issue/SHA-5
- Priority: High
- Labels: test, bug, solver, spec
- Status at planning time: Todo

## Problem

Phase C1 beam selection tracks a single undifferentiated `CommitDomainState.corridor` frozenset for both `SHAPE_BELT` and `FLUID_PIPE` paths. Shared-corridor fitness pressure counts spatial overlap across transport kinds, violating spec RC4 (separate route domains; cross-kind corridor merge forbidden).

## Scope

- Partition corridor tracking by `TransportKind` on `CommitDomainState`.
- Filter corridor-pressure computation in beam `_extend()` by candidate transport kind.
- Fix RC4 spec violation in commit-phase fitness scoring.

## Non-goals

- Changing Phase B route probe logic.
- Altering spatial overlap tolerance between belt and pipe paths (they may coexist).
- Unrelated beam selection heuristic refactors.

## Implementation Plan

1. Replace single `CommitDomainState.corridor` frozenset with `corridor_by_kind: dict[TransportKind, frozenset[Coord]]`.
2. In `beam_selector.py::_extend()`, compute `shared = len(state.domain.corridor_by_kind[candidate.transport_kind] & corridor)` before applying `corridor_pressure_weight`.
3. Update `try_commit_reprobe` in `commit_reprobe.py` to accumulate corridors into the matching kind bucket only.
4. Verify belt and pipe witness paths can coexist spatially without cross-kind fitness penalty.

## Files / Areas Likely Affected

- `src/shapez2_factory/application/asteroid_lab/layers/layer_03_rim_greedy_placement/commit_reprobe.py`
- `src/shapez2_factory/application/asteroid_lab/layers/layer_03_rim_greedy_placement/beam_selector.py`
- `docs/superpowers/specs/2026-05-31-layer-03-rim-placement-v2-design.md` (RC4 reference)

## Tests / Validation

- `pytest tests/unit/asteroid_lab/layers/test_narrow_corridor_regression.py -q`
- `python manage.py check`

## Acceptance Criteria

- [ ] Corridor pressure applies only within the same `TransportKind` domain
- [ ] RC4 violation fixed in `CommitDomainState` and `_extend()` logic
- [ ] Existing narrow-corridor regression pack stays green
- [ ] No unrelated beam selection behavior changed

## Risks

- State shape change affects all C1 beam extension paths; must update immutably when extending state.
- Interaction with SHA-1 transport_kind correctness — fluid candidates must have correct kind for bucket lookup.

## Human Review Required

- no
- reason: Spec-aligned correctness fix within existing RC4 contract.

## Automation Notes

Generated from Linear Todo issue by planning automation.
