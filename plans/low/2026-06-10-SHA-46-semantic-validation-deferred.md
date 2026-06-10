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

# Plan: IVVD semantic validation and seal algorithm (deferred)

## Source Issue

- Linear: SHA-46
- Status at planning time: Todo
- Priority: Low (deferred from SHA-46 non-goals)

## Problem

SHA-46 mid scope addresses sealing when xref/schema blocking issues exist. Full semantic validation (stub phase) and seal algorithm / canonical payload format changes remain out of scope.

## Scope

Track only. No implementation in SHA-46.

## Non-goals

- Implementing semantic validation stub phase.
- Changing seal hash algorithm or payload format.

## Implementation Plan

1. Complete SHA-46 mid plan (blocking-issue seal alignment).
2. Open separate issue if semantic validation phase needs implementation.
3. Document `IntegrityStatus.FAILED` usage after mid fix lands.

## Files / Areas Likely Affected

- `django_apps/shapez_core/services/basedata_import_service.py` (validation phases)
- TBD: future semantic validation module

## Validation Plan

- lint: N/A (deferred)
- typecheck: N/A (deferred)
- tests: N/A (deferred)
- build: N/A (deferred)
- manual verification: N/A (deferred)

## Acceptance Criteria

- [ ] Deferred items remain out of SHA-46 mid scope.

## Risks / Open Questions

- Operators may assume all validation classes are enforced after mid fix; semantic stub remains inactive.
