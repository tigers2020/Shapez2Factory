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

# Plan: Schedule run_solver_reap in production

## Source Issue

- Linear: SHA-47
- Status at planning time: Todo
- Priority: High

## Problem

PR-CLI-7 expects a background reap cron (`manage.py run_solver_reap`) but no deployment schedule invokes it. Orphaned `RUNNING` rows block the one-active-run guard (409 ACTIVE_RUN_EXISTS) until manual poll or reap.

## Scope

Add production schedule (Render cron, platform cron, or documented ops hook) running `python manage.py run_solver_reap` at bounded interval (1–5 minutes). Document interval in deploy docs.

## Non-goals

- Changing reconcile logic or async spawn behavior.
- Replacing UI status polling.
- New reap algorithm.

## Implementation Plan

1. Add Render cron job (or host equivalent) invoking `python manage.py run_solver_reap` every 1–5 minutes in web app environment.
2. Update `scripts/render_start.sh` or Render dashboard config as appropriate for cron service.
3. Document cron interval in PR-CLI-7 plan and deploy docs.
4. Add deploy-doc acceptance: detached async run reconciled without browser poll within interval.
5. Verify with `tests/unit/asteroid_lab/test_run_solver_reap.py` (existing command tests).

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/management/commands/run_solver_reap.py`
- `scripts/render_start.sh` or Render cron config
- `docs/superpowers/plans/2026-05-30-asteroid-lab-cli-first/pr-cli-7-async-solver-job.md`
- Deploy/ops documentation

## Validation Plan

- lint: `ruff check django_apps/asteroid_lab/`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/asteroid_lab/test_run_solver_reap.py -v`
- build: `python manage.py check`
- manual verification: Trigger async solver, close tab, wait for cron interval; confirm RUNNING reconciled and new run allowed.

## Acceptance Criteria

- [ ] Production runs `run_solver_reap` on schedule without user interaction.
- [ ] Detached async run reconciled within configured interval.
- [ ] Projects not permanently blocked by stale RUNNING rows.
- [ ] Deploy/ops docs mention cron and interval.
- [ ] No change to reconcile semantics beyond schedule wiring.

## Risks / Open Questions

- Render cron availability and cost on current hosting tier.
- Cron must share DB access and env vars with web app.
- Staging environment may need separate cron or documented manual reap.
