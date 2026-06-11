---
linear_issue: SHA-42
title: CI never verifies committed locale/ko .po/.mo match build_locale_ko.py output
priority: Mid
labels:
  - automation
  - infra
  - priority:mid
  - test
status: planned
created_by: todo-plan-automation
---

# Plan: CI gate for Korean locale catalog freshness

## Source Issue

- Linear: SHA-42
- Status at planning time: Todo
- Priority: Mid

## Problem

GitHub Actions never regenerates `locale/ko/LC_MESSAGES/*` via `scripts/build_locale_ko.py`. Committed catalogs can drift from template/JS gettext sources.

## Scope

Add CI or pytest gate that rebuilds catalogs and fails on diff. Regenerate and commit current catalogs when gate lands.

## Non-goals

- Translating missing KO strings (SHA-43).
- Replacing polib builder with GNU gettext.
- Changing Django locale middleware.

## Implementation Plan

1. Add contract test running `python scripts/build_locale_ko.py` and asserting clean diff under `locale/ko/LC_MESSAGES/`.
2. Wire into `.github/workflows/ci.yml`.
3. Regenerate and commit stale catalogs as part of implementation PR.
4. Update `documents/ai/manuals/testing.md` § Locale if needed.

## Files / Areas Likely Affected

- `scripts/build_locale_ko.py`
- `locale/ko/LC_MESSAGES/`
- `.github/workflows/ci.yml`
- `tests/unit/test_build_locale_ko_strict.py`

## Validation Plan

- tests: new catalog freshness contract test
- build: CI job

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- First gate landing may require large catalog commit from current drift.
