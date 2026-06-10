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

# Plan: Deferred semantic validation phase

## Source Issue

- Linear: SHA-46
- Status at planning time: Todo
- Priority: Low (deferred)

## Problem

IVVD validation has stub semantic phase; xref/schema issues are in scope for SHA-46 but full semantic rules are not.

## Scope

Track only — no implementation in SHA-46.

## Non-goals

- Implementing semantic validation rules
- Seal algorithm changes

## Implementation Plan

1. Note semantic phase remains stub after SHA-46 mid fix.
2. Schedule separate card if semantic blocking rules are needed.

## Files / Areas Likely Affected

- TBD — `basedata_import_service.py` validation phases

## Validation Plan

- N/A

## Acceptance Criteria

- [ ] Remaining risks documented per SHA-46 spec.

## Risks / Open Questions

- Seal-with-errors fix does not add semantic coverage.
