---
linear_issue: SHA-11
title: Missing regression for reconcile RECONCILE_FAILURE_LOG_FATAL (subprocess log fatal marker)
priority: Mid
labels:
  - test
  - priority:mid
status: in_progress
created_by: todo-plan-automation
---

# Plan: Regression test for RECONCILE_FAILURE_LOG_FATAL

## Source Issue

- Linear: SHA-11
- Status at planning time: Todo
- Priority: Mid

## Problem

`reconcile_solver_run` marks runs failed with `RECONCILE_FAILURE_LOG_FATAL` when sidecar log contains CLI `error:` markers, but no unit test covers this branch.

## Scope

Add unit test: sidecar log with `error:` line, no manifest → FAILED + `RECONCILE_FAILURE_LOG_FATAL`.

## Non-goals

- Do not change `_log_has_fatal_marker` heuristic.
- No real CLI integration test.

## Implementation Plan

1. Read `solver_run_reconcile.py` lines 214–223 and existing `test_reconcile_solver_run.py` patterns.
2. Extend `_running_run` fixture pattern with log file containing `error: manifest not found: ...`.
3. Call `reconcile_solver_run`; assert FAILED and error code.
4. Run `pytest tests/unit/asteroid_lab/test_reconcile_solver_run.py -v`.

## Files / Areas Likely Affected

- `tests/unit/asteroid_lab/test_reconcile_solver_run.py`
- `django_apps/asteroid_lab/services/solver_run_reconcile.py` (read-only)

## Validation Plan

- tests: `pytest tests/unit/asteroid_lab/test_reconcile_solver_run.py -v`

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Low: document stderr `error:` pattern in reconcile spec (separate plan).
