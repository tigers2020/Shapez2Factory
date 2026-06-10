---
linear_issue: SHA-32
title: L4 inner fill ignores LayerBudgetContext during routeable inner group placement
priority: Mid
labels:
  - bug
  - performance
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: Add budget polling to L4 place_routeable_inner_groups

## Source Issue

- Linear: SHA-32
- Status at planning time: Todo
- Priority: Mid

## Problem

Layer 04 inner pattern fill (`layer_05_inner_pattern_fill`) accepts `LayerBudgetContext` from `stack_runner` and polls remaining budget only in the 1×1 greedy placement loop. The preceding `place_routeable_inner_groups` phase runs up to `max_inner_routeable` iterations without any budget polling.

## Scope

- Add budget polling to `place_routeable_inner_groups` phase.
- Ensure consistent budget enforcement across all L4 placement loops.

## Non-goals

- Changing inner group placement algorithm beyond budget enforcement.
- Altering `max_inner_routeable` derivation.

## Implementation Plan

1. Read `layer_05_inner_pattern_fill` (or current L4 module path) and locate `place_routeable_inner_groups` and the 1×1 greedy loop that already polls budget.
2. Pass `LayerBudgetContext` into `place_routeable_inner_groups` if not already threaded.
3. Poll `remaining_budget` (or equivalent API) before each iteration and candidate scan in routeable inner group phase; early-exit with partial result when exhausted.
4. Mirror budget polling pattern from existing 1×1 loop for consistency.
5. Add regression test on large maps (e.g. many inner routeable groups) verifying L5+ layers still receive budget or stack fails gracefully within budget.
6. Run targeted layer tests: `pytest tests/unit/ -k 'inner_pattern or layer_04 or layer_05' -v` (adjust to actual test module names).

## Files / Areas Likely Affected

- `src/shapez2_factory/application/asteroid_lab/layers/` — L4 inner pattern fill module (grep `place_routeable_inner_groups`)
- `LayerBudgetContext` definition module (TBD — grep under `src/shapez2_factory/`)
- `stack_runner` (read-only — verify context threading)
- New or extended unit tests under `tests/unit/`

## Validation Plan

- lint: `ruff check src/shapez2_factory/application/asteroid_lab/layers/`
- typecheck: `mypy django_apps config src`
- tests: layer budget regression tests
- build: N/A
- manual verification: Large-map stack run does not exhaust budget entirely in L4 routeable phase

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Module naming (`layer_05_inner_pattern_fill` for L4 work) — verify against current layer numbering canon.
- Related SHA-31/SHA-14 budget gaps may need coordinated testing.
