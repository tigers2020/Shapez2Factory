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

# Plan: reconstruction_capacity authority drift and L6 validation stub (deferred)

## Source Issue

- Linear: SHA-36
- Status at planning time: In Progress
- Priority: Low (deferred from SHA-36 non-goals)

## Problem

Two related observability gaps were noted in SHA-36's priority breakdown but explicitly excluded from the mid-priority fix:

1. `reconstruction_capacity.by_resource.authority` is hardcoded to `"game_data_snapshot"` in CLI `_capacity_summary` while Django may use `MiningExtractionRule` authority semantics.
2. L6 `validation_passed` conflates stack success with real commit-validate (SHA-15).

## Scope

Document and track only. No implementation in this plan file unless a follow-up issue is opened.

## Non-goals

- Fixing authority drift in SHA-36 mid-priority work.
- Implementing L6 commit-validate (see SHA-15 plan: `plans/mid/2026-06-10-SHA-15-validation-passed-semantics.md`).

## Implementation Plan

1. After SHA-36 mid plan lands, verify whether Lab UI or ingest paths depend on `authority` field value.
2. If drift causes user-visible mismatch, open a dedicated issue (or extend SHA-28 provenance work).
3. Track L6 validation semantics via SHA-15; do not bundle into SHA-36.

## Files / Areas Likely Affected

- `src/shapez2_factory/application/asteroid_lab/run_stack.py` (`_capacity_summary` authority field)
- `django_apps/asteroid_lab/services/solver_run_lab_summary.py` (heuristic L1 completion)
- SHA-15: `run_stack.py` validation_passed semantics

## Validation Plan

- lint: N/A (deferred)
- typecheck: N/A (deferred)
- tests: N/A (deferred)
- build: N/A (deferred)
- manual verification: Compare CLI vs Django `reconstruction_capacity.by_resource.*.authority` on same fixture after SHA-36 mid fix.

## Acceptance Criteria

- [ ] Deferred items remain out of SHA-36 mid scope.
- [ ] Follow-up tracking documented if drift is user-visible.
- [ ] SHA-15 remains the owner for L6 validation semantics.

## Risks / Open Questions

- Lab UI `_completed_layer_slugs_from_summary` heuristics may mask authority drift until artifacts are canonical.
- Bundling authority fix into SHA-36 would expand scope beyond observability contract alignment.
