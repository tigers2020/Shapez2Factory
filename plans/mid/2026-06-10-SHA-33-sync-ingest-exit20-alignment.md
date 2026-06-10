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

# Plan: Align sync ingest path with async artifact-first contract (SHA-45 cross-ref)

## Source Issue

- Linear: SHA-33 (Mid slice — related ingest mapping with SHA-45)
- Status at planning time: In Progress
- Priority: Mid

## Problem

Related ingest mapping inconsistencies with SHA-45: sync `run_solver_subprocess` rejects exit 20 before artifact ingest, while async reconcile ingests from manifest regardless of return code. Even after SHA-33 High fixes `manifest.error_code` and ingest FAILED mapping, sync callers (`manage.py run_solver`, sync HTTP path) still discard stack-failure artifacts because `run_solver_subprocess` raises on non-zero exit before `ingest_artifact_for_project` runs.

## Scope

Document coordination with SHA-45 and verify end-to-end stack-failure indexing once both plans land. This Mid plan covers cross-path verification only if SHA-45 is not yet merged; if SHA-45 is already In Progress separately, limit to integration test wiring after both fixes.

## Non-goals

- Rewriting SHA-45 subprocess allowlist (owned by SHA-45 issue).
- Changing async reconcile behavior.
- CLI exit-code taxonomy (SHA-7).

## Implementation Plan

1. Read SHA-45 plan/issue and `django_apps/asteroid_lab/services/solver_subprocess_runner.py` raise path (lines ~192–195).
2. After SHA-33 High merges: add integration-style unit test that mocks subprocess returncode 20 + valid artifact dir with `error_code` set → assert `ingest_artifact_for_project` is reached and `SolverRun.status=FAILED`.
3. If SHA-45 not merged: file follow-up comment on SHA-45 linking this test dependency; do not duplicate subprocess allowlist work here.
4. Run `pytest tests/unit/asteroid_lab/test_solver_subprocess_runner.py tests/unit/asteroid_lab/test_artifact_ingest.py -v`.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/solver_subprocess_runner.py` (SHA-45 primary)
- `django_apps/asteroid_lab/services/solver_runtime_entry.py`
- `tests/unit/asteroid_lab/test_solver_subprocess_runner.py`
- `tests/unit/asteroid_lab/test_artifact_ingest.py`

## Validation Plan

- lint: `ruff check django_apps/asteroid_lab/services/`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/asteroid_lab/test_solver_subprocess_runner.py tests/unit/asteroid_lab/test_artifact_ingest.py -v`
- build: `python manage.py check`
- manual verification: `manage.py run_solver` on stack-failure fixture indexes FAILED row (requires SHA-45 + SHA-33 High)

## Acceptance Criteria

- [ ] Matches the source issue spec (Mid priority breakdown item).
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- SHA-45 is already In Progress separately — avoid duplicate implementation; this plan may reduce to verification-only.
- Sync/async divergence is a product contract decision documented in PR-CLI-7; confirm with canon before changing raise semantics.
