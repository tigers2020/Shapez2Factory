---
linear_issue: SHA-37
title: Lab page context serves stale composed replay without is_cache_summary_valid guard
priority: Mid
labels:
  - bug
  - ui
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Align Lab page context replay cache guard with lazy endpoint

## Source Issue

- Linear: SHA-37
- Status at planning time: Todo
- Priority: Mid

## Problem

`build_asteroid_lab_page_context` uses composed cache when frames are renderable only. `public_pages.py` lazy replay endpoint also requires `is_cache_summary_valid(manifest_summary)`. SSR Lab page and lazy JSON can show different replay payloads after cache schema bumps.

## Scope

Gate `build_asteroid_lab_page_context` cache hit with `is_cache_summary_valid` matching `public_pages.py`; recompose + persist on miss.

## Non-goals

- Changing artifact-jsonl first authority.
- Refactoring entire replay compose pipeline.
- Broad replay schema migration tooling.

## Proposed Approach

1. Import `is_cache_summary_valid` from `lab_replay_persisted_cache.py` into `asteroid_lab_page_context.py`.
2. Mirror `public_pages.py` lines 601–605 guard before accepting `cached_frames`.
3. On invalid summary, trigger recompose path (same as lazy endpoint).
4. Add test: manifest summary lacks `lab_replay_cache_schema_version` → page context recomposes, not stale cache.

## Files / Areas Likely Affected

- `django_apps/web/services/asteroid_lab_page_context.py`
- `django_apps/web/views/public_pages.py` (reference)
- `django_apps/asteroid_lab/services/lab_replay_persisted_cache.py`
- `tests/unit/asteroid_lab/test_artifact_first_replay.py`

## Validation Plan

- tests: extend `test_artifact_first_replay.py` or add page-context unit test
- manual: Lab SSR and lazy JSON show same frame count after schema bump

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Coordinate with SHA-38 loader-level fix to avoid double recompose.
- SHA-64 runtime compose removal may change recompose cost profile.
