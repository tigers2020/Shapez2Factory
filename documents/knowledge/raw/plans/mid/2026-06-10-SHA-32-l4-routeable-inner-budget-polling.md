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

Layer 04 inner pattern fill (`layer_05_inner_pattern_fill`) accepts `LayerBudgetContext` from `stack_runner` and polls remaining budget only in the 1×1 greedy placement loop. The preceding `place_routeable_inner_groups` phase runs up to `max_inner_routeable` iterations without any budget polling.

## Scope

- Add budget polling to `place_routeable_inner_groups` phase.
- Ensure consistent budget enforcement across all L4 placement loops.

## Non-goals

- Changing inner group placement algorithm beyond budget enforcement.
- Altering `max_inner_routeable` derivation.

## Implementation Plan

1. Pass `LayerBudgetContext` into `place_routeable_inner_groups` in `inner_routeable_group.py` (currently called from `greedy.py` without budget checks in the routeable phase).
2. Poll `remaining_budget_ms()` before each iteration and candidate scan; exit early with partial groups when budget exhausted.
3. Align interruption semantics with existing 1×1 greedy loop `budget_interrupted` pattern in the same module.
4. Add regression test on large maps (e.g. ~130 routeable groups) with capped budget verifying L5–L6 still execute.
5. Run `pytest tests/unit/asteroid_lab/layers/ -k inner -v`.

## Files / Areas Likely Affected

- `src/shapez2_factory/application/asteroid_lab/layers/layer_05_inner_pattern_fill/inner_routeable_group.py`
- `src/shapez2_factory/application/asteroid_lab/layers/layer_05_inner_pattern_fill/greedy.py`
- `src/shapez2_factory/application/asteroid_lab/stack_runner.py`
- `tests/unit/asteroid_lab/layers/` (inner pattern fill tests — TBD exact module)

## Validation Plan

- lint: `ruff check src/shapez2_factory/application/asteroid_lab/layers/layer_05_inner_pattern_fill/`
- typecheck: `mypy django_apps config src` (spot-check)
- tests: `pytest tests/unit/asteroid_lab/layers/ -k inner -v`
- build: N/A
- manual verification: Capped-budget stack run reaches L5/L6 on large inner-fill fixture

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Module directory `layer_05_inner_pattern_fill` vs L4 slug renumber — follow canon naming in code.
- Coordinate with SHA-31/SHA-14 budget patterns for consistent layer failure metadata.
