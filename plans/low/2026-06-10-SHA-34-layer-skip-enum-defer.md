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

# Plan: Deferred layer skip-reason and L6 validation work (SHA-34 Low)

## Source Issue

- Linear: SHA-34
- Status at planning time: In Progress
- Priority: Low

## Problem

SHA-34 Mid fix addresses the immediate fail-open orchestration bug. Two related improvements remain explicitly out of scope for the Mid slice:

1. **L6 validation stub** — `RunStackUseCase` may still report misleading `validation_passed` when L6 is a no-op ([SHA-15](https://linear.app/zkaufman/issue/SHA-15)).
2. **Layer skip-reason enum consistency** — Downstream layers use ad-hoc `layer_skip_reason` strings (e.g. L3 `MISSING_EXTERIOR_CONNECTION_PLAN`) without a unified cross-layer enum.

## Scope

Document and track deferred work only. No implementation in this plan file unless explicitly scheduled in a follow-up issue.

## Non-goals

- Implementing full L6 commit-validate validation.
- Broad refactor of all layer skip-reason enums in the SHA-34 Mid PR.

## Implementation Plan

1. After Mid fix lands, confirm L3+ no longer run when L2 fails closed (stack stops early).
2. If L6 `validation_passed` false positives remain, execute [SHA-15](https://linear.app/zkaufman/issue/SHA-15) Mid plan (`plans/mid/2026-06-10-SHA-15-validation-passed-semantics.md`).
3. If cross-layer skip telemetry needs standardization, open a dedicated refactor issue enumerating all `layer_skip_reason` values — do not expand SHA-34 Mid scope.

## Files / Areas Likely Affected

- TBD — follow-up issues SHA-15 and future skip-reason refactor
- Reference: `src/shapez2_factory/application/asteroid_lab/layers/layer_03_rim_greedy_placement/run.py`
- Reference: `src/shapez2_factory/application/asteroid_lab/layers/layer_06_commit_validate/run.py`

## Validation Plan

- lint: N/A (deferred)
- typecheck: N/A (deferred)
- tests: N/A (deferred)
- build: N/A (deferred)
- manual verification: After Mid fix, confirm stack stops at L2 and downstream skip reasons are not silently emitted on SUCCESS runs

## Acceptance Criteria

- [ ] Matches the source issue spec (Low items explicitly deferred, not blocking Mid).
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Deferring enum refactor may leave heterogeneous skip-reason strings in layer metrics/logs — acceptable until dedicated issue.
- SHA-15 should be prioritized if Lab UI still shows `validation_passed=true` on stacks that fail at L2 after Mid fix (should not occur if `run_ok` derives from `failed_layer_slug`).
