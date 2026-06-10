---
linear_issue: SHA-36
title: Deferred — reconstruction_capacity authority drift and L6 validation stub
priority: Low
labels:
  - bug
  - solver
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Deferred low-priority items from SHA-36 priority breakdown

## Source Issue

- Linear: SHA-36
- Status at planning time: In Progress
- Priority: Low (deferred; not in SHA-36 implementation scope)

## Problem

SHA-36 priority breakdown lists two low-severity follow-ups that are explicitly excluded from the Mid fix:

1. `reconstruction_capacity.by_resource.authority` drift (`game_data_snapshot` vs `MiningExtractionRule`) — CLI `_capacity_summary` hardcodes `authority="game_data_snapshot"` in `run_stack.py` line 93.
2. L6 validation stub — `validation_passed` conflates stack success with real L6 checks (SHA-15).

## Scope

**No implementation in SHA-36.** This plan documents tracking only:

- Authority drift: open a separate issue or fold into SHA-28 provenance work if product wants unified provenance semantics.
- L6 stub: implement via SHA-15 (`plans/mid/2026-06-10-SHA-15-validation-passed-semantics.md`).

## Non-goals

- Do not change `RunStackUseCase` authority strings while fixing L1 observability.
- Do not implement L6 validation in this track.

## Implementation Plan

1. After SHA-36 Mid plan lands, confirm Lab UI `_completed_layer_slugs_from_summary` heuristics still needed or removable.
2. If authority drift still matters, file/track dedicated issue with acceptance: `by_resource.*.authority` matches Django `MiningExtractionRule` source.
3. Execute SHA-15 for L6 `validation_passed` semantics.

## Files / Areas Likely Affected

- `src/shapez2_factory/application/asteroid_lab/run_stack.py` (`_capacity_summary` authority) — future issue
- SHA-15 files per existing plan — separate track

## Validation Plan

- lint: N/A (deferred)
- typecheck: N/A
- tests: N/A until dedicated issues implemented
- build: N/A
- manual verification: compare Django vs CLI `reconstruction_capacity.by_resource.shape.authority` after Mid fix

## Acceptance Criteria

- [ ] Matches the source issue spec (deferred items acknowledged, not silently dropped).
- [ ] Stays within the priority scope (no implementation here).
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Lab UI may keep heuristics until both L1 artifact truth (SHA-36 Mid) and authority provenance (future) land.
- SHA-15 product decision (false vs pending) still open.
