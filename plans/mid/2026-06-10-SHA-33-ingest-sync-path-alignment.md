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

# Plan: Ingest sync-path alignment for stack failures

## Source Issue

- Linear: SHA-33
- Status at planning time: Todo
- Priority: Mid

## Problem

Related ingest mapping inconsistencies exist between async artifact ingest and sync `run_solver_subprocess` path (SHA-45): sync path may reject exit 20 before ingest while async path ingests stack-failure artifacts as COMPLETED.

## Scope

- Align sync and async ingest behavior for stack-failure artifacts after High plan fixes manifest `error_code`.
- Ensure both paths index FAILED status consistently.

## Non-goals

- Changing subprocess exit code semantics.
- Rewriting async job queue architecture.

## Implementation Plan

1. After High plan merges, audit `solver_runtime_entry.py` and `solver_subprocess_runner.py` for exit-20 handling.
2. Compare async ingest path vs sync `run_solver_subprocess` rejection before ingest (SHA-45).
3. Unify: either both ingest with FAILED status (preferred) or both reject — document chosen contract.
4. Add regression test covering sync subprocess exit 20 → ingest → FAILED `SolverRun`.
5. Cross-reference SHA-45; close or link if resolved by same change set.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/solver_runtime_entry.py`
- `django_apps/asteroid_lab/services/solver_subprocess_runner.py`
- `tests/unit/asteroid_lab/test_solver_runtime_entry_layer02.py`
- `tests/unit/asteroid_lab/test_artifact_ingest.py`

## Validation Plan

- lint: `ruff check .`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/asteroid_lab/test_solver_runtime_entry_layer02.py tests/unit/asteroid_lab/test_artifact_ingest.py -v`
- build: `python manage.py check`
- manual verification: Compare sync vs async run-solver paths on stack-failure fixture.

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Depends on High plan (`plans/high/2026-06-10-SHA-33-stack-failure-manifest-error-code.md`).
- SHA-45 may need separate closure if sync rejection is intentional for a different contract.
