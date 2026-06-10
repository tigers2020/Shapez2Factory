---
linear_issue: SHA-30
title: Optional golden pytest marker and README polish
priority: Low
labels:
  - test
  - infra
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Golden pytest marker organization and README polish

## Source Issue

- Linear: SHA-30
- Status at planning time: Todo
- Priority: Low

## Problem

After mid-priority wiring, golden tests may run in the default unit slice without explicit marker filtering. Optional `golden` marker improves selective runs and documents intent in `pytest.ini` / `testing.md`.

## Scope

- Register `golden` marker in `pytest.ini` and `pyproject.toml`.
- Decorate golden fixture tests with `@pytest.mark.golden`.
- Extend `tests/golden/README.md` with marker usage examples.

## Non-goals

- Splitting golden tests to a separate CI job unless mid plan shows runtime cost.
- Changing comparator semantics.

## Implementation Plan

1. Add to `pytest.ini` markers: `golden: deterministic JSON golden regression (tests/golden fixtures)`.
2. Mirror in `pyproject.toml` `[tool.pytest.ini_options]`.
3. Apply `@pytest.mark.golden` and `@pytest.mark.unit` on harness golden tests.
4. Document in README: `pytest -m golden`, `pytest -m "unit and golden"`.
5. Optional: mention in `documents/ai/manuals/testing.md` under regression tiers.

## Files / Areas Likely Affected

- `pytest.ini`
- `pyproject.toml`
- `tests/unit/harness/test_golden_fixtures.py`
- `tests/golden/README.md`
- `documents/ai/manuals/testing.md` (optional)

## Validation Plan

- lint: `ruff check .`
- tests: `pytest -m golden -v`
- build: N/A
- manual verification: `pytest --markers` lists `golden`

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Defer if mid plan keeps golden tests unmarked and fast gate already covers them.
