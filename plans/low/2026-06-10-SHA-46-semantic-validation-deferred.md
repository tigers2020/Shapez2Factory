---
linear_issue: SHA-46
title: IVVD import_basedata_bundle seals release by default despite error-level integrity issues
priority: Low
labels:
  - bug
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: IVVD semantic validation and seal format changes (deferred)

## Source Issue

- Linear: SHA-46 (Low priority breakdown — out of SHA-46 scope)
- Status at planning time: In Progress
- Priority: Low

## Problem

SHA-46 Low breakdown lists future work explicitly excluded from the Mid seal fix:

1. Full semantic validation rules (currently stub phase)
2. Seal algorithm or canonical payload format changes

## Scope

**None for SHA-46 Mid work.** Document as follow-on backlog only.

## Non-goals

- Do not implement semantic validation in SHA-46 PR.
- Do not change seal hash algorithm as part of default fail-closed sealing fix.

## Implementation Plan

1. Complete SHA-46 Mid plan (`plans/mid/2026-06-10-SHA-46-ivvd-default-seal-fail-closed.md`).
2. Track semantic validation as separate spec/ADR when validation rules are defined.
3. Seal algorithm changes require contract brief + migration plan — not driven by SHA-46.

## Files / Areas Likely Affected

- TBD (semantic validation phase in `basedata_import_service.py`)
- TBD (seal hash utilities)

## Validation Plan

- lint: N/A (deferred)
- typecheck: N/A (deferred)
- tests: N/A (deferred)
- build: N/A (deferred)
- manual verification: N/A (deferred)

## Acceptance Criteria

- [ ] Matches the source issue spec (deferred only).
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Semantic validation scope undefined; stub phase may remain until game-data contract expands.
