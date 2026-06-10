---
linear_issue: SHA-54
title: L5 transport run.py returns failure-free empty plan when complete_map or rim_result is missing
priority: Low
labels:
  - priority:mid
  - test
  - reviewing
  - bug
  - solver
  - spec
status: planned
created_by: todo-plan-automation
---

# Plan: L5 metrics failure_reasons regression

## Source Issue

- Linear: SHA-54
- Status at planning time: Todo
- Priority: Low

## Problem

Metrics regression for `failure_reasons` on this path.

## Scope

Add regression ensuring `build_layer05_transport_post_summary_metrics` surfaces `failure_reasons` when `complete_map` or `rim_result` is missing.

## Non-goals

- LayerBudgetContext polling (SHA-14).
- stack_runner SUCCESS semantics when L2 returns None (SHA-34).
- Changing sequential A* routing logic beyond prerequisite guards.

## Implementation Plan

1. Identify metrics builder entry point for L5 transport post-summary (`build_layer05_transport_post_summary_metrics`).
2. Add unit test: invoke `run_layer_05_transport_routing` with missing `complete_map` or `rim_result` → feed result into metrics builder.
3. Assert `failure_reasons` includes the typed enum value from the Mid fix.
4. Confirm metrics for successful sequential routing paths unchanged.

## Files / Areas Likely Affected

- `tests/unit/asteroid_lab/layers/test_layer04_transport_routing_stub.py` (or dedicated metrics test module)
- `src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/run.py` (test target reference)

## Validation Plan

- lint: `ruff check .`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/asteroid_lab/layers/test_layer04_transport_routing_stub.py -v`
- build: N/A
- manual verification: N/A

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Depends on High/Mid typed-failure implementation landing first.
- Metrics test location may need a new test file if stub module scope is too narrow.
