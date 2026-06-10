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

# Plan: L4 routeable inner fill budget telemetry (SHA-32 Low)

## Source Issue

- Linear: SHA-32
- Status at planning time: In Progress
- Priority: Low

## Problem

After Mid-priority budget polling is wired into `place_routeable_inner_groups`, operators lack visibility into how many routeable placements were skipped due to budget vs placement exhaustion.

## Scope

- Add optional metrics/logging for routeable-phase budget skips (e.g. `routeable_budget_skipped_count` or post-summary field).
- Document new metric in L4 post-summary observability if added.

## Non-goals

- Changing placement algorithm.
- Stack runner budget contract changes.
- Replay schema version bump unless canon requires it.

## Implementation Plan

1. After Mid fix is verified, evaluate whether `Layer04FillMetrics` needs a `routeable_budget_skipped_count` or similar counter.
2. If useful, increment when `place_routeable_inner_groups` breaks on budget before reaching `max_groups`.
3. Surface in `build_layer04_inner_fill_post_summary_metrics` for replay/NDJSON observability.
4. Add test asserting metric appears when budget forces early exit.

## Files / Areas Likely Affected

- `src/shapez2_factory/application/asteroid_lab/layers/contracts/layer04_inner_fill.py`
- `src/shapez2_factory/application/asteroid_lab/layers/observability/post_summary_metrics.py`
- `tests/unit/asteroid_lab/layers/test_layer04_inner_fill_greedy.py`

## Validation Plan

- lint: `ruff check src/shapez2_factory/application/asteroid_lab/layers/`
- typecheck: `mypy django_apps config src` (spot-check)
- tests: `pytest tests/unit/asteroid_lab/layers/test_layer04_inner_fill_greedy.py -k budget -v`
- build: N/A
- manual verification: inspect L4 post-summary in solver run output

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Optional; defer until Mid fix is merged and validated.
- Replay schema change may require version bump — check `docs/superpowers/specs/2026-06-08-l4-inner-pattern-fill-contract.md` before adding fields.
