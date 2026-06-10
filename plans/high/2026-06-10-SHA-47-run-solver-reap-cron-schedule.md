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

# Plan: Schedule production run_solver_reap cron

## Source Issue

- Linear: SHA-47
- Status at planning time: Todo
- Priority: High

## Problem

PR-CLI-7 async solver design expects a background **reap cron** (`manage.py run_solver_reap`) to reconcile detached `SolverRun.status=RUNNING` rows when the Lab UI is not polling. The command and `reconcile_solver_run` logic exist, but the repository has **no deployment schedule** (Render start script, GitHub Actions cron, or other infra) that invokes it.

If a user triggers async solver (HTTP 202) and closes the tab before status polling finishes, the run can remain `RUNNING` indefinitely. The one-active-run guard then returns **409 ACTIVE_RUN_EXISTS** for subsequent runs on that project until someone manually polls the status URL or runs `run_solver_reap`. Reconcile timeout (`ASTEROID_LAB_SUBPROCESS_MAX_RUNTIME_SECONDS`) only runs inside `reconcile_solver_run`; without poll or reap, timeouts never fire.

## Scope

Wire a production (or documented staging) schedule that runs `python manage.py run_solver_reap` every 1–5 minutes in the same environment as the web app (shared DB + `ASTEROID_LAB_ARTIFACT_ROOT`). Add a thin shell wrapper if needed for Render cron parity with `scripts/render_start.sh` venv resolution.

## Non-goals

- Changing reconcile logic or async spawn behavior
- Replacing UI status polling
- Implementing a new reap algorithm
- Health/monitoring dashboards (see Low plan)

## Implementation Plan

1. Confirm production host: Render web service uses `scripts/render_start.sh` (migrate + gunicorn only); no `render.yaml` in repo today — decide Render Cron Job vs platform-equivalent.
2. Add `scripts/render_reap_cron.sh`:
   - `set -euo pipefail`, `cd` to repo root
   - Resolve Python like `render_start.sh` (`.venv/bin/python` or `python3`)
   - `exec "$PYTHON" manage.py run_solver_reap`
3. Add Render cron service definition (preferred when deploy is Render):
   - New `render.yaml` (or extend if added elsewhere) with `type: cron`, schedule `*/2 * * * *` (2-minute interval within 1–5 min spec)
   - Same `buildCommand` as web (`scripts/render_build.sh`) so env/venv/Playwright paths match
   - `startCommand`: `bash scripts/render_reap_cron.sh`
   - Same env group / secrets as web (DB, artifact root)
4. If Render cron is not viable for staging, document fallback: GitHub Actions `schedule` workflow calling reap against staging URL is **not** sufficient alone (needs DB access) — cron must share the app database.
5. Add integration smoke: extend `tests/unit/asteroid_lab/test_run_solver_reap.py` or add deploy-doc acceptance step — orphaned RUNNING row with finalized artifact is reaped when command runs (existing unit test covers command; add manual/staging checklist in Mid plan).
6. Verify locally: `python manage.py run_solver_reap` with a seeded RUNNING row transitions to terminal state.

## Files / Areas Likely Affected

- `scripts/render_reap_cron.sh` (create)
- `render.yaml` (create) or Render dashboard cron config (document if not infra-as-code)
- `scripts/render_start.sh` (reference only — no change required)
- `django_apps/asteroid_lab/management/commands/run_solver_reap.py` (no logic change)
- `django_apps/asteroid_lab/services/solver_run_reconcile.py` (no logic change)
- `tests/unit/asteroid_lab/test_run_solver_reap.py` (optional assertion only)

## Validation Plan

- lint: `ruff check scripts/` (if shell-only, skip)
- typecheck: N/A for shell/cron wiring
- tests: `python -m pytest tests/unit/asteroid_lab/test_run_solver_reap.py -v`
- build: `bash scripts/render_reap_cron.sh` exits 0 on empty RUNNING set
- manual verification: Trigger async solver, close tab, wait ≤ cron interval + `ASTEROID_LAB_SUBPROCESS_MAX_RUNTIME_SECONDS`, confirm project accepts new run (no 409)

## Acceptance Criteria

- [ ] Production (or documented staging) runs `run_solver_reap` on a schedule without user interaction.
- [ ] A detached async run left without UI polling is reconciled within the configured interval.
- [ ] Projects are not permanently blocked by stale RUNNING rows when artifacts exist or timeout applies.
- [ ] Stays within the priority scope (schedule wiring only).
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Render Cron Job must use same persistent DB as web; ephemeral SQLite on free tier may not share state across services — confirm `DATABASE_URL` wiring.
- Cron interval vs `ASTEROID_LAB_SUBPROCESS_MAX_RUNTIME_SECONDS` default: worst-case unblock delay ≈ interval + timeout; document chosen interval.
- Multi-instance web + single cron is safe (`select_for_update` in reconcile); duplicate cron schedules should be avoided.
