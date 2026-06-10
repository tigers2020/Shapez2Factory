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

# Plan: Loader-level cache validity (deferred to SHA-38)

## Source Issue

- Linear: SHA-37 (Low priority items)
- Status at planning time: In Progress
- Priority: Low

## Problem

SHA-37 Mid scope fixes the page-context consumer. Low-priority follow-ups remain at the loader layer and in migration tooling.

## Scope

Track only — no implementation in SHA-37:

- Loader-level fix: `load_composed_frames_for_run_id` column path skips `is_cache_summary_valid` while config fallback enforces it (SHA-38).
- Broad replay schema migration tooling (out of scope for both SHA-37 and SHA-38).

## Non-goals

- Implementing SHA-38 in this plan.
- Schema migration automation.

## Implementation Plan

1. No code changes under SHA-37 Low scope.
2. After SHA-37 Mid lands, implement SHA-38 per its own plan.
3. Optionally document cache validity contract in `lab_replay_persisted_cache.py` module docstring once both consumers and loader align.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/services/lab_replay_persisted_cache.py` (SHA-38)
- Related: SHA-38 plan when created

## Validation Plan

- lint: N/A (tracking only)
- typecheck: N/A
- tests: N/A for SHA-37 Low
- build: N/A
- manual verification: N/A

## Acceptance Criteria

- [ ] SHA-38 tracked separately; not blocked by SHA-37 Mid.
- [ ] No SHA-37 Mid changes depend on Low items.
- [ ] Remaining loader inconsistency documented in SHA-37 Mid risks.

## Risks / Open Questions

- Until SHA-38 lands, other consumers calling `load_composed_frames_for_run_id` directly may still see stale column-path cache.
