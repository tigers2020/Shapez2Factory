---
linear_issue: SHA-46
title: IVVD import_basedata_bundle seals release by default despite error-level integrity issues
priority: Mid
labels:
  - priority:mid
  - bug
status: planned
created_by: todo-plan-automation
---

# Plan: IVVD default seal behavior fix

## Source Issue

- Linear: SHA-46
- Status at planning time: Todo
- Priority: Mid

## Problem

`import_basedata_bundle()` writes `integrity_status=sealed` and computes `release_integrity_hash` after validation phases even when non-superseded error-level `ShapezIntegrityIssue` rows remain. Blocking enforcement exists only behind opt-in `strict_seal=True`.

## Scope

Align default import sealing with validation outcome: do not mark `SEALED` when error-level issues remain, or make strict behavior the default with documented override.

## Non-goals

- Implementing full semantic validation rules (stub phase)
- Rewriting xref/schema validators
- Changing seal algorithm or canonical payload format

## Implementation Plan

1. Read seal path in `django_apps/shapez_core/services/basedata_import_service.py` (lines ~724–761) and `_has_blocking_issues`.
2. After validation phases, if `_has_blocking_issues(release)`: set `integrity_status=failed`, skip seal hash write, return/raise per CLI contract.
3. Consider defaulting `import_shapez_basedata` to strict behavior with `--allow-seal-with-errors` escape hatch.
4. Add regression test: default path (`strict_seal=False`) does **not** seal when xref errors exist (mirror `test_strict_seal_raises_on_xref_errors`).
5. Update management command help/docs if CLI flags change.

## Files / Areas Likely Affected

- `django_apps/shapez_core/services/basedata_import_service.py`
- `django_apps/shapez_core/management/commands/import_shapez_basedata.py`
- `tests/unit/shapez_core/test_basedata_ivvd.py`
- `ShapezBasedataRelease.IntegrityStatus` model enum

## Validation Plan

- lint: `ruff check .`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/shapez_core/test_basedata_ivvd.py -v`
- build: `python manage.py check`
- manual verification: repro with orphan building id — `integrity_status` must not be `sealed` when issues remain

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Changing default CLI behavior may break operators relying on permissive seal — document migration.
- Related SHA-27 transaction pattern is distinct; do not conflate fixes.
