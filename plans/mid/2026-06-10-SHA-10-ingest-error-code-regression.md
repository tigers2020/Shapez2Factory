---
linear_issue: SHA-10
title: Missing regression for artifact ingest when manifest.error_code is set
priority: Mid
labels:
  - test
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Regression test for artifact ingest when manifest.error_code is set

## Source Issue

- Linear: SHA-10
- Status at planning time: Todo
- Priority: Mid

## Problem

`ingest_artifact_for_project` maps `manifest.error_code` to FAILED status and skips warm-cache for non-COMPLETED runs, but no unit test covers this path.

## Scope

Add unit test with hashed payload and non-null `error_code`; assert FAILED lifecycle and warm-cache not invoked.

## Non-goals

- Do not change CLI/subprocess error_code selection.
- Do not fix exit-code table (SHA-7).

## Implementation Plan

1. Review `artifact_ingest.py` branch on `manifest.error_code`.
2. Build fixture artifact with valid hashes and `error_code` (e.g. `STACK_UNAVAILABLE`).
3. Assert `SolverRun` status FAILED, `lifecycle_status=failed`, config preserved.
4. Mock warm-cache helper; assert not called.
5. Run `pytest tests/unit/asteroid_lab/test_artifact_ingest.py -v`.

## Files / Areas Likely Affected

- `tests/unit/asteroid_lab/test_artifact_ingest.py`
- `django_apps/asteroid_lab/services/artifact_ingest.py` (read-only)

## Validation Plan

- tests: `pytest tests/unit/asteroid_lab/test_artifact_ingest.py -v`
- lint: `ruff check tests/unit/asteroid_lab/`

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Pair with SHA-8 CLI exit test for E2E confidence (Low).
