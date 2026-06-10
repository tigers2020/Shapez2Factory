---
linear_issue: SHA-32
title: L4 inner fill ignores LayerBudgetContext during routeable inner group placement
priority: Low
labels:
  - bug
  - performance
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: L4 routeable group budget telemetry

## Source Issue

- Linear: SHA-32
- Status at planning time: Todo
- Priority: Low

## Problem

After Mid-priority budget polling for `place_routeable_inner_groups`, operators need telemetry when budget exhaustion truncates routeable inner group placement.

## Scope

- Add budget telemetry and logging for routeable inner group early-exit paths.

## Non-goals

- Changing budget enforcement (Mid plan).
- Altering `max_inner_routeable` policy.

## Implementation Plan

1. After Mid plan merges, instrument budget-exhausted exit in `place_routeable_inner_groups`.
2. Emit layer metrics or observability field for groups skipped due to budget.
3. Add or extend unit test asserting metric presence on forced budget exhaustion.

## Files / Areas Likely Affected

- `src/shapez2_factory/application/asteroid_lab/layers/layer_05_inner_pattern_fill/inner_routeable_group.py`
- `src/shapez2_factory/application/asteroid_lab/layers/layer_05_inner_pattern_fill/greedy.py`
- `tests/unit/shapez2_factory/application/asteroid_lab/layers/layer_05_inner_pattern_fill/`

## Validation Plan

- lint: `ruff check .`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/shapez2_factory/application/asteroid_lab/layers/layer_05_inner_pattern_fill/ -v`
- build: `python manage.py check`
- manual verification: TBD

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Depends on Mid plan (`plans/mid/2026-06-10-SHA-32-l4-routeable-budget-polling.md`).
