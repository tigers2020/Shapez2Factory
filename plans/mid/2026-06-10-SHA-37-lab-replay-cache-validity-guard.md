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

# Plan: Lab page context serves stale composed replay without is_cache_summary_valid guard

## Source Issue

- Linear: SHA-37
- Status at planning time: Todo
- Priority: Mid

## Problem

`build_asteroid_lab_page_context` accepts composed replay frames from `load_composed_frames_for_run_id` when renderable, but never checks `is_cache_summary_valid(manifest_summary)`. The lazy replay JSON endpoint in `public_pages.py` requires both renderability and valid `lab_replay_cache_schema_version`, so SSR Lab page and lazy-load API can disagree on replay payload.

## Scope

Align `build_asteroid_lab_page_context` replay cache hit logic with `public_pages` lazy replay endpoint: require `is_cache_summary_valid(manifest_summary)` (and existing renderability / stale L3 checks) before using composed cache; recompose + persist on miss.

## Non-goals

- Changing artifact-jsonl first authority semantics.
- Refactoring the entire replay compose pipeline.
- Broad replay schema version migration tooling.
- Loader-level fix in SHA-38 (related but separate).

## Implementation Plan

1. Read `django_apps/web/services/asteroid_lab_page_context.py` cache-hit branch (~L260–272) and mirror gate from `public_pages.py` (~L601–605).
2. Import `is_cache_summary_valid` from `django_apps/asteroid_lab/services/lab_replay_persisted_cache.py`.
3. Gate cache hit: require `lab_replay_frames_are_renderable(cached_frames)` AND `is_cache_summary_valid(manifest_summary)` (plus any existing stale L3 thin-cache rules already in page context).
4. On cache miss (invalid summary), call same recompose + persist path used by lazy endpoint — extract shared helper if duplication is large, but prefer minimal inline gate if paths are short.
5. Add unit or integration test: manifest summary lacks `lab_replay_cache_schema_version` but dedicated payload exists — page context should recompose, matching lazy endpoint (`test_dedicated_payload_wins_over_legacy_config_cache` pattern).
6. Regression: valid cache still hits; invalid schema version triggers recompose.

## Files / Areas Likely Affected

- `django_apps/web/services/asteroid_lab_page_context.py`
- `django_apps/web/views/public_pages.py` (read-only reference or shared helper extraction)
- `django_apps/asteroid_lab/services/lab_replay_persisted_cache.py` (`is_cache_summary_valid`, `CURRENT_LAB_REPLAY_CACHE_SCHEMA_VERSION`)
- `tests/unit/asteroid_lab/test_artifact_first_replay.py`

## Validation Plan

- lint: `ruff check .`
- typecheck: `mypy django_apps config src`
- tests: `pytest tests/unit/asteroid_lab/test_artifact_first_replay.py -v`
- build: `python manage.py check`
- manual verification: Lab page initial SSR vs lazy JSON load show same replay after cache schema bump scenario

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- SHA-38 fixes loader inconsistency at source; this issue fixes consumer guard — coordinate to avoid double-recompose hot paths.
- Extracting shared cache-hit helper between `public_pages` and `asteroid_lab_page_context` is optional; keep diff minimal unless duplication is error-prone.
