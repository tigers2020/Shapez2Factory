---
linear_issue: SHA-42
title: CI never verifies committed locale/ko .po/.mo match build_locale_ko.py output
priority: Low
labels:
  - automation
  - infra
  - priority:mid
  - test
status: planned
created_by: todo-plan-automation
---

# Plan: KO translation completeness and gettext migration (deferred)

## Source Issue

- Linear: SHA-42 (Low priority breakdown items — out of scope for SHA-42 implementation)
- Status at planning time: Todo
- Priority: Low

## Problem

Two follow-on quality gaps are documented in SHA-42's priority breakdown but explicitly excluded from SHA-42 scope:

1. **KO translation completeness** — `build_locale_ko.py --strict` only covers literal `_("...")` in `django_apps/web/views/public_pages.py`; other templates/JS msgids can ship with English fallback silently. Tracked separately as SHA-43.
2. **GNU gettext replacement** — the polib-based builder is a deliberate dev shortcut; migrating to standard `msgfmt`/`xgettext` toolchain is a larger infra change.

## Scope

**None for SHA-42.** This plan records deferred work only. Do not implement as part of SHA-42 Mid gate.

- SHA-43: expand or replace `--strict` coverage for broader KO dict completeness.
- GNU gettext: separate spike/ADR if pursued.

## Non-goals

- Do not block SHA-42 Mid drift gate on translation completeness.
- Do not replace polib builder during SHA-42.

## Implementation Plan

1. Complete SHA-42 Mid plan (`plans/mid/2026-06-10-SHA-42-locale-catalog-freshness-gate.md`) first.
2. Pick up KO completeness via Linear SHA-43 when prioritized.
3. Evaluate GNU gettext migration only if product/i18n policy changes — not driven by catalog drift gate.

## Files / Areas Likely Affected

- `scripts/build_locale_ko.py` (SHA-43 / future gettext work)
- `tests/unit/test_build_locale_ko_strict.py` (SHA-43)
- TBD for gettext migration

## Validation Plan

- lint: N/A (deferred)
- typecheck: N/A (deferred)
- tests: N/A (deferred)
- build: N/A (deferred)
- manual verification: N/A (deferred)

## Acceptance Criteria

- [ ] Matches the source issue spec (deferred items documented, not implemented in SHA-42).
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Drift gate (SHA-42 Mid) will pass even when new msgids use English msgstr — acceptable per issue non-goals; SHA-43 addresses completeness.
- gettext migration scope unknown; keep polib path until explicit decision.
