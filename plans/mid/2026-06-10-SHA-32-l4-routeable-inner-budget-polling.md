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

# Plan: Wire LayerBudgetContext into L4 routeable inner group placement

## Source Issue

- Linear: SHA-32
- Status at planning time: Todo
- Priority: Mid

## Problem

Layer 04 inner pattern fill (`layer_05_inner_pattern_fill`) accepts `LayerBudgetContext` from `stack_runner` and polls remaining budget only in the 1×1 greedy placement loop. The preceding `place_routeable_inner_groups` phase runs up to `max_inner_routeable` iterations without any budget polling, so large maps can exhaust the shared stack budget before the 1×1 loop or downstream L5–L6 layers run.

## Scope

- Thread `LayerBudgetContext` into `place_routeable_inner_groups` and its inner candidate scan.
- Poll `remaining_budget_ms()` before each routeable-group iteration and before anchor scans.
- Propagate `budget_interrupted` through `run_greedy_inner_fill` when the routeable phase exhausts budget (mirror existing 1×1 loop semantics).
- Add regression test proving routeable placement respects budget on large candidate sets.

## Non-goals

- Changing inner group placement algorithm beyond budget enforcement.
- Altering `max_inner_routeable` derivation or `target_routeable_group_count_for_field`.
- Changing global stack budget allocation in `stack_runner`.

## Implementation Plan

1. Add `budget_ctx: LayerBudgetContext` parameter to `place_routeable_inner_groups` in `inner_routeable_group.py`.
2. At the top of each `max_groups` iteration, check `budget_ctx.remaining_budget_ms() <= 0`; break early returning partial `placed` tuple.
3. Add optional `budget_ctx` to `try_place_one_routeable_inner_group`; before the anchor scan loop, poll budget and return `None` when exhausted.
4. Update `run_greedy_inner_fill` in `greedy.py` to pass `budget_ctx` into `place_routeable_inner_groups`.
5. If routeable phase stops with zero budget remaining, set `budget_interrupted=True` in `Layer04FillMetrics` (even when 1×1 loop never runs) and use `Layer04SkipReason.BUDGET_EXHAUSTED` when no cells were placed.
6. Add unit test in `tests/unit/asteroid_lab/layers/test_layer04_inner_fill_greedy.py` (or dedicated `test_layer04_inner_routeable_budget.py`): large interior candidate set + `target_routeable_group_count` high + fake `now_fn` that exhausts budget during routeable loop; assert `budget_interrupted` and partial/zero routeable groups.
7. Run `pytest tests/unit/asteroid_lab/layers/test_layer04_inner_fill_greedy.py -v`.

## Files / Areas Likely Affected

- `src/shapez2_factory/application/asteroid_lab/layers/layer_05_inner_pattern_fill/inner_routeable_group.py`
- `src/shapez2_factory/application/asteroid_lab/layers/layer_05_inner_pattern_fill/greedy.py`
- `tests/unit/asteroid_lab/layers/test_layer04_inner_fill_greedy.py`
- `src/shapez2_factory/application/asteroid_lab/layers/contracts/layer04_inner_fill.py` (only if skip/metrics contract needs routeable-phase flag)

## Validation Plan

- lint: `ruff check src/shapez2_factory/application/asteroid_lab/layers/layer_05_inner_pattern_fill/`
- typecheck: `mypy django_apps config src` (spot-check changed modules)
- tests: `pytest tests/unit/asteroid_lab/layers/test_layer04_inner_fill_greedy.py -v`
- build: N/A
- manual verification: Run solver on large-map fixture; confirm L5/L6 receive remaining budget when L4 routeable phase is interrupted

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Coordinate with SHA-31 (L3 Phase B budget) and SHA-14 (L5 sequential router budget) so polling cadence is consistent across layers.
- `try_place_first_routeable_inner_group` callers may need `budget_ctx` if used outside greedy fill — audit call sites before widening signature.
- Large-map regression may need a synthetic fixture rather than full 130-group golden map.
