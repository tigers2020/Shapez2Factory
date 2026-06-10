---
linear_issue: SHA-47
title: No scheduled run_solver_reap; orphaned RUNNING rows block async solver until manual poll
priority: Low
labels:
  - bug
  - automation
  - infra
  - priority:high
status: planned
created_by: todo-plan-automation
---

# Plan: Optional monitoring note for stale RUNNING solver rows

## Source Issue

- Linear: SHA-47
- Status at planning time: Todo
- Priority: Low

## Problem

Even with a reap cron, operators lack a lightweight signal when `SolverRun.status=RUNNING` rows exceed `ASTEROID_LAB_SUBPROCESS_MAX_RUNTIME_SECONDS` without reconciling — indicating cron failure, DB mismatch, or reconcile errors.

## Scope

Add an optional, lightweight health/monitoring note or log metric when stale RUNNING rows are detected during `run_solver_reap` or via a documented SQL/management query for ops. Non-blocking improvement after High cron ships.

## Non-goals

- Replacing UI status polling
- Building a full observability stack or pager integration
- Changing reconcile semantics
- New reap algorithm

## Implementation Plan

1. After High plan cron is live, evaluate minimal signal:
   - Option A: `run_solver_reap` logs WARNING when any RUNNING row age > `ASTEROID_LAB_SUBPROCESS_MAX_RUNTIME_SECONDS` before reconcile attempt.
   - Option B: Document ops query in deploy docs: count RUNNING rows older than threshold.
2. If Option A chosen: extend `reconcile_running_solver_runs()` or command `handle()` to emit structured log line (reuse ambient JSON log schema from `environment.md`).
3. Add unit test: stale RUNNING row triggers warning log (caplog) without changing reconcile outcome.
4. Cross-link from Mid deploy doc under "Troubleshooting".

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/management/commands/run_solver_reap.py` (optional log)
- `django_apps/asteroid_lab/services/solver_run_reconcile.py` (optional)
- `tests/unit/asteroid_lab/test_run_solver_reap.py`
- `documents/ai/manuals/environment.md` or deploy doc from Mid plan

## Validation Plan

- lint: `ruff check django_apps/asteroid_lab/management/commands/run_solver_reap.py`
- typecheck: `mypy django_apps/asteroid_lab`
- tests: `python -m pytest tests/unit/asteroid_lab/test_run_solver_reap.py -v`
- build: N/A
- manual verification: Seed old RUNNING row; run reap; confirm warning in logs

## Acceptance Criteria

- [ ] Matches the source issue spec (optional monitoring note).
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Issue marks this as optional — defer if High+Mid satisfy acceptance; skip implementation if ops doc query is sufficient.
- Warning noise if many legitimate long-running solves exceed timeout setting — tune threshold to `started_at + max_runtime`, not wall clock alone.
