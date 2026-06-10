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

# Plan: reconstruction_capacity authority drift follow-up (SHA-36 Low)

## Source Issue

- Linear: SHA-36
- Status at planning time: Todo
- Priority: Low

## Problem

`reconstruction_capacity.by_resource.authority` drift (`game_data_snapshot` vs `MiningExtractionRule`) noted in issue as separate from L1 summary omission.

## Scope

Track or document `reconstruction_capacity.by_resource.authority` drift separately from L1 observability fix.

## Non-goals

- Fixing authority drift in SHA-36 Mid scope.

## Implementation Plan

1. After Mid plan, grep authority fields in L1 metrics output.
2. If drift confirmed, file follow-up or cross-link existing provenance issues (SHA-28).

## Files / Areas Likely Affected

- TBD — follow-up issue only

## Validation Plan

- lint: N/A
- typecheck: N/A
- tests: N/A
- build: N/A
- manual verification: N/A

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Explicitly deferred per issue non-goals.
