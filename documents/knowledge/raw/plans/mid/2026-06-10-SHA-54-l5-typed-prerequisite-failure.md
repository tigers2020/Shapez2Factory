---
linear_issue: SHA-54
title: L5 transport run.py returns failure-free empty plan when complete_map or rim_result is missing
priority: Mid
labels:
  - bug
  - solver
  - spec
  - test
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Replace L5 fail-open branch with typed Layer05Failure (SHA-54 Mid)

## Source Issue

- Linear: SHA-54
- Status at planning time: In Progress
- Priority: Mid

## Problem

`run.py` lines 54–76 return empty plan without failures when `complete_map is None or rim_result is None`, while `exterior_plan is None` correctly returns `MISSING_L2_EXTERIOR_PLAN`.

## Scope

Replace fail-open branch with failure plan using `Layer05FailureReason` (likely `EMPTY_L3_PACKAGE` when `rim_result is None`; dedicated or existing reason when `complete_map is None`). Update stub test to assert failure contract.

## Non-goals

- Changing sequential A* routing beyond prerequisite guards.
- SHA-14 budget context or SHA-34 stack runner semantics.

## Implementation Plan

1. Read `run_layer_05_transport_routing` in `src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/run.py` and `Layer05FailureReason` in `layer05_route.py`.
2. Replace `complete_map is None or rim_result is None` early return with failure plan construction mirroring `exterior_plan is None` pattern.
3. Update `test_layer04_transport_routing_stub_returns_empty_plan` in `tests/unit/asteroid_lab/layers/test_layer04_transport_routing_stub.py` to assert failures for missing map/rim inputs.
4. Run `pytest tests/unit/asteroid_lab/layers/test_layer04_transport_routing_stub.py -v`.

## Files / Areas Likely Affected

- `src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/run.py`
- `src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/sequential_router.py` (reference)
- `tests/unit/asteroid_lab/layers/test_layer04_transport_routing_stub.py`
- `docs/superpowers/specs/2026-05-31-layer-04-transport-routing-design.md`

## Validation Plan

- tests: `pytest tests/unit/asteroid_lab/layers/test_layer04_transport_routing_stub.py -v`
- typecheck: `mypy src`
- lint: `ruff check src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/`

## Acceptance Criteria

- [ ] Missing `complete_map` or `rim_result` emits typed failure, not empty success plan.
- [ ] Stub test updated; metrics regression added (Low plan).
- [ ] Sequential router behavior unchanged beyond prerequisite guards.

## Risks / Open Questions

- Enum choice must match transport routing spec and existing sequential router `EMPTY_L3_PACKAGE` usage.
