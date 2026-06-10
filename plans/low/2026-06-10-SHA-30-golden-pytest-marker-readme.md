---
linear_issue: SHA-30
title: Golden harness compare_golden.py and tests/golden fixtures are not wired to pytest or CI
priority: Low
labels:
  - infra
  - priority:mid
  - test
status: planned
created_by: todo-plan-automation
---

# Plan: Golden pytest marker organization and README polish

## Source Issue

- Linear: SHA-30
- Status at planning time: In Progress (moved before plan creation)
- Priority: Low

## Problem

Optional pytest marker organization and README polish for the golden harness were deferred. Contributors lack a single marker/filter for golden-only runs.

## Scope

- Add `@pytest.mark.golden` registration and apply to golden harness tests.
- Polish `tests/golden/README.md` with marker usage, CI tier, and contributor workflow.

## Non-goals

- Core wiring of fixtures (covered by Mid plan).
- Changing comparator semantics.

## Implementation Plan

1. Add `golden` marker to `[tool.pytest.ini_options].markers` in `pyproject.toml` with description.
2. Decorate golden harness tests with `@pytest.mark.golden` (and `unit` if required for fast gate).
3. Extend README with: `pytest -m golden`, when golden runs in CI vs integration, and ADR/PR note requirement for fixture changes.

## Files / Areas Likely Affected

- `pyproject.toml`
- `tests/unit/harness/test_compare_golden.py`
- `tests/golden/README.md`

## Validation Plan

- lint: `ruff check tests/unit/harness/`
- tests: `python -m pytest -m golden -v`
- manual verification: marker discoverable via `pytest --markers`

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Coordinate with Mid plan to avoid duplicate README edits — merge in one PR if both land together.
