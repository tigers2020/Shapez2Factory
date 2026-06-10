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

# Plan: Production schedule for run_solver_reap

## Source Issue

- Linear: SHA-47
- Status at planning time: Todo
- Priority: High

## Problem

PR-CLI-7 expects a background reap cron (`manage.py run_solver_reap`) but no deployment schedule invokes it. Orphaned `RUNNING` rows block the one-active-run guard (409 ACTIVE_RUN_EXISTS) until manual poll or reap.

## Scope

Add production schedule (Render cron, platform cron, or documented ops hook) running `python manage.py run_solver_reap` at bounded interval (1–5 minutes).

## Non-goals

- Changing reconcile logic or async spawn behavior
- Replacing UI status polling
- Implementing new reap algorithm

## Implementation Plan

1. Read `scripts/render_start.sh` and host deploy config for cron hook points.
2. Add Render cron job (or equivalent) invoking `python manage.py run_solver_reap` every 1–5 minutes in web app environment.
3. Verify `tests/unit/asteroid_lab/test_run_solver_reap.py` covers command behavior.
4. Add deploy acceptance test scenario: detached async run without UI poll is reconciled within interval.
5. Document interval in PR-CLI-7 plan or deploy docs.

## Files / Areas Likely Affected

- `scripts/render_start.sh` (or Render dashboard cron config)
- `django_apps/asteroid_lab/management/commands/run_solver_reap.py`
- `django_apps/asteroid_lab/services/solver_run_reconcile.py`
- `docs/superpowers/plans/2026-05-30-asteroid-lab-cli-first/pr-cli-7-async-solver-job.md`
- deploy/ops documentation

## Validation Plan

- tests: `pytest tests/unit/asteroid_lab/test_run_solver_reap.py`
- manual verification: trigger async run, close tab, wait for cron interval, confirm RUNNING cleared

## Acceptance Criteria

- [ ] Production runs `run_solver_reap` on schedule without user interaction.
- [ ] Detached async run reconciled within configured interval.
- [ ] Projects not permanently blocked by stale RUNNING rows.
- [ ] Deploy/ops docs mention cron and interval.
- [ ] No change to reconcile semantics beyond schedule wiring.

## Risks / Open Questions

- Cron must share DB and env with web workers.
- Interval vs `ASTEROID_LAB_SUBPROCESS_MAX_RUNTIME_SECONDS` alignment.
