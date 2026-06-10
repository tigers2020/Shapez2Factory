---
linear_issue: SHA-32
title: L4 inner fill ignores LayerBudgetContext during routeable inner group placement
priority: Mid
labels:
  - bug
  - performance
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: L4 routeable inner group budget polling

## Source Issue

- Linear: SHA-32
- Status at planning time: Todo
- Priority: Mid

## Problem

`layer_05_inner_pattern_fill` (L4 inner fill) polls `LayerBudgetContext` only in the 1×1 greedy placement loop. The preceding `place_routeable_inner_groups` phase in `inner_routeable_group.py` runs up to `max_inner_routeable` iterations without budget polling, risking stack budget exhaustion before L5–L6.

## Scope

- Pass `LayerBudgetContext` into `place_routeable_inner_groups`.
- Poll budget before each iteration and candidate scan in the routeable inner group phase.
- Add regression test on large maps verifying budget is respected across all L4 placement loops.

## Non-goals

- Changing inner group placement algorithm beyond budget enforcement.
- Altering `max_inner_routeable` derivation.

## Implementation Plan

1. Trace `LayerBudgetContext` from `run_layer_04_inner_pattern_fill` in `greedy.py` into `place_routeable_inner_groups`.
2. Add `budget_ctx` parameter to `place_routeable_inner_groups` and `try_place_one_routeable_inner_group`; poll before each `max_groups` iteration.
3. On budget exhaustion, return partial `RouteableInnerGroupPlacement` tuple and proceed to 1×1 loop only if budget remains.
4. Ensure 1×1 greedy loop retains existing budget polling (no regression).
5. Add test with high `max_inner_routeable` (e.g. 130 groups) asserting L5 layer stub still executes within shared budget.
6. Run `pytest tests/unit/shapez2_factory/application/asteroid_lab/layers/layer_05_inner_pattern_fill/ -v`.

## Files / Areas Likely Affected

- `src/shapez2_factory/application/asteroid_lab/layers/layer_05_inner_pattern_fill/greedy.py`
- `src/shapez2_factory/application/asteroid_lab/layers/layer_05_inner_pattern_fill/inner_routeable_group.py`
- `src/shapez2_factory/application/asteroid_lab/layers/contracts/layer_budget.py`
- `tests/unit/shapez2_factory/application/asteroid_lab/layers/layer_05_inner_pattern_fill/`

## Validation Plan

- lint: `ruff check .`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/shapez2_factory/application/asteroid_lab/layers/layer_05_inner_pattern_fill/ -v`
- build: `python manage.py check`
- manual verification: Large-map solver run confirms L5+ layers execute.

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Partial routeable group placement may reduce inner fill completeness on budget-bound runs.
- Related: SHA-31, SHA-14.
