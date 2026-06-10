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

# Plan: Propagate stack-failure error_code and fix Django ingest status

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

- Changing CLI exit code enum values.
- Altering successful artifact schema.

## Implementation Plan

1. Trace CLI artifact finalization path for stack failures (`failed_layer_slug`, exit 20) in `src/shapez2_factory/interfaces/cli/asteroid_solve.py` and artifact writer/manifest builder modules.
2. Populate `manifest.error_code` from `failed_layer_slug` / stack failure reason during finalize (use existing error code constants if defined).
3. Read `django_apps/asteroid_lab/services/artifact_ingest.py` (`ingest_artifact_for_project`); identify COMPLETED indexing branch when `error_code` is null.
4. Update ingest to check `solver_summary.run_success`, `manifest.error_code`, and subprocess exit semantics before marking COMPLETED.
5. Add regression tests for exit-20 artifact ingest path (manifest has error_code; Django status FAILED not COMPLETED).
6. Run `pytest tests/unit/asteroid_lab/test_artifact_ingest.py -v` and related CLI exit-code tests.

## Files / Areas Likely Affected

- `src/shapez2_factory/interfaces/cli/asteroid_solve.py`
- Artifact manifest builder / `AtomicArtifactWriter` finalize path (TBD — grep `error_code` under `src/shapez2_factory/adapters/asteroid_lab/`)
- `django_apps/asteroid_lab/services/artifact_ingest.py`
- `tests/unit/asteroid_lab/test_artifact_ingest.py`
- `tests/unit/shapez2_factory/test_cli_exit_codes.py` (related exit 20 coverage)

## Validation Plan

- lint: `ruff check src/shapez2_factory/ django_apps/asteroid_lab/services/`
- typecheck: `mypy django_apps config src`
- tests: artifact ingest + CLI exit 20 regression tests
- build: N/A
- manual verification: Stack-failure artifact ingest shows FAILED lifecycle in Django admin/UI

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Error code enum alignment with SHA-7 exit-code docs and SHA-10 ingest regression scope.
- Async vs sync ingest paths (SHA-45) may need coordinated fix — Mid plan.
