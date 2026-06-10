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

# Plan: Consumer-only guard and pipeline refactor (deferred)

## Source Issue

- Linear: SHA-38 (Low priority items)
- Status at planning time: In Progress
- Priority: Low

## Problem

Low-priority follow-ups: consumer-only guard in SHA-37 and broad replay compose pipeline refactor.

## Scope

Track only — no implementation in SHA-38 Mid scope.

## Non-goals

- Implementing SHA-37 consumer guard as substitute for loader fix.
- Replay compose pipeline refactor.

## Implementation Plan

1. No code changes under SHA-38 Low scope.
2. SHA-37 consumer guard can land independently as defense-in-depth.
3. Pipeline refactor tracked separately if needed.

## Files / Areas Likely Affected

- TBD (future refactor)

## Validation Plan

- lint: N/A
- typecheck: N/A
- tests: N/A
- build: N/A
- manual verification: N/A

## Acceptance Criteria

- [ ] SHA-37 tracked separately.
- [ ] SHA-38 Mid does not depend on Low items.

## Risks / Open Questions

- Defense-in-depth: both SHA-37 and SHA-38 recommended for full contract alignment.
