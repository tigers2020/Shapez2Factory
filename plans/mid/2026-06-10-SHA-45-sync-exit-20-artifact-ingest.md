---
linear_issue: SHA-45
title: Sync run_solver_subprocess rejects exit 20 before artifact ingest (async path ingests)
priority: Mid
labels:
  - bug
  - test
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Sync run_solver_subprocess rejects exit 20 before artifact ingest (async path ingests)

## Source Issue

- Linear: SHA-45
- Status at planning time: Todo → In Progress (plan file committed on this branch)
- Priority: Mid

## Problem

The blocking Django subprocess runner (`run_solver_subprocess`) raises `SolverSubprocessError` on any non-zero CLI exit code before `solver_runtime_entry` can call `ingest_artifact_for_project`. The CLI returns exit `20` (`ExitCode.STACK_UNAVAILABLE`) when the L2–L6 stack fails but still finalizes a valid `ARTIFACT_WRITTEN` directory. Sync callers therefore discard stack-failure artifacts and return `SOLVER_SUBPROCESS_FAILED` with no `SolverRun` row, even though the artifact exists on disk.

The detached async path does not check return codes; `reconcile_solver_run` ingests from manifest per PR-CLI-7 ("completion uses artifact manifest, not returncode alone"). Sync and async behavior diverge.

## Scope

- Update `run_solver_subprocess` (and sync runtime entry only if needed) to allow ingest when exit code is `STACK_UNAVAILABLE` (20) and a verified artifact directory with `manifest.json` exists.
- Still fail closed on `VALIDATION_FAILED` (10) and unexpected exit codes when no valid manifest is present.
- Add regression test mocking `run_subprocess_with_tee` returncode 20 with artifact dir + manifest present; assert ingest is attempted via `run_solver_subprocess` returning successfully (not raising).

## Non-goals

- Fixing manifest `error_code=null` on stack failure (SHA-33).
- Changing async reconcile behavior.
- Rewriting CLI exit-code taxonomy (SHA-7).
- Adding CLI exit-20 coverage (SHA-8 — parallel but separate).

## Implementation Plan

1. Add Django-layer constant `STACK_UNAVAILABLE_EXIT_CODE = 20` in `django_apps/asteroid_lab/services/solver_subprocess_runner.py` (module string boundary — do not import CLI `ExitCode` enum into Django).
2. In `run_solver_subprocess`, after copying subprocess log to `artifact_dir/logs/subprocess.log`, replace the unconditional `if completed.returncode != 0: raise` block with artifact-first logic:
   - If `returncode == 0`: return `SolverSubprocessResult` (unchanged).
   - If `returncode == STACK_UNAVAILABLE_EXIT_CODE` and `artifact_dir / "manifest.json"` exists: call `read_verified_artifact_manifest(artifact_dir)`; on success return `SolverSubprocessResult` with non-zero `completed.returncode` preserved; on `ArtifactManifestReadError` raise `SolverSubprocessError` (fail closed).
   - Else: raise `SolverSubprocessError` (existing behavior for exit 10, missing manifest, unexpected codes).
3. Confirm `_run_subprocess_runtime_for_project` in `solver_runtime_entry.py` already ingests after `run_solver_subprocess` returns — no change expected unless return shape needs documenting; verify sync path surfaces failed run status from manifest/`solver_summary` after ingest (not `SOLVER_SUBPROCESS_FAILED`).
4. Add `test_run_solver_subprocess_allows_stack_unavailable_when_manifest_present` in `tests/unit/asteroid_lab/test_solver_subprocess_runner.py`:
   - Monkeypatch `run_subprocess_with_tee` to return `returncode=20`, create `artifact_dir` with minimal valid `manifest.json` fixture (reuse patterns from `test_artifact_manifest_reader.py` or sibling ingest tests).
   - Assert `run_solver_subprocess` returns without raising and `result.completed.returncode == 20`.
5. Add `test_run_solver_subprocess_stack_unavailable_without_manifest_raises` — returncode 20, no manifest → `SolverSubprocessError`.
6. Optionally add integration-level test in `test_solver_runtime_entry.py` asserting ingest attempted when subprocess returns 20 + manifest (only if existing fixtures make this cheap).
7. Run focused tests and lint gates.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/solver_subprocess_runner.py`
- `django_apps/asteroid_lab/services/artifact_manifest_reader.py` (import `read_verified_artifact_manifest`)
- `django_apps/asteroid_lab/services/solver_runtime_entry.py` (verify only; change only if ingest gate still blocks)
- `tests/unit/asteroid_lab/test_solver_subprocess_runner.py`
- `src/shapez2_factory/interfaces/cli/asteroid_solve.py` (read-only reference for exit 20 semantics)
- `django_apps/asteroid_lab/services/solver_run_reconcile.py` (read-only reference for async artifact-first pattern)
- `docs/superpowers/plans/2026-05-30-asteroid-lab-cli-first/pr-cli-7-async-solver-job.md` (contract reference)

## Validation Plan

- lint: `ruff check django_apps/asteroid_lab/services/solver_subprocess_runner.py tests/unit/asteroid_lab/test_solver_subprocess_runner.py`
- typecheck: `mypy django_apps config src` (spot-check changed modules)
- tests: `pytest tests/unit/asteroid_lab/test_solver_subprocess_runner.py -v`
- build: N/A
- manual verification: `manage.py run_solver --slug <slug-with-stack-failure>` should create `SolverRun` row when artifact dir exists despite exit 20

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- SHA-33: ingest may still index `COMPLETED` with `error_code=null` on stack failure — out of scope but affects surfaced status after this fix.
- Preserve non-zero `returncode` on `SolverSubprocessResult` so callers can log stack-unavailable without treating it as subprocess crash.
- Exit 20 without valid manifest must remain fail-closed (same as async reconcile `_attempt_artifact_ingest` guard).
