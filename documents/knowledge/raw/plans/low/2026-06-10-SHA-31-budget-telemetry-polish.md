---
linear_issue: SHA-31
title: L3 rim greedy placement ignores LayerBudgetContext during Phase B route probe expansion
priority: Low
labels:
  - bug
  - performance
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: L3 Phase B budget polling telemetry (SHA-31 Low)

## Source Issue

- Linear: SHA-31
- Status at planning time: Todo
- Priority: Low

## Problem

After Mid-priority budget polling lands in L3 Phase B, operators lack visibility into when and why budget exhaustion truncated candidate generation.

## Scope

Optional budget polling instrumentation and logging polish for L3 Phase B.

## Non-goals

- No algorithm changes beyond logging/telemetry.
- No new exit codes.

## Implementation Plan

1. After Mid plan lands, identify budget-exhaustion exit paths in Phase B.
2. Add structured log or layer summary field when Phase B stops due to budget (not placement failure).
3. Cross-link to stack_runner budget docs if a canonical field exists.

## Files / Areas Likely Affected

- `src/shapez2_factory/application/asteroid_lab/layers/layer_03_rim_greedy_placement/run.py`
- TBD — layer summary / replay metadata types if extended

## Validation Plan

- lint: `ruff check` on touched files
- typecheck: spot-check if types change
- tests: extend existing L3 test to assert budget-exhausted metadata when applicable
- build: N/A
- manual verification: Log output shows budget truncation reason on capped run

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Depends on Mid plan completion; defer if Mid not merged.
- Avoid noisy logs on every probe iteration — log at phase boundary only.
