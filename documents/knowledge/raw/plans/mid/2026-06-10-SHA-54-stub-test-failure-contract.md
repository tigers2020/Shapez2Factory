---
linear_issue: SHA-54
title: L5 transport run.py returns failure-free empty plan when complete_map or rim_result is missing
priority: Mid
labels:
  - priority:mid
  - test
  - bug
  - solver
  - spec
status: planned
created_by: todo-plan-automation
---

# Plan: Update L5 transport stub tests for missing-prerequisite failure contract

## Source Issue

- Linear: SHA-54
- Status at planning time: Todo
- Priority: Mid

## Problem

`test_layer04_transport_routing_stub_returns_empty_plan` asserts failure-free empty output when `complete_map=None` and `rim_result=None`, masking the orchestrator fail-open contract gap. After the orchestrator fix lands, this test must assert typed failures instead.

## Scope

Update stub unit tests in `test_layer04_transport_routing_stub.py` to lock the fail-closed contract for missing `complete_map` and `rim_result` prerequisites.

## Non-goals

- Sequential router integration tests (unchanged beyond prerequisite guards)
- stack_runner or replay compose wiring
- Metrics regression (covered in Low-priority plan)

## Implementation Plan

1. Rename or repurpose `test_layer04_transport_routing_stub_returns_empty_plan` to assert failure contract (e.g. `test_layer04_transport_routing_missing_map_or_rim_failure`).
2. Assert `len(plan.failures) == 1` and `plan.failures[0].reason is Layer04FailureReason.EMPTY_L3_PACKAGE` when both `complete_map=None` and `rim_result=None`.
3. Add separate cases if orchestrator distinguishes `complete_map=None` vs `rim_result=None` failure reasons.
4. Keep `test_layer04_transport_routing_missing_exterior_plan_failure` unchanged (already correct).
5. Run `pytest tests/unit/asteroid_lab/layers/test_layer04_transport_routing_stub.py -v` and confirm all pass after orchestrator fix.

## Files / Areas Likely Affected

- `tests/unit/asteroid_lab/layers/test_layer04_transport_routing_stub.py`

## Validation Plan

- lint: `ruff check tests/unit/asteroid_lab/layers/test_layer04_transport_routing_stub.py`
- typecheck: `mypy django_apps config src` (spot-check)
- tests: `pytest tests/unit/asteroid_lab/layers/test_layer04_transport_routing_stub.py -v`
- build: n/a
- manual verification: n/a

## Acceptance Criteria

- [ ] Stub test updated; asserts failure contract not failure-free empty plan
- [ ] Matches the source issue spec acceptance criteria for test coverage
- [ ] Stays within the priority scope (stub tests only)
- [ ] Required validation passes or failures are documented
- [ ] No unrelated behavior is changed

## Risks / Open Questions

- Test must land after or alongside orchestrator fix — TDD order: update test first (expect fail), then fix `run.py`.
- If `complete_map` and `rim_result` get distinct failure reasons, split assertions per case.
