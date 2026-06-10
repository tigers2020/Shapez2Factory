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

# Plan: Metrics regression for failure_reasons on missing prereq path

## Source Issue

- Linear: SHA-54
- Priority: Low

## Scope

Ensure `build_layer05_transport_post_summary_metrics` surfaces `failure_reasons` for missing map/rim path.

## Implementation Plan

1. Add test calling metrics builder after fail-closed plan.
2. Assert `failure_reasons` non-empty.

## Files / Areas Likely Affected

- TBD — metrics builder module for L5 transport post summary
- `tests/unit/asteroid_lab/layers/` (new or extended test)

## Acceptance Criteria

- [ ] Metrics regression added per issue spec.

## Risks / Open Questions

- Exact metrics module path to confirm during implementation.
