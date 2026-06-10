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

# Plan: Update L5 transport stub test to assert missing-prerequisite failure contract

## Source Issue

- Linear: SHA-54
- Status at planning time: In Progress
- Priority: Mid

## Problem

`test_layer04_transport_routing_stub_returns_empty_plan` asserts failure-free empty output when `complete_map=None` and `rim_result=None`, masking the orchestrator fail-open contract gap. After the High-priority fix lands, this test must assert the typed failure contract instead.

## Scope

Update stub test and add explicit coverage for missing `complete_map` and missing `rim_result` paths separately if behavior diverges.

## Non-goals

- Metrics regression (Low plan)
- Sequential router test changes beyond prerequisite guards
- stack_runner integration tests

## Implementation Plan

1. **Depends on:** `plans/high/2026-06-10-SHA-54-l5-missing-prereq-failure.md` implementation merged or applied first.
2. Rename or repurpose `test_layer04_transport_routing_stub_returns_empty_plan` to assert `len(plan.failures) >= 1` and `plan.failures[0].reason is Layer04FailureReason.EMPTY_L3_PACKAGE` (or chosen reason from High plan).
3. Add parametrized or separate tests:
   - `complete_map=None, rim_result=<valid stub>, exterior_plan=<obj>` → typed failure
   - `complete_map=<valid stub>, rim_result=None, exterior_plan=<obj>` → typed failure
4. Keep `test_layer04_transport_routing_missing_exterior_plan_failure` unchanged (already asserts `MISSING_L2_EXTERIOR_PLAN`).
5. Run `pytest tests/unit/asteroid_lab/layers/test_layer04_transport_routing_stub.py -v` — all pass.

## Files / Areas Likely Affected

- `tests/unit/asteroid_lab/layers/test_layer04_transport_routing_stub.py`
- `src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/run.py` (from High plan)

## Validation Plan

- lint: `ruff check tests/unit/asteroid_lab/layers/test_layer04_transport_routing_stub.py`
- tests: `pytest tests/unit/asteroid_lab/layers/test_layer04_transport_routing_stub.py -v`
- typecheck: spot-check only if test helpers need new imports

## Acceptance Criteria

- [ ] Stub test updated; asserts failure contract not empty success plan
- [ ] Matches the source issue spec
- [ ] Stays within the priority scope
- [ ] Required validation passes or failures are documented
- [ ] Sequential router behavior unchanged beyond prerequisite guards

## Risks / Open Questions

- Test may need minimal stub objects for `rim_result` / `complete_map` — reuse patterns from `test_layer04_sequential_router.py` if available.
