---
linear_issue: SHA-32
title: L4 inner fill ignores LayerBudgetContext during routeable inner group placement
priority: Low
labels:
  - bug
  - performance
  - priority:mid
status: planned
created_by: todo-plan-automation
---

# Plan: L4 routeable inner group budget telemetry (SHA-32 Low)

## Source Issue

- Linear: SHA-32
- Status at planning time: Todo
- Priority: Low

## Problem

After Mid-priority budget polling in `place_routeable_inner_groups`, layer summaries may not clearly distinguish budget truncation from placement failure.

## Scope

Budget telemetry and logging improvements for L4 routeable inner group phase.

## Non-goals

- No placement algorithm changes.
- No schema contract changes unless required for observability fields already used elsewhere.

## Implementation Plan

1. After Mid plan lands, review layer summary fields for routeable phase completion.
2. Add explicit budget-exhausted marker when `place_routeable_inner_groups` stops early.
3. Update inline docstring in `inner_routeable_group.py` describing budget behavior.

## Files / Areas Likely Affected

- `src/shapez2_factory/application/asteroid_lab/layers/layer_05_inner_pattern_fill/inner_routeable_group.py`
- TBD — layer summary types if extended

## Validation Plan

- lint: `ruff check` on touched files
- typecheck: spot-check
- tests: assert budget marker in unit test when budget forced low
- build: N/A
- manual verification: Layer summary shows budget stop reason

## Acceptance Criteria

- [ ] Matches the source issue spec.
- [ ] Stays within the priority scope.
- [ ] Required validation passes or failures are documented.
- [ ] No unrelated behavior is changed.
- [ ] Remaining risks are reported.

## Risks / Open Questions

- Depends on Mid plan completion.
- Keep telemetry consistent with SHA-31 Low polish if both land together.
