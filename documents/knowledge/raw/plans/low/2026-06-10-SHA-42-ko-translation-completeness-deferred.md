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

# Plan: Deferred KO completeness and gettext migration (SHA-42 Low)

## Source Issue

- Linear: SHA-42
- Status at planning time: Todo
- Priority: Low

## Problem

SHA-42 Mid scope adds catalog **freshness** (committed `.po`/`.mo` match builder output). Two related gaps remain explicitly out of scope:

1. **KO translation completeness** — `build_locale_ko.py --strict` only covers `public_pages.py` literals; other msgids can ship with English fallback silently (tracked in SHA-43).
2. **GNU gettext migration** — builder is polib-based by design; replacing with GNU gettext toolchain is a separate effort.

## Scope

No implementation in SHA-42. Document deferrals in Mid plan and cross-link SHA-43. Do not expand `--strict` coverage or swap build tooling under this issue.

## Non-goals

- Expanding `KO` dict coverage beyond current `--strict` scope.
- Introducing `msgfmt`/`xgettext` pipeline.
- Runtime locale middleware changes.

## Implementation Plan

1. When implementing SHA-42 Mid plan, note in PR description that KO completeness is SHA-43.
2. Do not add `--strict` expansion or gettext tooling to SHA-42 PR.
3. If SHA-43 is picked up later, follow its own Linear spec.

## Files / Areas Likely Affected

- None for SHA-42 (deferred only).
- Future SHA-43: `scripts/build_locale_ko.py`, `tests/unit/test_build_locale_ko_strict.py`.

## Validation Plan

- lint: N/A
- typecheck: N/A
- tests: N/A
- build: N/A
- manual verification: confirm SHA-42 PR does not claim KO translation completeness

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Freshness gate (Mid) can pass while many msgids remain untranslated — expected; SHA-43 addresses completeness.
- GNU gettext migration has no open issue; create one only if explicitly requested.
