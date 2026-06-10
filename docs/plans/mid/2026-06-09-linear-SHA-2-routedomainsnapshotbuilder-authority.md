# Plan: SHA-2 - RouteDomainSnapshotBuilder (Mid: refactor and regression)

## Source

- Linear issue: https://linear.app/zkaufman/issue/SHA-2
- Priority: Mid
- Labels: refactor, bug, solver, spec
- Status at planning time: Todo

## Problem

Inline domain construction in two probe paths lacks shared regression coverage proving parity.

## Scope

- Complete builder implementation and refactor both call sites.
- Add parity regression test between candidate probe and commit reprobe paths.

## Non-goals

- Probe algorithm changes.
- SHA-3 reject reason work.

## Implementation Plan

1. Implement builder with deterministic ordering for blocker sets and equipment cells.
2. Refactor `candidate_gen.py` probe path to call `RouteDomainSnapshotBuilder.build_snapshot`.
3. Refactor `commit_reprobe.py` reprobe path to use identical builder invocation.
4. Add regression test: same `complete_map`, exterior plan, and committed equipment → identical `WeightedTransportRouteDomain` from both paths.
5. Run existing narrow corridor and commit finalize test pack to confirm no behavior regression.

## Files / Areas Likely Affected

- `src/shapez2_factory/application/asteroid_lab/layers/layer_03_rim_greedy_placement/candidate_gen.py`
- `src/shapez2_factory/application/asteroid_lab/layers/layer_03_rim_greedy_placement/commit_reprobe.py`
- `tests/unit/asteroid_lab/layers/test_narrow_corridor_regression.py`
- New test file for builder parity if needed

## Tests / Validation

- `pytest tests/unit/asteroid_lab/layers/test_narrow_corridor_regression.py -q`
- New parity regression test for builder output equality

## Acceptance Criteria

- [ ] Shared builder implementation complete
- [ ] Both probe paths refactored
- [ ] Parity regression test passes

## Risks

- Existing tests may implicitly depend on inline construction ordering.

## Human Review Required

- no
- reason: Refactor within approved High-priority architecture decision.

## Automation Notes

Generated from Linear Todo issue by planning automation.

Depends on High-priority builder introduction in `docs/plans/high/2026-06-09-linear-SHA-2-routedomainsnapshotbuilder-authority.md`.
