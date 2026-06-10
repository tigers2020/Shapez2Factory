---
linear_issue: SHA-54
title: L5 transport run.py returns failure-free empty plan when complete_map or rim_result is missing
priority: High
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

# Plan: L5 fail-open empty plan observability fix

## Source Issue

- Linear: SHA-54
- Status at planning time: Todo
- Priority: High

## Problem

Missing prerequisites return failure-free empty plan — breaks observability and replay compose diagnostics.

## Scope

Align `run_layer_05_transport_routing` so missing `complete_map` or `rim_result` emits a typed `Layer05Failure` instead of `Layer04RoutePlan.empty()` with zero failures, restoring caller-visible failure signals.

## Non-goals

- LayerBudgetContext polling (SHA-14).
- stack_runner SUCCESS semantics when L2 returns None (SHA-34).
- Changing sequential A* routing logic beyond prerequisite guards.

## Implementation Plan

1. Reproduce: `run_layer_05_transport_routing(complete_map=None, exterior_plan=<obj>, rim_result=None)` → confirm `failures=[]`.
2. Compare with `exterior_plan=None` path (`MISSING_L2_EXTERIOR_PLAN`) and `route_layer04_sequential` empty-sources path (`EMPTY_L3_PACKAGE`).
3. Replace the `complete_map is None or rim_result is None` fail-open branch with a failure plan using appropriate `Layer05FailureReason` enum values.
4. Verify `build_layer05_transport_post_summary_metrics` surfaces `failure_reasons` for the corrected path.

## Files / Areas Likely Affected

- `src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/run.py`
- `src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/sequential_router.py`
- `src/shapez2_factory/domain/asteroid_lab/layer05_route.py` (`Layer05FailureReason`)
- `docs/superpowers/specs/2026-05-31-layer-04-transport-routing-design.md`

## Validation Plan

- lint: `ruff check .`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/asteroid_lab/layers/test_layer04_transport_routing_stub.py -v`
- build: `python manage.py check`
- manual verification: `python3 -c` repro — missing map/rim inputs return typed failure, not empty success plan

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Whether `EMPTY_L3_PACKAGE` covers both `rim_result is None` and `complete_map is None`, or a dedicated reason is needed.
- Mid plan updates stub test; Low plan adds metrics regression.
