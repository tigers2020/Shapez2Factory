---
linear_issue: SHA-38
title: load_composed_frames_for_run_id column path skips is_cache_summary_valid (config fallback enforces it)
priority: Low
labels:
  - bug
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Consumer-only cache guard (SHA-37 complement)

## Source Issue

- Linear: SHA-38
- Status at planning time: Todo
- Priority: Low

## Problem

SHA-37 adds `is_cache_summary_valid` guard in `build_asteroid_lab_page_context` as a consumer-side fix. If Mid loader unification (this issue's Mid plan) is delayed, individual consumers may need redundant guards until the loader enforces validity at source. This Low plan tracks optional consumer hardening and guard deduplication after loader fix lands.

## Scope

- Audit all replay cache consumers for consistent validity gating beyond page context.
- Remove redundant consumer guards once loader Mid plan is merged.

## Non-goals

- Loader path unification (Mid plan for SHA-38).
- Replay compose pipeline refactor.
- Schema migration tooling (SHA-37 Low).

## Implementation Plan

1. Inventory callers of `load_composed_frames_for_run_id` and direct column reads in `django_apps/asteroid_lab/services/solver_runtime_entry.py`, `django_apps/web/views/public_pages.py`, `django_apps/web/services/asteroid_lab_page_context.py`.
2. If Mid loader not yet merged, add defensive `is_cache_summary_valid` checks at any consumer still trusting loader output blindly.
3. After Mid loader lands, remove duplicate guards from consumers (keep single source of truth in `lab_replay_persisted_cache.py`).
4. Document consumer contract in module docstring: callers should not re-validate unless loader contract is uncertain.

## Files / Areas Likely Affected

- `django_apps/web/services/asteroid_lab_page_context.py`
- `django_apps/web/views/public_pages.py`
- `django_apps/asteroid_lab/services/solver_runtime_entry.py`
- `django_apps/asteroid_lab/services/lab_replay_persisted_cache.py` (reference)

## Validation Plan

- lint: `ruff check django_apps/web/services/ django_apps/asteroid_lab/services/`
- typecheck: spot-check if guard helpers extracted
- tests: extend `tests/unit/asteroid_lab/test_artifact_first_replay.py` for each consumer path
- build: N/A
- manual verification: No consumer serves stale replay when loader returns `None`

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Redundant guards increase maintenance burden — prefer Mid loader fix; use this plan only as interim or cleanup pass.
- SHA-37 Mid may land before SHA-38 Mid — avoid permanent double-validation without cleanup task.
