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

# Plan: IVVD default import must not seal releases with error-level integrity issues

## Source Issue

- Linear: SHA-46
- Status at planning time: Todo
- Priority: Mid

## Problem

`import_basedata_bundle()` always writes `integrity_status=sealed` and computes `release_integrity_hash` after validation phases, even when non-superseded error-level `ShapezIntegrityIssue` rows remain. Blocking-issue enforcement exists only behind the opt-in `strict_seal=True` flag.

Default management-command usage (`import_shapez_basedata` without `--strict-seal`) therefore persists xref/schema failures as a **sealed** canonical basedata release.

## Scope

Align default import sealing with validation outcome:

- Do not mark `IntegrityStatus.SEALED` when `_has_blocking_issues(release)` is true.
- Set `integrity_status=failed`, skip seal hash write, and skip canonical artifact creation on blocking issues.
- Preserve `strict_seal=True` abort semantics (raise `ValueError`) for operators who want hard failure.
- Add regression test for default (`strict_seal=False`) path asserting non-sealed status with orphan xref errors.
- Update CLI/docs only if flag semantics change (e.g. `--allow-seal-with-errors` escape hatch).

## Non-goals

- Implementing full semantic validation rules (stub phase remains out of scope).
- Rewriting xref/schema validators.
- Changing seal algorithm or canonical payload format.

## Implementation Plan

1. **Inspect seal path in `_run_validation_phases`** (`basedata_import_service.py` lines ~715–761).
   - Today: `if strict_seal and _has_blocking_issues` → set FAILED + raise; else unconditional seal.
   - Change: gate seal block on `_has_blocking_issues(release)` regardless of `strict_seal`.
2. **Define default vs strict behavior:**
   - When blocking issues exist and `strict_seal=True`: keep current behavior — set `integrity_status=FAILED`, raise `ValueError("strict_seal: unresolved error-level integrity issues remain.")`.
   - When blocking issues exist and `strict_seal=False`: set `integrity_status=FAILED`, leave `release_integrity_hash` empty/null, skip `ShapezCanonicalArtifact` creation, return release without raising.
3. **Optional CLI tightening (pick one, document in plan PR):**
   - **Option A (minimal):** service-only change; CLI unchanged; default import succeeds with exit 0 but release stays `failed`.
   - **Option B (issue suggestion):** flip management command default to strict (`--strict-seal` default True) and add `--allow-seal-with-errors` to permit Option A behavior explicitly.
   - Prefer Option A unless product wants CLI non-zero exit by default.
4. **Add regression test** in `tests/unit/shapez_core/test_basedata_ivvd.py`:
   - Reuse orphan-building fixture from `test_strict_seal_raises_on_xref_errors`.
   - Call `import_basedata_bundle(root, replace=True, strict_seal=False)`.
   - Assert: no exception; `integrity_status_id == FAILED`; `release_integrity_hash` is empty/falsy; `ShapezIntegrityIssue` count > 0; no `ShapezCanonicalArtifact` for derivation_step `import` (if applicable).
5. **Verify happy path unchanged:** `test_import_basedata_bundle_idempotent_and_sealed` still passes.
6. **Update docs** if CLI flags change: `documents/ai/plans/shapez2_basedata_django_persistence.md` `--strict-seal` section.

## Files / Areas Likely Affected

- `django_apps/shapez_core/services/basedata_import_service.py` (`_has_blocking_issues`, `_run_validation_phases` seal path)
- `django_apps/shapez_core/management/commands/import_shapez_basedata.py` (only if Option B CLI change)
- `tests/unit/shapez_core/test_basedata_ivvd.py`
- `documents/ai/plans/shapez2_basedata_django_persistence.md` (CLI contract note)

## Validation Plan

- lint: `ruff check django_apps/shapez_core/ tests/unit/shapez_core/test_basedata_ivvd.py`
- typecheck: `mypy django_apps/shapez_core`
- tests: `pytest tests/unit/shapez_core/test_basedata_ivvd.py -v`
- build: N/A
- manual verification: run `python manage.py import_shapez_basedata --root <bad-fixture>` without `--strict-seal`; confirm release row shows `failed` not `sealed`

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- **CLI exit code:** default import with errors currently prints SUCCESS via management command even when status is `failed`; consider follow-up UX issue.
- **Related SHA-27:** game_data import fail-open pattern is distinct module; do not conflate transaction boundaries.
- **Option A vs B:** product decision on whether operators want non-zero exit by default; plan assumes Option A unless issue owner prefers Option B.
