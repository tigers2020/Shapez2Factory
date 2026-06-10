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

# Plan: Track reconstruction_capacity authority drift separately

## Source Issue

- Linear: SHA-36
- Status at planning time: In Progress
- Priority: Low

## Problem

`reconstruction_capacity.by_resource.authority` may drift between `game_data_snapshot` and `MiningExtractionRule`. Issue spec lists this as Low priority follow-up, not part of core L1 summary fix.

## Scope

- Document or fix authority field consistency in L1 capacity envelope when surfaced in CLI artifacts.

## Non-goals

- Core L1 layer_summaries/replay_core wiring (Mid plan).
- L6 validation stub (SHA-15).

## Implementation Plan

1. Audit `reconstruction_capacity.by_resource.authority` in CLI vs Django L1 output.
2. If drift confirmed, align serializer or document intentional difference in artifact contract.
3. Add focused test if contract is unified.

## Files / Areas Likely Affected

- `src/shapez2_factory/application/asteroid_lab/run_stack.py`
- TBD: capacity envelope builders

## Validation Plan

- tests: add if contract change required
- manual verification: compare Django vs CLI L1 capacity JSON

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- May warrant separate Linear issue if scope grows beyond authority field.
