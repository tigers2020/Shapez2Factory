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

# Plan: Fail-closed default sealing for IVVD import

## Source Issue

- Linear: SHA-46
- Status at planning time: Todo
- Priority: Mid

## Problem

`import_basedata_bundle()` writes `integrity_status=sealed` even when error-level `ShapezIntegrityIssue` rows remain unless `strict_seal=True`. Default CLI import mis-labels xref/schema failures as sealed canonical releases.

## Scope

Align default import sealing with validation outcome: do not mark `SEALED` when error-level issues remain, or default `import_shapez_basedata` to strict with documented override.

## Non-goals

- Full semantic validation rules.
- Rewriting xref/schema validators.
- Changing seal algorithm or payload format.

## Implementation Plan

1. After validation phases, if `_has_blocking_issues(release)` set `integrity_status=failed`, skip seal hash.
2. Consider default `strict_seal=True` on management command with `--allow-seal-with-errors` escape hatch.
3. Add regression test: default path does not seal when xref errors exist (mirror `test_strict_seal_raises_on_xref_errors`).
4. Run `pytest tests/unit/shapez_core/test_basedata_ivvd.py -v`.

## Files / Areas Likely Affected

- `django_apps/shapez_core/services/basedata_import_service.py`
- `django_apps/shapez_core/management/commands/import_shapez_basedata.py`
- `tests/unit/shapez_core/test_basedata_ivvd.py`

## Validation Plan

- tests: `pytest tests/unit/shapez_core/test_basedata_ivvd.py -v`

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Coordinate with SHA-27 game_data import transaction pattern if overlapping.
