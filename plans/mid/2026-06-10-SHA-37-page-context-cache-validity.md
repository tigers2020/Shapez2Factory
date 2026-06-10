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

# Plan: Lab page context cache validity guard

## Source Issue

- Linear: SHA-37
- Status at planning time: Todo
- Priority: Mid

## Problem

`build_asteroid_lab_page_context` accepts composed replay cache when frames are renderable but never checks `is_cache_summary_valid(manifest_summary)`. Lazy replay JSON endpoint in `public_pages.py` requires both renderability and valid `lab_replay_cache_schema_version`, so SSR Lab page and lazy-load API can disagree.

## Scope

- Align `build_asteroid_lab_page_context` cache hit logic with `public_pages` lazy replay endpoint.
- Require `is_cache_summary_valid` + renderability + stale L3 checks before using composed cache.
- Recompose + persist on miss.
- Add test for manifest without schema version.

## Non-goals

- Changing artifact-jsonl first authority semantics.
- Refactoring entire replay compose pipeline.
- Broad replay schema migration tooling.

## Implementation Plan

1. Import `is_cache_summary_valid` in `asteroid_lab_page_context.py`.
2. Gate cache-hit branch same as `public_pages.py` lines 601–605.
3. On cache miss, trigger recompose + persist (mirror lazy endpoint).
4. Add unit/integration test: manifest summary lacks `lab_replay_cache_schema_version`; page context recomposes instead of serving stale cache.
5. Run `pytest tests/unit/asteroid_lab/test_artifact_first_replay.py -v`.

## Files / Areas Likely Affected

- `django_apps/web/services/asteroid_lab_page_context.py`
- `django_apps/web/views/public_pages.py` (reference only)
- `django_apps/asteroid_lab/services/lab_replay_persisted_cache.py`
- `tests/unit/asteroid_lab/test_artifact_first_replay.py`

## Validation Plan

- lint: `ruff check .`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/asteroid_lab/test_artifact_first_replay.py -v`
- build: `python manage.py check`
- manual verification: Bump cache schema; confirm SSR page matches lazy JSON replay.

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- SHA-38 loader-level fix may also be needed for full consistency.
- SHA-64 runtime compose removal may change recompose cost profile.
