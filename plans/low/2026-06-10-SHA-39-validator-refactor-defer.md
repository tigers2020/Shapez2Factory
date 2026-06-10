---
linear_issue: SHA-39
title: game_data browse dashboard omits validate_aggregate_root_inlines errors from staff UI
priority: Low
labels:
  - bug
  - ui
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Defer validator merge refactor

## Source Issue

- Linear: SHA-39
- Status at planning time: Todo
- Priority: Low

## Problem

Issue spec lists merging section and aggregate validators as Low priority non-goal / future cleanup.

## Scope

Document decision to keep separate validators; optional future unified error list with prefixes.

## Non-goals

- Browse UI wiring (Mid plan).

## Implementation Plan

1. After Mid plan lands, add brief comment in `registry.py` or browse view explaining dual-validator design.
2. No functional merge unless operator feedback requires it.

## Files / Areas Likely Affected

- `django_apps/game_data/browse/registry.py`

## Validation Plan

- n/a (docs-only)

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- None — explicitly deferred per issue non-goals.
