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

# Plan: SHA-38 Low — deferred consumer guard and non-goal items

## Source Issue

- Linear: SHA-38
- Status at planning time: In Progress (triggered from Todo)
- Priority: Low

## Problem

Low-priority items from SHA-38 priority breakdown are out of scope for the Mid loader fix but tracked for follow-up.

## Scope

Document and defer:

- Consumer-only `is_cache_summary_valid` guard in SHA-37 (`build_asteroid_lab_page_context`).
- Broad replay compose pipeline refactor (explicit non-goal).

## Non-goals

- Implementing SHA-37 in this card.
- Replay compose pipeline refactor.

## Implementation Plan

1. After Mid plan lands, verify whether SHA-37 page-context guard is still needed (loader fix may subsume it).
2. If SHA-37 remains open, implement consumer guard there per SHA-37 spec.
3. Do not pursue broad compose pipeline refactor unless a separate issue is opened.

## Files / Areas Likely Affected

- `django_apps/web/services/asteroid_lab_page_context.py` (SHA-37 only)
- TBD for compose refactor (not in scope)

## Validation Plan

- tests: SHA-37 acceptance tests when that card is implemented
- manual verification: Lab page serves no stale composed replay when manifest schema is invalid

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- SHA-37 may become redundant after Mid loader fix; reassess before implementing duplicate guards.
