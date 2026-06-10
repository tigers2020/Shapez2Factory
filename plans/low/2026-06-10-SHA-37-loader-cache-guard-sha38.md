---
linear_issue: SHA-37
title: Loader-level is_cache_summary_valid fix (SHA-38 coordination)
priority: Low
labels:
  - bug
  - ui
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Coordinate page-context fix with SHA-38 loader guard

## Source Issue

- Linear: SHA-37 / SHA-38
- Status at planning time: Todo
- Priority: Low

## Problem

`load_composed_frames_for_run_id` column path may skip `is_cache_summary_valid` while config fallback enforces it. Page-context fix (mid plan) may mask loader inconsistency if SHA-38 not addressed.

## Scope

- After SHA-37 mid plan, verify SHA-38 scope; apply guard at loader if page-context-only fix insufficient.
- Ensure single cache validity contract documented in `lab_replay_persisted_cache.py`.

## Non-goals

- Implementing SHA-38 fully unless mid plan test gaps require it.

## Implementation Plan

1. Run SHA-37 tests; if dedicated-payload path still bypasses guard, open follow-up or implement SHA-38 guard in loader.
2. Add docstring on `load_composed_frames_for_run_id` listing required preconditions.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/lab_replay_persisted_cache.py`
- TBD: loader module for `load_composed_frames_for_run_id`

## Validation Plan

- tests: `test_artifact_first_replay.py` column-path cases

## Acceptance Criteria

- [ ] Cache validity contract consistent or gap documented for SHA-38.

## Risks / Open Questions

- May be fully superseded by SHA-38 dedicated issue — treat as coordination note.
