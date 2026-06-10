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

# Plan: Stale RUNNING row monitoring (SHA-47 Low scope)

## Source Issue

- Linear: SHA-47
- Status at planning time: Todo
- Priority: Low

## Problem

SHA-47 Low section mentions optional health/monitoring when RUNNING rows exceed `ASTEROID_LAB_SUBPROCESS_MAX_RUNTIME_SECONDS` — out of scope for cron wiring.

## Scope

Track optional monitoring follow-up; no implementation in SHA-47 High/Mid PRs unless explicitly pulled forward.

## Non-goals

- Replacing UI status polling
- Building full observability stack

## Implementation Plan

1. Defer until cron is live and stale rows are rare.
2. If needed, add lightweight log/metric when reap finds timed-out RUNNING rows.

## Files / Areas Likely Affected

- TBD

## Validation Plan

- lint: N/A
- typecheck: N/A
- tests: N/A
- build: N/A
- manual verification: N/A

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Optional enhancement; cron wiring (High) is the blocker fix.
