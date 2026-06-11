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
- Status at planning time: Todo → In Progress
- Priority: Mid

## Problem

`build_asteroid_lab_page_context` accepts composed replay frames from `load_composed_frames_for_run_id` when they are renderable, but never checks `is_cache_summary_valid(manifest_summary)`. The lazy replay JSON endpoint in `public_pages.py` requires both renderability and a valid `lab_replay_cache_schema_version`, so the SSR Lab page and the lazy-load API can disagree on which replay payload to show.

## Scope

Align `build_asteroid_lab_page_context` replay cache-hit logic with `public_pages` lazy replay endpoint:

- Require `is_cache_summary_valid(manifest_summary)` before using composed DB cache.
- Keep existing renderability checks (`lab_replay_frames_are_renderable`).
- On cache miss (invalid summary or non-renderable frames), recompose via `build_lab_replay_frames_for_project` and persist with `persist_composed_replay_for_run_id`, matching the lazy endpoint path.

## Non-goals

- Changing artifact-jsonl first authority semantics.
- Refactoring the entire replay compose pipeline.
- Broad replay schema version migration tooling.
- Loader-level `load_composed_frames_for_run_id` column-path fix (tracked in SHA-38).

## Implementation Plan

1. Import `is_cache_summary_valid` in `django_apps/web/services/asteroid_lab_page_context.py` from `lab_replay_persisted_cache`.
2. Update the cache-hit branch (~lines 260–272) to mirror `public_pages.py` (~lines 602–605):

   ```python
   if (
       cached_frames is not None
       and lab_replay_frames_are_renderable(cached_frames)
       and is_cache_summary_valid(manifest_summary)
   ):
   ```

3. Ensure the existing `else` branch (recompose + persist) runs when summary is invalid, even if `load_composed_frames_for_run_id` returns renderable frames from the dedicated payload column path.
4. Add regression test: manifest summary lacks `lab_replay_cache_schema_version` but `lab_replay_payload_json.composed_frames` exists and is renderable — page context must recompose (not serve stale cache), matching lazy endpoint behavior.
5. Run focused tests:

   ```bash
   pytest tests/unit/asteroid_lab/test_artifact_first_replay.py -v
   pytest tests/integration/web/test_lab_replay_compose_defer.py -v
   ```

6. Run validation gates from `AGENTS.md` if touching imports only minimally; full PR gate before merge.

## Files / Areas Likely Affected

- `django_apps/web/services/asteroid_lab_page_context.py`
- `django_apps/web/views/public_pages.py` (reference only — do not change unless contract drift found)
- `django_apps/asteroid_lab/services/lab_replay_persisted_cache.py` (reference only)
- `tests/integration/web/test_lab_replay_compose_defer.py` or new unit test alongside `test_artifact_first_replay.py`

## Validation Plan

- lint: `ruff check django_apps/web/services/asteroid_lab_page_context.py`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/asteroid_lab/test_artifact_first_replay.py tests/integration/web/test_lab_replay_compose_defer.py -v`
- build: `python manage.py check`
- manual verification: Load Lab page for a run with stale composed cache (missing schema version); confirm SSR initial replay matches lazy JSON endpoint after fix.

## Acceptance Criteria

- [ ] Page context and lazy JSON endpoint apply the same cache validity contract (`renderable` + `is_cache_summary_valid`).
- [ ] Stale composed cache is not served on initial SSR after schema bump.
- [ ] Regression test added for invalid manifest summary + renderable dedicated payload.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are documented (SHA-38 loader path).

## Risks / Open Questions

- `load_composed_frames_for_run_id` dedicated-payload column path still returns frames without `is_cache_summary_valid` — page context fix gates at consumer level; SHA-38 addresses loader consistency.
- Recompose on SSR page load may add latency on first hit after schema bump; acceptable and matches lazy endpoint.
