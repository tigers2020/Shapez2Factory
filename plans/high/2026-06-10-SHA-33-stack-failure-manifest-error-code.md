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

# Plan: Stack-failure manifest error_code and ingest FAILED status

## Source Issue

- Linear: SHA-33
- Status at planning time: In Progress (triggered from Todo)
- Priority: High

## Problem

When the L2–L6 stack fails (`failed_layer_slug` set, CLI exit `STACK_UNAVAILABLE` / 20), the CLI still finalizes an artifact whose `manifest.error_code` is always `null`. Django `ingest_artifact_for_project` treats a null `error_code` as success and writes `SolverRun.status=COMPLETED` / `lifecycle_status=succeeded`, even though `solver_summary.json` records `run_success: false` and the subprocess exited non-zero.

Root cause in code: `RunStackUseCase.run()` returns `StackRunResult(error_code=None)` unconditionally at line 234 of `run_stack.py`, while `asteroid_solve._run_artifact` passes `result.error_code` into `ArtifactManifest`. Ingest status is derived solely from `manifest.error_code` at `artifact_ingest.py` lines 169–171.

## Scope

- Populate `manifest.error_code` on stack-failure artifact finalization (CLI / `RunStackUseCase`).
- Update Django ingest to treat stack-failure artifacts as failed runs (defense in depth via `run_success` and/or non-null `error_code`).
- Add regression tests for exit-20 artifact ingest path.

## Non-goals

- Changing CLI exit code enum values (`ExitCode.STACK_UNAVAILABLE = 20` stays).
- Altering successful artifact schema.
- Fixing sync subprocess exit-20 rejection before ingest (SHA-45 Mid plan).

## Implementation Plan

1. Define canonical manifest `error_code` string for stack failure (e.g. `stack_unavailable`) aligned with existing ingest/CLI string constants; grep `django_apps/` and `src/` for existing error-code enums before picking the value.
2. In `RunStackUseCase.run()` (`src/shapez2_factory/application/asteroid_lab/run_stack.py`), set `error_code` when `core_result.stack_result.failed_layer_slug is not None`; keep `error_code=None` on success.
3. Confirm `asteroid_solve._run_artifact` already forwards `result.error_code` into `ArtifactManifest` — no CLI change needed beyond step 2.
4. Harden `ingest_artifact_for_project` (`django_apps/asteroid_lab/services/artifact_ingest.py`): mark FAILED when `manifest.error_code` is set **or** `solver_summary.get("run_success") is False` (fail closed on contradiction).
5. Add unit test in `tests/unit/shapez2_factory/` asserting stack-failure `RunStackUseCase` result sets non-null `error_code` and CLI finalize writes it to manifest.
6. Add ingest regression in `tests/unit/asteroid_lab/test_artifact_ingest.py`: fixture with `run_success: false`, valid hashes, and `error_code: "stack_unavailable"` → `SolverRun.status=FAILED`, `lifecycle_status=failed`, warm-cache not invoked.
7. Add ingest regression for legacy gap: `run_success: false` with `error_code: null` → also FAILED after ingest hardening (documents transitional defense).
8. Run `pytest tests/unit/asteroid_lab/test_artifact_ingest.py tests/unit/shapez2_factory/test_cli_run_artifact.py -v`.

## Files / Areas Likely Affected

- `src/shapez2_factory/application/asteroid_lab/run_stack.py`
- `src/shapez2_factory/interfaces/cli/asteroid_solve.py` (verify only)
- `src/shapez2_factory/adapters/asteroid_lab/artifact_manifest.py`
- `django_apps/asteroid_lab/services/artifact_ingest.py`
- `tests/unit/asteroid_lab/test_artifact_ingest.py`
- `tests/unit/shapez2_factory/test_cli_run_artifact.py` (or new stack-failure manifest test)

## Validation Plan

- lint: `ruff check src/shapez2_factory/application/asteroid_lab/run_stack.py django_apps/asteroid_lab/services/artifact_ingest.py`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/asteroid_lab/test_artifact_ingest.py tests/unit/shapez2_factory/ -v -k "artifact or stack"`
- build: `python manage.py check`
- manual verification: Run CLI with a copy that fails a layer; confirm `manifest.error_code` non-null and ingest marks FAILED

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Manifest `error_code` string must match any existing Django/runtime enum (avoid free-form strings if constants exist).
- Ingest `run_success` fallback may mark FAILED for artifacts written before CLI fix lands — confirm that is desired fail-closed behavior.
- SHA-45 sync path still rejects exit 20 before ingest until its Mid plan lands; High plan does not fix that path.
