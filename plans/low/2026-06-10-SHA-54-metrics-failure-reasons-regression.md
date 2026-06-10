---
linear_issue: SHA-54
title: L5 transport run.py returns failure-free empty plan when complete_map or rim_result is missing
priority: Low
labels:
  - priority:mid
  - test
  - bug
  - solver
  - spec
status: planned
created_by: todo-plan-automation
---

# Plan: L5 transport post-summary metrics regression for missing-prerequisite failures

## Source Issue

- Linear: SHA-54
- Status at planning time: Todo
- Priority: Low

## Problem

When the orchestrator returns a failure plan for missing `complete_map` or `rim_result`, `build_layer05_transport_post_summary_metrics` must surface `failure_reasons` in post-summary output. Without a regression test, observability gaps can reappear silently.

## Scope

Add a unit regression test ensuring `build_layer05_transport_post_summary_metrics` (delegating to `build_layer04_transport_post_summary_metrics`) includes the expected `failure_reasons` entry when the orchestrator returns a missing-prerequisite failure plan.

## Non-goals

- Changing metrics builder implementation (already maps `plan.failures` to `failure_reasons`)
- stack_runner wiring changes
- Replay golden updates

## Implementation Plan

1. Add test module or extend existing transport metrics tests (e.g. `tests/unit/asteroid_lab/layers/test_layer05_post_summary_metrics.py` or colocate in stub test file if pattern exists).
2. Build a minimal `Layer04RoutePlan` with a single `EMPTY_L3_PACKAGE` failure (or call `run_layer_05_transport_routing` with missing prerequisites after orchestrator fix).
3. Call `build_layer05_transport_post_summary_metrics(plan)` and assert `"failure_reasons" in metrics` and `"empty_l3_package" in metrics["failure_reasons"]`.
4. Run `pytest` on the new/updated test file.

## Files / Areas Likely Affected

- `tests/unit/asteroid_lab/layers/` (new or extended metrics test)
- `src/shapez2_factory/application/asteroid_lab/layers/observability/layer05_post_summary_metrics.py` (read-only reference)
- `src/shapez2_factory/application/asteroid_lab/layers/observability/layer04_post_summary_metrics.py` (read-only reference)

## Validation Plan

- lint: `ruff check tests/unit/asteroid_lab/layers/`
- typecheck: `mypy django_apps config src` (spot-check)
- tests: `pytest tests/unit/asteroid_lab/layers/ -k "post_summary or transport_routing_stub" -v`
- build: n/a
- manual verification: n/a

## Acceptance Criteria

- [ ] Metrics regression added for `failure_reasons` on missing-prerequisite path
- [ ] Matches the source issue spec
- [ ] Stays within the priority scope (test only)
- [ ] Required validation passes or failures are documented
- [ ] No unrelated behavior is changed

## Risks / Open Questions

- If failure reason for `complete_map=None` differs from `EMPTY_L3_PACKAGE`, update assertion accordingly.
- Follow existing post-summary test patterns from `test_layer04_inner_fill_greedy.py` for consistency.
