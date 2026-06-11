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

# Plan: Fail-closed when complete_map or rim_result missing

## Source Issue

- Linear: SHA-54
- Priority: High

## Problem

`run_layer_05_transport_routing` returns `Layer04RoutePlan.empty()` with zero failures when `complete_map` or `rim_result` is None, unlike `exterior_plan is None` which emits `MISSING_L2_EXTERIOR_PLAN`.

## Scope

Return typed `Layer05Failure` instead of failure-free empty plan.

## Implementation Plan

1. Read `run.py` lines 54–76 early return branch.
2. Replace fail-open with failure plan using `EMPTY_L3_PACKAGE` or dedicated enum value.
3. Repro: `run_layer_05_transport_routing(complete_map=None, exterior_plan=<obj>, rim_result=None)` must have non-empty `failures`.

## Files / Areas Likely Affected

- `src/shapez2_factory/application/asteroid_lab/layers/layer_04_transport_routing/run.py`
- `src/shapez2_factory/domain/asteroid_lab/layer05_route.py`

## Acceptance Criteria

- [ ] Missing prerequisites emit typed failure.

## Risks / Open Questions

- Pick correct enum — align with transport routing spec.
