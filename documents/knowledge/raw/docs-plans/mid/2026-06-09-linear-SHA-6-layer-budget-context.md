# Plan: SHA-6 - LayerBudgetContext (Mid: metrics and tests)

## Source

- Linear issue: https://linear.app/zkaufman/issue/SHA-6
- Priority: Mid
- Labels: performance, test, bug, solver, spec
- Status at planning time: Todo

## Problem

`Layer03ExpansionMetrics.budget_skipped_count` is hardcoded to 0; no unit or stack tests prove L3 yields budget for downstream layers.

## Scope

- Increment `budget_skipped_count` for truncated expansion/selection steps.
- Add unit test for mid-generation budget abort.
- Add stack integration test for downstream budget availability.

## Non-goals

- Stack runner global budget contract changes.

## Implementation Plan

1. Increment `Layer03ExpansionMetrics.budget_skipped_count` whenever expansion or selection truncates due to budget exhaustion.
2. Add unit test: L3 aborts when `remaining_budget_ms()` hits 0 during candidate generation (mock `now_fn` or tight budget).
3. Add stack integration test: tight `LAYER_STACK_BUDGET_MS` leaves non-zero budget for L4 when L3 budget checks enabled.
4. Fix `candidate_gen.py:624` hardcoded `budget_skipped_count=0`.

## Files / Areas Likely Affected

- `src/shapez2_factory/application/asteroid_lab/layers/layer_03_rim_greedy_placement/candidate_gen.py`
- `tests/unit/asteroid_lab/layers/test_stack_runner_skeleton.py` or new budget-specific test
- `tests/unit/asteroid_lab/layers/test_stack_runner_layer04.py`

## Tests / Validation

- `pytest tests/unit/asteroid_lab/layers/ -k "budget or stack_runner" -q`
- `powershell -File scripts/test_fast.ps1` (if budget tests added to fast suite)

## Acceptance Criteria

- [ ] Accurate `budget_skipped_count` in `Layer03ExpansionMetrics`
- [ ] Unit test proves L3 aborts during candidate generation when budget hits zero
- [ ] Stack integration test confirms non-zero budget remains for L4 under tight constraints

## Risks

- Integration test timing may be flaky without injected `now_fn`; use deterministic clock.

## Human Review Required

- no
- reason: Metrics and test coverage for approved budget enforcement.

## Automation Notes

Generated from Linear Todo issue by planning automation.

Depends on High-priority budget threading in `docs/plans/high/2026-06-09-linear-SHA-6-layer-budget-context.md`.
