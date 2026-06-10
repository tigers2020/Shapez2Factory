---
linear_issue: SHA-47
title: No scheduled run_solver_reap; orphaned RUNNING rows block async solver until manual poll
priority: Mid
labels:
  - automation
  - infra
  - priority:high
  - bug
status: planned
created_by: todo-plan-automation
---

# Plan: Deploy documentation for reap cron

## Source Issue

- Linear: SHA-47 (Mid priority items)
- Status at planning time: Todo
- Priority: Mid

## Problem

Deploy docs missing cron interval documentation. PR-CLI-7 reap cron expectation unmet in infra documentation.

## Scope

Document cron interval, invocation command, and ops troubleshooting in deploy docs linked from PR-CLI-7.

## Non-goals

- Implementing cron itself (High plan).

## Implementation Plan

1. Add section to deploy/ops docs: command, interval, expected behavior when orphaned RUNNING exists.
2. Cross-link PR-CLI-7 async solver design doc.
3. Note manual fallback: `python manage.py run_solver_reap` and status URL polling.

## Files / Areas Likely Affected

- `docs/superpowers/plans/2026-05-30-asteroid-lab-cli-first/pr-cli-7-async-solver-job.md`
- Deploy/ops documentation (TBD path)

## Validation Plan

- docs review only

## Acceptance Criteria

- [ ] Deploy docs mention cron and interval.
- [ ] PR-CLI-7 expectation documented as met or staged.

## Risks / Open Questions

- Doc path may vary by hosting platform.
