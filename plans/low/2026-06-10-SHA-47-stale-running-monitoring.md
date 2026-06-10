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

# Plan: Optional stale RUNNING row monitoring

## Source Issue

- Linear: SHA-47
- Status at planning time: Todo
- Priority: Low (deferred)

## Problem

Even with reap cron, operators may want alerting when RUNNING rows exceed `ASTEROID_LAB_SUBPROCESS_MAX_RUNTIME_SECONDS`.

## Scope

Track optional health/monitoring note — not required for SHA-47 acceptance.

## Non-goals

- Building full observability stack
- Changing reap algorithm

## Implementation Plan

1. After cron lands, optionally add log/metric when reap finds stale rows.
2. Defer until production cron is verified.

## Files / Areas Likely Affected

- TBD — `run_solver_reap.py`, monitoring config

## Validation Plan

- N/A

## Acceptance Criteria

- [ ] Remaining risks documented.

## Risks / Open Questions

- Monitoring without cron does not fix blocking issue — high plan is prerequisite.
