---
linear_issue: SHA-43
title: build_locale_ko.py --strict covers only public_pages.py; 96 msgids silently English-fallback
priority: Low
labels:
  - ui
  - docs
  - priority:low
status: planned
created_by: todo-plan-automation
---

# Plan: build_locale_ko.py --strict covers only public_pages.py; 96 msgids silently English-fallback

## Source Issue

- Linear: SHA-43
- Status at planning time: Todo
- Priority: Low

## Problem

`scripts/build_locale_ko.py --strict` only requires explicit Korean entries in the `KO` dict for literal `_("...")` strings in `django_apps/web/views/public_pages.py`. Template `{% trans %}` / `{% blocktrans %}` msgids and JS catalog strings are collected into committed `.po` files but may lack explicit `KO`/`KO_JS` entries; the builder warns and uses English msgids as msgstr. Korean UI therefore shows English for many strings with no CI failure.

Current builder output (2026-06-10): `WARN [django]: missing KO mapping for 91 strings` and `WARN [djangojs]: missing KO mapping for 7 strings`. `--strict` exits 0 because it only checks `collect_python_msgids(STRICT_LOCALE_PY)`.

## Scope

Define and enforce the KO translation contract:

1. Extend `--strict` to fail on missing `KO`/`KO_JS` entries for all collected django/djangojs msgids (or a documented allowlist of intentional English-only strings).
2. Backfill missing `KO` and `KO_JS` entries so strict mode passes.
3. Update strict-mode tests and `documents/ai/manuals/testing.md` to describe coverage accurately.

## Non-goals

- Adding CI catalog freshness gate (tracked separately in SHA-42).
- Auto-translating strings via external services.
- Changing msgid extraction heuristics unless required for strict enforcement.

## Implementation Plan

1. **Inventory missing msgids**
   - Run `python3 scripts/build_locale_ko.py` and capture WARN output for django and djangojs domains.
   - Optionally add a temporary `--list-missing` flag or one-off script output to produce a sorted checklist of unmapped msgids for backfill review.

2. **Decide strict scope and allowlist**
   - Default contract: every msgid returned by `merge_django_msgids()` must exist in `KO`; every msgid from `collect_js_catalog_msgids()` must exist in `KO_JS`.
   - Document intentional English-only exceptions (e.g. brand slug `shapez2 planner`, proper nouns) in a small `ENGLISH_ONLY_KO` / `ENGLISH_ONLY_KO_JS` frozenset near the dicts if operators want to keep select strings untranslated.

3. **Extend `--strict` in `scripts/build_locale_ko.py`**
   - After `write_po_file` calls, when `args.strict`:
     - Collect `django_msgids = merge_django_msgids()` and `js_msgids = collect_js_catalog_msgids()`.
     - Compute `bad_django = [m for m in django_msgids if m not in KO and m not in ENGLISH_ONLY_KO]` (if allowlist used).
     - Compute `bad_js = [m for m in js_msgids if m not in KO_JS and m not in ENGLISH_ONLY_KO_JS]`.
     - Print domain-labeled stderr listings (mirror existing Python strict branch) and return exit code 1 if either list is non-empty.
   - Keep existing `STRICT_LOCALE_PY` / `collect_python_msgids` check as a subset or fold into the django msgid check (avoid duplicate failure reporting).

4. **Backfill `KO` dict (django domain)**
   - Add Korean `msgstr` entries in `scripts/build_locale_ko.py` `KO` dict for all 91 currently missing template/python msgids.
   - Group additions by template area (Asteroid Lab, Pattern Lab, game_data browse, solver pages, etc.) to keep the dict maintainable.
   - Re-run builder; confirm `WARN [django]` count drops to 0 (or only allowlisted strings).

5. **Backfill `KO_JS` dict (djangojs domain)**
   - Add entries to `KO_JS` for the 7 missing JS catalog strings.
   - Re-run builder; confirm `WARN [djangojs]` count drops to 0.

6. **Regenerate committed catalogs**
   - Run `python3 scripts/build_locale_ko.py` (no strict) to refresh `locale/ko/LC_MESSAGES/django.po`, `django.mo`, `djangojs.po`, `djangojs.mo`.
   - Commit updated `.po`/`.mo` together with dict changes.

7. **Update tests**
   - Extend `tests/unit/test_build_locale_ko_strict.py`:
     - Assert `--strict` exits 0 after backfill.
     - Optionally add a unit test that imports `merge_django_msgids` / `collect_js_catalog_msgids` and asserts every msgid is keyed in `KO`/`KO_JS` (minus documented allowlist) so regressions fail in pytest without subprocess.

8. **Update documentation**
   - Revise `documents/ai/manuals/testing.md` § Locale to state that `--strict` covers all collected django template msgids plus `public_pages.py` literals and all djangojs catalog msgids—not only `public_pages.py`.
   - Note relationship to SHA-42 (CI freshness) without implementing SHA-42 scope.

## Files / Areas Likely Affected

- `scripts/build_locale_ko.py` (`KO`, `KO_JS`, `--strict` branch, optional allowlist constants)
- `locale/ko/LC_MESSAGES/django.po`, `django.mo`, `djangojs.po`, `djangojs.mo`
- `tests/unit/test_build_locale_ko_strict.py`
- `documents/ai/manuals/testing.md`
- Template sources under `django_apps/web/templates/` (read-only for msgid inventory)
- JS sources under `django_apps/web/static/web/js/` (read-only for msgid inventory)

## Validation Plan

- lint: `ruff check scripts/build_locale_ko.py tests/unit/test_build_locale_ko_strict.py`
- typecheck: `mypy django_apps config src` (script is standalone; no new mypy surface expected)
- tests: `pytest tests/unit/test_build_locale_ko_strict.py -v`
- build: `python3 scripts/build_locale_ko.py --strict` (must exit 0); `python3 scripts/build_locale_ko.py` (no WARN for missing mappings)
- manual verification: Load key KO-locale pages (home, Asteroid Lab, Pattern Lab) and spot-check previously English-fallback strings render Korean

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] `--strict` fails when any in-scope django/djangojs msgid lacks an explicit `KO`/`KO_JS` entry.
- [ ] All 91 django + 7 djangojs missing mappings are resolved or documented as intentional English-only.
- [ ] `tests/unit/test_build_locale_ko_strict.py` and `documents/ai/manuals/testing.md` updated.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Msgid count may drift as templates/JS change; strict tests will fail until dict backfill—coordinate with SHA-42 if CI gate is added later.
- Some strings contain HTML markup or interpolation placeholders; Korean translations must preserve tags and `%(name)s`-style tokens.
- Translating technical solver/pattern-lab jargon may need domain review; prefer consistent terminology with existing `KO`/`KO_JS` entries.
- Allowlist vs full coverage: default to full coverage per issue spec; use allowlist only for clearly intentional English retention.
