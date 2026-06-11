# Plan: SHA-3 - Commit reprobe failures collapse to ROUTE_CROSSES_HARD_BLOCKER

## Source

- Linear issue: https://linear.app/zkaufman/issue/SHA-3
- Priority: High
- Labels: test, bug, solver
- Status at planning time: Todo

## Problem

`finalize_selection` maps every commit-time reprobe failure to `ROUTE_CROSSES_HARD_BLOCKER`, collapsing distinct failure modes like `DPS_UNREACHABLE`. Diagnostics and regression tests cannot distinguish unreachable goals from hard-blocker collisions.

## Scope

- Restore correct `RimGreedyRejectReason` mapping at commit finalize based on reprobe diagnostics.
- Fix diagnostic signal loss from boolean-only `try_commit_reprobe` return.

## Non-goals

- Route domain builder (SHA-2).
- Changing probe algorithm itself.

## Implementation Plan

1. Extend `try_commit_reprobe` in `commit_reprobe.py` to return structured failure info (reject reason / route probe status) instead of bare boolean.
2. Map probe diagnostics to the correct `RimGreedyRejectReason` enum in `finalize_selection` (`commit_finalize.py` ~131-132).
3. Ensure `DPS_UNREACHABLE` is assigned when probe reports unreachable goal.
4. Remove the 3-way union workaround in narrow corridor regression that masks reason collapse.

## Files / Areas Likely Affected

- `src/shapez2_factory/application/asteroid_lab/layers/layer_03_rim_greedy_placement/commit_reprobe.py`
- `src/shapez2_factory/application/asteroid_lab/layers/layer_03_rim_greedy_placement/commit_finalize.py`
- `src/shapez2_factory/application/asteroid_lab/layers/contracts/rim_greedy.py` (`RimGreedyRejectReason`, `DPS_UNREACHABLE`)
- `tests/unit/asteroid_lab/layers/test_narrow_corridor_regression.py`

## Tests / Validation

- `pytest tests/unit/asteroid_lab/layers/test_narrow_corridor_regression.py -q`
- `pytest tests/unit/asteroid_lab/ -k "commit_finalize or route_fragility" -q`

## Acceptance Criteria

- [ ] Reprobe failures map to correct `RimGreedyRejectReason`
- [ ] `DPS_UNREACHABLE` assigned when probe reports unreachable
- [ ] S1 narrow-corridor regression asserts single expected reason
- [ ] Commit finalize and route fragility tests pass

## Risks

- Return type change on `try_commit_reprobe` affects all callers; must update atomically.
- May interact with SHA-2 builder refactor if done in parallel — coordinate call-site updates.

## Human Review Required

- no
- reason: Diagnostic correctness fix within existing enum contract; no auth or schema change.

## Automation Notes

Generated from Linear Todo issue by planning automation.
