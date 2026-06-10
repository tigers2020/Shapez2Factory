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

# Plan: Wire golden harness fixtures to pytest and CI

## Source Issue

- Linear: SHA-30
- Status at planning time: Todo
- Priority: Mid

## Problem

`harness/validators/compare_golden.py` implements `assert_golden_match` and `golden_path`, and `tests/golden/` contains a committed `candidate_selector_trunk_split` input/expected pair. No pytest module imports the comparator; CI and `test_fast.ps1` never run golden comparisons. `tests/golden/README.md` still defers activation until `compare_golden.py` exists (it already does).

## Scope

- Add pytest coverage that loads golden fixtures via `golden_path` / `assert_golden_match`.
- Wire `candidate_selector_trunk_split` to the correct domain function, or document/remove if obsolete.
- Update `tests/golden/README.md` activation status.
- Include golden tests in `test_fast` or document integration-tier placement.

## Non-goals

- Changing solver selection algorithms unless required to match confirmed contract.
- Bulk-migrating inline golden tests under `tests/unit/asteroid_lab/`.
- Relaxing golden comparisons or deleting fixtures without rationale.

## Implementation Plan

1. **Comparator self-test**
   - Create `tests/unit/harness/test_compare_golden.py`.
   - Test `compare_json` detects type/len/value diffs.
   - Test `golden_path("candidate_selector_trunk_split", kind="input")` resolves under `tests/golden/`.
   - Test `assert_golden_match` passes when actual matches expected file.

2. **Identify domain producer for trunk_split fixture**
   - Input fields: `candidates[]` with `candidate_id`, `base_throughput`, `cost`, `goal_priority`, `goal_coord`, `transport_kind`, `extractor`.
   - Expected output: `ordered_candidate_ids: ["a:saturate", "c:to_b", "b:to_a"]`.
   - Grep codebase for selector ordering logic; if no module exists, add a short note in test file and mark fixture `xfail` with link to future selector issue — do not invent algorithm.

3. **Golden regression test module**
   - Create `tests/unit/harness/test_golden_fixtures.py` (or colocate in compare_golden test).
   - Load input JSON, invoke identified function, `assert_golden_match(result, golden_path(..., kind="expected"))`.
   - Parametrize over discovered `*_input.json` basenames for future fixtures.

4. **Update README**
   - Remove "wait for compare_golden.py" gate in `tests/golden/README.md`.
   - Document pytest entrypoint: `pytest tests/unit/harness/ -v`.
   - Keep manual-edit policy for golden files.

5. **CI / fast gate**
   - Confirm new tests live under `tests/unit/harness/` so `test_fast.ps1` (`-m "unit and not slow"`) picks them up automatically.
   - If marker `golden` added (low plan), ensure it is included in unit marker set or document exclusion.

## Files / Areas Likely Affected

- `harness/validators/compare_golden.py` (read-only unless path helper needs export)
- `tests/unit/harness/test_compare_golden.py` (new)
- `tests/unit/harness/test_golden_fixtures.py` (new)
- `tests/golden/README.md`
- `tests/golden/candidate_selector_trunk_split_{input,expected}.json` (read; update only if contract wrong)
- TBD: domain module producing `ordered_candidate_ids`

## Validation Plan

- lint: `ruff check .`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/harness/ -v`
- build: N/A
- manual verification: `powershell -File scripts/test_fast.ps1` includes new harness tests

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- `candidate_selector_trunk_split` may reference logic not yet implemented — fixture could be aspirational; confirm before deleting.
- Golden tests must stay deterministic (fixed seeds, no wall-clock).
