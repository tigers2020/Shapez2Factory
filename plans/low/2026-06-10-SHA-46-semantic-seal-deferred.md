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

# Plan: Deferred IVVD semantic validation and seal format work (SHA-46 Low)

## Source Issue

- Linear: SHA-46
- Status at planning time: Todo
- Priority: Low

## Problem

Low-priority items from SHA-46 are explicitly out of scope for the Mid fix: semantic validation stub phase and seal algorithm / canonical payload format changes.

## Scope

No implementation in this slice. Track as deferred follow-ups only if separately prioritized.

## Non-goals

- Implementing full semantic validation rules
- Changing seal algorithm or canonical payload format

## Implementation Plan

1. No code changes — deferred per source issue Non-goals.
2. If semantic validation is later prioritized, extend `_run_validation_phases` stub at `PHASE_SEMANTIC` with real domain rules.
3. If seal format changes are needed, update `canonical_seal_payload_v1` and migration strategy separately.

## Files / Areas Likely Affected

- `django_apps/shapez_core/services/basedata_import_service.py` (semantic stub)
- `django_apps/shapez_core/domain/basedata_seal.py` (seal algorithm)

## Validation Plan

- lint: N/A (no changes)
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

- Semantic stub currently always succeeds; real rules may surface additional blocking issues after Mid fix lands.
- Seal format changes would require version bump and backward-compat plan.
