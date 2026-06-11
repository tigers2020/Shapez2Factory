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

PR-CLI-7 async solver design expects a background reap cron (`manage.py run_solver_reap`) to reconcile detached `SolverRun.status=RUNNING` rows when the Lab UI is not polling. The command and `reconcile_solver_run` logic exist, but no deployment schedule invokes them. Orphaned RUNNING rows block the one-active-run guard (409 `ACTIVE_RUN_EXISTS`) and reconcile timeouts never fire without poll or cron.

## Scope

Add a production schedule that runs `python manage.py run_solver_reap` every 1–5 minutes in the same environment as the web app (Render cron job or equivalent host cron). Wire infra so detached async runs reconcile without browser polling.

## Non-goals

- Do not change reconcile logic or async spawn behavior.
- Do not replace UI status polling.
- Do not implement a new reap algorithm.

## Implementation Plan

1. Confirm current production host (Render per `scripts/render_start.sh` / `scripts/render_build.sh`) and whether `render.yaml` blueprint exists or must be added.
2. Add a Render **Cron Job** service (or platform-equivalent) that shares the web app image/env/DB and runs on a fixed interval (recommend **every 5 minutes**; max stale window = interval + `ASTEROID_LAB_SUBPROCESS_MAX_RUNTIME_SECONDS`).
3. Cron command (match `render_start.sh` Python resolution):

   ```bash
   cd /opt/render/project/src && .venv/bin/python manage.py run_solver_reap
   ```

   Or add `scripts/render_reap_cron.sh` mirroring `render_start.sh` venv/`PLAYWRIGHT_BROWSERS_PATH` conventions if the cron image differs.
4. If Render blueprint is used, add cron service to `render.yaml` with `schedule: "*/5 * * * *"` (or `*/2` for tighter bound) and same `envVars` / database attachment as the web service.
5. If Render dashboard-only: document exact Cron Job settings (name, schedule, start command, env group) in deploy docs (see Mid plan) and verify one manual trigger succeeds in staging.
6. Add a lightweight integration or smoke check: after deploying cron config, trigger async solver, close poll, wait one cron interval, assert RUNNING row transitions without status GET (can be manual acceptance in staging).
7. Run existing unit gate: `pytest tests/unit/asteroid_lab/test_run_solver_reap.py -v`.

## Files / Areas Likely Affected

- `render.yaml` (new or extend) — Render cron job service definition
- `scripts/render_reap_cron.sh` (optional thin wrapper)
- `scripts/render_start.sh` (reference only; no behavior change expected)
- `django_apps/asteroid_lab/management/commands/run_solver_reap.py` (no logic change)
- `django_apps/asteroid_lab/services/solver_run_reconcile.py` (no logic change)
- `django_apps/asteroid_lab/services/solver_run_registry.py` (`ActiveRunExistsError` guard — unchanged)
- `config/settings.py` (`ASTEROID_LAB_SUBPROCESS_MAX_RUNTIME_SECONDS`)

## Validation Plan

- lint: `ruff check django_apps/asteroid_lab/management/commands/run_solver_reap.py`
- typecheck: `mypy django_apps config src` (no new Python surface if infra-only)
- tests: `pytest tests/unit/asteroid_lab/test_run_solver_reap.py -v`
- build: `bash scripts/render_build.sh` (if cron shares build)
- manual verification: Staging — async POST 202, no status poll, wait ≤ cron interval + timeout setting; project accepts new run (no 409)

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Production (or documented staging) runs `run_solver_reap` on a schedule without user interaction.
- [ ] Detached async run left without UI polling is reconciled within the configured interval.
- [ ] Projects are not permanently blocked by stale RUNNING rows when artifacts exist or timeout applies.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Render Cron Job must attach to the **same database** as the web service; mis-wired env causes no-op reap.
- Cron interval vs `ASTEROID_LAB_SUBPROCESS_MAX_RUNTIME_SECONDS`: worst-case block time ≈ cron interval + timeout; document chosen values.
- If production is not Render, substitute host cron with equivalent env — confirm actual deploy target before merge.
