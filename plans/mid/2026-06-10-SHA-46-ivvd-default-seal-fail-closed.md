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

# Plan: IVVD default import must not seal with blocking integrity issues

## Source Issue

- Linear: SHA-46
- Status at planning time: In Progress
- Priority: Mid

## Problem

`import_basedata_bundle()` writes `integrity_status=sealed` and computes `release_integrity_hash` after validation phases even when non-superseded error-level `ShapezIntegrityIssue` rows remain. Blocking enforcement exists only behind opt-in `strict_seal=True`. Default `import_shapez_basedata` (without `--strict-seal`) can persist xref/schema failures as a sealed canonical basedata release.

## Scope

Align default import sealing with validation outcome: do not mark `SEALED` when error-level issues remain, or make strict behavior the management-command default with a documented override (`--allow-seal-with-errors`).

## Non-goals

- Full semantic validation rules (stub phase)
- Rewriting xref/schema validators
- Changing seal algorithm or canonical payload format

## Implementation Plan

1. **Read current seal path**
   - `django_apps/shapez_core/services/basedata_import_service.py`: `_run_validation_phases`, `_has_blocking_issues`, seal block (~lines 715–751).
   - `management/commands/import_shapez_basedata.py`: `--strict-seal` flag wiring.
   - `tests/unit/shapez_core/test_basedata_ivvd.py`: `test_strict_seal_raises_on_xref_errors` (abort path only).

2. **Change default sealing contract**
   - After validation, if `_has_blocking_issues(release)`:
     - Set `integrity_status=FAILED` (uses existing `ShapezBasedataRelease.IntegrityStatus.FAILED`).
     - Skip `release_integrity_hash` / sealed write.
     - Default CLI: exit non-zero or raise per existing `strict_seal` error pattern (mirror strict behavior for default path).
   - Only reach `SEALED` when no blocking issues OR explicit override flag passed.

3. **CLI flag decision (pick one per PR, document in command help)**
   - **Option A (issue-favored):** Default strict — `strict_seal=True` by default in `import_shapez_basedata`; add `--allow-seal-with-errors` to restore old permissive seal.
   - **Option B:** Keep `strict_seal=False` default but change seal block to check `_has_blocking_issues` unconditionally (failed status, no seal) without raising unless `strict_seal=True`.

4. **Regression tests**
   - Add test: `import_basedata_bundle(..., strict_seal=False)` with orphan building id → `integrity_status != sealed`, blocking issues present, no seal hash written.
   - Keep `test_strict_seal_raises_on_xref_errors` green.
   - Add test for override flag if Option A chosen.

5. **Docs**
   - Update basedata import docs / command help if default CLI behavior changes.

## Files / Areas Likely Affected

- `django_apps/shapez_core/services/basedata_import_service.py`
- `django_apps/shapez_core/management/commands/import_shapez_basedata.py`
- `tests/unit/shapez_core/test_basedata_ivvd.py`
- `django_apps/shapez_core/models/` (IntegrityStatus enum reference)

## Validation Plan

- lint: `ruff check .`
- typecheck: `mypy django_apps config src` (or CI scope)
- tests: `pytest tests/unit/shapez_core/test_basedata_ivvd.py -v`
- build: `python manage.py check`
- manual verification: run `import_shapez_basedata` with known-bad fixture; confirm not sealed

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- **Option A vs B** changes operator ergonomics — confirm with issue author if scripts/automation rely on permissive default.
- Related SHA-27 (game_data import fail-open) is separate module; do not mix transaction fixes into this PR.
- Existing sealed releases in DB are historical; migration/backfill not in scope.
