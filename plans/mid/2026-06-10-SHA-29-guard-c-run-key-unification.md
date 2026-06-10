---
linear_issue: SHA-29
title: AtomicArtifactWriter accepts run_key outside Guard C charset (weaker than run_key_safety)
priority: Mid
labels:
  - bug
  - test
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Unify Guard C run_key validation in AtomicArtifactWriter

## Source Issue

- Linear: SHA-29
- Status at planning time: Todo
- Priority: Mid

## Problem

`AtomicArtifactWriter` uses a local `_validate_run_key` that only rejects empty, `.`/`..`, path separators, and control characters. It does not enforce the Guard C charset `^[A-Za-z0-9._-]+$` that `run_key_safety.resolve_artifact_dir` applies. Keys like `foo bar` or `foo@bar` pass writer construction but fail the canonical Guard C module, splitting the BA-5 artifact write path from the artifact design spec.

## Scope

- Replace `_validate_run_key` in `artifact_writer.py` with delegation to `run_key_safety` (map `ArtifactPathError` → `InvalidRunKeyError`).
- Add regression tests proving `AtomicArtifactWriter` rejects non-Guard-C run keys (`foo bar`, `foo@bar`, `foo*bar`, etc.).
- Deduplicate Django `solver_subprocess_runner._RUN_KEY_RE` by importing the same guard from `run_key_safety`.

## Non-goals

- Changing the allowed run_key charset itself.
- Altering CLI exit-code mapping or artifact manifest schema.
- Broad refactor of all path-safety call sites beyond run_key validation unification.
- Exporting a shared `assert_safe_run_key` helper (deferred to low-priority plan).

## Implementation Plan

1. **Export charset validation from `run_key_safety`**
   - Add `assert_safe_run_key(run_key: str) -> None` that raises `ArtifactPathError` on invalid charset/separators/dot tokens (no path resolution).
   - Refactor `resolve_artifact_dir` to call `assert_safe_run_key` before containment check.
   - Update `__all__` to export `assert_safe_run_key`.

2. **Delegate writer validation**
   - In `artifact_writer.py`, replace `_validate_run_key` body:
     ```python
     from shapez2_factory.adapters.asteroid_lab.run_key_safety import (
         ArtifactPathError,
         assert_safe_run_key,
     )

     def _validate_run_key(run_key: str) -> None:
         try:
             assert_safe_run_key(run_key)
         except ArtifactPathError as exc:
             raise InvalidRunKeyError(str(exc)) from exc
     ```

3. **Write failing regression test**
   - Create `tests/unit/shapez2_factory/test_artifact_writer_run_key_guard.py` (or add to existing collision test module).
   - Parametrize bad keys: `foo bar`, `foo@bar`, `foo*bar`, `foo:bar`, `a$b`, `abc\n`, `""`, `.`, `..`, `a/b`.
   - Assert `pytest.raises(InvalidRunKeyError)` on `AtomicArtifactWriter(tmp_path, bad_key)`.
   - Assert valid key `run-abc_1.2` still constructs.

4. **Deduplicate Django subprocess guard**
   - In `solver_subprocess_runner.py`, remove local `_RUN_KEY_RE` and `re` import.
   - Import `assert_safe_run_key` and `ArtifactPathError` from `run_key_safety`.
   - In `resolve_subprocess_artifact_dir`, call `assert_safe_run_key(run_key)` and map `ArtifactPathError` → `SolverSubprocessError`.
   - Keep containment `relative_to` logic in Django layer (or optionally delegate full path to `resolve_artifact_dir` — only if error mapping stays equivalent).

5. **Run validation gates**
   - `pytest tests/unit/shapez2_factory/test_artifact_writer_run_key_guard.py tests/unit/shapez2_factory/test_run_key_safety.py tests/unit/shapez2_factory/test_artifact_writer_collision.py -v`
   - `ruff check .`
   - `mypy django_apps config src`

## Files / Areas Likely Affected

- `src/shapez2_factory/adapters/asteroid_lab/run_key_safety.py`
- `src/shapez2_factory/adapters/asteroid_lab/artifact_writer.py`
- `django_apps/asteroid_lab/services/solver_subprocess_runner.py`
- `tests/unit/shapez2_factory/test_artifact_writer_run_key_guard.py` (new)
- `tests/unit/shapez2_factory/test_run_key_safety.py` (extend if `assert_safe_run_key` exported)
- `docs/superpowers/specs/2026-05-30-asteroid-lab-cli-first-artifact-design.md` (reference only; no schema change)

## Validation Plan

- lint: `ruff check .`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/shapez2_factory/test_artifact_writer_run_key_guard.py tests/unit/shapez2_factory/test_run_key_safety.py -v`
- build: N/A
- manual verification: confirm `AtomicArtifactWriter(tmp, "foo bar")` raises `InvalidRunKeyError` in REPL

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Writer validates charset only at construction; containment under `allowed_root` remains CLI/Django responsibility via `resolve_artifact_dir`. This matches current writer API (no `allowed_root` param).
- Django `resolve_subprocess_artifact_dir` duplicates containment logic from `resolve_artifact_dir`; full dedup to one function is out of scope unless error mapping is preserved exactly.
- Existing tests that construct `AtomicArtifactWriter` with previously-accepted weak keys must be audited (grep for `AtomicArtifactWriter(`).
