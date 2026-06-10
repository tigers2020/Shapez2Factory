---
linear_issue: SHA-33
title: Stack-failure artifacts write manifest.error_code=null; Django ingest indexes COMPLETED
priority: High
labels:
  - bug
  - priority:high
status: planned
created_by: todo-plan-automation
---

# Plan: Stack-failure manifest error_code and ingest status

## Source Issue

- Linear: SHA-33
- Status at planning time: Todo
- Priority: High

## Problem

When the L2–L6 stack fails (`failed_layer_slug` set, CLI exit `STACK_UNAVAILABLE` / 20), the CLI finalizes an artifact with `manifest.error_code=null`. Django `ingest_artifact_for_project` treats null `error_code` as success and writes `SolverRun.status=COMPLETED` / `lifecycle_status=succeeded`, contradicting `solver_summary.run_success: false` and non-zero subprocess exit.

## Scope

- Populate `manifest.error_code` on stack-failure artifact finalization in CLI.
- Update Django ingest to treat stack-failure artifacts as failed runs (check `error_code` and/or `run_success`).
- Add regression tests for exit-20 artifact ingest path.

## Non-goals

- Changing CLI exit code enum values.
- Altering successful artifact schema.

## Implementation Plan

1. Locate CLI artifact finalization where `manifest.error_code` is written (artifact writer / `RunStackUseCase`).
2. When `failed_layer_slug` is set or stack returns failure, set `manifest.error_code` to `STACK_UNAVAILABLE` (or canonical error constant from exit-code table).
3. In `django_apps/asteroid_lab/services/artifact_ingest.py`, extend status derivation: if `manifest.error_code` is set OR `solver_summary.run_success` is false, mark `SolverRun.RunStatus.FAILED`.
4. Add unit test in `tests/unit/asteroid_lab/test_artifact_ingest.py`: fixture artifact with `failed_layer_slug` + `run_success: false` ingests as FAILED.
5. Add CLI unit test asserting finalized manifest carries non-null `error_code` on stack failure.
6. Run `pytest tests/unit/asteroid_lab/test_artifact_ingest.py tests/unit/shapez2_factory/test_validate_artifact.py -v`.

## Files / Areas Likely Affected

- `src/shapez2_factory/` (artifact writer, `RunStackUseCase`, manifest DTO)
- `django_apps/asteroid_lab/services/artifact_ingest.py`
- `tests/unit/asteroid_lab/test_artifact_ingest.py`
- `tests/unit/shapez2_factory/test_validate_artifact.py`

## Validation Plan

- lint: `ruff check .`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/asteroid_lab/test_artifact_ingest.py tests/unit/shapez2_factory/test_validate_artifact.py -v`
- build: `python manage.py check`
- manual verification: Trigger stack failure via CLI; ingest artifact; confirm Django shows FAILED.

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Must align with SHA-10 (manifest.error_code regression) and SHA-8 (exit 20 coverage) without duplicating tests.
- `ingest_artifact_for_project` line 170 currently: `FAILED if manifest.error_code else COMPLETED` — fix depends on CLI populating error_code.
