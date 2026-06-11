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

# Plan: Loader-level cache validity and migration tooling (SHA-37 Low — deferred)

## Source Issue

- Linear: SHA-37
- Priority: Low (deferred from SHA-37 priority breakdown)

## Problem

SHA-37 Mid scope fixes the page-context consumer. Two Low-priority items remain out of Mid scope:

- Loader-level fix: `load_composed_frames_for_run_id` column path skips `is_cache_summary_valid` — tracked in SHA-38.
- Broad replay schema migration tooling for bulk cache invalidation after version bumps.

## Scope

**None for SHA-37 implementation.** Document deferral only.

## Non-goals

- Implementing SHA-38 loader changes in this issue.
- Building schema migration CLI or batch recompose tooling.

## Implementation Plan

1. Do not implement in SHA-37 PR.
2. Link SHA-38 in PR description / risks when closing SHA-37.
3. Track migration tooling as separate infra issue if needed after SHA-38 lands.

## Files / Areas Likely Affected

- TBD — SHA-38: `django_apps/asteroid_lab/services/lab_replay_persisted_cache.py`

## Validation Plan

- N/A for SHA-37 closure.

## Acceptance Criteria

- [ ] SHA-37 Mid fix does not expand into loader refactor.
- [ ] SHA-38 referenced in remaining risks.
- [ ] No unrelated behavior is changed.

## Risks / Open Questions

- Until SHA-38 lands, other consumers calling `load_composed_frames_for_run_id` directly may still see stale dedicated-payload cache without consumer-side guard.
