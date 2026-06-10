---
linear_issue: SHA-34
title: stack_runner marks L2 COMPLETED and returns SUCCESS when exterior transport returns None
priority: Low
labels:
  - bug
  - solver
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Layer skip-reason enum refactor (deferred)

## Source Issue

- Linear: SHA-34
- Status at planning time: Todo
- Priority: Low

## Problem

Broader layer skip-reason enum consistency across L2–L6 is out of scope for the Mid fix but noted as follow-up cleanup.

## Scope

- Document deferred skip-reason enum refactor opportunity after Mid fail-closed fix lands.

## Non-goals

- Changing stack_runner fail-closed behavior (Mid plan).

## Implementation Plan

1. After Mid plan merges, audit skip-reason usage across layers.
2. Propose unified `SKIPPED_INPUT` / failure outcome enum if duplication found.
3. Track as separate issue if scope exceeds Low.

## Files / Areas Likely Affected

- `src/shapez2_factory/application/asteroid_lab/layers/contracts/` (TBD)

## Validation Plan

- tests: TBD if enum refactor proceeds
- manual verification: N/A until scoped

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- May warrant separate Linear issue if refactor is non-trivial.
