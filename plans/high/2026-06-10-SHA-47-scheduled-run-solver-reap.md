---
linear_issue: SHA-47
title: No scheduled run_solver_reap; orphaned RUNNING rows block async solver until manual poll
priority: High
labels:
  - automation
  - infra
  - bug
  - priority:high
status: planned
created_by: todo-plan-automation
---

# Plan: Schedule production run_solver_reap cron

## Source Issue

- Linear: SHA-47
- Status at planning time: Todo
- Priority: High

## Problem

PR-CLI-7 async solver design expects a background reap cron (`manage.py run_solver_reap`) to reconcile detached `SolverRun.status=RUNNING` rows when the Lab UI is not polling. The command exists but no deployment schedule invokes it. Orphaned RUNNING rows block the one-active-run guard (409 ACTIVE_RUN_EXISTS) until manual poll or reap.

## Scope

Add a production schedule (Render cron, platform cron, or documented ops hook) that runs `python manage.py run_solver_reap` at a bounded interval (1–5 minutes). Document interval and link from PR-CLI-7 / deploy docs.

## Non-goals

- Changing reconcile logic or async spawn behavior
- Replacing UI status polling
- Implementing a new reap algorithm

## Implementation Plan

1. Read `django_apps/asteroid_lab/management/commands/run_solver_reap.py` and `solver_run_reconcile.py` entry points.
2. Inspect `scripts/render_start.sh` and Render/host cron configuration patterns in repo.
3. Add Render cron job (or equivalent) invoking:
   ```bash
   python manage.py run_solver_reap
   ```
   every 1–5 minutes in same environment as web app (DB access required).
4. Verify `ASTEROID_LAB_SUBPROCESS_MAX_RUNTIME_SECONDS` timeout fires via reap without UI poll.
5. Add deploy-doc acceptance scenario: detached async run reconciled within interval.
6. Optionally add monitoring note for RUNNING rows exceeding max runtime (defer to mid plan if separate).

## Files / Areas Likely Affected

- Render cron config / `render.yaml` or host infra files (TBD — confirm canonical deploy path)
- `scripts/render_start.sh`
- `django_apps/asteroid_lab/management/commands/run_solver_reap.py`
- `docs/superpowers/plans/2026-05-30-asteroid-lab-cli-first/pr-cli-7-async-solver-job.md`
- Deploy/ops documentation (TBD path)

## Validation Plan

- tests: `pytest tests/unit/asteroid_lab/test_run_solver_reap.py -v`
- manual verification: staging repro — trigger async run, close tab, wait for cron interval, confirm RUNNING cleared

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- **Host-specific:** Render cron syntax vs other platforms — confirm production host.
- Cron must share DB/network with web workers.
- Staging may need separate schedule or documented manual ops hook if cron unavailable in dev.
