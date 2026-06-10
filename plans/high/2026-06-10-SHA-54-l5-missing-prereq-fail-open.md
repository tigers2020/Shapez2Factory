---
linear_issue: SHA-54
title: L5 transport run.py returns failure-free empty plan when complete_map or rim_result is missing
priority: High
labels:
  - bug
  - solver
  - spec
  - test
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Fail-closed L5 transport when map/rim prerequisites missing (SHA-54 High)

## Source Issue

- Linear: SHA-54
- Status at planning time: In Progress
- Priority: High

## Problem

`run_layer_05_transport_routing` fail-open when `complete_map is None` or `rim_result is None`: returns `Layer04RoutePlan.empty()` with zero `failures`. Callers see success-like empty route plan instead of typed failure, breaking observability and replay compose diagnostics.

## Scope

Align orchestrator prerequisite handling with sequential router and L5 failure enum. Mid plan implements typed failures and test updates.

## Non-goals

- LayerBudgetContext polling (SHA-14).
- stack_runner SUCCESS when L2 returns None (SHA-34).

## Implementation Plan

1. Reproduce via `python3 -c` or unit test: `run_layer_05_transport_routing(complete_map=None, exterior_plan=<obj>, rim_result=None)` → `failures=[]` today.
2. After Mid fix, same call emits appropriate `Layer05Failure` in plan.failures.
3. Verify `build_layer05_transport_post_summary_metrics` surfaces `failure_reasons` (Low plan).

## Files / Areas Likely Affected

- `src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/run.py`
- `tests/unit/asteroid_lab/layers/test_layer04_transport_routing_stub.py`

## Validation Plan

- tests: stub + metrics regressions in Mid/Low plans
- manual verification: repro script shows typed failure

## Acceptance Criteria

- [ ] Missing `complete_map` or `rim_result` emits typed failure, not empty success plan.
- [ ] Failure reason aligned with L5 enum and transport routing spec.

## Risks / Open Questions

- Choose between reusing `EMPTY_L3_PACKAGE` vs dedicated missing-input reason per spec `docs/superpowers/specs/2026-05-31-layer-04-transport-routing-design.md`.
