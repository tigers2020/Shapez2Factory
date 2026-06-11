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
- Status at planning time: Todo
- Priority: Mid

## Problem

The blocking Django subprocess runner (`run_solver_subprocess`) raises `SolverSubprocessError` on any non-zero CLI exit code before `solver_runtime_entry` can call `ingest_artifact_for_project`. The CLI returns exit `20` (`ExitCode.STACK_UNAVAILABLE`) when the L2–L6 stack fails but still finalizes a valid `ARTIFACT_WRITTEN` directory. Sync callers therefore discard stack-failure artifacts and return `SOLVER_SUBPROCESS_FAILED` with no `SolverRun` row, even though the artifact exists on disk.

The detached async path does not check return codes; `reconcile_solver_run` ingests from manifest per PR-CLI-7 ("completion uses artifact manifest, not returncode alone"). Sync and async behavior diverge.

## Scope

- Update `run_solver_subprocess` (and sync runtime entry only if the runner change is insufficient) to allow ingest when exit code is `STACK_UNAVAILABLE` (20) and a verified artifact directory with `manifest.json` exists after subprocess completes.
- Still fail closed on `VALIDATION_FAILED` (10) and unexpected exit codes when no valid manifest is present.
- Add regression test mocking `run_subprocess_with_tee` with `returncode=20`, artifact dir, and manifest present; assert `run_solver_subprocess` returns `SolverSubprocessResult` (does not raise) and runtime entry attempts ingest.

## Non-goals

- Fixing manifest `error_code=null` on stack failure (SHA-33).
- Changing async reconcile behavior.
- Rewriting CLI exit-code taxonomy (SHA-7).
- Adding CLI-level exit-20 test (SHA-8).

## Implementation Plan

1. Add a Django adapter constant for CLI exit `20` (duplicate `STACK_UNAVAILABLE = 20` in `solver_subprocess_runner.py` or a small `cli_exit_codes.py` module — do not import `shapez2_factory` from Django to preserve module boundary).
2. In `run_solver_subprocess`, after copying the sidecar log to `artifact_dir/logs/subprocess.log`, replace the unconditional `if completed.returncode != 0: raise` block with artifact-first logic:
   - If `returncode == 0`: return `SolverSubprocessResult` as today.
   - If `returncode == STACK_UNAVAILABLE` and `(artifact_dir / "manifest.json").is_file()`: return `SolverSubprocessResult` with non-zero `completed.returncode` (do not raise).
   - Else: raise `SolverSubprocessError` with existing message including exit code.
3. Confirm `_run_subprocess_runtime_for_project` in `solver_runtime_entry.py` already calls `ingest_artifact_for_project` when `run_solver_subprocess` returns — no runtime-entry change expected unless ingest is gated elsewhere on `returncode`.
4. Add `test_run_solver_subprocess_allows_stack_unavailable_when_manifest_present` in `tests/unit/asteroid_lab/test_solver_subprocess_runner.py`:
   - Monkeypatch `run_subprocess_with_tee` to create `artifact_dir`, write sidecar log, write minimal `manifest.json`, return `returncode=20`.
   - Assert `run_solver_subprocess` returns without raising; `result.completed.returncode == 20`; subprocess log copied under artifact dir.
5. Add integration-style unit test (optional same file or `test_solver_runtime_entry.py`) asserting `_run_subprocess_runtime_for_project` reaches `ingest_artifact_for_project` when subprocess returns exit 20 with valid manifest (mock ingest if ORM setup is heavy).
6. Add negative case: `returncode=20` without `manifest.json` still raises `SolverSubprocessError`.
7. Add negative case: `returncode=10` (`VALIDATION_FAILED`) still raises even if artifact dir exists (fail closed per spec).

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/solver_subprocess_runner.py`
- `django_apps/asteroid_lab/services/solver_runtime_entry.py` (verify only; change only if needed)
- `tests/unit/asteroid_lab/test_solver_subprocess_runner.py`
- `src/shapez2_factory/interfaces/cli/asteroid_solve.py` (read-only reference for `ExitCode.STACK_UNAVAILABLE`)
- `docs/superpowers/plans/2026-05-30-asteroid-lab-cli-first/pr-cli-7-async-solver-job.md` (contract reference)

## Validation Plan

- lint: `ruff check django_apps/asteroid_lab/services/solver_subprocess_runner.py tests/unit/asteroid_lab/test_solver_subprocess_runner.py`
- typecheck: `mypy django_apps/asteroid_lab/services/solver_subprocess_runner.py`
- tests: `pytest tests/unit/asteroid_lab/test_solver_subprocess_runner.py -v`
- build: N/A
- manual verification: Run `manage.py run_solver` against a fixture that produces stack failure with artifact written; confirm `SolverRun` row is created and artifact is indexed (optional smoke if fixture available)

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- **SHA-33 follow-on:** After ingest proceeds, manifest `error_code=null` may still yield wrong `COMPLETED` status — out of scope here but implementer should not paper over with hard-coded FAILED; ingest should reflect manifest/solver_summary as today.
- **Manifest verification depth:** Spec says "verified artifact directory"; align with `read_verified_artifact_manifest` usage in reconcile path vs simple `manifest.json` existence check — prefer matching reconcile artifact-first gate without duplicating full verify in runner if existence + ingest-time verify is sufficient.
- **Module boundary:** Duplicating exit constant `20` in Django layer is intentional; document inline comment referencing `asteroid_solve.ExitCode.STACK_UNAVAILABLE`.
- **invariant:** Artifact-first completion must not use subprocess returncode alone as solver input; manifest remains authority per PR-CLI-7.
