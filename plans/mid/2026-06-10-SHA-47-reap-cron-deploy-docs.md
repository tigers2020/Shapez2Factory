---
linear_issue: SHA-47
title: No scheduled run_solver_reap; orphaned RUNNING rows block async solver until manual poll
priority: Mid
labels:
  - automation
  - infra
  - bug
  - priority:high
status: planned
created_by: todo-plan-automation
---

# Plan: Document run_solver_reap cron in deploy docs (SHA-47 mid)

## Source Issue

- Linear: SHA-47
- Status at planning time: Todo
- Priority: Mid (section of SHA-47 priority breakdown)

## Problem

PR-CLI-7 lists reap cron as expected production caller alongside UI poll, but deploy docs do not document the cron interval or ops wiring. Operators cannot verify the async solver orphan-recovery contract without reading source.

## Scope

Document the `run_solver_reap` schedule, interval, and acceptance criteria in deploy/ops docs and cross-link PR-CLI-7 plan.

## Non-goals

- Implementing the cron itself (see `plans/high/2026-06-10-SHA-47-scheduled-run-solver-reap.md`)
- Health/monitoring dashboards for stale RUNNING rows (low priority in source issue)

## Implementation Plan

1. After high-priority cron wiring lands, add section to deploy docs (TBD — `documents/ai/` or Render README) covering:
   - Command: `python manage.py run_solver_reap`
   - Interval: 1–5 minutes
   - Purpose: reconcile orphaned RUNNING `SolverRun` rows
2. Update `pr-cli-7-async-solver-job.md` with link to deploy doc and "implemented" note.
3. Add ops acceptance checklist: detached async run reconciled without browser poll.

## Files / Areas Likely Affected

- `docs/superpowers/plans/2026-05-30-asteroid-lab-cli-first/pr-cli-7-async-solver-job.md`
- Deploy/ops documentation (TBD)
- `scripts/render_start.sh` (comment cross-link only)

## Validation Plan

- manual verification: docs review against actual cron config

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Depends on high-priority cron implementation for accurate interval/host details.
