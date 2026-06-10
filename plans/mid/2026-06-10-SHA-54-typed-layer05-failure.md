---
linear_issue: SHA-54
title: L5 transport run.py returns failure-free empty plan when complete_map or rim_result is missing
priority: Mid
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

# Plan: Typed Layer05Failure for missing prerequisites

## Source Issue

- Linear: SHA-54
- Status at planning time: Todo
- Priority: Mid

## Problem

Replace fail-open branch with typed `Layer05Failure`; update stub test to assert failure contract.

## Scope

Replace the `complete_map is None or rim_result is None` early-return in `run_layer_05_transport_routing` with a failure-bearing plan, and update the stub unit test that currently masks the contract gap.

## Non-goals

- LayerBudgetContext polling (SHA-14).
- stack_runner SUCCESS semantics when L2 returns None (SHA-34).
- Changing sequential A* routing logic beyond prerequisite guards.

## Implementation Plan

1. In `run.py` lines 54–76, replace `Layer04RoutePlan.empty()` return with a plan carrying `Layer05Failure` (likely `EMPTY_L3_PACKAGE` when `rim_result is None`; evaluate dedicated reason for `complete_map is None`).
2. Keep `exterior_plan is None` → `MISSING_L2_EXTERIOR_PLAN` path unchanged.
3. Update `test_layer04_transport_routing_stub_returns_empty_plan` to assert typed failure instead of failure-free empty output.
4. Confirm `route_layer04_sequential` behavior unchanged beyond prerequisite guards.

## Files / Areas Likely Affected

- `src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/run.py`
- `src/shapez2_factory/domain/asteroid_lab/layer05_route.py`
- `tests/unit/asteroid_lab/layers/test_layer04_transport_routing_stub.py`

## Validation Plan

- lint: `ruff check .`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/asteroid_lab/layers/test_layer04_transport_routing_stub.py -v`
- build: `python manage.py check`
- manual verification: N/A

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Overlaps High plan — implement together in one PR if practical.
- Low plan adds metrics regression for `failure_reasons`.
