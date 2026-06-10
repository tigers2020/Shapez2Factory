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

# Plan: Fail-closed L5 transport routing when map or rim prerequisites are missing

## Source Issue

- Linear: SHA-54
- Status at planning time: In Progress (moved from Todo after prior automation pass)
- Priority: High

## Problem

`run_layer_05_transport_routing` fail-open when `complete_map is None` or `rim_result is None`: it returns `Layer04RoutePlan.empty()` with zero `failures`. The same entrypoint fail-closed for `exterior_plan is None` (`MISSING_L2_EXTERIOR_PLAN`), and `route_layer04_sequential` fail-closed for an empty L3 source list (`EMPTY_L3_PACKAGE`). Callers that omit map/rim inputs therefore see a success-like empty route plan instead of a typed failure, breaking observability and replay compose diagnostics.

## Scope

Replace the `complete_map is None or rim_result is None` branch in `run_layer_05_transport_routing` so missing prerequisites emit a typed `Layer05Failure` instead of `Layer04RoutePlan.empty()`.

## Non-goals

- LayerBudgetContext polling (SHA-14)
- stack_runner SUCCESS semantics when L2 returns None (SHA-34)
- Changing sequential A* routing logic beyond prerequisite guards

## Implementation Plan

1. Open `src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/run.py` and locate lines 74–76 (`if complete_map is None or rim_result is None`).
2. Replace `Layer04RoutePlan.empty(...)` with a failure-bearing plan mirroring the `exterior_plan is None` branch (lines 54–68).
3. Use `EMPTY_L3_PACKAGE` when `rim_result is None` (no L3 source package to route). When `complete_map is None` but `rim_result` is present, use `EMPTY_L3_PACKAGE` or document a dedicated reason if spec requires split semantics — align with `docs/superpowers/specs/2026-05-31-layer-04-transport-routing-design.md`.
4. Preserve `resource_kind` / `transport_kind` derivation (`space_belt` vs `space_pipe`) on the failure plan.
5. Reproduce pre-fix behavior with `python3 -c` snippet from issue; confirm post-fix returns `failures` with typed reason.

## Files / Areas Likely Affected

- `src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/run.py`
- `src/shapez2_factory/application/asteroid_lab/layers/contracts/layer05_route.py` (read-only unless new enum needed)
- `docs/superpowers/specs/2026-05-31-layer-04-transport-routing-design.md` (authority for failure reason choice)

## Validation Plan

- lint: `ruff check src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/run.py`
- typecheck: `mypy django_apps config src` (spot-check transport routing module)
- tests: `pytest tests/unit/asteroid_lab/layers/test_layer04_transport_routing_stub.py -v`
- manual verification: `python3 -c` repro from issue — `complete_map=None, rim_result=None` must return non-empty `failures`

## Acceptance Criteria

- [ ] Missing `complete_map` or `rim_result` emits typed failure, not empty success plan
- [ ] Failure reason aligned with L5 enum and transport routing spec
- [ ] Matches the source issue spec
- [ ] Stays within the priority scope
- [ ] No unrelated behavior is changed

## Risks / Open Questions

- Whether `complete_map is None` and `rim_result is None` share `EMPTY_L3_PACKAGE` or need distinct reasons — issue suggests `EMPTY_L3_PACKAGE` for rim; confirm against spec before adding a new enum value.
