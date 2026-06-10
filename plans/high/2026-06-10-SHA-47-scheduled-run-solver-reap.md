---
linear_issue: SHA-47
title: No scheduled run_solver_reap; orphaned RUNNING rows block async solver until manual poll
priority: High
labels:
  - bug
  - automation
  - infra
  - priority:high
status: planned
created_by: todo-plan-automation
---

# Plan: No scheduled run_solver_reap; orphaned RUNNING rows block async solver until manual poll

## Source Issue

- Linear: SHA-47
- Status at planning time: Todo
- Priority: High

## Problem

PR-CLI-7 async solver design expects a background reap cron (`manage.py run_solver_reap`) to reconcile detached `SolverRun.status=RUNNING` rows. The command exists but no deployment schedule invokes it. Orphaned RUNNING rows block the one-active-run guard (409 ACTIVE_RUN_EXISTS) until manual poll or reap.

## Scope

- Add production schedule (Render cron, platform cron, or documented ops hook) running `python manage.py run_solver_reap` at bounded interval.
- Document interval and link from PR-CLI-7 / deploy docs.

## Non-goals

- Changing reconcile logic or async spawn behavior.
- Replacing UI status polling.
- Implementing a new reap algorithm.

## Implementation Plan

1. Read `django_apps/asteroid_lab/management/commands/run_solver_reap.py` and `solver_run_reconcile.py`; confirm `reconcile_solver_run` entry points (status poll + reap command only).
2. Add Render cron job (or equivalent in `render.yaml` / deploy config) invoking `python manage.py run_solver_reap` every 1–5 minutes in web app environment.
3. Verify `scripts/render_start.sh` remains migrate + gunicorn only; cron is separate service.
4. Document cron interval and purpose in `docs/superpowers/plans/2026-05-30-asteroid-lab-cli-first/pr-cli-7-async-solver-job.md` and deploy/ops doc (TBD path under `documents/` or `docs/`).
5. Add acceptance test scenario in `tests/unit/asteroid_lab/test_run_solver_reap.py` if not already covering timeout reconcile path.
6. Manual acceptance: trigger async run, close tab, wait cron interval, confirm RUNNING row reconciled and new run allowed.

## Files / Areas Likely Affected

- `render.yaml` or platform cron config (TBD — grep existing Render/deploy config)
- `django_apps/asteroid_lab/management/commands/run_solver_reap.py` (read-only)
- `django_apps/asteroid_lab/services/solver_run_reconcile.py` (read-only)
- `scripts/render_start.sh` (read-only)
- `docs/superpowers/plans/2026-05-30-asteroid-lab-cli-first/pr-cli-7-async-solver-job.md`
- `tests/unit/asteroid_lab/test_run_solver_reap.py`

## Validation Plan

- lint: `ruff check .`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/asteroid_lab/test_run_solver_reap.py -v`
- build: `python manage.py check`
- manual verification: Staging/prod cron fires; detached RUNNING reconciled within interval

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Render cron availability and env parity with web dyno (DB access, settings module).
- Interval vs `ASTEROID_LAB_SUBPROCESS_MAX_RUNTIME_SECONDS` — cron should run more frequently than max runtime for timely reap.
