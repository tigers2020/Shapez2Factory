---
linear_issue: SHA-15
title: RunStackUseCase sets validation_passed from stack success while L6 commit-validate is no-op
priority: Mid
labels:
  - bug
  - solver
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Align validation_passed with L6 commit-validate reality

## Source Issue

- Linear: SHA-15
- Status at planning time: Todo
- Priority: Mid

## Problem

`solver_summary.validation_passed = run_ok` conflates stack completion with L6 validation. L6 is currently a no-op stub, causing false-positive validation in CLI artifacts and Lab UI.

## Scope

Adjust `validation_passed` semantics or surface pending/stub state without implying L6 ran real checks.

## Non-goals

- Do not implement full L6 validation in this issue unless spec expands.
- Do not change unrelated layer behavior.

## Implementation Plan

1. Read `run_stack.py` and `layer_06_commit_validate/run.py` stub behavior.
2. Read layer-stack renumber spec for intended L6 contract.
3. Choose contract: `validation_passed=false` when L6 stub, or new field `validation_pending=true`.
4. Update `solver_run_lab_summary.py` display mapping.
5. Update `test_cli_run_artifact.py` expectations.
6. Document semantics in spec or inline until L6 implemented.

## Files / Areas Likely Affected

- `src/shapez2_factory/application/asteroid_lab/run_stack.py`
- `src/shapez2_factory/application/asteroid_lab/layers/layer_06_commit_validate/run.py`
- `django_apps/asteroid_lab/services/solver_run_lab_summary.py`
- `tests/unit/shapez2_factory/test_cli_run_artifact.py`
- `docs/superpowers/specs/2026-05-31-layer-stack-l4-l5-renumber-design.md`

## Validation Plan

- tests: `pytest tests/unit/shapez2_factory/test_cli_run_artifact.py -v`
- lint/typecheck on touched modules

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Product decision: false vs pending semantics.
