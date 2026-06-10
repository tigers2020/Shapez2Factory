---
linear_issue: SHA-30
title: Golden harness compare_golden.py and tests/golden fixtures are not wired to pytest or CI
priority: Low
labels:
  - test
  - infra
status: planned
created_by: todo-plan-automation
---

# Plan: Golden pytest marker and README polish

## Source Issue

- Linear: SHA-30
- Status at planning time: Todo
- Priority: Low

## Problem

Optional organization for golden regression tests: no `golden` pytest marker exists, and README polish can clarify contributor workflow once harness tests are active.

## Scope

- Add `@pytest.mark.golden` to golden fixture tests.
- Document marker usage in `tests/golden/README.md` and optionally `documents/ai/manuals/testing.md`.
- Optionally allow `pytest -m golden` for targeted runs.

## Non-goals

- Changing comparator semantics.
- Moving golden tests to integration tier unless mid-priority wiring proves they are too slow for `test_fast`.

## Implementation Plan

1. Add `golden: deterministic golden JSON regression (tests/unit/harness)` to `pytest.ini` and `pyproject.toml` markers.
2. Decorate golden tests with `@pytest.mark.golden` and `@pytest.mark.unit`.
3. Update `tests/golden/README.md` with marker examples (`pytest -m golden -v`).
4. If golden tests exceed fast gate budget, document exclusion in `docs/agent-workflows/validation-routine.md` — otherwise note they run under default `unit and not slow`.

## Files / Areas Likely Affected

- `pytest.ini`
- `pyproject.toml`
- `tests/unit/harness/test_golden_fixtures.py`
- `tests/golden/README.md`
- `documents/ai/manuals/testing.md` (optional)

## Validation Plan

- lint: `ruff check .`
- typecheck: N/A
- tests: `pytest -m golden -v`
- build: N/A
- manual verification: `pytest -m "unit and golden" -v` lists only golden unit tests

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Marker is organizational only; mid-priority plan must land first.
- If many golden fixtures are added later, may need `slow` marker — out of scope for SHA-30.
