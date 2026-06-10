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
- Status at planning time: In Progress
- Priority: Mid

## Problem

Layer 04 inner pattern fill (`layer_05_inner_pattern_fill`) accepts `LayerBudgetContext` from `stack_runner` and polls `remaining_budget_ms()` only in the 1×1 greedy placement loop inside `run_greedy_inner_fill`. The preceding `place_routeable_inner_groups` phase runs up to `max_inner_routeable` iterations without any budget polling, so a large map can exhaust the shared stack budget before the 1×1 loop runs.

## Scope

- Pass `LayerBudgetContext` into `place_routeable_inner_groups` (and inner candidate scan if needed).
- Poll budget before each routeable-group iteration and before heavy candidate ranking in `try_place_one_routeable_inner_group`.
- Set `budget_interrupted=True` in `Layer04FillMetrics` when routeable placement stops due to budget.
- Add regression test on large maps verifying budget is respected across both L4 phases.

## Non-goals

- Changing inner group placement algorithm beyond budget enforcement.
- Altering `max_inner_routeable` derivation (`target_routeable_group_count_for_field` minus rim count).
- Stack runner global budget allocation changes.

## Implementation Plan

1. Add optional `budget_ctx: LayerBudgetContext | None = None` to `place_routeable_inner_groups` and `try_place_one_routeable_inner_group` in `inner_routeable_group.py`.
2. At the top of each `max_groups` iteration in `place_routeable_inner_groups`, check `budget_ctx is not None and budget_ctx.remaining_budget_ms() <= 0` and break early, returning groups placed so far.
3. Before the anchor scan loop in `try_place_one_routeable_inner_group`, poll budget once; optionally re-poll every N anchors on large candidate sets (match SHA-31 L3 probe pattern).
4. In `greedy.py` `run_greedy_inner_fill`, pass `budget_ctx` into `place_routeable_inner_groups`.
5. Track whether routeable placement stopped due to budget; merge with existing `budget_interrupted` flag from the 1×1 loop before building `Layer04FillMetrics`.
6. If routeable phase exhausts budget with zero placements and zero 1×1 placements, return `Layer04SkipReason.BUDGET_EXHAUSTED` (existing branch at `greedy.py` lines 122–133).
7. Add unit test in `tests/unit/asteroid_lab/layers/test_layer04_inner_fill_greedy.py`:
   - Use deterministic `now_fn` that advances on each poll so budget expires during routeable loop.
   - Assert `budget_interrupted is True` and routeable group count is less than `max_inner_routeable` when budget is tight.
8. Add large-map regression (reuse `tests/unit/asteroid_lab/layers/fixtures/large_fluid_map.py` or similar) verifying L5/L6 still receive non-zero budget when L4 routeable phase is budget-capped.
9. Run `pytest tests/unit/asteroid_lab/layers/test_layer04_inner_fill_greedy.py -v`.

## Files / Areas Likely Affected

- `src/shapez2_factory/application/asteroid_lab/layers/layer_05_inner_pattern_fill/inner_routeable_group.py`
- `src/shapez2_factory/application/asteroid_lab/layers/layer_05_inner_pattern_fill/greedy.py`
- `tests/unit/asteroid_lab/layers/test_layer04_inner_fill_greedy.py`
- `tests/unit/asteroid_lab/layers/fixtures/large_fluid_map.py` (if large-map regression added)

## Validation Plan

- lint: `ruff check src/shapez2_factory/application/asteroid_lab/layers/layer_05_inner_pattern_fill/`
- typecheck: `mypy django_apps config src` (spot-check touched modules)
- tests: `pytest tests/unit/asteroid_lab/layers/test_layer04_inner_fill_greedy.py -v`
- build: N/A (solver layer only)
- manual verification: `python manage.py run_solver --slug <large-fluid-slug>` with tight `LAYER_STACK_BUDGET_MS` and confirm L5/L6 execute

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Similar fix landed for SHA-31 (L3 rim greedy Phase B); mirror polling cadence for consistency.
- Large-map regression may need injected `now_fn` to avoid flaky timing; prefer deterministic clock over real sleep.
- `Layer04FillMetrics` does not currently distinguish routeable vs 1×1 budget interruption; optional metric field is Low priority (see low plan).
