---
linear_issue: SHA-29
title: AtomicArtifactWriter accepts run_key outside Guard C charset (weaker than run_key_safety)
priority: Low
labels:
  - bug
  - test
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Consolidate assert_safe_run_key across writer, CLI, and Django subprocess

## Source Issue

- Linear: SHA-29
- Status at planning time: In Progress
- Priority: Low (optional follow-up from SHA-29)

## Problem

Guard C charset validation is duplicated: `run_key_safety._RUN_KEY_RE`, `artifact_writer._validate_run_key` (pre-fix), and `solver_subprocess_runner._RUN_KEY_RE`. Even after the mid-priority writer fix, three call sites may still diverge unless a single exported helper is adopted everywhere.

## Scope

- Export `assert_safe_run_key(run_key: str) -> None` from `run_key_safety` (if not done in mid plan).
- Refactor `solver_subprocess_runner` to use the shared helper instead of local regex.
- Audit CLI `asteroid_solve.py` for redundant inline checks; delegate to shared helper where charset-only validation is needed.
- Add unit test that all three entry points reject the same bad-key set.

## Non-goals

- Changing containment (`relative_to`) logic in `resolve_artifact_dir`.
- Altering error types at CLI/Django boundaries beyond mapping to existing exceptions.

## Implementation Plan

1. Confirm `assert_safe_run_key` exists and is exported from `run_key_safety.__all__`.
2. Replace `_RUN_KEY_RE` usage in `django_apps/asteroid_lab/services/solver_subprocess_runner.py` with `assert_safe_run_key`; map `ArtifactPathError` → `SolverSubprocessError`.
3. Grep for other `_RUN_KEY_RE` or ad-hoc run_key regex in repo; replace with import.
4. Add `test_run_key_guard_consistency_across_call_sites` asserting identical rejection for `["foo bar", "foo@bar"]` at writer, subprocess runner, and `resolve_artifact_dir`.
5. Run `pytest tests/unit/shapez2_factory/test_run_key_safety.py tests/unit/asteroid_lab/test_solver_subprocess_runner.py -v` (adjust path if needed).
6. Commit: `refactor(artifact): single assert_safe_run_key for all run_key guards`.

## Files / Areas Likely Affected

- `src/shapez2_factory/adapters/asteroid_lab/run_key_safety.py`
- `django_apps/asteroid_lab/services/solver_subprocess_runner.py`
- `src/shapez2_factory/interfaces/cli/asteroid_solve.py` (audit only)
- `tests/unit/shapez2_factory/test_run_key_safety.py`

## Validation Plan

- lint: `ruff check .`
- typecheck: `mypy django_apps config src`
- tests: targeted pytest on run_key and subprocess modules
- build: N/A
- manual verification: grep shows no duplicate `_RUN_KEY_RE` outside `run_key_safety.py`

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Optional; defer if mid plan already deduplicates Django runner.
- Django layer importing pure `run_key_safety` is allowed (adapter boundary).
