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

# Plan: Deferred KO translation completeness (SHA-43)

## Source Issue

- Linear: SHA-42
- Status at planning time: Todo
- Priority: Low (deferred from SHA-42 breakdown)

## Problem

Catalog freshness (SHA-42 mid plan) ensures msgids exist in committed `.po` files. Explicit Korean translations for all msgids are a separate gap tracked in SHA-43.

## Scope

Track only — no implementation in SHA-42.

## Non-goals

- Extending `--strict` coverage (SHA-43)
- Auto-translating via external services

## Implementation Plan

1. After SHA-42 mid plan lands, link SHA-43 in PR description.
2. Defer KO backfill until freshness gate is stable.

## Files / Areas Likely Affected

- TBD — `scripts/build_locale_ko.py`, SHA-43

## Validation Plan

- N/A (tracking only)

## Acceptance Criteria

- [ ] Remaining risks from SHA-42 spec are reported.
- [ ] SHA-43 referenced as follow-up.

## Risks / Open Questions

- Freshness gate may pass while Korean UI still shows English for unmapped msgids.
