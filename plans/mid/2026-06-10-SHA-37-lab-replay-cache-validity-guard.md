---
linear_issue: SHA-37
title: Lab page context serves stale composed replay without is_cache_summary_valid guard
priority: Mid
labels:
  - bug
  - ui
status: planned
created_by: todo-plan-automation
---

# Plan: Align Lab page context replay cache guard with lazy JSON endpoint

## Source Issue

- Linear: SHA-37
- Status at planning time: Todo
- Priority: Mid

## Problem

`build_asteroid_lab_page_context` serves composed replay from DB cache when frames are renderable, but skips `is_cache_summary_valid(manifest_summary)`. The lazy replay JSON endpoint in `public_pages.py` requires both renderability and valid `lab_replay_cache_schema_version`, so SSR and lazy-load can disagree.

## Scope

Gate `build_asteroid_lab_page_context` cache hits the same way as `public_pages.py`: require `is_cache_summary_valid`, existing renderability, and stale L3 thin-cache rules before using composed cache; recompose + persist on miss.

## Non-goals

- Changing artifact-jsonl first authority semantics.
- Refactoring entire replay compose pipeline.
- Broad replay schema version migration tooling.

## Implementation Plan

1. Import `is_cache_summary_valid` from `django_apps/asteroid_lab/services/lab_replay_persisted_cache.py` into `django_apps/web/services/asteroid_lab_page_context.py`.
2. Mirror `public_pages.py` cache-hit branch: renderable AND `is_cache_summary_valid(summary)` before accepting `load_composed_frames_for_run_id` result.
3. On miss, recompose and persist fresh frames (same path as lazy endpoint).
4. Add unit or integration test: manifest summary lacks `lab_replay_cache_schema_version` but dedicated payload exists — page context should recompose, matching lazy endpoint.
5. Extend or reference `tests/unit/asteroid_lab/test_artifact_first_replay.py::test_dedicated_payload_wins_over_legacy_config_cache` pattern.

## Files / Areas Likely Affected

- `django_apps/web/services/asteroid_lab_page_context.py`
- `django_apps/web/views/public_pages.py` (reference only)
- `django_apps/asteroid_lab/services/lab_replay_persisted_cache.py`
- `tests/unit/asteroid_lab/test_artifact_first_replay.py` (or new web service test)

## Validation Plan

- lint: `ruff check django_apps/web/services/ django_apps/asteroid_lab/services/`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/asteroid_lab/test_artifact_first_replay.py -v` plus new guard test
- build: `python manage.py check`
- manual verification: Load Lab page for run with stale cache schema; confirm SSR matches lazy JSON payload after fix

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- SHA-38 targets loader-level inconsistency; coordinate to avoid duplicate fixes.
- Recompose on every page load if cache invalid may add latency — acceptable per issue (matches lazy endpoint).
