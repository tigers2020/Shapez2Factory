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

`import_basedata_bundle()` always writes `integrity_status=sealed` and computes `release_integrity_hash` after validation phases, even when non-superseded error-level `ShapezIntegrityIssue` rows remain. Blocking-issue enforcement exists only behind opt-in `strict_seal=True`. Default CLI usage therefore persists xref/schema failures as a sealed canonical basedata release.

## Scope

Align default import sealing with validation outcome: do not mark `SEALED` when error-level issues remain, or make `--strict-seal` the default for the management command with documented override.

## Non-goals

- Implementing full semantic validation rules (stub phase)
- Rewriting xref/schema validators
- Changing seal algorithm or canonical payload format

## Implementation Plan

1. Read seal path in `django_apps/shapez_core/services/basedata_import_service.py` (lines ~724–761) and `_has_blocking_issues`.
2. After validation phases, if `_has_blocking_issues(release)`:
   - Set `integrity_status=failed` (or intermediate checked state per enum)
   - Skip seal hash write
   - Return/raise per existing CLI contract
3. Consider flipping `import_shapez_basedata` default to strict (`--strict-seal` True) with `--allow-seal-with-errors` escape hatch.
4. Add regression test: default path with orphan building id does **not** seal (mirror `test_strict_seal_raises_on_xref_errors`).
5. Update management command help text if default behavior changes.

## Files / Areas Likely Affected

- `django_apps/shapez_core/services/basedata_import_service.py`
- `django_apps/shapez_core/management/commands/import_shapez_basedata.py`
- `tests/unit/shapez_core/test_basedata_ivvd.py`

## Validation Plan

- tests: `pytest tests/unit/shapez_core/test_basedata_ivvd.py -v`
- manual verification: import bundle with known xref error, assert not sealed

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- **Breaking change:** Operators relying on default seal-with-errors need escape hatch documented.
- `IntegrityStatus.FAILED` exists but default import never sets it today — confirm enum usage with existing admin/UI.
