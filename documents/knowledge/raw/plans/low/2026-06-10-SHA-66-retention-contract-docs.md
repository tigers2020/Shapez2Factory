---
linear_issue: SHA-66
title: Layer post-summary log retention is non-deterministic (mtime-only sort prunes wrong runs)
priority: Low
labels:
  - bug
  - test
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Document layer post-summary log retention ordering contract

## Source Issue

- Linear: SHA-66
- Status at planning time: Todo
- Priority: Low

## Problem

After the Mid-priority fix for deterministic retention, the ordering contract (mtime primary, name secondary tie-break) should be explicit in code/docs so future changes do not reintroduce mtime-only sorting or ambiguous pruning behavior.

## Scope

Document retention ordering contract in module docstring or observability notes. Optionally update `daily-project-inspection-log.md` to note the fix and close the prior xdist/mtime flake observation.

## Non-goals

- Changing retention logic (handled in Mid plan)
- Changing default `ASTEROID_LAB_LAYER_POST_SUMMARY_LOG_MAX_RUNS`
- Broader observability schema changes

## Implementation Plan

1. Add a short docstring or module-level comment on `_prune_old_runs` describing:
   - Sort key: `(st_mtime, directory_name)` ascending; oldest pruned first.
   - Pruning runs before new directory creation; current session dir is not yet on disk during prune.
   - Custom `run_id` values should be monotonic or time-ordered when mtimes may collide.

2. Optionally add one line to `django_apps/asteroid_lab/layers/observability/layer_post_summary_log.py` module docstring referencing retention behavior.

3. Update `docs/agent-workflows/daily-project-inspection-log.md`:
   - Mark the `_prune_old_runs` mtime flake item as resolved (reference SHA-66).
   - Remove or annotate stale repro steps if they no longer apply.

4. No new tests required beyond Mid plan; docs-only validation.

## Files / Areas Likely Affected

- `django_apps/asteroid_lab/layers/observability/layer_post_summary_log.py` (docstring on `_prune_old_runs` or module header)
- `docs/agent-workflows/daily-project-inspection-log.md` (optional resolution note)

## Validation Plan

- lint: N/A (docs/comments only)
- typecheck: N/A
- tests: N/A
- build: N/A
- manual verification: read docstring and inspection log entry for clarity and accuracy

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.
- [ ] Retention ordering contract is discoverable without reading test code.

## Risks / Open Questions

- Defer doc update until Mid fix is merged to avoid documenting behavior that does not yet exist.
- Keep inspection-log edit minimal — one resolution bullet, not a full rewrite.
