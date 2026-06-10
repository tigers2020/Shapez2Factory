---
linear_issue: SHA-46
title: IVVD import_basedata_bundle seals release by default despite error-level integrity issues
priority: Mid
labels:
  - bug
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Align default IVVD import sealing with validation outcome

## Source Issue

- Linear: SHA-46
- Status at planning time: Todo
- Priority: Mid

## Problem

`import_basedata_bundle()` always writes `integrity_status=sealed` and computes `release_integrity_hash` after validation phases, even when non-superseded error-level `ShapezIntegrityIssue` rows remain. Blocking-issue enforcement exists only behind the opt-in `strict_seal=True` flag.

Default management-command usage (`import_shapez_basedata` without `--strict-seal`) therefore persists xref/schema failures as a **sealed** canonical basedata release.

## Scope

Align default import sealing with validation outcome: do not mark `SEALED` when error-level issues remain. Set `integrity_status=failed` and skip seal hash write on the default path; preserve `strict_seal=True` abort behavior.

## Non-goals

- Implementing full semantic validation rules (stub phase remains out of scope)
- Rewriting xref/schema validators
- Changing seal algorithm or canonical payload format

## Implementation Plan

1. Read seal path in `django_apps/shapez_core/services/basedata_import_service.py` (`_run_validation_phases`, lines ~715–761) and `_has_blocking_issues`.
2. Before the seal block, add a shared guard for blocking issues:
   - If `_has_blocking_issues(release)` and `strict_seal`: keep existing behavior (set `failed`, raise `ValueError`).
   - If `_has_blocking_issues(release)` and not `strict_seal`: set `integrity_status=FAILED`, skip `release_integrity_hash` / `seal_input_canonical_json` / `sealed_at` / `ShapezCanonicalArtifact` creation, return release without sealing.
3. Evaluate CLI contract for default path:
   - Recommended: `import_basedata_bundle` returns the release with `failed` status (no raise); management command prints non-success styling when status is `failed`.
   - Optional follow-up: flip `import_shapez_basedata` default to `strict_seal=True` with `--allow-seal-with-errors` escape hatch (document in help text if adopted).
4. Add regression test `test_default_import_does_not_seal_on_xref_errors` in `tests/unit/shapez_core/test_basedata_ivvd.py`:
   - Reuse orphan-building fixture from `test_strict_seal_raises_on_xref_errors`.
   - Call `import_basedata_bundle(root, replace=True, strict_seal=False)`.
   - Assert `integrity_status_id == ShapezBasedataRelease.IntegrityStatus.FAILED.value`.
   - Assert `release_integrity_hash` is empty/null and `sealed_at` is null.
   - Assert `ShapezIntegrityIssue` count > 0 with `is_superseded=False`.
5. Run focused tests and lint gates.

## Files / Areas Likely Affected

- `django_apps/shapez_core/services/basedata_import_service.py`
- `django_apps/shapez_core/management/commands/import_shapez_basedata.py`
- `tests/unit/shapez_core/test_basedata_ivvd.py`

## Validation Plan

- lint: `ruff check django_apps/shapez_core/`
- typecheck: `mypy django_apps/shapez_core`
- tests: `pytest tests/unit/shapez_core/test_basedata_ivvd.py -v`
- build: N/A
- manual verification: import bundle with orphan building id without `--strict-seal`; confirm release stays `failed` and is not sealed

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Whether default CLI should exit non-zero when status is `failed` vs exit 0 with visible warning.
- Issue mentions intermediate `checked` states vs `failed`; confirm `FAILED` is correct default (not `xref_checked`).
- Related SHA-27 (game_data import fail-open) is a distinct module; no coupling required.
- Existing happy-path test `test_import_basedata_bundle_idempotent_and_sealed` must remain green.
