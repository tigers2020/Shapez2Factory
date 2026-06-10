---
linear_issue: SHA-30
title: Golden harness compare_golden.py and tests/golden fixtures are not wired to pytest or CI
priority: Mid
labels:
  - infra
  - priority:mid
  - test
status: planned
created_by: todo-plan-automation
---

# Plan: Wire golden harness fixtures to pytest

## Source Issue

- Linear: SHA-30
- Status at planning time: In Progress (moved before plan creation)
- Priority: Mid

## Problem

Phase 2 golden regression harness (`harness/validators/compare_golden.py`) is implemented and `tests/golden/` contains a committed input/expected pair, but no pytest module imports the comparator and CI never runs golden comparisons. `tests/golden/README.md` still defers activation until `compare_golden.py` exists.

## Scope

- Add pytest coverage loading golden fixtures via `golden_path` / `assert_golden_match`.
- Wire first fixture (`candidate_selector_trunk_split`) to the correct domain function, or document/remove if obsolete.
- Update `tests/golden/README.md` activation status.
- Optionally ensure golden tests run in `test_fast` or integration gate per `structure.md`.

## Non-goals

- Changing solver selection algorithms unless required to match confirmed contract.
- Bulk-migrating inline golden tests under `tests/unit/asteroid_lab/`.
- Relaxing golden comparisons or deleting fixtures without rationale.

## Implementation Plan

1. Add `tests/unit/harness/test_compare_golden.py` with comparator self-check (identical JSON passes; type/len/value diffs fail with path messages).
2. Add parametrized golden fixture runner: for each `tests/golden/*_input.json`, load input, invoke domain function, call `assert_golden_match` against `*_expected.json`.
3. Investigate `candidate_selector_trunk_split` fixture: input has `candidates` with throughput/cost/goal fields; expected has `ordered_candidate_ids`. No current symbol `ordered_candidate_ids` or `trunk_split` in codebase — trace to producing module (likely L3 beam/selector ordering) or mark obsolete per issue scope.
4. If module found: build minimal adapter from JSON input to domain types, run selector, serialize `ordered_candidate_ids` (or equivalent), assert golden match.
5. If obsolete: document in README + PR rationale; remove or replace fixture pair only with explicit acceptance.
6. Register `@pytest.mark.golden` in `pyproject.toml` if marker used; ensure tests are picked up by fast gate (`unit` marker or default collection).
7. Update `tests/golden/README.md`: remove stale wait-for-compare_golden gate; document add/change policy and pytest entrypoint.

## Files / Areas Likely Affected

- `harness/validators/compare_golden.py`
- `tests/golden/candidate_selector_trunk_split_input.json`
- `tests/golden/candidate_selector_trunk_split_expected.json`
- `tests/golden/README.md`
- `tests/unit/harness/test_compare_golden.py` (new)
- `pyproject.toml` (pytest markers)
- `scripts/test_fast.ps1` (only if golden tests need explicit inclusion)
- `.github/workflows/ci.yml` (only if not covered by existing pytest step)
- Domain module producing `ordered_candidate_ids`: TBD until fixture owner identified

## Validation Plan

- lint: `ruff check harness/validators/compare_golden.py tests/unit/harness/`
- typecheck: `mypy django_apps config src` (spot-check new tests)
- tests: `python -m pytest tests/unit/harness/ -v`
- build: n/a
- manual verification: `compare_golden.py` imported by pytest; golden pair exercised or obsolete path documented

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- `candidate_selector_trunk_split` may reference removed/refactored selector logic — fixture owner must be confirmed before wiring.
- Fast gate marker strategy: golden tests should not be `slow` if included in `test_fast.ps1` (`-m "unit and not slow"`).
