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

# Plan: Layer skip-reason enum refactor (SHA-34 Low)

## Source Issue

- Linear: SHA-34
- Status at planning time: Todo
- Priority: Low

## Problem

After Mid-priority L2 nil-plan fail-closed lands, layer skip reasons remain inconsistent across layers (e.g. L3 `MISSING_EXTERIOR_CONNECTION_PLAN` vs stack-level `COMPLETED` stub metrics). A cross-layer skip-reason enum refactor would unify observability but is explicitly deferred from the Mid scope.

## Scope

- Document and optionally normalize layer skip-reason enums and stack outcome mapping across L2–L6.
- Align skip-reason metadata in layer summaries and replay frames with fail-closed stack status.

## Non-goals

- Changing L2 nil-plan fail-closed behavior (Mid plan).
- Implementing L6 validation stub fix (SHA-15).
- Altering core layer algorithm behavior.

## Implementation Plan

1. Inventory skip-reason constants across `src/shapez2_factory/application/asteroid_lab/layers/` (start with L2 `run.py`, L3 `layer_03_rim_greedy_placement/run.py` L68–72).
2. Propose shared skip-reason taxonomy in observability layer (`layers/observability/layer_behavior_catalog.py` or equivalent).
3. Update stack_runner outcome mapping so skip reasons propagate to `solver_summary.layer_summaries` and replay `layer_done` frames consistently.
4. Add regression tests in `tests/unit/asteroid_lab/layers/` covering skip-reason emission when upstream plan is missing.

## Files / Areas Likely Affected

- `src/shapez2_factory/application/asteroid_lab/layers/layer_03_rim_greedy_placement/run.py`
- `src/shapez2_factory/application/asteroid_lab/layers/observability/layer_behavior_catalog.py`
- `src/shapez2_factory/application/asteroid_lab/stack_runner.py`
- TBD — shared skip-reason enum module if introduced

## Validation Plan

- lint: `ruff check src/shapez2_factory/application/asteroid_lab/layers/`
- typecheck: spot-check if enum/types change
- tests: `pytest tests/unit/asteroid_lab/layers/ -v`
- build: N/A
- manual verification: Lab UI layer summary shows consistent skip reason after upstream L2 failure

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Depends on Mid plan (L2 fail-closed) landing first; defer if Mid not merged.
- Broad enum refactor may touch many layers — keep PR-sized to observability mapping only.
