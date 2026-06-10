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

# Plan: IVVD import_basedata_bundle seals release by default despite error-level integrity issues

## Source Issue

- Linear: SHA-46
- Status at planning time: Todo
- Priority: Mid

## Problem

`import_basedata_bundle()` always writes `integrity_status=sealed` after validation phases, even when non-superseded error-level `ShapezIntegrityIssue` rows remain. Blocking enforcement exists only behind opt-in `strict_seal=True`. Default `import_shapez_basedata` usage can persist xref/schema failures as a sealed canonical basedata release.

## Scope

Align default import sealing with validation outcome: do not mark `SEALED` when error-level issues remain, or make `--strict-seal` the default with documented override.

## Non-goals

- Implementing full semantic validation rules.
- Rewriting xref/schema validators.
- Changing seal algorithm or canonical payload format.

## Implementation Plan

1. Read seal path in `django_apps/shapez_core/services/basedata_import_service.py` (~L724–761) and `_has_blocking_issues`.
2. After validation phases, if `_has_blocking_issues(release)`: set `integrity_status=failed`, skip seal hash write; raise or return per CLI contract (mirror `test_strict_seal_raises_on_xref_errors`).
3. Evaluate making `import_shapez_basedata` default to strict behavior (`--strict-seal` default True) with `--allow-seal-with-errors` escape hatch — pick minimal change aligned with issue spec.
4. Add regression test: default import path with orphan building id does **not** seal when issues remain.
5. Update management command help text and any operator docs referencing seal behavior.
6. Confirm `ShapezBasedataRelease.IntegrityStatus.FAILED` is used on blocking issues path.

## Files / Areas Likely Affected

- `django_apps/shapez_core/services/basedata_import_service.py`
- `django_apps/shapez_core/management/commands/import_shapez_basedata.py`
- `tests/unit/shapez_core/test_basedata_ivvd.py`

## Validation Plan

- lint: `ruff check .`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/shapez_core/test_basedata_ivvd.py -v`
- build: `python manage.py check`
- manual verification: Import bundle with xref error; confirm `integrity_status != sealed`

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Breaking change if operators rely on default seal-with-errors; escape hatch flag may be required.
- Related SHA-27 (game_data import transaction boundary) is distinct module — cross-link only.
