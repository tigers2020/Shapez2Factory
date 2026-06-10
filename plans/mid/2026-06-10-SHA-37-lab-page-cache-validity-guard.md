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

# Plan: Align Lab page context replay cache guard with lazy JSON endpoint

## Source Issue

- Linear: SHA-37
- Status at planning time: In Progress
- Priority: Mid

## Problem

`build_asteroid_lab_page_context` accepts composed replay frames from `load_composed_frames_for_run_id` when they are renderable, but never checks `is_cache_summary_valid(manifest_summary)`. The lazy replay JSON endpoint in `public_pages.py` requires both renderability and a valid `lab_replay_cache_schema_version`, so the SSR Lab page and the lazy-load API can disagree on which replay payload to show.

## Scope

Align `build_asteroid_lab_page_context` replay cache hit logic with `public_pages` lazy replay endpoint: require `is_cache_summary_valid(manifest_summary)` (and existing renderability / stale L3 checks) before using composed cache; recompose + persist on miss.

## Non-goals

- Changing artifact-jsonl first authority semantics.
- Refactoring the entire replay compose pipeline.
- Broad replay schema version migration tooling.
- Loader-level `load_composed_frames_for_run_id` column-path fix (tracked in SHA-38).

## Implementation Plan

1. Import `is_cache_summary_valid` from `django_apps.asteroid_lab.services.lab_replay_persisted_cache` in `asteroid_lab_page_context.py`.
2. Change the cache-hit branch at lines 265–272 to mirror `public_pages.py` lines 602–606:
   - Require `cached_frames is not None`
   - AND `lab_replay_frames_are_renderable(cached_frames)`
   - AND `is_cache_summary_valid(manifest_summary)`
3. On cache miss (invalid summary or non-renderable frames), fall through to existing recompose path (`build_lab_replay_frames_for_project` + `persist_composed_replay_for_run_id`).
4. Add unit or integration test: manifest summary lacks `lab_replay_cache_schema_version` but dedicated `lab_replay_payload_json` exists with renderable frames — page context must recompose (not serve stale cache), matching lazy endpoint behavior.
5. Run focused tests:
   - `pytest tests/unit/asteroid_lab/test_artifact_first_replay.py -v`
   - `pytest tests/integration/web/test_lab_replay_compose_defer.py -v`
   - Add new test in `tests/unit/web/` or `tests/integration/web/` for page context cache guard.

## Files / Areas Likely Affected

- `django_apps/web/services/asteroid_lab_page_context.py`
- `django_apps/web/views/public_pages.py` (reference only — do not change unless shared helper extraction is trivial)
- `django_apps/asteroid_lab/services/lab_replay_persisted_cache.py` (`is_cache_summary_valid`, `CURRENT_LAB_REPLAY_CACHE_SCHEMA_VERSION`)
- `tests/unit/asteroid_lab/test_artifact_first_replay.py`
- `tests/integration/web/test_lab_replay_compose_defer.py`
- New or extended test under `tests/unit/web/` or `tests/integration/web/`

## Validation Plan

- lint: `ruff check django_apps/web/services/asteroid_lab_page_context.py`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/asteroid_lab/test_artifact_first_replay.py tests/integration/web/test_lab_replay_compose_defer.py -v` plus new page-context test
- build: `python manage.py check`
- manual verification: Load Lab SSR page for a run with stale manifest summary (missing schema version); confirm initial render matches lazy JSON replay after fix.

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- `load_composed_frames_for_run_id` column path still returns frames without `is_cache_summary_valid` (SHA-38); page-context guard fixes consumer mismatch but loader inconsistency remains until SHA-38 lands.
- `test_dedicated_payload_wins_over_legacy_config_cache` documents loader behavior where dedicated payload wins without schema check — page context must not rely on that path for cache hit when summary is invalid.
- Coordinate with SHA-38 if both land in same release to avoid double-recompose churn.
