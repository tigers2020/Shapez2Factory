---
linear_issue: SHA-33
title: Stack-failure artifacts write manifest.error_code=null; Django ingest indexes COMPLETED
priority: Mid
labels:
  - bug
  - priority:high
status: planned
created_by: todo-plan-automation
---

# Plan: Align sync subprocess ingest with exit-20 stack-failure handling (SHA-33 Mid)

## Source Issue

- Linear: SHA-33
- Status at planning time: Todo
- Priority: Mid

## Problem

Related ingest mapping inconsistencies exist between async artifact ingest and the sync `run_solver_subprocess` path (SHA-45): sync may reject exit 20 before artifact ingest while async path ingests stack-failure artifacts as success.

## Scope

Reconcile sync vs async subprocess ingest behavior for `ExitCode.STACK_UNAVAILABLE` (20) after High-priority manifest fix lands.

## Non-goals

- Changing CLI exit code values.
- Rewriting entire subprocess runner architecture.

## Implementation Plan

1. After High plan lands, read `solver_subprocess_runner.py` (or equivalent) sync and async ingest branches.
2. Ensure both paths: (a) respect non-zero exit 20, (b) read `manifest.error_code` and `solver_summary.run_success` consistently.
3. Add or extend regression test covering sync subprocess path with exit-20 artifact.
4. Cross-link SHA-45 if separate fix is still required; document any intentional divergence.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/solver_subprocess_runner.py` (TBD — grep `STACK_UNAVAILABLE` / exit 20)
- `tests/unit/asteroid_lab/test_solver_runtime_entry_layer02.py`
- `tests/unit/asteroid_lab/test_artifact_ingest.py`

## Validation Plan

- lint: `ruff check django_apps/asteroid_lab/`
- typecheck: `mypy django_apps config src`
- tests: targeted pytest for sync subprocess + exit 20
- build: `python manage.py check`
- manual verification: Sync and async paths produce same SolverRun status for stack-failure artifact

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Depends on High plan; may overlap SHA-45 — implementer should check for duplicate work.
- Async path may ingest partial artifacts by design; confirm contract before changing reject behavior.
