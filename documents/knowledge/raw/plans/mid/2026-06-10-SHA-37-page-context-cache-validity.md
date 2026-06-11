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

`build_asteroid_lab_page_context` accepts composed replay frames from `load_composed_frames_for_run_id` when they are renderable, but never checks `is_cache_summary_valid(manifest_summary)`. The lazy replay JSON endpoint in `public_pages.py` requires both renderability and a valid `lab_replay_cache_schema_version`, so the SSR Lab page and the lazy-load API can disagree on which replay payload to show.

## Scope

Align `build_asteroid_lab_page_context` replay cache hit logic with `public_pages` lazy replay endpoint: require `is_cache_summary_valid(manifest_summary)` (and existing renderability / stale L3 checks) before using composed cache; recompose + persist on miss.

## Non-goals

- Changing artifact-jsonl first authority semantics.
- Refactoring the entire replay compose pipeline.
- Broad replay schema version migration tooling.

## Implementation Plan

1. Import `is_cache_summary_valid` from `django_apps/asteroid_lab/services/lab_replay_persisted_cache.py` into `django_apps/web/services/asteroid_lab_page_context.py`.
2. Gate the cache-hit branch at lines 260–272 the same way as `django_apps/web/views/public_pages.py` lines 601–605: require renderable frames + `is_cache_summary_valid(summary)` + existing stale L3 thin-cache rules.
3. On cache miss, trigger recompose + persist path matching lazy endpoint behavior.
4. Add integration or unit test (extend `tests/unit/asteroid_lab/test_artifact_first_replay.py` or new page-context test) where manifest summary lacks `lab_replay_cache_schema_version` but dedicated payload exists: page context should recompose, matching lazy endpoint.
5. Cross-check loader behavior in SHA-38 — consumer guard may still be needed until loader is unified.

## Files / Areas Likely Affected

- `django_apps/web/services/asteroid_lab_page_context.py`
- `django_apps/web/views/public_pages.py` (reference contract)
- `django_apps/asteroid_lab/services/lab_replay_persisted_cache.py` (`is_cache_summary_valid`, `CURRENT_LAB_REPLAY_CACHE_SCHEMA_VERSION`)
- `tests/unit/asteroid_lab/test_artifact_first_replay.py`

## Validation Plan

- lint: `ruff check django_apps/web/services/asteroid_lab_page_context.py`
- typecheck: `mypy django_apps config src` (spot-check changed modules)
- tests: `pytest tests/unit/asteroid_lab/test_artifact_first_replay.py -v`
- build: N/A
- manual verification: Lab SSR page and lazy JSON endpoint show same replay after cache schema bump

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Loader-level inconsistency (SHA-38) may still serve stale frames to other callers until fixed at source.
- Recompose on every invalid manifest may increase DB write load — acceptable per existing lazy endpoint contract.
