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

# Plan: KO translation completeness (SHA-43 follow-up)

## Source Issue

- Linear: SHA-42
- Status at planning time: Todo
- Priority: Low

## Problem

Catalog freshness (Mid plan) is separate from KO translation completeness tracked in SHA-43.

## Scope

Cross-link SHA-43; no translation work in SHA-42.

## Non-goals

- SHA-43 strict coverage expansion.

## Implementation Plan

1. Note in SHA-42 PR that freshness gate does not enforce KO msgstr completeness.
2. Link SHA-43 for i18n backlog.

## Files / Areas Likely Affected

- TBD documentation only

## Validation Plan

- n/a

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- None.
