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

# Plan: IVVD default import must not seal releases with blocking integrity issues

## Source Issue

- Linear: SHA-46
- Status at planning time: Todo
- Priority: Mid

## Problem

`import_basedata_bundle()` always writes `integrity_status=sealed` after validation phases, even when non-superseded error-level `ShapezIntegrityIssue` rows remain. Blocking enforcement exists only behind opt-in `strict_seal=True`. Default CLI usage therefore persists xref/schema failures as a sealed canonical basedata release.

## Scope

Align default import sealing with validation outcome: do not mark `SEALED` when error-level issues remain, or make strict sealing the management-command default with documented override.

## Non-goals

- Implementing full semantic validation rules (stub phase).
- Rewriting xref/schema validators.
- Changing seal algorithm or canonical payload format.

## Implementation Plan

1. Read `basedata_import_service.py` seal path (lines ~724–761) and `_has_blocking_issues`.
2. After validation phases, if `_has_blocking_issues(release)`: set `integrity_status=failed`, skip seal hash write, return/raise per CLI contract.
3. Evaluate making `import_shapez_basedata` default to strict behavior with `--allow-seal-with-errors` escape hatch.
4. Add regression test: default path (`strict_seal=False`) with orphan building id must **not** seal; mirror `test_strict_seal_raises_on_xref_errors`.
5. Update management command help text if default changes.

## Files / Areas Likely Affected

- `django_apps/shapez_core/services/basedata_import_service.py`
- `django_apps/shapez_core/management/commands/import_shapez_basedata.py`
- `tests/unit/shapez_core/test_basedata_ivvd.py`
- `ShapezBasedataRelease.IntegrityStatus` enum usage

## Validation Plan

- lint: `ruff check django_apps/shapez_core/`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/shapez_core/test_basedata_ivvd.py -v`
- build: `python manage.py check`
- manual verification: Import bundle with known xref error; confirm `integrity_status != sealed` on default path

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Breaking change if operators rely on default seal-with-errors behavior.
- CLI exit code contract when import completes with failed integrity status needs confirmation.
