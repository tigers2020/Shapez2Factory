---
linear_issue: SHA-42
title: CI never verifies committed locale/ko .po/.mo match build_locale_ko.py output
priority: Low
labels:
  - automation
  - infra
  - test
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: KO translation completeness (deferred to SHA-43)

## Source Issue

- Linear: SHA-42 (Low priority items)
- Status at planning time: Todo
- Priority: Low

## Problem

SHA-42 Mid covers catalog freshness only. KO translation completeness and GNU gettext migration are separate Low items.

## Scope

Track only — implement in SHA-43.

## Non-goals

- Expanding `--strict` coverage in SHA-42.

## Implementation Plan

1. No changes under SHA-42 Low scope.
2. Follow SHA-43 for `build_locale_ko.py --strict` expansion.

## Files / Areas Likely Affected

- `scripts/build_locale_ko.py` (SHA-43)

## Validation Plan

- N/A (tracking only)

## Acceptance Criteria

- [ ] SHA-43 tracked separately.

## Risks / Open Questions

- Fresh catalogs may still contain English msgstr until SHA-43.
