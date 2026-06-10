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

# Plan: Loader-level cache guard (SHA-38 coordination)

## Source Issue

- Linear: SHA-37
- Status at planning time: Todo
- Priority: Low

## Problem

SHA-38 targets `load_composed_frames_for_run_id` column path skipping `is_cache_summary_valid` at loader source — complementary to page-context consumer fix.

## Scope

Coordinate with SHA-38 loader-level fix after Mid consumer guard lands.

## Non-goals

- Implementing SHA-38 in SHA-37 Mid scope.

## Implementation Plan

1. After Mid plan, review SHA-38 scope for loader centralization.
2. If loader fix makes consumer guard redundant, document single canonical cache-hit function.
3. Avoid duplicate validity checks in three places — prefer one loader API.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/lab_replay_persisted_cache.py` (SHA-38)
- TBD — loader module for `load_composed_frames_for_run_id`

## Validation Plan

- lint: N/A until SHA-38
- typecheck: N/A
- tests: existing replay cache tests
- build: N/A
- manual verification: Single cache contract across all consumers

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Depends on SHA-38 scheduling; Mid plan valid standalone.
