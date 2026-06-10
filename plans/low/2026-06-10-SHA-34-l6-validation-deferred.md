---
linear_issue: SHA-34
title: stack_runner marks L2 COMPLETED and returns SUCCESS when exterior transport returns None
priority: Low
labels:
  - bug
  - solver
status: planned
created_by: todo-plan-automation
---

# Plan: Deferred L6 validation and skip-reason cleanup (SHA-34 low scope)

## Source Issue

- Linear: SHA-34
- Status at planning time: Todo
- Priority: Low

## Problem

L6 validation stub (SHA-15) and cross-layer skip-reason enum consistency remain out of mid-priority SHA-34 scope but are noted as follow-on maintainability items.

## Scope

- Document deferred SHA-15 / skip-reason work in PR or issue comment after mid fix lands.
- No implementation in SHA-34 unless mid fix exposes an obvious one-line doc gap.

## Non-goals

- Implementing L6 commit-validate.
- Broad enum refactor.

## Implementation Plan

1. After mid fix merges, add a short note in `docs/` or Linear linking SHA-15 as the owner for L6 validation stub.
2. If skip-reason strings diverge after L2 fail-closed change, file a separate issue rather than expanding SHA-34.

## Files / Areas Likely Affected

- TBD (docs only if needed)

## Validation Plan

- lint: N/A
- typecheck: N/A
- tests: N/A
- build: N/A
- manual verification: Confirm SHA-15 remains open and referenced

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Low-priority items may be absorbed into SHA-15; this plan can be closed without code if mid fix is sufficient.
