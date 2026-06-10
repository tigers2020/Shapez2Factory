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

# Plan: Schedule run_solver_reap production cron

## Source Issue

- Linear: SHA-47
- Status at planning time: Todo
- Priority: High

## Problem

PR-CLI-7 expects a background reap cron (`manage.py run_solver_reap`) to reconcile detached `SolverRun.status=RUNNING` rows when the Lab UI is not polling. The command exists but no deployment schedule invokes it. Orphaned RUNNING rows block the one-active-run guard (409 ACTIVE_RUN_EXISTS) until manual poll or reap.

## Scope

Add a production schedule (Render cron, platform cron, or documented ops hook) running `python manage.py run_solver_reap` at a bounded interval (1–5 minutes). Document interval in deploy docs.

## Non-goals

- Changing reconcile logic or async spawn behavior
- Replacing UI status polling
- Implementing a new reap algorithm

## Implementation Plan

1. Review `django_apps/asteroid_lab/management/commands/run_solver_reap.py` and `solver_run_reconcile.py` for env requirements.
2. Add Render (or host) cron job invoking `python manage.py run_solver_reap` every 1–5 minutes in the same environment as the web app.
3. Update `scripts/render_start.sh` docs or add `render.yaml` / deploy config for cron if applicable.
4. Link cron expectation from `docs/superpowers/plans/2026-05-30-asteroid-lab-cli-first/pr-cli-7-async-solver-job.md`.
5. Add deploy-doc acceptance test scenario: detached async run reconciled without browser poll.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/management/commands/run_solver_reap.py`
- `django_apps/asteroid_lab/services/solver_run_reconcile.py`
- `django_apps/asteroid_lab/services/solver_run_registry.py`
- `scripts/render_start.sh`
- `render.yaml` or equivalent deploy config (TBD)
- `docs/superpowers/plans/2026-05-30-asteroid-lab-cli-first/pr-cli-7-async-solver-job.md`
- `tests/unit/asteroid_lab/test_run_solver_reap.py`

## Validation Plan

- lint: `ruff check .`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/asteroid_lab/test_run_solver_reap.py -v`
- build: `python manage.py check`
- manual verification: staging cron reconciles orphaned RUNNING row within configured interval

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Render cron availability and cost — confirm platform supports scheduled jobs.
- Cron interval vs `ASTEROID_LAB_SUBPROCESS_MAX_RUNTIME_SECONDS` — document relationship.
