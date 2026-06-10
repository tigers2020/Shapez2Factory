---
linear_issue: SHA-12
title: reconcile_solver_run leaks ArtifactIngestError to async status poll (HTTP 500)
priority: High
labels:
  - bug
  - priority:high
status: done
created_by: todo-plan-automation
---

# Plan: Catch ArtifactIngestError in reconcile_solver_run

## Source Issue

- Linear: SHA-12
- Status at planning time: Todo
- Priority: High

## Problem

`_attempt_artifact_ingest` does not catch `ArtifactIngestError`. Valid manifest+hash but failed ingest (e.g. invalid JSON in hashed `solver_summary`) raises through reconcile → async status GET returns HTTP 500.

## Scope

Catch `ArtifactIngestError` in reconcile path; mark run terminal failed; ensure status view always returns JSON.

## Non-goals

- Do not change manifest hash rules.
- Do not fix SHA-9 empty-summary root cause in this plan.

## Implementation Plan

1. Read `_attempt_artifact_ingest` in `solver_run_reconcile.py`; note existing `ArtifactManifestReadError` handling.
2. Wrap `ingest_artifact_for_project` in try/except `ArtifactIngestError`.
3. On catch: `_mark_run_failed_locked` with `artifact_ingest_failed` or mirror `RECONCILE_FAILURE_VALIDATION` pattern per issue.
4. Add unit test: hashed `NOT-JSON` solver_summary → failed run, no exception leak.
5. Verify async status view returns structured JSON on reconcile failure.
6. Run `pytest tests/unit/asteroid_lab/test_reconcile_solver_run.py -v`.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/solver_run_reconcile.py`
- `django_apps/asteroid_lab/services/artifact_ingest.py`
- `django_apps/web/views/public_pages.py` (status view)
- `tests/unit/asteroid_lab/test_reconcile_solver_run.py`

## Validation Plan

- tests: `pytest tests/unit/asteroid_lab/test_reconcile_solver_run.py -v`
- lint: `ruff check django_apps/asteroid_lab/services/solver_run_reconcile.py`
- manual verification: Repro from issue (hashed invalid JSON)

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Error code naming must align with existing reconcile failure enums.
