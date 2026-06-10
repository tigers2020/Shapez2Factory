---
linear_issue: SHA-38
title: load_composed_frames_for_run_id column path skips is_cache_summary_valid (config fallback enforces it)
priority: Low
labels:
  - bug
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Consumer-only page-context cache guard (SHA-37 follow-up, deferred)

## Source Issue

- Linear: SHA-38 (Low priority breakdown item; tracked separately as SHA-37)
- Status at planning time: Todo
- Priority: Low

## Problem

SHA-37 reports that `build_asteroid_lab_page_context` can serve stale composed replay without an `is_cache_summary_valid` guard at the consumer layer. SHA-38 fixes the loader inconsistency at the source; a redundant consumer guard may still be desirable for defense-in-depth.

## Scope

Document and defer consumer-only gating to SHA-37. Do not implement page-context changes as part of SHA-38 Mid work.

## Non-goals

- Implementing SHA-37 in this card.
- Broad replay compose pipeline refactor.

## Implementation Plan

1. After SHA-38 Mid lands, verify whether `build_asteroid_lab_page_context` still needs an explicit `is_cache_summary_valid` check when calling `load_composed_frames_for_run_id`.
2. If loader contract is sufficient, close SHA-37 with rationale; otherwise implement consumer guard per SHA-37 spec.

## Files / Areas Likely Affected

- `django_apps/web/services/asteroid_lab_page_context.py` (SHA-37 scope, not SHA-38)

## Validation Plan

- tests: SHA-37 acceptance tests when that card is implemented
- manual verification: Lab page replay with schema-stale cache after SHA-38 fix

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Redundant guards vs single loader authority—prefer loader fix (SHA-38) as canonical; consumer guard is optional hardening only.
