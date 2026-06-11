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

# Plan: Propagate stack-failure error codes through manifest and Django ingest

## Source Issue

- Linear: SHA-33
- Status at planning time: Todo
- Priority: High

## Problem

When the L2–L6 stack fails (`failed_layer_slug` set, CLI exit `STACK_UNAVAILABLE` / 20), the CLI still finalizes an artifact whose `manifest.error_code` is always `null`. Django `ingest_artifact_for_project` treats a null `error_code` as success and writes `SolverRun.status=COMPLETED` / `lifecycle_status=succeeded`, even though `solver_summary.json` records `run_success: false` and the subprocess exited non-zero.

## Scope

- Set `manifest.error_code` on stack-failure artifact finalization.
- Update Django ingest to treat stack-failure artifacts as failed runs.

## Non-goals

- Changing CLI exit code enum values (0/10/20).
- Altering successful artifact schema.

## Implementation Plan

1. Trace CLI artifact finalization in `asteroid_solve.py` / `run_stack.py` — locate where `manifest.error_code` is written; populate from `failed_layer_slug` or stack failure reason when `run_success` is false.
2. Confirm canonical error code constant for stack unavailable (align with `ExitCode.STACK_UNAVAILABLE` / manifest schema).
3. Update `ingest_artifact_for_project` (`django_apps/asteroid_lab/services/`) to fail closed when `manifest.error_code` is set or `solver_summary.run_success` is false before marking `SolverRun.status=COMPLETED`.
4. Add regression tests in `tests/unit/asteroid_lab/test_artifact_ingest.py` for exit-20 / stack-failure artifact ingest path.
5. Run `pytest tests/unit/asteroid_lab/test_artifact_ingest.py tests/unit/shapez2_factory/test_cli_exit_codes.py -v`.

## Files / Areas Likely Affected

- `src/shapez2_factory/interfaces/cli/asteroid_solve.py`
- `src/shapez2_factory/application/asteroid_lab/run_stack.py`
- `django_apps/asteroid_lab/services/` (artifact ingest — grep `ingest_artifact_for_project`)
- `tests/unit/asteroid_lab/test_artifact_ingest.py`
- `tests/unit/shapez2_factory/test_cli_exit_codes.py`

## Validation Plan

- lint: `ruff check django_apps/asteroid_lab/ src/shapez2_factory/`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/asteroid_lab/test_artifact_ingest.py tests/unit/shapez2_factory/test_cli_exit_codes.py -v`
- build: `python manage.py check`
- manual verification: Stack-failure artifact ingest yields FAILED SolverRun, not COMPLETED

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Sync subprocess path (SHA-45) may reject exit 20 before ingest — coordinate but do not expand scope.
- Do not collapse `VALIDATION_FAILED` (10) with stack failure (20) semantics.
