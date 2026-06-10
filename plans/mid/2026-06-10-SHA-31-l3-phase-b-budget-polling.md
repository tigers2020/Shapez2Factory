---
linear_issue: SHA-31
title: L3 rim greedy placement ignores LayerBudgetContext during Phase B route probe expansion
priority: Mid
labels:
  - bug
  - performance
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: L3 Phase B budget polling

## Source Issue

- Linear: SHA-31
- Status at planning time: Todo
- Priority: Mid

## Problem

`layer_03_rim_greedy_placement` accepts `LayerBudgetContext` from `stack_runner` but Phase B candidate generation (`candidate_gen.py`) runs nested weighted A* route probes (anchors × gene entries × D4 variants × cardinal output sides) without polling remaining budget. Large maps can exhaust the shared 60s stack budget inside L3 and starve L4–L6.

## Scope

- Thread `LayerBudgetContext` into Phase B inner loops (`candidate_gen.py`, callers in `run.py`).
- Poll remaining budget before each route probe expansion; exit gracefully when exhausted.
- Add regression test verifying L4+ layers still receive budget on anchor-heavy maps.

## Non-goals

- Changing rim placement algorithm logic beyond budget enforcement.
- Altering global stack budget allocation policy.

## Implementation Plan

1. Trace `LayerBudgetContext` from `stack_runner` through `run_layer_03_rim_greedy_placement` into `generate_rim_bundle_candidates` (Phase B entry).
2. Add `budget_ctx` parameter to Phase B probe loops in `candidate_gen.py`; call `budget_ctx.remaining_ms()` (or existing poll helper) before each `weighted_route_probe`.
3. On budget exhaustion, stop candidate expansion and return partial candidate set with observable skip reason (reuse existing `Layer03SkipReason` or budget-exhausted metric if present).
4. Mirror budget-poll pattern from other budget-aware layers (e.g. SHA-14 L5 fix) for consistency.
5. Add unit/integration test with many rim anchors + gene seeds asserting L3 terminates before consuming full stack budget and downstream layer stubs still run.
6. Run `pytest tests/unit/shapez2_factory/application/asteroid_lab/layers/layer_03_rim_greedy_placement/ -v` and stack runner smoke if present.

## Files / Areas Likely Affected

- `src/shapez2_factory/application/asteroid_lab/layers/layer_03_rim_greedy_placement/run.py`
- `src/shapez2_factory/application/asteroid_lab/layers/layer_03_rim_greedy_placement/candidate_gen.py`
- `src/shapez2_factory/application/asteroid_lab/layers/contracts/layer_budget.py`
- `tests/unit/shapez2_factory/application/asteroid_lab/layers/layer_03_rim_greedy_placement/` (new or extended)

## Validation Plan

- lint: `ruff check .`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/shapez2_factory/application/asteroid_lab/layers/layer_03_rim_greedy_placement/ -v`
- build: `python manage.py check`
- manual verification: Run solver on large-map fixture; confirm L4+ layers execute within shared budget.

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Partial Phase B pools may change beam-selection outcomes on budget-bound runs; document as acceptable degradation vs correctness fix.
- Related: SHA-32, SHA-14 share the same budget-polling pattern.
