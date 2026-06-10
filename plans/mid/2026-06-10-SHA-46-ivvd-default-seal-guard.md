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

# Plan: IVVD default import must not seal with blocking issues

## Source Issue

- Linear: SHA-46
- Status at planning time: Todo
- Priority: Mid

## Problem

`import_basedata_bundle()` writes `integrity_status=sealed` after validation even when error-level `ShapezIntegrityIssue` rows remain. Blocking enforcement exists only behind `strict_seal=True`.

## Scope

Align default import sealing with validation outcome: do not mark `SEALED` when error-level issues remain, or make strict behavior the default with documented override.

## Non-goals

- Full semantic validation rules (stub phase)
- Rewriting xref/schema validators
- Changing seal algorithm or canonical payload format

## Implementation Plan

1. Read `basedata_import_service.py` seal block (lines ~724–761) and `_has_blocking_issues`.
2. After validation phases, if `_has_blocking_issues(release)`: set `integrity_status=failed`, skip seal hash, surface error per CLI contract.
3. Consider `import_shapez_basedata` default `strict_seal=True` with `--allow-seal-with-errors` escape hatch.
4. Add regression test: default path with orphan xref does **not** seal (mirror `test_strict_seal_raises_on_xref_errors`).
5. Update management command help text if default changes.

## Files / Areas Likely Affected

- `django_apps/shapez_core/services/basedata_import_service.py`
- `django_apps/shapez_core/management/commands/import_shapez_basedata.py`
- `tests/unit/shapez_core/test_basedata_ivvd.py`

## Validation Plan

- tests: `pytest tests/unit/shapez_core/test_basedata_ivvd.py`
- manual verification: import bundle with known xref error, assert `integrity_status != sealed`

## Acceptance Criteria

- [ ] The confirmed problem is fixed or resolved.
- [ ] The fix stays within scope.
- [ ] Relevant tests/docs are added or updated.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are documented.

## Risks / Open Questions

- Changing default may break operators relying on seal-with-warnings — document migration.
- Related SHA-27 (game_data import fail-open) is distinct module.
