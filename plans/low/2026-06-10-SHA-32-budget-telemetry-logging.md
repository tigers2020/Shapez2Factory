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

# Plan: L4 routeable-phase budget telemetry and logging polish

## Source Issue

- Linear: SHA-32
- Status at planning time: Todo
- Priority: Low

## Problem

After SHA-32 mid-priority work wires budget polling into `place_routeable_inner_groups`, operators lack visibility into whether L4 budget exhaustion happened during the routeable inner-group phase versus the 1×1 greedy loop. Post-summary metrics and replay observability do not distinguish the two phases today.

## Scope

- Extend L4 post-summary / replay metrics to record routeable-phase budget interruption when applicable.
- Optional debug logging at routeable-loop early exit (behind existing observability patterns).

## Non-goals

- Changing budget enforcement logic (covered by mid-priority plan).
- Adding new replay event types unless required by existing post-summary contract.
- UI changes in Django Lab viewer.

## Implementation Plan

1. After mid plan lands, inspect `build_layer04_inner_fill_post_summary_metrics` in `post_summary_metrics.py` for `budget_interrupted` fields.
2. Add metric key (e.g. `routeable_budget_interrupted` or phase-qualified `budget_interrupted_phase`) when routeable loop exits due to budget.
3. Thread flag from `Layer04FillMetrics` or greedy result if not already distinguishable.
4. Update `test_layer04_post_summary_metrics_partial_fill_budget_interrupted` (or add sibling) to assert new key when routeable phase triggers interruption.
5. Run `pytest tests/unit/asteroid_lab/layers/test_layer04_inner_fill_greedy.py -v`.

## Files / Areas Likely Affected

- `src/shapez2_factory/application/asteroid_lab/layers/observability/post_summary_metrics.py`
- `src/shapez2_factory/application/asteroid_lab/layers/contracts/layer04_inner_fill.py`
- `tests/unit/asteroid_lab/layers/test_layer04_inner_fill_greedy.py`
- `django_apps/asteroid_lab/services/solver_run_lab_summary.py` (if lab summary surfaces L4 metrics)

## Validation Plan

- lint: `ruff check src/shapez2_factory/application/asteroid_lab/layers/observability/`
- typecheck: `mypy django_apps config src` (spot-check)
- tests: `pytest tests/unit/asteroid_lab/layers/test_layer04_inner_fill_greedy.py -v`
- build: N/A
- manual verification: Inspect solver_summary / post-summary row for routeable-phase budget flag after forced exhaustion

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Depends on mid-priority SHA-32 implementation completing first.
- Metric naming should align with SHA-31/SHA-14 budget telemetry if those add similar phase keys.
