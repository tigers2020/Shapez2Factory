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

# Plan: Consolidate assert_safe_run_key helper (SHA-29 Low)

## Source Issue

- Linear: SHA-29
- Status at planning time: Todo
- Priority: Low

## Problem

Run_key validation logic is duplicated across `AtomicArtifactWriter`, `run_key_safety`, CLI (`asteroid_solve.py`), and Django `solver_subprocess_runner`. After Mid-priority unification, optional consolidation can reduce future drift.

## Scope

Optional: export a single `assert_safe_run_key(run_key: str) -> None` used by writer, CLI, and Django subprocess wrapper.

## Non-goals

- Changing the allowed run_key charset.
- Broad path-safety refactor beyond run_key assertion helper.
- Blocking Mid plan on this polish.

## Implementation Plan

1. After Mid plan lands, inventory all run_key validation entry points via `rg '_validate_run_key|_RUN_KEY_RE|resolve_artifact_dir' src/ django_apps/`.
2. If `run_key_safety` already exposes sufficient API post-Mid, add thin `assert_safe_run_key` alias or document existing function as canonical.
3. Replace inline `_RUN_KEY_RE` checks in `solver_subprocess_runner.py` with import from shared module (if layer boundary allows).
4. Add one-line doc cross-link in artifact design spec cross-cutting guards table if helper name changes.
5. Run existing run_key and subprocess tests to confirm no behavior change.

## Files / Areas Likely Affected

- `src/shapez2_factory/adapters/asteroid_lab/run_key_safety.py`
- `django_apps/asteroid_lab/services/solver_subprocess_runner.py`
- `src/shapez2_factory/interfaces/cli/asteroid_solve.py` (read-only unless import swap is trivial)
- TBD — other call sites found by grep

## Validation Plan

- lint: `ruff check src/shapez2_factory/adapters/asteroid_lab/ django_apps/asteroid_lab/services/`
- typecheck: `mypy django_apps config src` (changed modules)
- tests: `pytest tests/unit/shapez2_factory/test_run_key_safety.py -v` plus subprocess runner tests if present
- build: N/A
- manual verification: No duplicate regex definitions remain in subprocess runner

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Depends on Mid plan completion; defer if Mid not merged.
- Django adapter importing from `src/` may already be established pattern — verify before new coupling.
