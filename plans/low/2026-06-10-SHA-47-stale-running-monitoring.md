---
linear_issue: SHA-47
title: No scheduled run_solver_reap; orphaned RUNNING rows block async solver until manual poll
priority: Low
labels:
  - automation
  - infra
  - priority:high
  - bug
status: planned
created_by: todo-plan-automation
---

# Plan: Health monitoring for stale RUNNING solver rows

## Source Issue

- Linear: SHA-47
- Status at planning time: Todo
- Priority: Low

## Problem

Optional health/monitoring when RUNNING rows exceed `ASTEROID_LAB_SUBPROCESS_MAX_RUNTIME_SECONDS` was listed as Low priority follow-up.

## Scope

Add lightweight monitoring note or metric when RUNNING rows exceed max runtime threshold.

## Non-goals

- Core cron schedule (High plan).

## Implementation Plan

1. Evaluate logging/metric hook in `run_solver_reap` when rows exceed threshold.
2. Document alert threshold for operators.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/solver_run_reconcile.py`
- `django_apps/asteroid_lab/management/commands/run_solver_reap.py`

## Validation Plan

- manual verification: log/metric emitted for stale RUNNING row in test env

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Monitoring stack availability on host platform.
