---
linear_issue: SHA-47
title: No scheduled run_solver_reap; orphaned RUNNING rows block async solver until manual poll
priority: High
labels:
  - automation
  - infra
  - priority:high
  - bug
status: planned
created_by: todo-plan-automation
---

# Plan: Schedule production run_solver_reap cron

## Source Issue

- Linear: SHA-47
- Status at planning time: Todo
- Priority: High

## Problem

`manage.py run_solver_reap` exists but no production schedule invokes it. Detached async solver runs can remain `RUNNING` indefinitely, blocking the one-active-run guard (409 ACTIVE_RUN_EXISTS) until manual poll or reap.

## Scope

Add production schedule (Render cron, platform cron, or documented ops hook) running `python manage.py run_solver_reap` every 1–5 minutes. Document interval in deploy docs.

## Non-goals

- Changing reconcile logic or async spawn behavior.
- Replacing UI status polling.
- New reap algorithm.

## Implementation Plan

1. Add Render/host cron job invoking `python manage.py run_solver_reap` in web app environment.
2. Verify reconcile timeout (`ASTEROID_LAB_SUBPROCESS_MAX_RUNTIME_SECONDS`) fires via cron without browser poll.
3. Add deploy acceptance test scenario: detached async run reaped within interval.
4. Document cron in PR-CLI-7 / deploy docs.

## Files / Areas Likely Affected

- `scripts/render_start.sh` or Render cron config (TBD per host)
- `django_apps/asteroid_lab/management/commands/run_solver_reap.py`
- `docs/superpowers/plans/2026-05-30-asteroid-lab-cli-first/pr-cli-7-async-solver-job.md`

## Validation Plan

- tests: `pytest tests/unit/asteroid_lab/test_run_solver_reap.py -v`
- manual verification: orphaned RUNNING row reaped without UI poll

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Host platform cron syntax (Render vs other) must match production environment.
