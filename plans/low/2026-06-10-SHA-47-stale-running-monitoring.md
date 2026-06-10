---
linear_issue: SHA-47
title: No scheduled run_solver_reap; orphaned RUNNING rows block async solver until manual poll
priority: Low
labels:
  - automation
  - infra
  - priority:high
  - bug
status: planned
created_by: todo-plan-automation
---

# Plan: Optional monitoring note for stale RUNNING SolverRun rows

## Source Issue

- Linear: SHA-47
- Status at planning time: Todo
- Priority: Low

## Problem

Operators have no lightweight signal when RUNNING rows exceed `ASTEROID_LAB_SUBPROCESS_MAX_RUNTIME_SECONDS` before cron or poll reconciles them. Issue lists optional health/monitoring as low priority.

## Scope

Add a lightweight monitoring or ops note (log line, admin query snippet, or documented SQL) for stale RUNNING rows — not a full alerting product.

## Non-goals

- Do not replace UI status polling.
- Do not build external paging/alerting integration in this slice.
- Do not change reconcile or cron wiring (High plan).

## Implementation Plan

1. Query pattern: `SolverRun.objects.filter(status=RUNNING, started_at__lt=now() - timedelta(seconds=ASTEROID_LAB_SUBPROCESS_MAX_RUNTIME_SECONDS))`.
2. Option A (minimal): extend `run_solver_reap` stdout to log count of stale RUNNING rows before reconcile loop.
3. Option B (docs-only): add ops runbook snippet in deploy doc from Mid plan with management command or Django shell one-liner.
4. Option C (deferred): Django admin filter on stale RUNNING — only if admin is in active use for Asteroid Lab.
5. Pick smallest option that satisfies "lightweight health/monitoring note" without new dependencies.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/management/commands/run_solver_reap.py` (optional log line)
- Deploy/ops doc from Mid plan (runbook snippet)
- `django_apps/asteroid_lab/models.py` (read-only query reference)
- TBD: admin customization if Option C chosen

## Validation Plan

- lint: `ruff check django_apps/asteroid_lab/management/commands/run_solver_reap.py` (if code touched)
- typecheck: `mypy django_apps` (if code touched)
- tests: extend `tests/unit/asteroid_lab/test_run_solver_reap.py` only if stdout/logging behavior changes
- build: N/A
- manual verification: Stale RUNNING row produces visible log or documented query result

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Operators can detect stale RUNNING rows without reading DB ad hoc.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Logging noise if cron runs every 5 minutes — log only when stale count > 0.
- Optional slice; safe to defer after High + Mid land.
