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

# Plan: Extend KO locale strict coverage and backfill missing translations

## Source Issue

- Linear: SHA-43
- Status at planning time: Todo → In Progress (plan automation)
- Priority: Low

## Problem

`scripts/build_locale_ko.py --strict` only requires explicit Korean entries in the `KO` dict for literal `_("...")` strings in `django_apps/web/views/public_pages.py` (`STRICT_LOCALE_PY`). Template `{% trans %}` / `{% blocktrans %}` msgids and JS catalog strings are collected into committed `.po` files but may lack explicit `KO`/`KO_JS` entries; the builder warns and uses English msgids as msgstr. Korean UI therefore shows English for many strings with no CI failure.

Current builder output (2026-06-10): `WARN [django]: missing KO mapping for 91 strings` and `WARN [djangojs]: missing KO mapping for 7 strings`. `--strict` exits 0 because it only checks `collect_python_msgids(STRICT_LOCALE_PY)`.

## Scope

1. Define and document the KO translation contract for `--strict` (all collected django/djangojs msgids vs. documented allowlist).
2. Extend `--strict` to fail on missing `KO`/`KO_JS` entries for in-scope msgids.
3. Backfill `KO`/`KO_JS` entries for currently unmapped msgids (or document intentional English-only strings in an allowlist consumed by strict mode).
4. Update `documents/ai/manuals/testing.md` § Locale to describe strict coverage accurately.
5. Extend `tests/unit/test_build_locale_ko_strict.py` to assert the new strict behavior.

## Non-goals

- Adding CI catalog freshness gate (tracked separately in SHA-42).
- Auto-translating strings via external services.
- Changing msgid extraction heuristics unless required for strict enforcement.

## Implementation Plan

1. **Decide strict scope (contract).**
   - Recommended: `--strict` fails when any msgid in `merge_django_msgids()` lacks an explicit `KO` entry and any msgid in `collect_js_catalog_msgids()` lacks an explicit `KO_JS` entry.
   - Alternative: maintain `ENGLISH_ONLY_MSGIDS` / `ENGLISH_ONLY_JS_MSGIDS` frozensets for brand names, slugs, and technical tokens that must stay English; strict checks `msgid not in hand_ko and msgid not in allowlist`.
   - Record the decision in `testing.md` and in the `--strict` argparse help string.

2. **Refactor strict checking in `main()`.**
   - After `write_po_file` calls, compute missing django msgids: `[m for m in msgids if m not in KO]` (minus allowlist if used).
   - Compute missing djangojs msgids: `[m for m in js_msgids if m not in KO_JS]` (minus allowlist if used).
   - Keep existing `STRICT_LOCALE_PY` python-literal check as a subset or merge into django check (avoid duplicate failure messages).
   - Exit 1 with stderr listing missing msgids (cap listing like `write_po_file` WARN output).

3. **Inventory missing strings.**
   - Run `python3 scripts/build_locale_ko.py` and capture full WARN output (redirect to a temp file; 91 django + 7 djangojs as of planning).
   - Group by source template (`django_apps/web/templates/**`) or JS file (`django_apps/web/static/web/js/**`) for translation batching.

4. **Backfill `KO` dict entries.**
   - Add Korean `msgstr` values to `KO` in `scripts/build_locale_ko.py` for all in-scope django msgids.
   - Prefer consistent terminology with existing nav/chrome translations (e.g. "Solver" → "솔버", "Gallery" → "갤러리").
   - Leave brand/slug strings in allowlist only if product decision requires English (document each).

5. **Backfill `KO_JS` dict entries.**
   - Add entries for the 7 missing djangojs strings in `KO_JS`.
   - Re-run builder; confirm zero WARN lines for both domains.

6. **Regenerate committed catalogs.**
   - Run `python3 scripts/build_locale_ko.py` (no flags) to refresh `locale/ko/LC_MESSAGES/django.po`, `django.mo`, `djangojs.po`, `djangojs.mo`.
   - Commit regenerated `.po`/`.mo` alongside dict changes.

7. **Update tests.**
   - Keep `test_build_locale_ko_strict_exits_zero` (should pass after backfill).
   - Add regression test: temporarily inject a fake msgid into collection path or use subprocess with a fixture — prefer documenting that strict failure is covered by ensuring builder passes after backfill; optional unit test for strict missing-entry exit code via mocking if subprocess-only is too heavy.

8. **Update documentation.**
   - Revise `documents/ai/manuals/testing.md` § Locale: state that `--strict` covers all template + `STRICT_LOCALE_PY` django msgids and all JS catalog msgids (or document allowlist path).
   - Note relationship to SHA-42 (CI freshness) as out of scope here.

## Files / Areas Likely Affected

- `scripts/build_locale_ko.py` — `STRICT_LOCALE_PY`, `KO`, `KO_JS`, `main()` `--strict` branch, optional allowlist constants
- `locale/ko/LC_MESSAGES/django.po`, `django.mo`, `djangojs.po`, `djangojs.mo`
- `django_apps/web/templates/**` — source of template msgids (read-only for inventory)
- `django_apps/web/static/web/js/**` — source of JS msgids (read-only for inventory)
- `tests/unit/test_build_locale_ko_strict.py`
- `documents/ai/manuals/testing.md` § Locale

## Validation Plan

- lint: `ruff check .`
- typecheck: `mypy django_apps config src` (script is outside mypy scope; no new mypy failures)
- tests: `python -m pytest tests/unit/test_build_locale_ko_strict.py -v`
- build: `python3 scripts/build_locale_ko.py` (no WARN), `python3 scripts/build_locale_ko.py --strict` (exit 0)
- manual verification: Spot-check Korean UI pages that previously showed English fallback strings (home, gallery, solver, pattern lab templates)

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- **Strict scope decision:** Full coverage vs. allowlist for English-only tokens — needs one explicit choice before implementation; default recommendation is full coverage with a small documented allowlist for brands/slugs only.
- **Translation quality:** Manual Korean copy for ~98 strings; no machine translation per non-goals. Review by native speaker may be follow-up.
- **Count drift:** Issue cited 89+7=96; current repo reports 91+7=98 — strict backfill should target live builder output, not stale counts.
- **SHA-42 dependency:** This issue fixes mapping completeness and strict local gate; CI still won't catch catalog drift until SHA-42 lands.
