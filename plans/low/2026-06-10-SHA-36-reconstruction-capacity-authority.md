---
linear_issue: SHA-36
title: CLI RunStackUseCase omits layer_01_reconstruction from layer_summaries and replay_core
priority: Low
labels:
  - bug
  - solver
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: reconstruction_capacity authority drift

## Source Issue

- Linear: SHA-36
- Status at planning time: Todo
- Priority: Low

## Problem

`reconstruction_capacity.by_resource.authority` may drift between `game_data_snapshot` and `MiningExtractionRule` sources. Not blocking L1 summary emission but noted in issue spec.

## Scope

- Audit and document authority field consistency after Mid L1 summary fix.

## Non-goals

- L1 summary emission (Mid plan).

## Implementation Plan

1. Compare CLI vs Django L1 metrics authority fields post-Mid fix.
2. File separate issue if drift requires code change.

## Files / Areas Likely Affected

- `src/shapez2_factory/application/asteroid_lab/reconstruction_capacity.py` (TBD)

## Validation Plan

- manual verification: Compare L1 metrics in CLI vs Django artifacts

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Depends on Mid plan; may be out of scope for SHA-36.
