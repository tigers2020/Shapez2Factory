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

# Plan: Unify AtomicArtifactWriter run_key validation with Guard C

## Source Issue

- Linear: SHA-29
- Status at planning time: Todo
- Priority: Mid

## Problem

`AtomicArtifactWriter` uses a local `_validate_run_key` that is weaker than Guard C in `run_key_safety.resolve_artifact_dir`. The writer accepts run keys containing spaces, `@`, `*`, `:`, and other characters outside `[A-Za-z0-9._-]`, while the canonical Guard C module rejects them.

This splits the BA-5 artifact write path from the Guard C contract documented in the artifact design spec.

## Scope

- Make `AtomicArtifactWriter` delegate run_key validation to `run_key_safety` (or share one helper) so charset and containment rules cannot drift.
- Add regression test(s) proving writer rejects keys like `foo bar`, `foo@bar`, and other non-`[A-Za-z0-9._-]` values.
- Optionally deduplicate Django `solver_subprocess_runner._RUN_KEY_RE` to import the same guard.

## Non-goals

- Changing the allowed run_key charset itself.
- Altering CLI exit-code mapping or artifact manifest schema.
- Broad refactor of all path-safety call sites beyond run_key validation unification.

## Implementation Plan

1. Read `_validate_run_key` in `src/shapez2_factory/adapters/asteroid_lab/artifact_writer.py` and `_RUN_KEY_RE` / `resolve_artifact_dir` in `src/shapez2_factory/adapters/asteroid_lab/run_key_safety.py`; document the gap (writer allows charset violations Guard C rejects).
2. Replace `_validate_run_key` body with a call into `run_key_safety` (map `ArtifactPathError` → `InvalidRunKeyError` or existing writer exception type).
3. Add `test_artifact_writer_rejects_non_guard_c_run_key` in `tests/unit/shapez2_factory/` covering `foo bar`, `foo@bar`, and at least one other non-charset key; assert writer raises before creating artifact dir.
4. Verify existing `tests/unit/shapez2_factory/test_run_key_safety.py` cases still pass unchanged.
5. Inspect `django_apps/asteroid_lab/services/solver_subprocess_runner.py` for duplicate `_RUN_KEY_RE`; if low-risk, route through shared guard helper (see Low plan if deferred).
6. Run targeted tests: `pytest tests/unit/shapez2_factory/test_run_key_safety.py tests/unit/shapez2_factory/test_artifact_writer*.py -v` (adjust glob to actual test module name).

## Files / Areas Likely Affected

- `src/shapez2_factory/adapters/asteroid_lab/artifact_writer.py`
- `src/shapez2_factory/adapters/asteroid_lab/run_key_safety.py`
- `src/shapez2_factory/interfaces/cli/asteroid_solve.py` (read-only — CLI already calls `resolve_artifact_dir`)
- `django_apps/asteroid_lab/services/solver_subprocess_runner.py` (optional dedup)
- `tests/unit/shapez2_factory/test_run_key_safety.py`
- New or extended test module for artifact writer run_key rejection
- `docs/superpowers/specs/2026-05-30-asteroid-lab-cli-first-artifact-design.md` (cross-cutting guards reference — verify only)

## Validation Plan

- lint: `ruff check src/shapez2_factory/adapters/asteroid_lab/`
- typecheck: `mypy django_apps config src` (spot-check changed modules)
- tests: `pytest tests/unit/shapez2_factory/test_run_key_safety.py -v` plus new writer regression test
- build: N/A
- manual verification: Confirm `AtomicArtifactWriter(tmp, "foo bar")` raises; `resolve_artifact_dir` behavior unchanged

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Exception type mapping (`ArtifactPathError` vs `InvalidRunKeyError`) must preserve existing caller expectations.
- Django subprocess runner dedup may be deferred to Low plan if import boundary is awkward.
