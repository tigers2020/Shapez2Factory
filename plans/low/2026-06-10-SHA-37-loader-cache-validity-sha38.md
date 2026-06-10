---
linear_issue: SHA-37
title: Lab page context serves stale composed replay without is_cache_summary_valid guard
priority: Low
labels:
  - bug
  - ui
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Loader-level cache validity (SHA-38 alignment)

## Source Issue

- Linear: SHA-37
- Status at planning time: Todo
- Priority: Low

## Problem

`load_composed_frames_for_run_id` column path may skip `is_cache_summary_valid` while config fallback enforces it (SHA-38). Page-context fix alone may not fully unify cache contract.

## Scope

- Cross-check SHA-38 loader fix after Mid page-context guard lands.
- Ensure all consumers use same validity contract.

## Non-goals

- Page context guard (Mid plan).

## Implementation Plan

1. After SHA-37 Mid merges, verify SHA-38 scope overlap.
2. Close or link SHA-38 if loader fix still needed.
3. Add integration test across page context + loader if gap remains.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/lab_replay_persisted_cache.py` (TBD)
- SHA-38 tracked separately

## Validation Plan

- tests: `pytest tests/unit/asteroid_lab/ -v -k cache`

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- SHA-38 may be the authoritative fix; coordinate to avoid duplicate work.
