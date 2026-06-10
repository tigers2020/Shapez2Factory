---
linear_issue: SHA-11
title: Missing regression for reconcile RECONCILE_FAILURE_LOG_FATAL
priority: Low
labels:
  - test
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Document reconcile stderr error: pattern (SHA-11 Low)

## Source Issue

- Linear: SHA-11
- Priority: Low

## Scope

Add short note in agent workflow or reconcile service docstring describing `_log_has_fatal_marker` contract.

## Implementation Plan

1. After Mid regression test lands, document expected log line format.
2. Link from PR-CLI-7 checklist if applicable.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/solver_run_reconcile.py` or `docs/agent-workflows/` TBD

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Optional polish.
