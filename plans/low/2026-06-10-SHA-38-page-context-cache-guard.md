---
linear_issue: SHA-38
title: load_composed_frames_for_run_id column path skips is_cache_summary_valid
priority: Low
labels:
  - bug
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Consumer-only cache guard in page context (SHA-37)

## Source Issue

- Linear: SHA-38
- Status at planning time: Todo
- Priority: Low

## Problem

SHA-37 tracks page-context serving stale composed replay without `is_cache_summary_valid`. Loader fix (Mid plan) should address root cause; consumer guard may remain as defense in depth.

## Scope

Evaluate whether `build_asteroid_lab_page_context` needs explicit `is_cache_summary_valid` after loader unification.

## Non-goals

- Loader unification (Mid plan).
- Broad replay compose refactor.

## Implementation Plan

1. After SHA-38 loader fix, retest page context with invalid manifest summary.
2. If loader returns `None`, remove redundant consumer guard or add explicit test documenting behavior.
3. Close or update SHA-37 based on outcome.

## Files / Areas Likely Affected

- `django_apps/web/services/asteroid_lab_page_context.py`

## Validation Plan

- tests: page context integration tests if present
- manual verification: stale cache does not render in lab UI

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- SHA-37 may be closable as duplicate once loader is fixed.
