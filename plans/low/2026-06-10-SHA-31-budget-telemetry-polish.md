---
linear_issue: SHA-31
title: L3 rim greedy placement ignores LayerBudgetContext during Phase B route probe expansion
priority: Low
labels:
  - bug
  - performance
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: L3 Phase B budget telemetry polish

## Source Issue

- Linear: SHA-31
- Status at planning time: Todo
- Priority: Low

## Problem

After Mid-priority budget polling lands for L3 Phase B, operators lack clear observability when budget exhaustion truncates candidate expansion.

## Scope

- Add budget polling instrumentation and logging for Phase B early-exit paths.
- Surface budget-exhausted metrics in layer observability output if not already emitted.

## Non-goals

- Changing budget enforcement logic (covered by Mid plan).
- Altering replay frame schema.

## Implementation Plan

1. After Mid plan merges, identify where Phase B exits on budget exhaustion.
2. Emit `Layer03ExpansionMetrics` or layer observability field recording probes skipped due to budget.
3. Add log/span hook consistent with `stack_runner` layer_done telemetry.
4. Extend existing L3 observability test if metrics contract exists.

## Files / Areas Likely Affected

- `src/shapez2_factory/application/asteroid_lab/layers/layer_03_rim_greedy_placement/candidate_gen.py`
- `src/shapez2_factory/application/asteroid_lab/layers/contracts/layer03_observability.py`
- `tests/unit/shapez2_factory/application/asteroid_lab/layers/layer_03_rim_greedy_placement/` (observability assertions)

## Validation Plan

- lint: `ruff check .`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/shapez2_factory/application/asteroid_lab/layers/layer_03_rim_greedy_placement/ -v`
- build: `python manage.py check`
- manual verification: Inspect layer observability output on budget-bound fixture run.

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Depends on Mid plan (`plans/mid/2026-06-10-SHA-31-l3-phase-b-budget-polling.md`) completing first.
