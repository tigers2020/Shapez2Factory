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

# Plan: Fail-closed default sealing for IVVD basedata import

## Source Issue

- Linear: SHA-46
- Status at planning time: Todo
- Priority: Mid

## Problem

`import_basedata_bundle()` writes `integrity_status=sealed` even when error-level `ShapezIntegrityIssue` rows remain. Blocking enforcement only behind `strict_seal=True`.

## Scope

Align default import sealing with validation outcome: do not mark `SEALED` when error-level issues remain, or make strict behavior the management-command default with documented override.

## Non-goals

- Full semantic validation rules (stub phase).
- Rewriting xref/schema validators.
- Changing seal algorithm or canonical payload format.

## Implementation Plan

1. After validation phases in `basedata_import_service.py`, if `_has_blocking_issues(release)` set `integrity_status=failed`, skip seal hash.
2. Consider `import_shapez_basedata` default strict with `--allow-seal-with-errors` escape hatch.
3. Add regression test: default path does **not** seal when xref errors exist (mirror `test_strict_seal_raises_on_xref_errors`).
4. Run `pytest tests/unit/shapez_core/test_basedata_ivvd.py -v`.

## Files / Areas Likely Affected

- `django_apps/shapez_core/services/basedata_import_service.py`
- `django_apps/shapez_core/management/commands/import_shapez_basedata.py`
- `tests/unit/shapez_core/test_basedata_ivvd.py`

## Validation Plan

- lint: `ruff check django_apps/shapez_core/`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/shapez_core/test_basedata_ivvd.py -v`
- build: `python manage.py check`
- manual verification: Import bundle with orphan building id; confirm not sealed by default.

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are documented.

## Risks / Open Questions

- Breaking change for operators relying on default seal-with-errors behavior.
- Document migration path for `--allow-seal-with-errors` if default flips.
