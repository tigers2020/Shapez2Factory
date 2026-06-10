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

# Plan: Health monitoring for stale RUNNING rows (optional)

## Source Issue

- Linear: SHA-47 (Low priority items)
- Status at planning time: Todo
- Priority: Low

## Problem

Optional health/monitoring note when RUNNING rows exceed `ASTEROID_LAB_SUBPROCESS_MAX_RUNTIME_SECONDS`.

## Scope

Optional follow-up — not required for High cron wiring.

## Non-goals

- Replacing UI status polling.

## Implementation Plan

1. Defer unless ops requests alerting.
2. If implemented: log or metric when RUNNING age exceeds timeout threshold.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/solver_run_reconcile.py` (TBD)

## Validation Plan

- N/A until implemented

## Acceptance Criteria

- [ ] Not blocking High/Mid delivery.

## Risks / Open Questions

- Monitoring stack availability on current host.
