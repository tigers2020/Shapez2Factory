---
linear_issue: SHA-36
title: CLI RunStackUseCase omits layer_01_reconstruction from layer_summaries and replay_core
priority: Low
labels:
  - bug
  - solver
status: planned
created_by: todo-plan-automation
---

# Plan: Deferred reconstruction_capacity authority drift (SHA-36 low scope)

## Source Issue

- Linear: SHA-36
- Status at planning time: Todo
- Priority: Low

## Problem

`reconstruction_capacity.by_resource.authority` drift (`game_data_snapshot` vs `MiningExtractionRule`) and L6 validation stub (SHA-15) are noted in the issue but out of mid scope.

## Scope

- Track as separate follow-on; no code in SHA-36 mid fix unless L1 metrics expose an obvious doc gap.

## Non-goals

- Authority field unification.
- L6 validation implementation.

## Implementation Plan

1. After mid fix, confirm whether L1 metrics make authority drift visible in artifacts.
2. File or link existing issue if drift remains user-visible.

## Files / Areas Likely Affected

- TBD

## Validation Plan

- lint: N/A
- typecheck: N/A
- tests: N/A
- build: N/A
- manual verification: SHA-28 / SHA-15 remain tracked separately

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- May merge into SHA-28 if provenance work already covers authority fields.
