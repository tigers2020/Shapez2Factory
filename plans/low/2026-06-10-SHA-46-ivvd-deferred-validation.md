---
linear_issue: SHA-46
title: IVVD import_basedata_bundle seals release by default despite error-level integrity issues
priority: Low
labels:
  - priority:mid
  - bug
status: planned
created_by: todo-plan-automation
---

# Plan: IVVD deferred validation items (SHA-46 Low scope)

## Source Issue

- Linear: SHA-46
- Status at planning time: Todo
- Priority: Low

## Problem

SHA-46 Low section lists full semantic validation rules (stub phase) and seal algorithm / canonical payload format changes — explicitly out of scope for the Mid seal-behavior fix.

## Scope

Track deferred items only; no implementation in SHA-46 Mid PR.

## Non-goals

- Implementing semantic validation stub phase
- Changing seal hash algorithm or payload format

## Implementation Plan

1. Confirm Mid fix does not expand validator scope.
2. Open separate issues if semantic validation or seal format changes are requested later.

## Files / Areas Likely Affected

- TBD

## Validation Plan

- lint: N/A
- typecheck: N/A
- tests: N/A
- build: N/A
- manual verification: N/A

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Tracking-only plan for Low section items listed in SHA-46 spec.
