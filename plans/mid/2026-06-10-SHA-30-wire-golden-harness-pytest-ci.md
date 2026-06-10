---
linear_issue: SHA-30
title: Golden harness compare_golden.py and tests/golden fixtures are not wired to pytest or CI
priority: Mid
labels:
  - test
  - infra
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Wire golden harness to pytest and CI

## Source Issue

- Linear: SHA-30
- Status at planning time: Todo
- Priority: Mid

## Problem

The Phase 2 golden regression harness (`harness/validators/compare_golden.py`) is implemented and `tests/golden/` contains a committed input/expected pair, but no pytest module imports the comparator and CI never runs golden comparisons. The `tests/golden/README.md` activation note is stale and still defers wiring tests until after `compare_golden.py` exists.

## Scope

- Add pytest coverage loading golden fixtures via `golden_path` / `assert_golden_match`.
- Wire first fixture (`candidate_selector_trunk_split`) to correct domain function or document/remove if obsolete.
- Update `tests/golden/README.md` activation status.
- Optionally add CI or `test_fast` hook for golden harness tests.

## Non-goals

- Changing solver selection algorithms unless required to match confirmed contract.
- Bulk-migrating inline golden tests under `tests/unit/asteroid_lab/`.
- Relaxing golden comparisons or deleting fixtures without rationale.

## Implementation Plan

1. Read `harness/validators/compare_golden.py` (`assert_golden_match`, `golden_path`) and `tests/golden/` fixture layout; confirm `candidate_selector_trunk_split` input/expected pair structure.
2. Add `tests/unit/harness/test_compare_golden.py` with a comparator self-check (identical payloads pass; intentional diff fails with clear message).
3. Identify the domain module producing `ordered_candidate_ids` for `candidate_selector_trunk_split`; add regression test invoking that function and asserting via `assert_golden_match`.
4. If fixture targets obsolete API, document removal rationale in issue comment and delete or quarantine fixture — do not silently skip.
5. Add pytest marker (e.g. `golden`) in `pyproject.toml` or `pytest.ini` if project uses markers; register in `test_fast` or integration tier per `structure.md`.
6. Update `tests/golden/README.md` to remove stale wait-for-compare_golden gate; document how to add new golden pairs.
7. Optionally add golden step to `.github/workflows/ci.yml` or `scripts/test_fast.ps1` if not covered by pytest discovery.

## Files / Areas Likely Affected

- `harness/validators/compare_golden.py` (read-only)
- `tests/golden/` (fixtures + README)
- `tests/unit/harness/test_compare_golden.py` (new)
- Domain test module for `candidate_selector_trunk_split` (TBD after fixture inspection)
- `.github/workflows/ci.yml`
- `scripts/test_fast.ps1`
- `pyproject.toml` or `pytest.ini` (marker registration)

## Validation Plan

- lint: `ruff check harness/validators/ tests/unit/harness/`
- typecheck: `mypy django_apps config src` (if new test imports domain code)
- tests: `pytest tests/unit/harness/test_compare_golden.py -v` then golden-marked tests
- build: N/A
- manual verification: Confirm CI/fast gate runs golden tests; README activation note removed

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- `candidate_selector_trunk_split` may target moved/renamed domain API — verify before wiring.
- Golden tests may be slow; marker tier placement affects CI duration.
