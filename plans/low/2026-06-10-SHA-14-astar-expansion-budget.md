---
linear_issue: SHA-14
title: L5 transport routing ignores LayerBudgetContext during sequential A* routing
priority: Low
labels:
  - bug
  - solver
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: A* expansion-level budget polling (SHA-14 Low)

## Source Issue

- Linear: SHA-14
- Priority: Low

## Scope

Optional finer-grained budget polling inside A* expansion loop (beyond per-source check).

## Implementation Plan

1. Evaluate if per-source polling insufficient after Mid fix.
2. Add expansion-level poll only if regression tests show need.

## Files / Areas Likely Affected

- `src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/sequential_router.py`

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Optional; defer after Mid.
