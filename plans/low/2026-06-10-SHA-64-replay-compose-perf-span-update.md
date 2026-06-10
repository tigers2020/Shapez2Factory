---
linear_issue: SHA-64
title: Lab artifact replay compose re-executes L2-L5 solver stack from Django
priority: Low
labels:
  - bug
  - performance
  - test
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Update replay compose perf spans after artifact-only path (SHA-64 Low)

## Source Issue

- Linear: SHA-64
- Status at planning time: Todo
- Priority: Low

## Problem

Perf span tests in `test_lab_replay_compose_perf_spans.py` may assert spans from the removed runtime re-execution path. After Mid plan removes in-process L2–L5 compose, spans need alignment.

## Scope

Update perf span tests and documentation after artifact-only compose path lands.

## Non-goals

- New performance optimizations beyond path removal.
- Changing span instrumentation in unrelated modules.

## Implementation Plan

1. After Mid plan lands, run `pytest tests/unit/asteroid_lab/test_lab_replay_compose_perf_spans.py -v` and capture failures.
2. Update expected span names/counts to match artifact-only compose (no layer execution spans).
3. If spans are removed entirely, document expected compose timeline in test docstring.
4. Verify no regression in compose latency assertions (thresholds may need adjustment if re-execution was inflating baselines).

## Files / Areas Likely Affected

- `tests/unit/asteroid_lab/test_lab_replay_compose_perf_spans.py`
- TBD — compose service if span emitters need rename only

## Validation Plan

- lint: N/A
- typecheck: N/A
- tests: `pytest tests/unit/asteroid_lab/test_lab_replay_compose_perf_spans.py -v`
- build: N/A
- manual verification: Span output matches artifact-only compose flow

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Depends on Mid plan completion.
- Perf thresholds may need recalibration after removing expensive re-execution path.
