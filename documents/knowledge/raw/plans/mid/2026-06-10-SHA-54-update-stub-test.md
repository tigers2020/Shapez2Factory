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

# Plan: Update layer04 transport routing stub test

## Source Issue

- Linear: SHA-54
- Priority: Mid

## Scope

Fix `test_layer04_transport_routing_stub_returns_empty_plan` which masks contract gap.

## Implementation Plan

1. Update test to assert failure when map/rim missing.
2. Keep success empty-plan case only when inputs valid.
3. Run `pytest tests/unit/asteroid_lab/layers/test_layer04_transport_routing_stub.py -v`.

## Files / Areas Likely Affected

- `tests/unit/asteroid_lab/layers/test_layer04_transport_routing_stub.py`

## Acceptance Criteria

- [ ] Stub test asserts failure contract.
