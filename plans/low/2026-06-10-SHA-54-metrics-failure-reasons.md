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

# Plan: Metrics regression for L5 missing-prerequisite failure_reasons

## Source Issue

- Linear: SHA-54
- Status at planning time: In Progress
- Priority: Low

## Problem

After fixing the fail-open branch, `build_layer05_transport_post_summary_metrics` should surface `failure_reasons` for the missing-prerequisite path so stack_runner post-summary and replay compose diagnostics reflect the typed failure.

## Scope

Add regression test ensuring `build_layer05_transport_post_summary_metrics` includes the expected `failure_reasons` entry when the orchestrator returns a missing-prerequisite failure plan.

## Non-goals

- Changing metrics builder implementation (already maps `plan.failures` to `failure_reasons`)
- stack_runner wiring changes
- UI/replay renderer changes

## Implementation Plan

1. **Depends on:** High and Mid plans applied.
2. In a new or existing test module (e.g. `tests/unit/asteroid_lab/layers/test_layer05_post_summary_metrics.py` or extend stub test file), call `run_layer_05_transport_routing(complete_map=None, exterior_plan=..., rim_result=None)`.
3. Pass result to `build_layer05_transport_post_summary_metrics(plan)`.
4. Assert `metrics["failure_reasons"] == ["empty_l3_package"]` (or chosen reason string from High plan).
5. Assert `metrics["failed_source_count"]` or `route_count` reflect zero routes (no false success signal).
6. Run `pytest tests/unit/asteroid_lab/layers/ -k "post_summary or transport_routing" -v`.

## Files / Areas Likely Affected

- `tests/unit/asteroid_lab/layers/test_layer05_post_summary_metrics.py` (create if absent)
- `src/shapez2_factory/application/asteroid_lab/layers/observability/layer05_post_summary_metrics.py` (read-only)
- `src/shapez2_factory/application/asteroid_lab/layers/observability/layer04_post_summary_metrics.py` (read-only)

## Validation Plan

- tests: `pytest tests/unit/asteroid_lab/layers/ -k "post_summary" -v`
- lint: `ruff check tests/unit/asteroid_lab/layers/`

## Acceptance Criteria

- [ ] Metrics regression added for `failure_reasons` on missing-prerequisite path
- [ ] Matches the source issue spec
- [ ] Stays within the priority scope
- [ ] No unrelated behavior is changed

## Risks / Open Questions

- If no dedicated metrics test file exists, prefer a focused new file over bloating stub tests.
