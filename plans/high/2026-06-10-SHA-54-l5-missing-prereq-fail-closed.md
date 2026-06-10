---
linear_issue: SHA-54
title: L5 transport run.py returns failure-free empty plan when complete_map or rim_result is missing
priority: High
labels:
  - priority:mid
  - test
  - bug
  - solver
  - spec
status: planned
created_by: todo-plan-automation
---

# Plan: L5 transport orchestrator fail-closed on missing map/rim prerequisites

## Source Issue

- Linear: SHA-54
- Status at planning time: Todo
- Priority: High

## Problem

`run_layer_05_transport_routing` returns `Layer04RoutePlan.empty()` with zero `failures` when `complete_map is None` or `rim_result is None`, while the same entrypoint fail-closes for `exterior_plan is None` (`MISSING_L2_EXTERIOR_PLAN`) and `route_layer04_sequential` fail-closes for empty L3 sources (`EMPTY_L3_PACKAGE`). Callers that omit map/rim inputs see a success-like empty route plan instead of a typed failure, breaking observability and replay compose diagnostics.

## Scope

Replace the `complete_map is None or rim_result is None` early-return branch in `run_layer_05_transport_routing` with a failure-bearing `Layer04RoutePlan` aligned to `Layer05FailureReason` and transport routing spec.

## Non-goals

- LayerBudgetContext polling (SHA-14)
- stack_runner SUCCESS semantics when L2 returns None (SHA-34)
- Changing sequential A* routing logic beyond prerequisite guards
- Adding new routing heuristics or catalog behavior

## Implementation Plan

1. In `run.py`, after the `exterior_plan is None` guard and resource_kind resolution, replace lines 74–76 (`Layer04RoutePlan.empty(...)`) with explicit failure plan construction mirroring the `MISSING_L2_EXTERIOR_PLAN` pattern.
2. When `rim_result is None`, emit `Layer04Failure(reason=Layer04FailureReason.EMPTY_L3_PACKAGE)` — consistent with `route_layer04_sequential` empty-source path.
3. When `complete_map is None` (with `rim_result` present), emit a typed failure: prefer reusing `EMPTY_L3_PACKAGE` if spec-aligned, otherwise add a dedicated `Layer05FailureReason` only after confirming against `docs/superpowers/specs/2026-05-31-layer-04-transport-routing-design.md` § failure enum.
4. Preserve `resource_kind` and derived `transport_kind` on the failure plan (same as current empty branch).
5. Repro before/after: `python3 -c` call with `complete_map=None, exterior_plan=<obj>, rim_result=None` must return `len(plan.failures) == 1`.

## Files / Areas Likely Affected

- `src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/run.py`
- `src/shapez2_factory/application/asteroid_lab/layers/contracts/layer05_route.py` (only if new failure reason required)
- `docs/superpowers/specs/2026-05-31-layer-04-transport-routing-design.md` (reference only unless enum extended)

## Validation Plan

- lint: `ruff check src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/run.py`
- typecheck: `mypy django_apps config src` (spot-check transport routing module)
- tests: `pytest tests/unit/asteroid_lab/layers/test_layer04_transport_routing_stub.py -v`
- build: `python manage.py check`
- manual verification: repro snippet from issue description shows typed failure, not empty success plan

## Acceptance Criteria

- [ ] Missing `complete_map` or `rim_result` emits typed failure, not empty success plan
- [ ] Failure reason aligned with L5 enum and transport routing spec
- [ ] Stays within the priority scope (orchestrator guard only)
- [ ] Required validation passes or failures are documented
- [ ] Sequential router behavior unchanged beyond prerequisite guards

## Risks / Open Questions

- Whether `complete_map is None` warrants a new enum member vs reusing `EMPTY_L3_PACKAGE` — confirm against spec before adding enum.
- `Layer04FailureReason` is an alias of `Layer05FailureReason`; keep imports consistent with surrounding `run.py` code.
