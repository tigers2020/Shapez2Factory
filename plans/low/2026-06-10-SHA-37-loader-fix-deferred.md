---
linear_issue: SHA-37
title: Lab page context serves stale composed replay without is_cache_summary_valid guard
priority: Low
labels:
  - bug
  - ui
status: planned
created_by: todo-plan-automation
---

# Plan: Deferred loader-level cache fix (SHA-38) and schema migration tooling

## Source Issue

- Linear: SHA-37
- Status at planning time: Todo
- Priority: Low

## Problem

Loader-level fix for `load_composed_frames_for_run_id` is tracked in SHA-38. Broad replay schema migration tooling is out of scope.

## Scope

- Document SHA-38 as owner for loader path after mid consumer guard lands.
- No loader refactor in SHA-37 unless mid fix reveals shared helper extraction.

## Non-goals

- Implementing SHA-38.
- Schema migration tooling.

## Implementation Plan

1. After mid fix merges, verify page context and lazy endpoint agree; leave loader hardening to SHA-38.
2. Add PR cross-reference to SHA-38 if both touch `lab_replay_persisted_cache.py`.

## Files / Areas Likely Affected

- TBD (SHA-38)

## Validation Plan

- lint: N/A
- typecheck: N/A
- tests: N/A
- build: N/A
- manual verification: SHA-38 remains open

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Mid fix at consumer layer may mask loader bug until SHA-38 lands — acceptable per issue priority split.
