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

# Plan: Stale RUNNING row monitoring (deferred)

## Source Issue

- Linear: SHA-47
- Status at planning time: Todo
- Priority: Low

## Problem

Optional health/monitoring when RUNNING rows exceed `ASTEROID_LAB_SUBPROCESS_MAX_RUNTIME_SECONDS` was noted in the issue but is out of scope for the cron wiring fix.

## Scope

Track only. Optional follow-up after cron lands.

## Non-goals

- Building full observability stack in SHA-47.
- Replacing UI status polling.

## Implementation Plan

1. Complete SHA-47 high plan (cron schedule).
2. Evaluate whether existing logging/metrics suffice.
3. Open follow-up if operators need alerts on stale RUNNING count.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/solver_run_reconcile.py`
- TBD: monitoring integration

## Validation Plan

- lint: N/A (deferred)
- typecheck: N/A (deferred)
- tests: N/A (deferred)
- build: N/A (deferred)
- manual verification: N/A (deferred)

## Acceptance Criteria

- [ ] Deferred items remain out of SHA-47 high/mid scope.

## Risks / Open Questions

- Without monitoring, cron failures may go unnoticed until user reports 409 blocks.
