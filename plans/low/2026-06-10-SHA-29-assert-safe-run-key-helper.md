---
linear_issue: SHA-29
title: Optional assert_safe_run_key consolidation across call sites
priority: Low
labels:
  - bug
  - test
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Consolidate assert_safe_run_key across CLI and Django call sites

## Source Issue

- Linear: SHA-29
- Status at planning time: Todo
- Priority: Low

## Problem

After the mid-priority fix, `assert_safe_run_key` may exist in `run_key_safety` but CLI (`asteroid_solve.py`) and Django (`solver_subprocess_runner.py`) may still duplicate charset or containment checks inline. Optional consolidation reduces future drift.

## Scope

- Audit all `run_key` validation call sites (CLI, Django, writer).
- Where charset-only checks duplicate `assert_safe_run_key`, replace with import.
- Where full path resolution is needed, prefer `resolve_artifact_dir` over reimplemented containment.

## Non-goals

- Changing error types or exit-code mapping at CLI boundary.
- Refactoring unrelated path-safety guards (Guard A/B/D from artifact spec).
- Mandatory completion — skip if mid plan already fully deduplicates.

## Implementation Plan

1. Grep for `_RUN_KEY_RE`, `_validate_run_key`, `unsafe run_key`, `ArtifactPathError` across repo.
2. In `asteroid_solve.py`, confirm `resolve_artifact_dir` is the sole Guard C entry; remove any redundant inline charset checks if present.
3. In `solver_subprocess_runner.py`, if mid plan left duplicate containment, replace `resolve_subprocess_artifact_dir` body with `resolve_artifact_dir` + `SolverSubprocessError` wrapper.
4. Add a short comment in `run_key_safety.py` docstring listing canonical consumers (writer, CLI, Django).
5. No new tests unless a dedup reveals a gap; rely on existing `test_run_key_safety.py`.

## Files / Areas Likely Affected

- `src/shapez2_factory/interfaces/cli/asteroid_solve.py`
- `django_apps/asteroid_lab/services/solver_subprocess_runner.py`
- `src/shapez2_factory/adapters/asteroid_lab/run_key_safety.py`

## Validation Plan

- lint: `ruff check .`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/shapez2_factory/test_run_key_safety.py -v`
- build: N/A
- manual verification: grep confirms no remaining `_RUN_KEY_RE` outside `run_key_safety.py`

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Django layer may need `SolverSubprocessError` instead of `ArtifactPathError` — wrapper required, not raw import.
- Defer entirely if mid plan already achieves single-source charset validation and containment dedup is judged too invasive.
