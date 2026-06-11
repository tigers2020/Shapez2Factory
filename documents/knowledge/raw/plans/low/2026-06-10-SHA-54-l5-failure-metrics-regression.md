---
linear_issue: SHA-54
title: L5 transport run.py returns failure-free empty plan when complete_map or rim_result is missing
priority: Low
labels:
  - bug
  - solver
  - spec
  - test
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Metrics regression for L5 missing-prerequisite failures (SHA-54 Low)

## Source Issue

- Linear: SHA-54
- Status at planning time: In Progress
- Priority: Low

## Problem

Even after typed failures are returned from `run_layer_05_transport_routing`, compose/replay metrics may not surface `failure_reasons` on this path unless explicitly tested.

## Scope

Add regression ensuring `build_layer05_transport_post_summary_metrics` surfaces `failure_reasons` when map/rim prerequisites are missing.

## Non-goals

- Changing metrics schema beyond asserting existing `failure_reasons` wire.

## Implementation Plan

1. Locate `build_layer05_transport_post_summary_metrics` and existing tests for L5 post-summary metrics.
2. Add unit test: run orchestrator with missing `rim_result` or `complete_map`, pass result into metrics builder, assert `failure_reasons` contains expected enum value.
3. Run targeted pytest for metrics module.

## Files / Areas Likely Affected

- L5 metrics builder module (TBD — grep `build_layer05_transport_post_summary_metrics`)
- `tests/unit/asteroid_lab/layers/` (new or extended test)

## Validation Plan

- tests: new metrics regression green with Mid plan

## Acceptance Criteria

- [ ] Metrics regression added for `failure_reasons` on missing-prerequisite path.
- [ ] Stays within Low scope.

## Risks / Open Questions

- Exact metrics module path to confirm at implementation time via repo search.
