---
linear_issue: SHA-30
title: Golden harness compare_golden.py and tests/golden fixtures are not wired to pytest or CI
priority: Mid
labels:
  - test
  - infra
status: planned
created_by: todo-plan-automation
---

# Plan: Wire golden harness to pytest and fast gate

## Source Issue

- Linear: SHA-30
- Status at planning time: Todo
- Priority: Mid

## Problem

`harness/validators/compare_golden.py` is implemented and `tests/golden/` holds a committed input/expected pair, but no pytest module imports the comparator and CI / `test_fast.ps1` never run golden comparisons. `tests/golden/README.md` still defers activation until after `compare_golden.py` exists.

## Scope

- Add pytest coverage that loads golden fixtures via `golden_path` / `assert_golden_match`.
- Wire the first fixture (`candidate_selector_trunk_split`) to the correct domain function, or document/remove if obsolete.
- Update `tests/golden/README.md` activation status.
- Include golden harness tests in the fast unit gate (or document integration-tier placement per `structure.md`).

## Non-goals

- Changing solver selection algorithms unless required to match a confirmed contract.
- Bulk-migrating inline golden tests under `tests/unit/asteroid_lab/`.
- Relaxing golden comparisons or deleting fixtures without rationale.

## Implementation Plan

1. Add `tests/unit/harness/test_compare_golden.py` with comparator self-checks (`compare_json`, `assert_golden_match`, path helpers).
2. Add `tests/unit/harness/test_golden_fixtures.py` that discovers `tests/golden/*_input.json` pairs and exercises each via domain call + `assert_golden_match`.
3. For `candidate_selector_trunk_split`: identify the module that produces `ordered_candidate_ids` from the input shape (fixture has `candidates` with `candidate_id`, throughput, goal, extractor). Grep shows no current reference to the scenario name — investigate `layer_03_rim_greedy_placement/beam_selector.py` and trunk-sharing regressions (`test_trunk_sharing_penalty_regression`) as likely owners; if no match, open a short ADR note in the PR and either rewire or remove the fixture with rationale.
4. Register `@pytest.mark.golden` in `pytest.ini` / `pyproject.toml` (low-priority file handles marker polish; mid plan only depends on tests being runnable under `-m unit`).
5. Ensure `scripts/test_fast.ps1` (`pytest -m "unit and not slow"`) picks up new tests under `tests/unit/harness/` without extra flags.
6. Update `tests/golden/README.md`: remove stale “wait for compare_golden” gate; document naming, manual edit policy, and that pytest enforces pairs.

## Files / Areas Likely Affected

- `harness/validators/compare_golden.py`
- `tests/unit/harness/test_compare_golden.py` (new)
- `tests/unit/harness/test_golden_fixtures.py` (new)
- `tests/golden/candidate_selector_trunk_split_{input,expected}.json`
- `tests/golden/README.md`
- `pytest.ini`
- `scripts/test_fast.ps1` (verify only — likely no change if tests are `unit`)
- `.github/workflows/ci.yml` (verify `test-fast` matrix includes harness tests)

## Validation Plan

- lint: `ruff check harness/validators/ tests/unit/harness/`
- typecheck: `mypy django_apps config src` (harness is untyped; spot-check if mypy scope expands)
- tests: `pytest tests/unit/harness/ -v` then `pytest -m "unit and not slow" tests/unit/harness/ -v`
- build: N/A
- manual verification: Temporarily perturb `candidate_selector_trunk_split_expected.json` and confirm pytest fails with golden diff output

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- `candidate_selector_trunk_split` fixture may be orphaned (no code references per `.agent-loop/reviewed-areas.md`); owner module is TBD until investigation.
- If the producing function changed since the fixture was committed, golden test may fail — treat as signal, not test weakness.
- CI may already pass via `test-fast` once unit tests exist; explicit golden marker is optional (see low-priority plan).
