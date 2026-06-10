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

# Plan: Poll LayerBudgetContext in L4 routeable inner group placement

## Source Issue

- Linear: SHA-32
- Status at planning time: In Progress (moved before plan creation)
- Priority: Mid

## Problem

Layer 04 inner pattern fill (`layer_05_inner_pattern_fill`) accepts `LayerBudgetContext` from `stack_runner` and polls remaining budget only in the 1×1 greedy placement loop. The preceding `place_routeable_inner_groups` phase runs up to `max_inner_routeable` iterations without any budget polling, risking stack budget exhaustion before L5–L6.

## Scope

- Add budget polling to `place_routeable_inner_groups` phase.
- Ensure consistent budget enforcement across all L4 placement loops.

## Non-goals

- Changing inner group placement algorithm beyond budget enforcement.
- Altering `max_inner_routeable` derivation.

## Implementation Plan

1. Extend `place_routeable_inner_groups` signature to accept `budget_ctx: LayerBudgetContext`.
2. Before each iteration in the `max_groups` loop, check `budget_ctx.remaining_budget_ms() <= 0`; break early and return partial placements.
3. Optionally poll inside `try_place_one_routeable_inner_group` anchor scan if single-iteration cost is high (match SHA-31 granularity if needed).
4. Update `run_greedy_inner_fill` call site to pass `budget_ctx` into `place_routeable_inner_groups`.
5. Propagate `budget_interrupted` when routeable phase exits early due to budget (align with existing 1×1 loop `Layer04SkipReason.BUDGET_EXHAUSTED` semantics).
6. Add regression test with fake `now_fn` / tight budget: verify routeable loop stops before `max_groups` and downstream layers can still run.
7. Run `pytest tests/unit/asteroid_lab/layers/test_layer04_inner_fill_greedy.py -v`.

## Files / Areas Likely Affected

- `src/shapez2_factory/application/asteroid_lab/layers/layer_05_inner_pattern_fill/inner_routeable_group.py`
- `src/shapez2_factory/application/asteroid_lab/layers/layer_05_inner_pattern_fill/greedy.py`
- `tests/unit/asteroid_lab/layers/test_layer04_inner_fill_greedy.py`

## Validation Plan

- lint: `ruff check src/shapez2_factory/application/asteroid_lab/layers/layer_05_inner_pattern_fill/`
- typecheck: `mypy django_apps config src` (spot-check)
- tests: `python -m pytest tests/unit/asteroid_lab/layers/test_layer04_inner_fill_greedy.py -v`
- manual verification: large-map stack run does not starve L5–L6 when budget is tight

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Coordinate with SHA-31 (L3) and SHA-14 (L5) budget wiring for consistent interrupt semantics.
- Partial routeable placement vs empty result on budget exhaustion — follow existing `budget_interrupted` contract in `greedy.py`.
