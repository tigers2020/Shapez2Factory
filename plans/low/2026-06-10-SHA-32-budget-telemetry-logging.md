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

# Plan: L4 routeable inner group budget telemetry and logging

## Source Issue

- Linear: SHA-32
- Status at planning time: In Progress (moved before plan creation)
- Priority: Low

## Problem

When L4 routeable inner group placement consumes stack budget, there is limited telemetry to diagnose how many groups were placed before interruption versus budget exhaustion in the 1×1 loop.

## Scope

- Add optional metrics/logging for budget interruption during routeable inner group phase.
- Improve debuggability without changing placement algorithm.

## Non-goals

- Core budget polling fix (Mid plan).
- Changing `max_inner_routeable` derivation.

## Implementation Plan

1. Extend `Layer04FillMetrics` (or layer debug payload) with routeable-phase counters: `routeable_groups_placed`, `routeable_budget_interrupted`.
2. Surface counts in existing layer result / replay metadata if contract allows.
3. Add test asserting metrics populated when budget forces early exit in routeable phase.

## Files / Areas Likely Affected

- `src/shapez2_factory/application/asteroid_lab/layers/contracts/layer04_inner_fill.py`
- `src/shapez2_factory/application/asteroid_lab/layers/layer_05_inner_pattern_fill/greedy.py`
- `tests/unit/asteroid_lab/layers/test_layer04_inner_fill_greedy.py`

## Validation Plan

- tests: extend greedy inner fill tests for new metric fields
- manual verification: replay/debug output shows routeable budget stop reason

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Contract change to `Layer04FillMetrics` may affect replay DTOs — verify serialization boundaries before adding fields.
